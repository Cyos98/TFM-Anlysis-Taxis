"""Orquestación idempotente de discovery, Bronze y calidad."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
from typing import Any
from uuid import UUID, uuid4

from nyc_taxi_pipeline import __version__
from nyc_taxi_pipeline.config import AppConfig, ModeConfig, resolve_mode
from nyc_taxi_pipeline.control import ControlRepository
from nyc_taxi_pipeline.discovery import discover_tlc_files, probe_remote_files
from nyc_taxi_pipeline.models import SourceFile, StoredFile
from nyc_taxi_pipeline.quality import QualityCheck, ValidationReport, validate_parquet
from nyc_taxi_pipeline.samples import demo_source_files, materialize_demo_file
from nyc_taxi_pipeline.storage import (
    bronze_path,
    download_atomic,
    inspect_file,
    quarantine_file,
)


class PipelineExecutionError(RuntimeError):
    """La ejecución no puede completarse manteniendo sus garantías."""


def _discover(config: AppConfig, mode_name: str, mode: ModeConfig) -> list[SourceFile]:
    files = (
        demo_source_files(mode)
        if mode_name == "demo"
        else discover_tlc_files(config.tlc_source, mode)
    )
    discovered_services = {item.service_type for item in files}
    missing_services = sorted(set(mode.services) - discovered_services)
    if missing_services:
        raise PipelineExecutionError(
            "No se descubrieron ficheros para: " + ", ".join(missing_services)
        )
    if not files:
        raise PipelineExecutionError("El discovery no devolvió ningún fichero")
    return files


def _validate_and_persist(
    repository: ControlRepository,
    run_id: UUID,
    file_id: int,
    source_file: SourceFile,
    stored_file: StoredFile,
) -> ValidationReport:
    try:
        report = validate_parquet(stored_file.path, source_file.service_type)
    except Exception as exc:
        repository.record_quality_checks(
            run_id,
            file_id,
            (
                QualityCheck(
                    "parquet_readable",
                    "FAIL",
                    type(exc).__name__,
                    "Parquet legible",
                    {"message": str(exc)},
                ),
            ),
        )
        raise PipelineExecutionError(
            f"No se puede leer {source_file.filename} como Parquet"
        ) from exc
    repository.record_quality_checks(run_id, file_id, report.checks)
    if not report.is_valid:
        raise PipelineExecutionError(
            f"El fichero {source_file.filename} no supera la validación Bronze"
        )
    repository.mark_downloaded(file_id, run_id, stored_file)
    repository.mark_validated(file_id, run_id, report.row_count)
    return report


def _process_file(
    repository: ControlRepository,
    config: AppConfig,
    run_id: UUID,
    source_file: SourceFile,
) -> dict[str, object]:
    row = repository.register_file(run_id, source_file)
    file_id = int(row["file_id"])
    destination = bronze_path(config.paths.data_root, source_file)
    action = "generated" if source_file.source_kind == "demo" else "downloaded"

    if destination.is_file():
        existing = inspect_file(destination)
        registered_hash = row.get("sha256")
        if registered_hash and registered_hash != existing.sha256:
            repository.record_quality_checks(
                run_id,
                file_id,
                (
                    QualityCheck(
                        "sha256_matches_registry",
                        "FAIL",
                        existing.sha256,
                        str(registered_hash),
                        {"action": "quarantined_and_recovered"},
                    ),
                ),
            )
            quarantine_file(config.paths.data_root, destination)
        else:
            if registered_hash:
                repository.record_quality_checks(
                    run_id,
                    file_id,
                    (
                        QualityCheck(
                            "sha256_matches_registry",
                            "PASS",
                            existing.sha256,
                            str(registered_hash),
                            {},
                        ),
                    ),
                )
            try:
                report = _validate_and_persist(
                    repository,
                    run_id,
                    file_id,
                    source_file,
                    existing,
                )
                action = "reused" if row.get("status") == "VALIDATED" else "adopted"
                return {
                    "action": action,
                    "file_id": file_id,
                    "rows": report.row_count,
                    "bytes": existing.size_bytes,
                    "sha256": existing.sha256,
                }
            except Exception:
                quarantine_file(config.paths.data_root, destination)

    stored = (
        materialize_demo_file(source_file, destination)
        if source_file.source_kind == "demo"
        else download_atomic(source_file, destination, config.tlc_source)
    )
    try:
        report = _validate_and_persist(
            repository,
            run_id,
            file_id,
            source_file,
            stored,
        )
    except Exception:
        if stored.path.is_file():
            quarantine_file(config.paths.data_root, stored.path)
        raise
    return {
        "action": action,
        "file_id": file_id,
        "rows": report.row_count,
        "bytes": stored.size_bytes,
        "sha256": stored.sha256,
    }


def _process_file_task(
    repository: ControlRepository,
    config: AppConfig,
    run_id: UUID,
    source_file: SourceFile,
) -> tuple[SourceFile, dict[str, object]]:
    task_id = repository.start_task(
        run_id,
        f"ingest:{source_file.filename}",
        source_file.service_type,
    )
    try:
        metrics = _process_file(repository, config, run_id, source_file)
        task_status = "SKIPPED" if metrics["action"] == "reused" else "SUCCEEDED"
        repository.finish_task(task_id, task_status, metrics)
        return source_file, metrics
    except Exception as exc:
        registered = repository.register_file(run_id, source_file)
        repository.mark_file_failed(int(registered["file_id"]), run_id, str(exc))
        repository.finish_task(task_id, "FAILED", error_message=str(exc))
        raise


def _preflight_full_download(
    repository: ControlRepository,
    config: AppConfig,
    run_id: UUID,
    source_files: list[SourceFile],
) -> dict[str, object]:
    task_id = repository.start_task(run_id, "preflight_download")
    try:
        manifest_path = config.paths.logs_root / "tlc_download_plan.json"
        planned_sizes: dict[str, int] = {}
        size_source = "remote_probe"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                planned_sizes = {
                    str(item["source_url"]): int(item["size_bytes"])
                    for item in manifest.get("inventory", [])
                    if item.get("size_bytes") is not None
                }
                expected_urls = {item.source_url for item in source_files}
                if set(planned_sizes) != expected_urls:
                    planned_sizes = {}
                else:
                    size_source = "validated_manifest"
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                planned_sizes = {}
        if not planned_sizes:
            probes = probe_remote_files(source_files, config.tlc_source)
            failed_probes = [probe for probe in probes if probe.size_bytes is None]
            if failed_probes:
                raise PipelineExecutionError(
                    f"No se pudo obtener el tamaño de {len(failed_probes)} ficheros"
                )
            planned_sizes = {
                probe.source_file.source_url: int(probe.size_bytes or 0)
                for probe in probes
            }
        config.paths.data_root.mkdir(parents=True, exist_ok=True)
        missing_urls = {
            source_file.source_url
            for source_file in source_files
            if not bronze_path(config.paths.data_root, source_file).is_file()
        }
        remaining_bytes = sum(
            size
            for source_url, size in planned_sizes.items()
            if source_url in missing_urls
        )
        free_bytes = shutil.disk_usage(config.paths.data_root).free
        required_bytes = int(
            remaining_bytes * config.tlc_source.minimum_free_space_ratio
        )
        metrics: dict[str, object] = {
            "inventory_files": len(source_files),
            "remaining_files": len(missing_urls),
            "remaining_bytes": remaining_bytes,
            "free_bytes": free_bytes,
            "required_bytes_with_margin": required_bytes,
            "size_source": size_source,
        }
        if free_bytes < required_bytes:
            raise PipelineExecutionError(
                "Espacio insuficiente: "
                f"libre={free_bytes}, requerido_con_margen={required_bytes}"
            )
        repository.finish_task(task_id, "SUCCEEDED", metrics)
        return metrics
    except Exception as exc:
        repository.finish_task(task_id, "FAILED", error_message=str(exc))
        raise


def execute_pipeline(
    config: AppConfig,
    mode_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Ejecuta Bronze y devuelve métricas sin exponer secretos."""

    mode = resolve_mode(config, mode_name, start_date, end_date)
    assert mode.end_date is not None
    repository = ControlRepository(config.database)
    applied_migrations = repository.apply_migrations(config.paths.sql_root)
    run_id = uuid4()
    code_version = os.getenv("TFM_CODE_VERSION", __version__)
    parameters: dict[str, object] = {
        "services": list(mode.services),
        "max_files_per_service": mode.max_files_per_service,
        "source_kind": "demo" if mode_name == "demo" else "tlc",
    }
    repository.start_run(
        run_id,
        mode_name,
        mode.start_date,
        mode.end_date,
        parameters,
        code_version,
    )

    summary: dict[str, Any] = {
        "event": "pipeline_run_completed",
        "run_id": str(run_id),
        "mode": mode_name,
        "start_date": mode.start_date.isoformat(),
        "end_date": mode.end_date.isoformat(),
        "migrations_applied": applied_migrations,
        "files": [],
        "counts": {"generated": 0, "downloaded": 0, "adopted": 0, "reused": 0},
        "bytes_processed": 0,
    }

    try:
        discovery_task = repository.start_task(run_id, "discover")
        try:
            source_files = _discover(config, mode_name, mode)
            repository.finish_task(
                discovery_task,
                "SUCCEEDED",
                {"files_discovered": len(source_files)},
            )
        except Exception as exc:
            repository.finish_task(discovery_task, "FAILED", error_message=str(exc))
            raise

        if mode_name == "full":
            summary["preflight"] = _preflight_full_download(
                repository,
                config,
                run_id,
                source_files,
            )

        workers = config.tlc_source.download_workers if mode_name == "full" else 1
        failures: list[str] = []
        completed = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _process_file_task,
                    repository,
                    config,
                    run_id,
                    source_file,
                ): source_file
                for source_file in source_files
            }
            for future in as_completed(futures):
                source_file = futures[future]
                try:
                    completed_source, metrics = future.result()
                    completed += 1
                    action = str(metrics["action"])
                    summary["counts"][action] += 1
                    summary["bytes_processed"] += int(metrics["bytes"])
                    if mode_name == "demo":
                        summary["files"].append(
                            {
                                "service_type": completed_source.service_type,
                                "filename": completed_source.filename,
                                **metrics,
                            }
                        )
                    print(
                        json.dumps(
                            {
                                "event": "file_completed",
                                "run_id": str(run_id),
                                "completed": completed,
                                "total": len(source_files),
                                "service_type": completed_source.service_type,
                                "filename": completed_source.filename,
                                "action": action,
                                "bytes": metrics["bytes"],
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        flush=True,
                    )
                except Exception as exc:
                    completed += 1
                    failures.append(f"{source_file.filename}: {exc}")
                    print(
                        json.dumps(
                            {
                                "event": "file_failed",
                                "run_id": str(run_id),
                                "completed": completed,
                                "total": len(source_files),
                                "filename": source_file.filename,
                                "message": str(exc),
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        flush=True,
                    )

        if failures:
            raise PipelineExecutionError(
                f"Fallaron {len(failures)} ficheros; primer error: {failures[0]}"
            )

        repository.finish_run(run_id, "SUCCEEDED")
        summary["files_processed"] = completed
        if mode_name == "full":
            summary.pop("files", None)
        return summary
    except Exception as exc:
        repository.finish_run(run_id, "FAILED", str(exc))
        raise
