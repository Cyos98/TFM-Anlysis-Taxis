-- Control operacional e idempotencia de Bronze.

CREATE TABLE IF NOT EXISTS control.pipeline_runs (
    run_id UUID PRIMARY KEY,
    mode TEXT NOT NULL CHECK (mode IN ('demo', 'full')),
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    code_version TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    error_message TEXT,
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS control.pipeline_tasks (
    task_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES control.pipeline_runs(run_id),
    task_name TEXT NOT NULL,
    service_type TEXT,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED', 'SKIPPED')),
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS control.ingestion_files (
    file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('demo', 'tlc')),
    service_type TEXT NOT NULL CHECK (service_type IN ('yellow', 'green', 'fhv', 'fhvhv')),
    year SMALLINT NOT NULL CHECK (year BETWEEN 2009 AND 2100),
    month SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    filename TEXT NOT NULL,
    source_url TEXT NOT NULL,
    local_path TEXT,
    size_bytes BIGINT CHECK (size_bytes IS NULL OR size_bytes >= 0),
    sha256 CHAR(64),
    row_count BIGINT CHECK (row_count IS NULL OR row_count >= 0),
    status TEXT NOT NULL CHECK (
        status IN ('DISCOVERED', 'DOWNLOADED', 'VALIDATED', 'FAILED')
    ),
    first_run_id UUID NOT NULL REFERENCES control.pipeline_runs(run_id),
    last_run_id UUID NOT NULL REFERENCES control.pipeline_runs(run_id),
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    downloaded_at TIMESTAMPTZ,
    validated_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    UNIQUE (source_kind, service_type, year, month, filename)
);

CREATE TABLE IF NOT EXISTS control.data_quality_results (
    quality_result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES control.pipeline_runs(run_id),
    file_id BIGINT REFERENCES control.ingestion_files(file_id),
    check_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARN')),
    observed_value TEXT,
    expected_value TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_tasks_run_id
    ON control.pipeline_tasks (run_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_files_status
    ON control.ingestion_files (status, service_type, year, month);
CREATE INDEX IF NOT EXISTS idx_quality_results_run_id
    ON control.data_quality_results (run_id, status);

COMMENT ON TABLE control.pipeline_runs IS 'Una fila por ejecución manual o programada';
COMMENT ON TABLE control.pipeline_tasks IS 'Estado y métricas de cada tarea de una ejecución';
COMMENT ON TABLE control.ingestion_files IS 'Inventario idempotente de ficheros Bronze';
COMMENT ON TABLE control.data_quality_results IS 'Resultados auditables de validaciones de datos';
