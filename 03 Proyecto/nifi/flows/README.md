# Flujos versionados

La fuente primaria es `../parameters/flow_spec.json`. No contiene secretos y se
restaura mediante la API, sin configuración manual:

```powershell
docker compose up -d postgres nifi dbt ml
docker compose run --rm nifi-bootstrap
docker compose run --rm nifi-bootstrap python /bootstrap/smoke_test.py
```

El bootstrap actualiza componentes por nombre y reconoce alias explícitos para
renombrados. No borra componentes desconocidos ni inicia procesadores.

No se usa como fuente primaria un `flow.json.gz` del runtime porque puede estar
acoplado a la clave de propiedades sensibles del entorno.

