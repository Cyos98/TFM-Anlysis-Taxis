#!/usr/bin/env sh
set -eu

docker compose up -d --build postgres pipeline
docker compose run --rm pipeline migrate
docker compose run --rm pipeline run --mode demo
docker compose run --rm pipeline load-landing --source-kind demo
docker compose --profile tools run --rm dbt build
docker compose run --rm pipeline train-ml --mode demo

silver_rows="$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-tfm}" -d "${POSTGRES_DB:-tfm_mobility}" -tAc "SELECT count(*) FROM silver.trips")"
gold_rows="$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-tfm}" -d "${POSTGRES_DB:-tfm_mobility}" -tAc "SELECT count(*) FROM gold.fact_trip")"
ml_status="$(docker compose exec -T postgres psql -U "${POSTGRES_USER:-tfm}" -d "${POSTGRES_DB:-tfm_mobility}" -tAc "SELECT status FROM ml.model_runs ORDER BY started_at DESC LIMIT 1")"

if [ "$silver_rows" -ne 8 ]; then
    echo "Silver no contiene las 8 filas demo esperadas: $silver_rows" >&2
    exit 1
fi
if [ "$gold_rows" -ne 8 ]; then
    echo "Gold no reconcilia las 8 filas demo esperadas: $gold_rows" >&2
    exit 1
fi
if [ "$ml_status" != "SUCCEEDED" ]; then
    echo "La última ejecución ML no terminó correctamente: $ml_status" >&2
    exit 1
fi

printf '{"event":"e2e_demo_passed","silver_rows":%s,"gold_rows":%s,"ml_status":"%s"}\n' \
    "$silver_rows" "$gold_rows" "$ml_status"

