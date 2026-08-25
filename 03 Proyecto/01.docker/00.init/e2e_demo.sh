#!/usr/bin/env sh
set -eu

# Demo NiFi local no destructiva. Genera dos registros; no descarga TLC.
docker compose up -d --build postgres nifi dbt ml redis superset
docker compose run --rm nifi-bootstrap
docker compose run --rm nifi-bootstrap python /bootstrap/smoke_test.py
docker compose run --rm nifi-bootstrap python /bootstrap/run_demo.py

ml_status="$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-tfm}" -d "${POSTGRES_DB:-tfm_mobility}" -tAc "SELECT status FROM ml.model_runs ORDER BY started_at DESC LIMIT 1")"
landing_rows="$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-tfm}" -d "${POSTGRES_DB:-tfm_mobility}" -tAc "SELECT count(*) FROM landing.trip_records WHERE source_filename = 'yellow_tripdata_2024-01_nifi_demo.parquet'")"

if [ "$ml_status" != "SUCCEEDED" ]; then
    echo "La última ejecución ML no terminó correctamente: $ml_status" >&2
    exit 1
fi
if [ "$landing_rows" -ne 2 ]; then
    echo "Landing no conserva las dos filas NiFi esperadas: $landing_rows" >&2
    exit 1
fi

printf '{"event":"nifi_e2e_demo_passed","landing_rows":%s,"ml_status":"%s"}\n' "$landing_rows" "$ml_status"
