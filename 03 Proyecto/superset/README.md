# Apache Superset

Superset 6 se inicializa mediante `superset/init.sh` y
`superset/bootstrap_assets.py`. El bootstrap es idempotente y crea:

- una conexión analítica a PostgreSQL;
- siete datasets Gold/ML;
- ocho gráficos;
- cuatro dashboards publicados en español.

```powershell
docker compose up -d
docker compose ps
```

Interfaz: <http://localhost:8088>.

Los ZIP bajo `superset/exports/` se generaron con la CLI oficial. La contraseña
de la conexión aparece enmascarada y debe facilitarse al importar en otro
entorno. Nunca se versiona `.env` ni una clave secreta real.
