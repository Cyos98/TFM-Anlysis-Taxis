from __future__ import annotations

import os
from urllib.parse import quote_plus

from celery.schedules import crontab


SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

db_user = quote_plus(os.getenv("POSTGRES_USER", "tfm"))
db_password = quote_plus(os.environ["POSTGRES_PASSWORD"])
db_name = quote_plus(os.getenv("POSTGRES_DB", "tfm_mobility"))
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{db_user}:{db_password}@postgres:5432/{db_name}"
    "?options=-csearch_path%3Dsuperset"
)

REDIS_HOST = "redis"
REDIS_PORT = 6379
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_cache_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": 1,
}
DATA_CACHE_CONFIG = CACHE_CONFIG
RATELIMIT_STORAGE_URI = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"

FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}
ENABLE_PROXY_FIX = True
TALISMAN_ENABLED = False
CONTENT_SECURITY_POLICY_WARNING = False
WTF_CSRF_ENABLED = True
SCARF_ANALYTICS = False
LANGUAGES = {"es": {"flag": "es", "name": "Español"}}
BABEL_DEFAULT_LOCALE = "es"


class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    imports = ("superset.sql_lab", "superset.tasks.scheduler")
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        }
    }


CELERY_CONFIG = CeleryConfig
