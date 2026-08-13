# Catálogo resumido de datos

| Esquema/capa | Relación | Grano | Naturaleza |
|---|---|---|---|
| `control` | `pipeline_runs`, `pipeline_tasks` | ejecución/tarea | auditoría |
| `control` | `ingestion_files` | fichero Bronze | procedencia, hash y estado |
| `control` | `data_quality_results` | control por fichero | calidad |
| `landing` | `trip_records` | fila normalizada mínima | interfaz relacional |
| `silver` | `trips` | viaje válido | observado/homologado |
| `silver` | `trip_quarantine` | viaje rechazado | evidencia y motivo |
| `gold` | `dim_date`, `dim_time` | fecha/hora | dimensión |
| `gold` | `dim_taxi_zone` | zona TLC | dimensión oficial |
| `gold` | `dim_service_type` | servicio TLC | dimensión |
| `gold` | `fact_trip` | viaje | hecho |
| `gold` | `fact_zone_hourly_demand` | fecha-hora-zona-servicio | demanda |
| `gold` | `fact_zone_daily_performance` | fecha-zona-servicio | rendimiento |
| `gold` | `mart_*` | caso de uso | consumo Superset |
| `ml` | `model_runs` | entrenamiento | auditoría ML |
| `ml` | `model_metrics` | modelo-horizonte | evaluación |
| `ml` | `predictions` | predicción de test | real/predicho |

La definición detallada de columnas y tests reside junto a cada modelo dbt en
sus archivos `schema.yml`.
