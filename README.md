# TFM — raíz del repositorio

El proyecto técnico se ha estructurado en [`03 Proyecto/`](03%20Proyecto/).

Ejecute Docker y los comandos operativos desde esa carpeta:

```powershell
Set-Location "03 Proyecto"
Copy-Item .env.example .env
docker compose config --quiet
docker compose up -d --build
docker compose run --rm nifi-bootstrap python /bootstrap/run_demo.py
```

La documentación, el código NiFi, dbt, ML, Superset y la implementación Python
preservada están dentro de `03 Proyecto/`. Los directorios `00 Papeleos`, `01
Documentación`, `02 Memoria` y `99 Referencias` quedan fuera de la plataforma
técnica.

Consulta el [README técnico](03%20Proyecto/README.md) para arquitectura,
conexiones y operación.
<!-- Fin de la guía de la raíz Git -->
