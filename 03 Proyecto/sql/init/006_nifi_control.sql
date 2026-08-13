-- Extensiones aditivas para la orquestación principal con Apache NiFi.

ALTER TABLE control.pipeline_runs
    ADD COLUMN IF NOT EXISTS orchestrator TEXT NOT NULL DEFAULT 'python',
    ADD COLUMN IF NOT EXISTS files_discovered INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS files_downloaded INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS files_skipped INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS files_failed INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS rows_processed BIGINT NOT NULL DEFAULT 0;

ALTER TABLE control.pipeline_runs
    DROP CONSTRAINT IF EXISTS pipeline_runs_orchestrator_check;

ALTER TABLE control.pipeline_runs
    ADD CONSTRAINT pipeline_runs_orchestrator_check
    CHECK (orchestrator IN ('python', 'nifi'));

ALTER TABLE control.ingestion_files
    ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error TEXT,
    ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS current_run_id UUID REFERENCES control.pipeline_runs(run_id);

ALTER TABLE control.ingestion_files
    DROP CONSTRAINT IF EXISTS ingestion_files_status_check;

ALTER TABLE control.ingestion_files
    ADD CONSTRAINT ingestion_files_status_check CHECK (
        status IN (
            'DISCOVERED',
            'DOWNLOADING',
            'DOWNLOADED',
            'VALIDATED',
            'PROCESSED',
            'FAILED',
            'QUARANTINED'
        )
    );

CREATE INDEX IF NOT EXISTS idx_ingestion_files_retry
    ON control.ingestion_files (status, retry_count, last_attempt_at);

COMMENT ON COLUMN control.pipeline_runs.orchestrator IS
    'Motor que coordinó la ejecución: python preservado o nifi principal';
COMMENT ON COLUMN control.ingestion_files.retry_count IS
    'Número de reintentos finitos realizados sobre el fichero actual';
COMMENT ON COLUMN control.ingestion_files.current_run_id IS
    'Ejecución NiFi que adquirió el fichero para procesarlo';
