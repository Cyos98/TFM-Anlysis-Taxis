# Línea base de rendimiento local

> Esta medición corresponde a la arquitectura Python + cron preservada. No es
> una medición de NiFi ni permite afirmar que una arquitectura supera a otra.

Mediciones de cierre en Docker Desktop sobre el equipo de desarrollo. No son
benchmarks generalizables; sirven para detectar regresiones futuras.

| Operación | Resultado observado |
|---|---:|
| Descarga Bronze TLC inicial | 387 archivos, 50.232.683.972 bytes, 1 h 04 min 34 s |
| Revalidación Bronze idempotente | 387 reutilizados, 0 descargados, 2 min 38 s |
| `dbt build` demo | 99/99 nodos, aproximadamente 2 s de ejecución dbt |
| Entrenamiento ML demo | 34.560 puntos, seis evaluaciones, aproximadamente 9 s |
| Job scheduler completo demo | Bronze + landing + dbt + ML, aproximadamente 16 s |

Memoria en reposo observada tras el smoke test:

| Servicio | Memoria aproximada |
|---|---:|
| Superset | 185 MiB |
| Pipeline | 79 MiB |
| PostgreSQL | 66 MiB |
| Redis | 4 MiB |
| Scheduler cron | < 1 MiB |

Total aproximado: 336 MiB, sin contar Docker Desktop y caché del sistema.

La revalidación Bronze calcula nuevamente SHA-256 y lee metadatos Parquet, por
lo que su coste es proporcional a los 46,78 GiB aunque no haya red.

La prioridad de optimización futura es preagregar los Parquet reales por
mes/servicio con un motor columnar antes de PostgreSQL. No se justifica cargar
2.426 millones de viajes crudos en una base relacional local.
