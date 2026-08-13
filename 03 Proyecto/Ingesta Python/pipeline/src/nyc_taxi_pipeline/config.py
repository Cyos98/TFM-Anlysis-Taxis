"""Carga y validación de la configuración del pipeline."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
import os
from pathlib import Path
import tomllib


SUPPORTED_SERVICES = ("yellow", "green", "fhv", "fhvhv")


class ConfigurationError(ValueError):
    """Indica que la configuración no permite una ejecución segura."""


@dataclass(frozen=True)
class PathsConfig:
    data_root: Path
    logs_root: Path
    sql_root: Path


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class TlcSourceConfig:
    index_url: str
    timeout_seconds: int
    max_retries: int
    chunk_size_bytes: int
    probe_workers: int
    download_workers: int
    minimum_free_space_ratio: float
    retry_backoff_seconds: int
    download_start_interval_seconds: int


@dataclass(frozen=True)
class ModeConfig:
    start_date: date
    end_date: date | None
    services: tuple[str, ...]
    max_files_per_service: int


@dataclass(frozen=True)
class AppConfig:
    project_name: str
    environment: str
    paths: PathsConfig
    database: DatabaseConfig
    tlc_source: TlcSourceConfig
    demo: ModeConfig
    full: ModeConfig
    source_path: Path


def _parse_date(value: str | None, field_name: str, *, required: bool) -> date | None:
    normalized = (value or "").strip()
    if not normalized:
        if required:
            raise ConfigurationError(f"Falta la fecha obligatoria: {field_name}")
        return None
    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise ConfigurationError(
            f"{field_name} debe usar el formato YYYY-MM-DD: {normalized!r}"
        ) from exc


def _load_mode(raw: dict[str, object], mode_name: str) -> ModeConfig:
    services = tuple(str(service).lower() for service in raw.get("services", []))
    if not services:
        raise ConfigurationError(f"El modo {mode_name!r} no define servicios")
    unknown = sorted(set(services) - set(SUPPORTED_SERVICES))
    if unknown:
        raise ConfigurationError(
            f"Servicios no soportados en {mode_name}: {', '.join(unknown)}"
        )

    start_date = _parse_date(
        str(raw.get("start_date", "")),
        f"modes.{mode_name}.start_date",
        required=True,
    )
    end_date = _parse_date(
        str(raw.get("end_date", "")),
        f"modes.{mode_name}.end_date",
        required=False,
    )
    max_files = int(raw.get("max_files_per_service", 0))
    if max_files < 0:
        raise ConfigurationError("max_files_per_service no puede ser negativo")

    assert start_date is not None
    if end_date is not None and end_date < start_date:
        raise ConfigurationError(
            f"La fecha final de {mode_name} no puede ser anterior a la inicial"
        )
    return ModeConfig(start_date, end_date, services, max_files)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Carga TOML y aplica overrides seguros mediante variables de entorno."""

    selected_path = Path(
        config_path or os.getenv("TFM_CONFIG_PATH", "configs/pipeline.toml")
    ).resolve()
    if not selected_path.is_file():
        raise ConfigurationError(f"No existe el fichero de configuración: {selected_path}")

    with selected_path.open("rb") as stream:
        raw = tomllib.load(stream)

    project = raw.get("project", {})
    paths = raw.get("paths", {})
    database = raw.get("database", {})
    sources = raw.get("sources", {})
    modes = raw.get("modes", {})
    if not isinstance(project, dict) or not isinstance(paths, dict):
        raise ConfigurationError("Las secciones project y paths deben ser tablas TOML")
    if not isinstance(database, dict) or not isinstance(sources, dict):
        raise ConfigurationError("Las secciones database y sources deben ser tablas TOML")
    if not isinstance(modes, dict):
        raise ConfigurationError("La sección modes debe ser una tabla TOML")

    tlc_source = sources.get("tlc", {})
    if not isinstance(tlc_source, dict):
        raise ConfigurationError("Debe existir la tabla sources.tlc")

    demo_raw = modes.get("demo", {})
    full_raw = modes.get("full", {})
    if not isinstance(demo_raw, dict) or not isinstance(full_raw, dict):
        raise ConfigurationError("Deben existir las tablas modes.demo y modes.full")

    db_port = int(os.getenv("TFM_DATABASE_PORT", str(database.get("port", 5432))))
    if not 1 <= db_port <= 65535:
        raise ConfigurationError("TFM_DATABASE_PORT debe estar entre 1 y 65535")

    return AppConfig(
        project_name=str(project.get("name", "tfm-nyc-mobility-platform")),
        environment=os.getenv(
            "TFM_ENVIRONMENT", str(project.get("environment", "local"))
        ),
        paths=PathsConfig(
            data_root=Path(
                os.getenv("TFM_DATA_ROOT", str(paths.get("data_root", "data")))
            ),
            logs_root=Path(
                os.getenv("TFM_LOGS_ROOT", str(paths.get("logs_root", "logs")))
            ),
            sql_root=Path(
                os.getenv("TFM_SQL_ROOT", str(paths.get("sql_root", "sql/init")))
            ),
        ),
        database=DatabaseConfig(
            host=os.getenv("TFM_DATABASE_HOST", str(database.get("host", "postgres"))),
            port=db_port,
            name=os.getenv("POSTGRES_DB", str(database.get("name", "tfm_mobility"))),
            user=os.getenv("POSTGRES_USER", str(database.get("user", "tfm"))),
            password=os.getenv("POSTGRES_PASSWORD", ""),
        ),
        tlc_source=TlcSourceConfig(
            index_url=os.getenv(
                "TFM_TLC_INDEX_URL",
                str(tlc_source.get("index_url", "")),
            ),
            timeout_seconds=int(tlc_source.get("timeout_seconds", 30)),
            max_retries=int(tlc_source.get("max_retries", 3)),
            chunk_size_bytes=int(tlc_source.get("chunk_size_bytes", 1_048_576)),
            probe_workers=int(tlc_source.get("probe_workers", 8)),
            download_workers=int(tlc_source.get("download_workers", 4)),
            minimum_free_space_ratio=float(
                tlc_source.get("minimum_free_space_ratio", 1.20)
            ),
            retry_backoff_seconds=int(tlc_source.get("retry_backoff_seconds", 60)),
            download_start_interval_seconds=int(
                tlc_source.get("download_start_interval_seconds", 3)
            ),
        ),
        demo=_load_mode(demo_raw, "demo"),
        full=_load_mode(full_raw, "full"),
        source_path=selected_path,
    )


def resolve_mode(
    config: AppConfig,
    mode: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ModeConfig:
    """Resuelve fechas de CLI sobre la configuración y valida el intervalo."""

    if mode not in {"demo", "full"}:
        raise ConfigurationError(f"Modo no soportado: {mode}")
    selected = config.demo if mode == "demo" else config.full
    resolved_start = (
        _parse_date(start_date, "start_date", required=True)
        if start_date
        else selected.start_date
    )
    resolved_end = (
        _parse_date(end_date, "end_date", required=True)
        if end_date
        else selected.end_date
    )

    if mode == "full" and resolved_end is None:
        raise ConfigurationError(
            "El modo full exige --end-date; la fecha final no se codifica de forma rígida"
        )
    assert resolved_start is not None
    if resolved_end is not None and resolved_end < resolved_start:
        raise ConfigurationError("end_date no puede ser anterior a start_date")
    return replace(selected, start_date=resolved_start, end_date=resolved_end)
