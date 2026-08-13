# Proyecto dbt

Transforma `landing.trip_records` en:

- `staging.stg_trip_records`: homologación y clasificación de errores.
- `silver.trips`: registros válidos.
- `silver.trip_quarantine`: registros inválidos con motivo.
- `gold.dim_*`: dimensiones de fecha, hora, servicio y zona TLC.
- `gold.fact_trip`: viaje individual homologado.
- `gold.fact_zone_hourly_demand`: demanda por zona, hora y servicio.
- `gold.fact_zone_daily_performance`: rendimiento diario por zona y servicio.
- `gold.mart_*`: vistas consumibles por Superset y fases analíticas posteriores.

Ejecución:

```powershell
docker compose run --rm pipeline load-landing --source-kind demo
docker compose --profile tools run --rm dbt build
```

Las credenciales llegan exclusivamente por variables de entorno de Compose.
Los supuestos del escenario de rentabilidad se configuran bajo
`vars.profitability_scenario` en `dbt_project.yml`.
