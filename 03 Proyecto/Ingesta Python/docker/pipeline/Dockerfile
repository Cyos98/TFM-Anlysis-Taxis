FROM python:3.11.9-slim-bookworm AS pipeline

LABEL org.opencontainers.image.title="TFM NYC Mobility Pipeline"
LABEL org.opencontainers.image.description="Contenedor base del pipeline reproducible de movilidad NYC"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/pipeline/src \
    TFM_CONFIG_PATH=/app/configs/pipeline.toml \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

RUN groupadd --system --gid 10001 tfm \
    && useradd --system --uid 10001 --gid tfm --create-home tfm

WORKDIR /app

COPY ["Ingesta Python/pipeline/requirements.lock", "/app/pipeline/requirements.lock"]

RUN python -m pip install --no-cache-dir --requirement /app/pipeline/requirements.lock

COPY --chown=tfm:tfm ["Ingesta Python/pipeline/src", "/app/pipeline/src"]
COPY --chown=tfm:tfm ["Ingesta Python/pipeline/tests", "/app/tests"]
COPY --chown=tfm:tfm ["Ingesta Python/pipeline/pyproject.toml", "/app/pipeline/pyproject.toml"]
COPY --chown=tfm:tfm ["Ingesta Python/configs", "/app/configs"]
COPY --chown=tfm:tfm sql /app/sql

RUN mkdir -p /app/data /app/logs \
    && chown -R tfm:tfm /app

USER tfm

ENTRYPOINT ["python", "-m", "nyc_taxi_pipeline"]
CMD ["service"]

FROM pipeline AS scheduler

USER root

RUN apt-get update \
    && apt-get install --yes --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir \
        dbt-core==1.8.3 \
        dbt-postgres==1.8.2

COPY --chown=tfm:tfm dbt /app/dbt
COPY --chown=tfm:tfm ["Ingesta Python/docker/scheduler/run_scheduled_demo.sh", "/app/scripts/run_scheduled_demo.sh"]
COPY --chown=root:root ["Ingesta Python/docker/scheduler/entrypoint.sh", "/usr/local/bin/tfm-scheduler-entrypoint"]

RUN chmod 0755 /app/scripts/run_scheduled_demo.sh /usr/local/bin/tfm-scheduler-entrypoint

ENTRYPOINT ["/usr/local/bin/tfm-scheduler-entrypoint"]
