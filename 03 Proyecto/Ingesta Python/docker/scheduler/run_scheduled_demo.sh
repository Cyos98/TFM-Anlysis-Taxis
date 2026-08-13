#!/bin/sh
set -eu

python -m nyc_taxi_pipeline run --mode demo
python -m nyc_taxi_pipeline load-landing --source-kind demo
dbt build --project-dir /app/dbt --profiles-dir /app/dbt
python -m nyc_taxi_pipeline train-ml --mode demo
