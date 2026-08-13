# Contexto del TFM

## 1. Información general

**Estudiante:** Carlos Monteagudo Tobarra
**Tipo de trabajo:** Trabajo Fin de Máster
**Área:** Big Data, Data Analysis e Inteligencia Artificial
**Caso de estudio:** Movilidad urbana y servicios de taxi en Nueva York
**Fuente principal:** NYC Taxi & Limousine Commission Trip Record Data
**Entorno de ejecución:** Local, Windows, Docker Desktop y Visual Studio Code
**Repositorio final:** GitHub público
**Idioma de la documentación:** Español

---

## 2. Objetivo general

Diseñar, implementar y evaluar una plataforma de datos reproducible que permita:

* Descargar datos de movilidad.
* Procesarlos de forma incremental.
* Aplicar una arquitectura medallón.
* Analizar patrones espaciales y temporales.
* Construir indicadores de negocio.
* Comparar diferentes servicios de movilidad.
* Predecir la demanda por zona y franja temporal.
* Visualizar los resultados en Apache Superset.

La plataforma debe tener un nivel de acabado cercano a producción, aunque se ejecutará en un único equipo mediante Docker Compose.

---

## 3. División del trabajo

El proyecto se divide en dos entregas.

### Parte 1: implementación práctica

Debe entregarse una solución funcional y reproducible que incluya:

* Infraestructura.
* Código.
* Datos de demostración.
* Pipelines.
* Modelo analítico.
* Machine learning.
* Dashboards.
* Tests.
* Documentación técnica.

### Parte 2: memoria académica

Debe elaborarse una memoria completa y lista para entregar.

La memoria no debe comenzar hasta que Carlos apruebe expresamente la parte práctica.

---

## 4. Contexto académico

El proyecto surge de una propuesta de análisis de negocio de los patrones de movilidad en Nueva York.

Las líneas planteadas inicialmente fueron:

* Evolución de los patrones de movilidad.
* Congestión.
* Comparación entre tipos de servicio.
* Ocupación de los taxis.
* Análisis para nuevos taxistas.
* Estudio de rentabilidad.
* Predicción de movilidad.
* Predicción de demanda.
* Predicción de ingresos.

El tutor consideró que el dataset TLC ofrecía suficiente riqueza para desarrollar el trabajo.

También recomendó:

* Cuidar especialmente la memoria.
* Explicar con claridad el problema.
* Justificar la relevancia.
* Analizar el estado del arte.
* Describir el diseño de la solución.
* Explicar la implementación.
* Detallar el entorno experimental.
* Presentar resultados y evaluación.
* Utilizar AutoML o PyCaret cuando simplifique la comparación de modelos.

La memoria final se estima aproximadamente entre 60 y 90 páginas, aunque su extensión exacta dependerá de las normas académicas y del contenido necesario.

---

## 5. Estado previo del trabajo

El estudiante dispone de trabajo previo almacenado en Visual Studio Code.

Según la información proporcionada, existen o han existido:

* Scripts de descarga de Parquet.
* Unión y clasificación de datasets.
* Procesos de borrado lógico.
* Limpieza de datasets.
* Análisis de componentes.
* Procesos de ingesta en PostgreSQL.
* Transformaciones con dbt.
* Configuración inicial de contenedores.
* Orquestación sencilla con Python.
* Trabajo preliminar de predicción.
* Documentación y presentación parcial.

El objetivo no es empezar automáticamente desde cero.

Primero debe inspeccionarse el código existente y decidir:

* Qué conservar.
* Qué adaptar.
* Qué refactorizar.
* Qué descartar.
* Qué falta por construir.

---

## 6. Entorno local

Equipo informado:

* Sistema operativo: Windows.
* Memoria RAM: 32 GB.
* Procesador: AMD Ryzen.
* Almacenamiento total: 1 TB.
* Motor de contenedores: Docker Desktop.
* Editor: Visual Studio Code.

La solución debe ejecutarse completamente mediante Docker Compose.

No debe depender de una instalación local de PostgreSQL, Python, dbt o Superset.

Se recomienda usar WSL2 para mejorar:

* Rendimiento de volúmenes.
* Compatibilidad Linux.
* Ejecución de scripts.
* Gestión de permisos.
* Integración con Docker.

---

## 7. Periodo de análisis

El estudiante indicó que desea comenzar en 2018 para disponer de datos anteriores a la pandemia y poder analizar su efecto.

Como configuración inicial se asume:

```text
Fecha inicial: 2018-01-01
Fecha final: último año completo configurado
```

La fecha final debe ser un parámetro.

La interpretación inicial es analizar desde 2018 hasta el último año completo disponible que se decida incorporar.

Este punto debe confirmarse antes de ejecutar una descarga masiva.

---

## 8. Tipos de servicio

Se desea analizar todos los tipos de taxi y servicios disponibles.

Como mínimo:

* Yellow Taxi.
* Green Taxi.
* For-Hire Vehicles.
* High Volume For-Hire Vehicles.

Debe tenerse en cuenta que:

* Los esquemas cambian entre servicios.
* Los esquemas pueden variar entre años.
* No todos los campos tienen equivalencia.
* Algunos tipos de servicio contienen menos información económica.
* La disponibilidad histórica puede ser diferente.

Debe construirse un modelo común cuando sea posible y conservar atributos específicos por servicio cuando aporten valor.

---

## 9. Fuentes externas

Se desea enriquecer el análisis con toda la información externa razonablemente útil.

Fuentes prioritarias:

### 9.1 Zonas TLC

* Taxi Zone Lookup.
* Borough.
* Service zone.
* Geometrías de las zonas.
* Shapefiles oficiales.

Uso:

* Mapas.
* Agregaciones geográficas.
* Orígenes y destinos.
* Indicadores por borough.
* Visualizaciones en Superset.

### 9.2 Calendario

* Día de la semana.
* Fin de semana.
* Mes.
* Estación.
* Festivos.
* Víspera de festivo.
* Periodos vacacionales.

Uso:

* Análisis temporal.
* Ingeniería de variables.
* Predicción de demanda.

### 9.3 Meteorología

Variables potenciales:

* Temperatura.
* Precipitación.
* Nieve.
* Viento.
* Visibilidad.
* Condiciones meteorológicas.

Uso:

* Explicar cambios en movilidad.
* Mejorar predicciones.
* Analizar demanda bajo condiciones adversas.

### 9.4 Otras fuentes

Podrán incorporarse otras fuentes cuando:

* Tengan una procedencia fiable.
* Su licencia permita el uso.
* Exista correspondencia temporal o espacial.
* Aporten valor demostrable.

No debe ampliarse el alcance de forma ilimitada.

---

## 10. Arquitectura

### 10.1 Vista general

```text
Fuentes TLC y externas
        ↓
Descarga e ingesta con Python
        ↓
Bronze en Parquet
        ↓
Validación y normalización
        ↓
Silver en PostgreSQL mediante dbt
        ↓
Modelo dimensional y marts Gold
        ↓
Entrenamiento y evaluación
        ↓
Predicciones y métricas en PostgreSQL
        ↓
Apache Superset
```

### 10.2 Bronze

Se ha decidido almacenar Bronze en Parquet.

Objetivos:

* Conservar datos originales.
* Evitar cargar todos los registros brutos en PostgreSQL.
* Facilitar reejecuciones.
* Mantener trazabilidad.
* Reducir coste de almacenamiento relacional.

Estructura aproximada:

```text
data/
├── bronze/
│   ├── tlc/
│   │   ├── yellow/
│   │   ├── green/
│   │   ├── fhv/
│   │   └── fhvhv/
│   ├── weather/
│   ├── calendar/
│   └── geography/
├── quarantine/
├── samples/
└── exports/
```

Los datos reales deben permanecer fuera de Git.

### 10.3 Silver

Silver debe contener:

* Viajes tipados.
* Fechas válidas.
* Duraciones.
* Distancias.
* Importes.
* Identificadores de zona.
* Tipo de servicio.
* Campos homologados.
* Variables temporales.
* Variables geográficas.
* Variables meteorológicas.
* Registros válidos para análisis.

### 10.4 Gold

Gold debe responder directamente a casos de negocio y visualización.

Debe incluir:

* Demanda horaria por zona.
* Demanda diaria.
* Ingresos.
* Duración.
* Distancia.
* Velocidad.
* Propinas.
* Ranking de zonas.
* Comparación entre servicios.
* Indicadores de congestión.
* Indicadores de oportunidad.
* Features para modelos.
* Predicciones.
* Métricas.

---

## 11. Objetivo de negocio aprobado

El objetivo aprobado es:

> Diseñar e implementar una plataforma reproducible de datos para analizar los patrones de movilidad de los servicios de taxi y vehículos de alquiler en Nueva York, y predecir la demanda de viajes por zona y franja temporal.

Objetivos secundarios:

* Analizar la evolución histórica de la movilidad.
* Identificar zonas de alta y baja demanda.
* Analizar diferencias por hora, día y temporada.
* Estudiar el impacto de la pandemia.
* Comparar tipos de servicio.
* Construir indicadores aproximados de congestión.
* Analizar ingresos y eficiencia operativa.
* Identificar oportunidades para conductores.
* Proporcionar estimaciones configurables de rentabilidad.

---

## 12. Indicadores de negocio

Indicadores previstos:

* Número de viajes.
* Viajes por hora.
* Viajes por zona.
* Viajes por tipo de servicio.
* Ingreso bruto.
* Importe medio por viaje.
* Ingreso por milla.
* Ingreso por hora ocupada.
* Distancia media.
* Duración media.
* Velocidad media.
* Propina media.
* Porcentaje de propina.
* Peajes.
* Recargos.
* Viajes entre boroughs.
* Orígenes más frecuentes.
* Destinos más frecuentes.
* Demanda por franja.
* Demanda por festivo.
* Demanda por meteorología.
* Indicador de oportunidad de zona.
* Indicador aproximado de congestión.

Debe diferenciarse entre:

* Métricas observadas.
* Métricas derivadas.
* Estimaciones.
* Simulaciones.

---

## 13. Simulador de rentabilidad

Los datos TLC no proporcionan todos los costes necesarios para calcular un beneficio neto real.

Por tanto, se construirá un simulador parametrizable.

Entradas potenciales:

* Tipo de vehículo.
* Consumo.
* Precio de combustible o energía.
* Coste de mantenimiento.
* Seguro.
* Alquiler o amortización.
* Coste de licencia.
* Comisiones.
* Costes fijos.
* Horas trabajadas.
* Tiempo sin pasajero.

Salidas:

* Ingreso bruto estimado.
* Costes variables.
* Costes fijos prorrateados.
* Margen estimado.
* Beneficio estimado.
* Punto de equilibrio.
* Comparación entre zonas.
* Comparación entre horarios.
* Comparación entre servicios.

Los resultados deberán presentarse como escenarios configurables.

---

## 14. Predicción

### 14.1 Variable objetivo

```text
Número de viajes iniciados por zona TLC y hora
```

### 14.2 Granularidad

* Tipo de servicio.
* Zona de recogida.
* Fecha.
* Hora.

### 14.3 Horizontes

Se desarrollarán dos horizontes:

* Demanda para la siguiente hora.
* Demanda para las siguientes veinticuatro horas.

Debe decidirse durante la implementación si el horizonte de veinticuatro horas se modela:

* Como predicción directa.
* Como múltiples pasos horarios.
* Como predicción agregada diaria.

La elección debe justificarse experimentalmente.

### 14.4 Modelos

Se compararán tres modelos.

Propuesta inicial:

1. Baseline histórico o regresión regularizada.
2. Random Forest o Extra Trees.
3. Gradient Boosting, XGBoost o LightGBM.

Los tres modelos definitivos se elegirán según:

* Volumen.
* Tiempo de entrenamiento.
* Interpretabilidad.
* Rendimiento.
* Requisitos de memoria.
* Facilidad de reproducir el experimento.

### 14.5 Modelos por servicio

Se desea un modelo por tipo de servicio.

Debe evaluarse la viabilidad para:

* Yellow.
* Green.
* FHV.
* FHVHV.

Cuando un dataset no contenga información suficiente, debe explicarse y adaptarse el objetivo sin inventar variables.

### 14.6 Evaluación

La validación será temporal.

Ejemplo:

```text
Entrenamiento: periodo histórico inicial
Validación: periodo posterior
Test: último periodo no visto
```

Evitar fuga de información.

Métricas:

* MAE.
* RMSE.
* WAPE o MAPE.
* R² complementario.
* Error por zona.
* Error por hora.
* Error por servicio.
* Error por horizonte.

La elección del modelo final debe quedar justificada mediante una tabla comparativa.

---

## 15. Orquestación

Se utilizará una solución sencilla pero profesional:

* Python como coordinador.
* Cron en un contenedor scheduler.
* Tabla de control en PostgreSQL.
* Procesamiento incremental.
* Reintentos.
* Logs estructurados.
* Estados.
* Códigos de salida.
* Ejecución manual.

No se utilizará inicialmente Airflow.

Flujo aproximado:

```text
discover
download
validate_bronze
load_reference_data
run_dbt_silver
run_dbt_gold
run_quality_checks
build_features
train_or_load_models
generate_predictions
persist_metrics
refresh_outputs
```

---

## 16. Calidad y observabilidad

Se desean capacidades cercanas a producción.

Controles:

* Ficheros descargados.
* Ficheros corruptos.
* Esquemas.
* Columnas.
* Tipos.
* Duplicados.
* Fechas.
* Distancias.
* Duraciones.
* Importes.
* Zonas.
* Integridad.
* Volúmenes anómalos.
* Resultados de dbt.

Observabilidad:

* Logs JSON.
* Identificador de ejecución.
* Inicio y fin.
* Duración.
* Estado.
* Filas leídas.
* Filas válidas.
* Filas rechazadas.
* Error.
* Reintentos.
* Versión del código.
* Parámetros utilizados.

Great Expectations podrá utilizarse si complementa los controles de dbt y Python.

---

## 17. Dashboards en Superset

### Dashboard 1: Resumen ejecutivo

* Viajes totales.
* Evolución temporal.
* Ingresos.
* Distancias.
* Duración.
* Comparación entre servicios.
* Impacto de la pandemia.

### Dashboard 2: Análisis geográfico

* Demanda por zona.
* Orígenes.
* Destinos.
* Boroughs.
* Velocidad.
* Duración.
* Congestión aproximada.
* Mapas.

### Dashboard 3: Oportunidades para conductores

* Zonas con mayor demanda.
* Horas con mayor demanda.
* Ingreso por hora.
* Ingreso por milla.
* Rankings.
* Simulación de rentabilidad.
* Comparación de escenarios.

### Dashboard 4: Predicción

* Real frente a predicho.
* Predicción a una hora.
* Predicción a veinticuatro horas.
* Error por zona.
* Error por servicio.
* Métricas.
* Modelo seleccionado.

No se desarrollará Streamlit.

---

## 18. Modelo dimensional inicial

Dimensiones:

```text
dim_date
dim_time
dim_taxi_zone
dim_service_type
dim_payment_type
dim_weather
dim_holiday
```

Hechos:

```text
fact_trip
fact_zone_hourly_demand
fact_zone_daily_performance
fact_model_predictions
fact_model_metrics
```

Marts:

```text
mart_mobility_overview
mart_service_comparison
mart_driver_opportunity
mart_congestion_proxy
mart_prediction_monitoring
```

El diseño definitivo debe documentarse mediante un diagrama entidad-relación y un esquema estrella.

---

## 19. Estructura objetivo del repositorio

```text
tfm-nyc-mobility-platform/
├── AGENTS.md
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── Makefile
├── configs/
├── data/
│   ├── samples/
│   └── README.md
├── docker/
│   ├── postgres/
│   ├── pipeline/
│   ├── dbt/
│   └── superset/
├── pipeline/
│   ├── src/
│   ├── tests/
│   └── pyproject.toml
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── silver/
│   │   ├── gold/
│   │   └── marts/
│   ├── macros/
│   ├── seeds/
│   ├── snapshots/
│   └── tests/
├── ml/
│   ├── notebooks/
│   ├── src/
│   ├── configs/
│   ├── tests/
│   └── artifacts/
├── superset/
│   ├── assets/
│   └── exports/
├── sql/
│   ├── init/
│   └── control/
├── scripts/
├── docs/
│   ├── context/
│   ├── audit/
│   ├── architecture/
│   ├── data/
│   ├── operations/
│   └── results/
└── logs/
```

La estructura podrá adaptarse al código existente.

---

## 20. Modos de ejecución

### Demo

Objetivo:

* Validar la solución.
* Ejecutarse en un equipo normal.
* Usar pocos meses o una muestra.
* Completar el flujo end-to-end.
* Servir para evaluación y defensa.

```bash
docker compose run --rm pipeline run --mode demo
```

### Full

Objetivo:

* Procesar el periodo configurado.
* Descargar todos los servicios.
* Generar Silver y Gold.
* Entrenar modelos.
* Crear predicciones.

```bash
docker compose run --rm pipeline run \
  --mode full \
  --start-date 2018-01-01 \
  --end-date 2025-12-31
```

---

## 21. Reproducibilidad

Una persona externa debe poder:

1. Clonar el repositorio.
2. Copiar `.env.example` a `.env`.
3. Ejecutar Docker Compose.
4. Lanzar el modo demo.
5. Acceder a Superset.
6. Consultar PostgreSQL.
7. Ejecutar los tests.
8. Reproducir las métricas principales.

Debe evitarse toda dependencia de rutas, credenciales o configuraciones exclusivas del equipo del estudiante.

---

## 22. Publicación

El repositorio será público.

Antes de publicar debe realizarse:

* Revisión de secretos.
* Revisión de código empresarial.
* Revisión de datos personales.
* Revisión de archivos grandes.
* Revisión de licencias.
* Revisión del historial Git.

Los datos originales no se subirán.

Se incluirán scripts de descarga y muestras pequeñas cuando su licencia lo permita.

---

## 23. Primera fase inmediata

La primera fase no consiste en reescribir el proyecto.

Debe realizarse una auditoría del repositorio existente.

Resultado esperado:

```text
docs/audit/initial_repository_audit.md
```

Después de la auditoría se decidirá:

* Arquitectura definitiva.
* Código reutilizable.
* Migración a la estructura objetivo.
* Primer milestone.
* Orden de implementación.
* Riesgos.
* Volumen de datos inicial.
* Estrategia de pruebas.

---

## 24. Decisiones pendientes

Antes de lanzar la descarga completa deben confirmarse:

1. Fecha final exacta del dataset.
2. Espacio libre real disponible para Docker.
3. Ubicación del disco virtual de Docker.
4. Existencia de código empresarial o confidencial.
5. Estado de WSL2.
6. URL del repositorio GitHub.
7. Cobertura histórica real de cada tipo de servicio.
8. Fuente meteorológica definitiva.
9. Configuración del modo demo.
10. Modelos definitivos tras el análisis inicial.

---

## 25. Definición de éxito

El proyecto tendrá éxito cuando demuestre:

* Arquitectura reproducible.
* Uso correcto de Docker.
* Procesamiento incremental.
* Idempotencia.
* Trazabilidad.
* Calidad de datos.
* Modelado dimensional.
* Análisis de negocio.
* Comparación de servicios.
* Evaluación predictiva rigurosa.
* Visualización clara.
* Documentación suficiente.
* Ejecución local de extremo a extremo.
