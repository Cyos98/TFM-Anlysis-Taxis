# Resolución de incidencias

## Estado general

```powershell
docker compose ps -a
docker compose logs --tail=150 postgres nifi nifi-bootstrap dbt ml superset redis
docker compose run --rm nifi-bootstrap python /bootstrap/smoke_test.py
```

## PostgreSQL no acepta conexiones

Compruebe `docker compose ps postgres` y que `POSTGRES_PORT` no esté ocupado.
Desde DBeaver use host `localhost`, el puerto publicado, base
`tfm_mobility`, usuario `tfm` y la contraseña de `.env`. `postgres:5432` solo
funciona entre contenedores. No use `docker compose down -v`.

## NiFi no abre

La URL es `https://localhost:8443/nifi`; es HTTPS y el certificado local es
autofirmado. Si está saludable pero falta el flujo, reejecute el bootstrap.

## NiFi no puede escribir Bronze

Una instalación migrada puede contener directorios con el UID del pipeline
Python. Ejecute:

```powershell
docker compose run --rm nifi-data-init
```

Solo ajusta grupo y permiso de escritura de directorios; no cambia ni elimina
Parquet.

## dbt falla

```powershell
docker compose exec -T dbt dbt debug --project-dir /usr/app --profiles-dir /usr/app
docker compose exec -T dbt dbt build --project-dir /usr/app --profiles-dir /usr/app
```

Revise el primer nodo `ERROR`; los posteriores pueden quedar `SKIP`.

## Demo NiFi

```powershell
docker compose run --rm nifi-bootstrap python /bootstrap/run_demo.py
```

Si se interrumpe, el script intenta detener `05_DEMO_PIPELINE`. Revise sus
bulletins, Data Provenance y las tablas de `control`.

## TLC responde 403 o 5xx

La ruta TLC remota sigue **PARTIAL** y no debe arrancarse para periodos amplios.
Respete `MAX_RETRIES`, `HTTP_TIMEOUT` y backpressure. La demo no usa red.

## Superset no inicia

```powershell
docker compose up superset-init
docker compose logs --tail=200 superset-init superset
```

Una `SUPERSET_SECRET_KEY` distinta impide descifrar conexiones previas. Restaure
la clave correcta; no borre el volumen para ocultar el problema.
