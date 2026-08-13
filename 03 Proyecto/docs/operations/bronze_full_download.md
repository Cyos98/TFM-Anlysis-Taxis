# Histórico Bronze local y futura descarga completa con NiFi

## Datos existentes

La auditoría local del 2026-08-13 encontró 387 Parquet TLC y cuatro ficheros
demo, aproximadamente 50,23 GB. Ese corpus fue descargado por la implementación
Python preservada y no se ha reescrito durante la migración.

| Servicio | Primer mes | Último mes inventariado | Archivos |
|---|---:|---:|---:|
| Yellow | 2018-01 | 2026-04 | 100 |
| Green | 2018-01 | 2026-04 | 100 |
| FHV | 2018-01 | 2026-04 | 100 |
| FHVHV | 2019-02 | 2026-04 | 87 |

Estas cifras describen la copia local auditada, no garantizan la publicación
actual de TLC.

## Estado NiFi

El modo remoto completo está **PARTIAL**: existen discovery parametrizado,
InvokeHTTP, retry finito, SHA-256 y PutFile, pero faltan el manifest
consult-before-download transaccional, conexiones intergrupo y contratos por
servicio. Por seguridad todavía no se publica un comando de descarga histórica.

Los parámetros previstos son `PIPELINE_MODE=full`, `TLC_START_DATE`,
`TLC_END_DATE` y `TLC_SERVICES`; no están codificados rígidamente.

## Referencia Python

Los comandos históricos `discover`, `plan` y `run --mode full` siguen
disponibles exclusivamente en `Ingesta Python/`. Se conservan para
reproducibilidad, no son la arquitectura principal. No los ejecute para
intervalos amplios sin autorización y espacio verificado.

## Consulta de control

```sql
select service_type,
       min(make_date(year, month, 1)) as first_month,
       max(make_date(year, month, 1)) as last_month,
       count(*) as files,
       sum(size_bytes) as bytes
from control.ingestion_files
where source_kind = 'tlc' and status in ('VALIDATED', 'PROCESSED')
group by service_type
order by service_type;
```
