-- Landing relacional mínimo para que dbt construya Silver.

CREATE SCHEMA IF NOT EXISTS landing;

ALTER TABLE control.ingestion_files
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS rows_loaded BIGINT;

CREATE TABLE IF NOT EXISTS landing.trip_records (
    source_kind TEXT NOT NULL,
    source_file_id BIGINT NOT NULL REFERENCES control.ingestion_files(file_id),
    source_filename TEXT NOT NULL,
    source_row_number BIGINT NOT NULL,
    service_type TEXT NOT NULL,
    pickup_datetime TIMESTAMP,
    dropoff_datetime TIMESTAMP,
    pickup_location_id INTEGER,
    dropoff_location_id INTEGER,
    trip_distance DOUBLE PRECISION,
    total_amount DOUBLE PRECISION,
    dispatching_base_num TEXT,
    hvfhs_license_num TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_kind, source_file_id, source_row_number)
);

CREATE INDEX IF NOT EXISTS idx_landing_trip_records_pickup
    ON landing.trip_records (pickup_datetime, service_type);
CREATE INDEX IF NOT EXISTS idx_landing_trip_records_zones
    ON landing.trip_records (pickup_location_id, dropoff_location_id);

COMMENT ON SCHEMA landing IS 'Interfaz relacional incremental entre Bronze Parquet y dbt';
COMMENT ON TABLE landing.trip_records IS 'Columnas comunes extraídas de Bronze sin aplicar reglas Silver';
