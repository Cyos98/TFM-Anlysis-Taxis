FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/ml/src \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

RUN groupadd --system --gid 10002 tfmml \
    && useradd --system --uid 10002 --gid tfmml --create-home tfmml

WORKDIR /app

COPY ml/requirements.lock /app/ml/requirements.lock
RUN python -m pip install --no-cache-dir --requirement /app/ml/requirements.lock

COPY --chown=tfmml:tfmml ml/src /app/ml/src
COPY --chown=tfmml:tfmml ml/tests /app/tests
COPY --chown=tfmml:tfmml sql /app/sql

RUN mkdir -p /app/ml/artifacts && chown -R tfmml:tfmml /app/ml

USER tfmml

EXPOSE 8081

ENTRYPOINT ["python", "-m", "nyc_taxi_ml"]
CMD ["serve"]
