"""Persistencia de auditoría y estado operacional en PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from nyc_taxi_pipeline.config import DatabaseConfig
from nyc_taxi_pipeline.models import SourceFile, StoredFile
from nyc_taxi_pipeline.quality import QualityCheck


class ControlRepository:
    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        return psycopg.connect(
            host=self._config.host,
            port=self._config.port,
            dbname=self._config.name,
            user=self._config.user,
            password=self._config.password,
            connect_timeout=5,
            row_factory=dict_row,
        )

    def apply_migrations(self, sql_root: Path) -> list[str]:
        migration_files = sorted(sql_root.glob("*.sql"))
        if not migration_files:
            raise FileNotFoundError(f"No hay migraciones SQL en {sql_root}")
        applied: list[str] = []
        with self._connect() as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS control")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS control.schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            for migration_file in migration_files:
                existing = connection.execute(
                    "SELECT 1 FROM control.schema_migrations WHERE version = %s",
                    (migration_file.name,),
                ).fetchone()
                if existing:
                    continue
                sql = migration_file.read_text(encoding="utf-8")
                connection.execute(sql, prepare=False)
                connection.execute(
                    "INSERT INTO control.schema_migrations(version) VALUES (%s)",
                    (migration_file.name,),
                )
                applied.append(migration_file.name)
        return applied

    def start_run(
        self,
        run_id: UUID,
        mode: str,
        start_date: object,
        end_date: object,
        parameters: dict[str, object],
        code_version: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO control.pipeline_runs (
                    run_id, mode, status, start_date, end_date, parameters, code_version
                ) VALUES (%s, %s, 'RUNNING', %s, %s, %s, %s)
                """,
                (run_id, mode, start_date, end_date, Jsonb(parameters), code_version),
            )

    def finish_run(
        self,
        run_id: UUID,
        status: str,
        error_message: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE control.pipeline_runs
                SET status = %s,
                    finished_at = CURRENT_TIMESTAMP,
                    error_message = %s
                WHERE run_id = %s
                """,
                (status, error_message, run_id),
            )

    def start_task(
        self,
        run_id: UUID,
        task_name: str,
        service_type: str | None = None,
    ) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO control.pipeline_tasks (
                    run_id, task_name, service_type, status
                ) VALUES (%s, %s, %s, 'RUNNING')
                RETURNING task_id
                """,
                (run_id, task_name, service_type),
            ).fetchone()
        assert row is not None
        return int(row["task_id"])

    def finish_task(
        self,
        task_id: int,
        status: str,
        metrics: dict[str, object] | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE control.pipeline_tasks
                SET status = %s,
                    metrics = %s,
                    error_message = %s,
                    finished_at = CURRENT_TIMESTAMP
                WHERE task_id = %s
                """,
                (status, Jsonb(metrics or {}), error_message, task_id),
            )

    def register_file(
        self,
        run_id: UUID,
        source_file: SourceFile,
    ) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO control.ingestion_files (
                    source_kind, service_type, year, month, filename, source_url,
                    status, first_run_id, last_run_id
                ) VALUES (%s, %s, %s, %s, %s, %s, 'DISCOVERED', %s, %s)
                ON CONFLICT (source_kind, service_type, year, month, filename)
                DO UPDATE SET
                    source_url = EXCLUDED.source_url,
                    last_run_id = EXCLUDED.last_run_id,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
                """,
                (
                    source_file.source_kind,
                    source_file.service_type,
                    source_file.year,
                    source_file.month,
                    source_file.filename,
                    source_file.source_url,
                    run_id,
                    run_id,
                ),
            ).fetchone()
        assert row is not None
        return row

    def mark_downloaded(
        self,
        file_id: int,
        run_id: UUID,
        stored_file: StoredFile,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE control.ingestion_files
                SET status = 'DOWNLOADED',
                    local_path = %s,
                    size_bytes = %s,
                    sha256 = %s,
                    downloaded_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    last_run_id = %s,
                    error_message = NULL
                WHERE file_id = %s
                """,
                (
                    str(stored_file.path),
                    stored_file.size_bytes,
                    stored_file.sha256,
                    run_id,
                    file_id,
                ),
            )

    def mark_validated(
        self,
        file_id: int,
        run_id: UUID,
        row_count: int,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE control.ingestion_files
                SET status = 'VALIDATED',
                    row_count = %s,
                    validated_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    last_run_id = %s,
                    error_message = NULL
                WHERE file_id = %s
                """,
                (row_count, run_id, file_id),
            )

    def mark_file_failed(self, file_id: int, run_id: UUID, message: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE control.ingestion_files
                SET status = 'FAILED',
                    error_message = %s,
                    last_run_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE file_id = %s
                """,
                (message, run_id, file_id),
            )

    def record_quality_checks(
        self,
        run_id: UUID,
        file_id: int,
        checks: tuple[QualityCheck, ...],
    ) -> None:
        rows = [
            (
                run_id,
                file_id,
                check.name,
                check.status,
                check.observed,
                check.expected,
                Jsonb(check.details),
            )
            for check in checks
        ]
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO control.data_quality_results (
                        run_id, file_id, check_name, status,
                        observed_value, expected_value, details
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )
