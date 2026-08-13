"""Interfaz de línea de comandos del pipeline."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import signal
import sys
from threading import Event

import psycopg

from nyc_taxi_pipeline import __version__
from nyc_taxi_pipeline.config import ConfigurationError, load_config, resolve_mode
from nyc_taxi_pipeline.control import ControlRepository
from nyc_taxi_pipeline.discovery import discover_tlc_files, probe_remote_files
from nyc_taxi_pipeline.landing import load_landing
from nyc_taxi_pipeline.ml import train_demand_models
from nyc_taxi_pipeline.orchestrator import PipelineExecutionError, execute_pipeline
from nyc_taxi_pipeline.samples import demo_source_files


def _emit(payload: dict[str, object], *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=stream)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tfm-pipeline",
        description="Pipeline reproducible de movilidad NYC",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--config",
        help="Ruta al fichero TOML (por defecto TFM_CONFIG_PATH o configs/pipeline.toml)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "validate-config", help="Valida la configuración sin ejecutar el pipeline"
    )

    subparsers.add_parser(
        "migrate", help="Aplica de forma idempotente las migraciones SQL pendientes"
    )

    landing_parser = subparsers.add_parser(
        "load-landing", help="Carga columnas comunes de Bronze validado en PostgreSQL"
    )
    landing_parser.add_argument(
        "--source-kind", choices=("demo", "tlc"), default="demo"
    )

    ml_parser = subparsers.add_parser(
        "train-ml", help="Entrena y evalúa modelos de demanda con corte temporal"
    )
    ml_parser.add_argument("--mode", choices=("demo", "full"), default="demo")

    for command, help_text in (
        ("discover", "Descubre ficheros sin descargarlos"),
        ("plan", "Calcula número y tamaño remoto sin descargar Parquet"),
        ("run", "Ejecuta discovery, Bronze, calidad y auditoría"),
    ):
        command_parser = subparsers.add_parser(command, help=help_text)
        command_parser.add_argument("--mode", choices=("demo", "full"), required=True)
        command_parser.add_argument("--start-date", help="Fecha inicial YYYY-MM-DD")
        command_parser.add_argument("--end-date", help="Fecha final YYYY-MM-DD")

    subparsers.add_parser(
        "service", help="Mantiene el contenedor preparado para ejecuciones manuales"
    )
    return parser


def _run_service() -> int:
    stop_event = Event()

    def request_stop(_signum: int, _frame: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    _emit({"event": "pipeline_service_ready", "version": __version__})
    stop_event.wait()
    _emit({"event": "pipeline_service_stopped"})
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate-config":
            _emit(
                {
                    "event": "configuration_valid",
                    "config": str(config.source_path),
                    "environment": config.environment,
                }
            )
            return 0
        if args.command == "service":
            return _run_service()
        if args.command == "migrate":
            applied = ControlRepository(config.database).apply_migrations(
                config.paths.sql_root
            )
            _emit({"event": "migrations_complete", "applied": applied})
            return 0
        if args.command == "load-landing":
            _emit(load_landing(config, args.source_kind))
            return 0
        if args.command == "train-ml":
            _emit(train_demand_models(config, args.mode))
            return 0
        if args.command == "discover":
            mode = resolve_mode(config, args.mode, args.start_date, args.end_date)
            files = (
                demo_source_files(mode)
                if args.mode == "demo"
                else discover_tlc_files(config.tlc_source, mode)
            )
            _emit(
                {
                    "event": "discovery_complete",
                    "mode": args.mode,
                    "file_count": len(files),
                    "files": [
                        {
                            "service_type": item.service_type,
                            "year": item.year,
                            "month": item.month,
                            "filename": item.filename,
                            "source_url": item.source_url,
                        }
                        for item in files
                    ],
                }
            )
            return 0
        if args.command == "plan":
            mode = resolve_mode(config, args.mode, args.start_date, args.end_date)
            if args.mode != "full":
                raise ConfigurationError("plan solo se utiliza con --mode full")
            files = discover_tlc_files(config.tlc_source, mode)
            probes = probe_remote_files(files, config.tlc_source)
            by_service: dict[str, dict[str, int]] = {}
            for service in mode.services:
                selected = [
                    probe
                    for probe in probes
                    if probe.source_file.service_type == service
                ]
                by_service[service] = {
                    "files": len(selected),
                    "bytes": sum(probe.size_bytes or 0 for probe in selected),
                    "unknown_sizes": sum(
                        1 for probe in selected if probe.size_bytes is None
                    ),
                }
            manifest = {
                "event": "download_plan_complete",
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "start_date": mode.start_date.isoformat(),
                "end_date": mode.end_date.isoformat() if mode.end_date else None,
                "files": len(probes),
                "bytes": sum(probe.size_bytes or 0 for probe in probes),
                "unknown_sizes": sum(
                    1 for probe in probes if probe.size_bytes is None
                ),
                "by_service": by_service,
                "inventory": [
                    {
                        "service_type": probe.source_file.service_type,
                        "year": probe.source_file.year,
                        "month": probe.source_file.month,
                        "filename": probe.source_file.filename,
                        "source_url": probe.source_file.source_url,
                        "size_bytes": probe.size_bytes,
                        "etag": probe.etag,
                        "last_modified": probe.last_modified,
                        "error": probe.error,
                    }
                    for probe in probes
                ],
            }
            manifest_path = config.paths.logs_root / "tlc_download_plan.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = Path(f"{manifest_path}.tmp")
            temp_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            temp_path.replace(manifest_path)
            _emit(
                {
                    key: value
                    for key, value in manifest.items()
                    if key != "inventory"
                }
                | {"manifest_path": str(manifest_path)}
            )
            return 0
        if args.command == "run":
            summary = execute_pipeline(
                config,
                args.mode,
                args.start_date,
                args.end_date,
            )
            _emit(summary)
            return 0
    except ConfigurationError as exc:
        _emit({"event": "configuration_error", "message": str(exc)}, error=True)
        return 2
    except psycopg.OperationalError as exc:
        _emit({"event": "database_unavailable", "message": str(exc)}, error=True)
        return 3
    except PipelineExecutionError as exc:
        _emit({"event": "pipeline_failed", "message": str(exc)}, error=True)
        return 4
    except Exception as exc:
        _emit({"event": "unexpected_error", "message": str(exc)}, error=True)
        return 1
    return 1
