# Arquitectura técnica consolidada

Apache NiFi es la capa principal de ingesta y orquestación. Bronze conserva
Parquet originales; dbt es propietario de Silver/Gold; PostgreSQL almacena el
control y el modelo analítico; Python se mantiene para ML; Superset consume
Gold y las métricas/predicciones.

```mermaid
flowchart LR
    SRC[Fuentes TLC y externas] --> NF[Apache NiFi]
    NF --> B[Bronze Parquet]
    NF --> C[(PostgreSQL control)]
    B --> D[dbt]
    D --> S[(Silver / Gold)]
    S --> ML[Python ML]
    ML --> S
    S --> SS[Superset]
    R[(Redis)] --- SS
```

La implementación reemplazada se conserva en `Ingesta Python/`. El estado
detallado, incluida la distinción entre **IMPLEMENTED**, **PARTIAL** y
**PLANNED**, está en [Arquitectura NiFi](nifi_architecture.md).
