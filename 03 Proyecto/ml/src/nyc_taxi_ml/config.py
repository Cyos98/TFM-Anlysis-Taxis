"""Configuración mínima del servicio ML."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


SUPPORTED_SERVICES = ("yellow", "green", "fhv", "fhvhv")


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig
    sql_root: Path
    artifacts_root: Path


def load_config() -> AppConfig:
    port = int(os.getenv("TFM_DATABASE_PORT", "5432"))
    if not 1 <= port <= 65535:
        raise ValueError("TFM_DATABASE_PORT debe estar entre 1 y 65535")
    return AppConfig(
        database=DatabaseConfig(
            host=os.getenv("TFM_DATABASE_HOST", "postgres"),
            port=port,
            name=os.getenv("POSTGRES_DB", "tfm_mobility"),
            user=os.getenv("POSTGRES_USER", "tfm"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
        ),
        sql_root=Path(os.getenv("TFM_SQL_ROOT", "/app/sql/init")),
        artifacts_root=Path(os.getenv("TFM_ML_ARTIFACTS_ROOT", "/app/ml/artifacts")),
    )
