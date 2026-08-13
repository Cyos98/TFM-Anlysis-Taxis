# Contrato de datos Bronze

## Invariantes

- Un fichero representa un servicio y un mes.
- Los originales TLC se almacenan sin transformar bajo `data/bronze/tlc/`.
- Las muestras sintéticas se aíslan bajo `data/bronze/demo/`.
- La ruta contiene `service/year=YYYY/month=MM/`.
- Cada fichero tiene URL de origen, tamaño, SHA-256, estado y ejecución asociados.
- Bronze nunca se concatena ni se elimina durante una ejecución normal.

## Validaciones mínimas

Todos los ficheros deben:

- Ser Parquet legible.
- Contener al menos una fila y una columna.
- Incluir fechas de recogida y bajada.
- Incluir zona de recogida y zona de destino.
- Cumplir las alternativas de nomenclatura declaradas para Yellow, Green, FHV o FHVHV.

Estas validaciones protegen la entrada, pero no sustituyen los contratos históricos detallados que se desarrollarán con Silver.

## Estados

```text
DISCOVERED -> DOWNLOADED -> VALIDATED
                         -> FAILED
```

Los resultados individuales se guardan en `control.data_quality_results`. Los ficheros que no pueden validarse se conservan en `data/quarantine/bronze/`.
