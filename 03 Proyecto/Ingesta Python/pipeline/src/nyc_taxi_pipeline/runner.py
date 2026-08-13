"""Coordinación mínima de la fase de fundación."""

from __future__ import annotations

from datetime import UTC, datetime
import socket
from typing import Any

from nyc_taxi_pipeline.config import AppConfig, resolve_mode


class DatabaseUnavailableError(ConnectionError):
    """La base de datos configurada no acepta conexiones TCP."""


def check_database(config: AppConfig, timeout_seconds: float = 3.0) -> None:
    """Comprueba conectividad TCP sin exponer ni registrar credenciales."""

    target = (config.database.host, config.database.port)
    try:
        with socket.create_connection(target, timeout=timeout_seconds):
            return
    except OSError as exc:
        raise DatabaseUnavailableError(
            f"PostgreSQL no está disponible en {target[0]}:{target[1]}"
        ) from exc


def build_execution_plan(
    config: AppConfig,
    mode: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    selected = resolve_mode(config, mode, start_date, end_date)
    return {
        "event": "pipeline_foundation_ready",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "project": config.project_name,
        "environment": config.environment,
        "mode": mode,
        "start_date": selected.start_date.isoformat(),
        "end_date": selected.end_date.isoformat() if selected.end_date else None,
        "services": list(selected.services),
        "max_files_per_service": selected.max_files_per_service,
        "data_root": str(config.paths.data_root),
        "database": {
            "host": config.database.host,
            "port": config.database.port,
            "name": config.database.name,
            "user": config.database.user,
        },
        "implemented_phase": 1,
        "message": (
            "Configuración y conectividad validadas. La ingesta se implementará "
            "en la fase 2."
        ),
    }
