# Arquitectura de fase 3: landing y Silver con dbt

> El modelo dbt continúa vigente; las referencias a `pipeline load-landing`
> describen la arquitectura Python preservada.

## Flujo demo implementado

```text
Bronze Parquet validado
        |
        | pipeline load-landing
        v
landing.trip_records
        |
        | dbt staging
        v
staging.stg_trip_records
        |
        +-----------------------+
        |                       |
        v                       v
silver.trips          silver.trip_quarantine
```

## Landing

El cargador Python extrae únicamente columnas comunes y conserva:

- Identidad del fichero y número de fila.
- Tipo de servicio.
- Fechas de recogida/bajada.
- Zonas de origen/destino.
- Distancia e importe cuando existen.
- Identificadores específicos de FHV/FHVHV.

La clave `(source_kind, source_file_id, source_row_number)` permite reejecutar la carga sin duplicar.

## Reglas Silver actuales

Se envían a cuarentena filas con:

- Fechas ausentes o bajada anterior a recogida.
- Zonas ausentes o fuera de 1–265.
- Distancia o importe negativos.

Los campos económicos ausentes en FHV no se inventan y permanecen nulos.

## Estado de la demo

- 4 Parquet Bronze.
- 8 filas landing.
- 8 filas `silver.trips`.
- 0 filas `silver.trip_quarantine`.
- 3 modelos dbt y 19 tests de datos; `dbt build` ejecuta 22 nodos en total.

La carga masiva a landing requerirá una estrategia `COPY` por lotes y particionado antes de procesar el histórico completo.
