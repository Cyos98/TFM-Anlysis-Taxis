"""Inicialización idempotente de las tablas propias de ML."""

from __future__ import annotations

import psycopg

from nyc_taxi_ml.config import AppConfig


def connection_args(config: AppConfig) -> dict[str, object]:
    return {
        "host": config.database.host,
        "port": config.database.port,
        "dbname": config.database.name,
        "user": config.database.user,
        "password": config.database.password,
        "connect_timeout": 5,
    }


def apply_ml_migration(config: AppConfig) -> None:
    migration = config.sql_root / "004_create_ml.sql"
    if not migration.is_file():
        raise FileNotFoundError(f"No existe la migración ML: {migration}")
    with psycopg.connect(**connection_args(config)) as connection:
        connection.execute(migration.read_text(encoding="utf-8"), prepare=False)
