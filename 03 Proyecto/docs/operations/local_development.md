# Operación local con NiFi

## Preparación y arranque

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

El job `nifi-bootstrap` termina con código 0 después de reconciliar parámetros,
grupos, procesadores y conexiones definidos en Git. Puede reejecutarse:

```powershell
docker compose run --rm nifi-bootstrap
docker compose run --rm nifi-bootstrap python /bootstrap/smoke_test.py
docker compose run --rm nifi-bootstrap python /bootstrap/run_demo.py
```

El smoke test comprueba contextos, grupos, validación de procesadores y la
presencia de DBCP y `ParquetReader` en el catálogo runtime.

## Migración sobre un volumen existente

Los scripts de `/docker-entrypoint-initdb.d` se aplican automáticamente solo al
crear una base nueva. Para un volumen previo, aplique de forma aditiva:

```powershell
docker compose exec -T postgres psql -U tfm -d tfm_mobility `
  -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/006_nifi_control.sql
```

## Comprobaciones

```powershell
docker compose ps -a
docker compose logs --tail=100 postgres nifi nifi-bootstrap dbt ml superset
docker compose exec -T dbt dbt build --project-dir /usr/app --profiles-dir /usr/app
docker compose exec -T ml python -m nyc_taxi_ml train --mode demo
```

Todos los procesadores NiFi quedan inicialmente detenidos para evitar descargas
accidentales. `run_demo.py` activa solo `05_DEMO_PIPELINE`, espera a que vacíe
sus colas y lo detiene. La demo es completa; el modo TLC remoto sigue **PARTIAL**.

## Auditoría PostgreSQL

```powershell
docker compose exec -T postgres psql -U tfm -d tfm_mobility `
  -c "SELECT run_id, orchestrator, mode, status, started_at, finished_at FROM control.pipeline_runs ORDER BY started_at DESC;"

docker compose exec -T postgres psql -U tfm -d tfm_mobility `
  -c "SELECT service_type, filename, status, retry_count, last_attempt_at FROM control.ingestion_files ORDER BY updated_at DESC LIMIT 50;"
```

## Parada segura

```powershell
docker compose down
```

No añada `-v`: esa opción elimina los volúmenes persistentes de PostgreSQL y
NiFi. Los avisos por contenedores huérfanos `pipeline`/`scheduler` pueden
aparecer en una instalación migrada; están detenidos y no se eliminan
automáticamente para preservar el estado local.
