#!/bin/bash
set -euo pipefail

superset db upgrade
superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME}" \
    --firstname TFM \
    --lastname Admin \
    --email "${SUPERSET_ADMIN_EMAIL}" \
    --password "${SUPERSET_ADMIN_PASSWORD}" || true
superset init
python /app/superset/bootstrap_assets.py
