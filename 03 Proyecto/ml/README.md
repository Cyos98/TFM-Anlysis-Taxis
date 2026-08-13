# Machine learning

La implementación principal vive en `ml/src/nyc_taxi_ml/` como servicio
Python independiente de la ingesta. Ofrece:

- features horarias calculadas solo con información disponible en el origen;
- horizontes de 1 h y 24 h;
- corte temporal 80/20 sin mezcla aleatoria;
- baseline estacional, Extra Trees y Gradient Boosting;
- MAE, RMSE, WAPE y R²;
- persistencia en `ml.model_runs`, `ml.model_metrics` y `ml.predictions`;
- artefactos locales para el modelo seleccionado en cada horizonte.

NiFi puede activarlo dentro de la red Compose mediante:

```text
POST http://ml:8081/train?mode=demo
```

El servicio no publica puertos al host ni accede al socket Docker.

Ejecución manual:

```powershell
docker compose exec ml python -m nyc_taxi_ml train --mode demo
```

La demo es sintética y valida reproducibilidad técnica, no rendimiento real
sobre viajes TLC.
