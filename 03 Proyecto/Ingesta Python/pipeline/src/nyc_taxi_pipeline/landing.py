"""Carga incremental de columnas comunes desde Bronze Parquet a landing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import psycopg
from psycopg.rows import dict_row
import pyarrow.parquet as pq

from nyc_taxi_pipeline.config import AppConfig
from nyc_taxi_pipeline.control import ControlRepository


_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "pickup_datetime": (
        "tpep_pickup_datetime",
        "lpep_pickup_datetime",
        "pickup_datetime",
    ),
    "dropoff_datetime": (
        "tpep_dropoff_datetime",
        "lpep_dropoff_datetime",
        "dropOff_datetime",
        "dropoff_datetime",
    ),
    "pickup_location_id": ("PULocationID", "PUlocationID"),
    "dropoff_location_id": ("DOLocationID", "DOlocationID"),
    "trip_distance": ("trip_distance", "trip_miles"),
    "total_amount": ("total_amount", "base_passenger_fare"),
    "dispatching_base_num": ("dispatching_base_num",),
    "hvfhs_license_num": ("hvfhs_license_num",),
}


def normalize_bronze_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for target, aliases in _COLUMN_ALIASES.items():
        normalized[target] = next(
            (row.get(alias) for alias in aliases if row.get(alias) is not None),
            None,
        )
    return normalized


def _iter_rows(path: Path, batch_size: int = 10_000) -> Iterable[dict[str, Any]]:
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=batch_size):
        yield from batch.to_pylist()


def load_landing(config: AppConfig, source_kind: str = "demo") -> dict[str, object]:
    if source_kind not in {"demo", "tlc"}:
        raise ValueError("source_kind debe ser demo o tlc")
    repository = ControlRepository(config.database)
    migrations = repository.apply_migrations(config.paths.sql_root)
    connection_args = {
        "host": config.database.host,
        "port": config.database.port,
        "dbname": config.database.name,
        "user": config.database.user,
        "password": config.database.password,
        "connect_timeout": 5,
        "row_factory": dict_row,
    }
    files_loaded = 0
    rows_seen = 0
    with psycopg.connect(**connection_args) as connection:
        files = connection.execute(
            """
            SELECT file_id, service_type, filename, local_path
            FROM control.ingestion_files
            WHERE source_kind = %s AND status = 'VALIDATED'
            ORDER BY service_type, year, month
            """,
            (source_kind,),
        ).fetchall()
        for file_row in files:
            path = Path(str(file_row["local_path"]))
            if not path.is_file():
                raise FileNotFoundError(f"No existe Bronze validado: {path}")
            file_rows = 0
            with connection.cursor() as cursor:
                for row_number, raw_row in enumerate(_iter_rows(path), start=1):
                    normalized = normalize_bronze_row(raw_row)
                    cursor.execute(
                        """
                        INSERT INTO landing.trip_records (
                            source_kind, source_file_id, source_filename,
                            source_row_number, service_type,
                            pickup_datetime, dropoff_datetime,
                            pickup_location_id, dropoff_location_id,
                            trip_distance, total_amount,
                            dispatching_base_num, hvfhs_license_num
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (source_kind, source_file_id, source_row_number)
                        DO UPDATE SET
                            pickup_datetime = EXCLUDED.pickup_datetime,
                            dropoff_datetime = EXCLUDED.dropoff_datetime,
                            pickup_location_id = EXCLUDED.pickup_location_id,
                            dropoff_location_id = EXCLUDED.dropoff_location_id,
                            trip_distance = EXCLUDED.trip_distance,
                            total_amount = EXCLUDED.total_amount,
                            dispatching_base_num = EXCLUDED.dispatching_base_num,
                            hvfhs_license_num = EXCLUDED.hvfhs_license_num,
                            loaded_at = CURRENT_TIMESTAMP
                        """,
                        (
                            source_kind,
                            file_row["file_id"],
                            file_row["filename"],
                            row_number,
                            file_row["service_type"],
                            normalized["pickup_datetime"],
                            normalized["dropoff_datetime"],
                            normalized["pickup_location_id"],
                            normalized["dropoff_location_id"],
                            normalized["trip_distance"],
                            normalized["total_amount"],
                            normalized["dispatching_base_num"],
                            normalized["hvfhs_license_num"],
                        ),
                    )
                    file_rows += 1
            connection.execute(
                """
                UPDATE control.ingestion_files
                SET processed_at = CURRENT_TIMESTAMP, rows_loaded = %s
                WHERE file_id = %s
                """,
                (file_rows, file_row["file_id"]),
            )
            files_loaded += 1
            rows_seen += file_rows
    return {
        "event": "landing_load_complete",
        "source_kind": source_kind,
        "files_loaded": files_loaded,
        "rows_seen": rows_seen,
        "migrations_applied": migrations,
    }
