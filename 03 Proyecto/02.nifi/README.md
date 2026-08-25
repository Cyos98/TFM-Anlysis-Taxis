# Apache NiFi

Apache NiFi 2.10.0 es la capa principal de ingesta y orquestación. La versión
está fijada; no se usa `latest`. La imagen añade pgJDBC 42.7.11 y los NAR de
Parquet/Hadoop con hashes SHA-256 verificados.

## Estructura

```text
nifi/
├── README.md
├── bootstrap/
├── docs/
├── flows/
├── parameters/flow_spec.json
├── scripts/
└── sql/
```

`flow_spec.json` es la fuente declarativa no sensible. El bootstrap crea de
forma idempotente Parameter Contexts, Process Groups, Controller Services,
procesadores y conexiones. Las contraseñas proceden del entorno.

## Demo local

```powershell
docker compose run --rm nifi-bootstrap python /bootstrap/run_demo.py
```

Genera dos viajes deterministas, los convierte a Parquet, calcula SHA-256,
escribe Bronze, registra control/Landing, ejecuta dbt y dispara el ML demo. La
reejecución conserva el archivo y no duplica filas.

`nifi-data-init` solo hace escribibles por el grupo NiFi los directorios Bronze
y cuarentena. Es necesario porque la arquitectura Python preservada utilizaba
otro UID; no modifica ni elimina contenido.

Interfaz: `https://localhost:8443/nifi`. El certificado local es autofirmado.
Los estados reales están en `docs/architecture/nifi_architecture.md`.

