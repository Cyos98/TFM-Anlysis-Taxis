CREATE SCHEMA IF NOT EXISTS ml;

CREATE TABLE IF NOT EXISTS ml.model_runs (
    model_run_id UUID PRIMARY KEY,
    mode TEXT NOT NULL CHECK (mode IN ('demo', 'full')),
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED')),
    data_version TEXT NOT NULL,
    code_version TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS ml.model_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_run_id UUID NOT NULL REFERENCES ml.model_runs(model_run_id),
    model_name TEXT NOT NULL,
    horizon_hours SMALLINT NOT NULL CHECK (horizon_hours IN (1, 24)),
    split TEXT NOT NULL CHECK (split IN ('test')),
    mae DOUBLE PRECISION NOT NULL,
    rmse DOUBLE PRECISION NOT NULL,
    wape DOUBLE PRECISION,
    r2 DOUBLE PRECISION,
    sample_count INTEGER NOT NULL CHECK (sample_count > 0),
    is_selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (model_run_id, model_name, horizon_hours, split)
);

CREATE TABLE IF NOT EXISTS ml.predictions (
    prediction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_run_id UUID NOT NULL REFERENCES ml.model_runs(model_run_id),
    model_name TEXT NOT NULL,
    horizon_hours SMALLINT NOT NULL CHECK (horizon_hours IN (1, 24)),
    target_timestamp TIMESTAMP NOT NULL,
    service_type TEXT NOT NULL,
    taxi_zone_key INTEGER NOT NULL,
    actual_demand DOUBLE PRECISION NOT NULL,
    predicted_demand DOUBLE PRECISION NOT NULL,
    split TEXT NOT NULL CHECK (split IN ('test'))
);

CREATE INDEX IF NOT EXISTS idx_ml_metrics_run
    ON ml.model_metrics (model_run_id, horizon_hours, mae);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_run
    ON ml.predictions (model_run_id, horizon_hours, target_timestamp);

COMMENT ON TABLE ml.model_runs IS 'Ejecuciones reproducibles de entrenamiento y evaluación temporal';
COMMENT ON TABLE ml.model_metrics IS 'Métricas comparables por modelo y horizonte';
COMMENT ON TABLE ml.predictions IS 'Predicciones de test persistidas con su valor real';
