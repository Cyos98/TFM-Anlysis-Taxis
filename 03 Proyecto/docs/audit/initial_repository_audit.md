# Auditoría inicial del repositorio

**Fecha de inspección:** 2026-08-04  
**Rama:** `main`  
**Commit inspeccionado:** `6fba2e4` (`[TEST] prueba ssh`)  
**Estado de Git al iniciar:** limpio, sin cambios pendientes; `main` alineada con `origin/main`  
**Naturaleza de la revisión:** inspección estática y de solo lectura, sin descargar datos, instalar dependencias, arrancar contenedores ni ejecutar procesos destructivos

## 1. Resumen ejecutivo

El repositorio contiene un prototipo inicial útil como fuente de requisitos y como prueba de concepto de descarga de datos TLC, pero todavía no constituye una plataforma reproducible ni una arquitectura medallón funcional. El trabajo reutilizable se concentra en el descubrimiento de enlaces Parquet, el filtrado temporal, la clasificación básica de servicios, los primeros notebooks de perfilado y los activos geográficos de zonas TLC.

La distancia respecto a la arquitectura objetivo es grande: no existen Docker Compose, imágenes de servicios, PostgreSQL, dbt, Silver/Gold implementados, tablas de control, calidad persistente, tests, Superset ni un pipeline de machine learning reproducible. La ingesta actual es interactiva, instala paquetes durante el import, no registra ejecuciones y contiene rutas destructivas que eliminan Bronze, por lo que no debe usarse sobre un corpus real sin refactorización.

Los riesgos más urgentes no son de volumen de datos, pues no hay Parquet versionados actualmente, sino de publicación:

1. Existe en el directorio local un archivo ignorado con credenciales en texto claro. No está versionado, pero debe trasladarse fuera del árbol de trabajo y las credenciales deben rotarse si son vigentes.
2. El historial Git conserva varios PDF académicos de terceros que fueron versionados y después eliminados. Añadirlos a `.gitignore` no los retira del historial; antes de publicar debe revisarse su licencia y decidir, con autorización expresa, si se reescribe el historial.
3. Hay rutas locales con nombre de usuario en notebooks y en versiones históricas de scripts. No son secretos por sí solas, pero reducen la reproducibilidad y exponen información del entorno personal.

La recomendación es conservar el repositorio y migrarlo incrementalmente, sin una reescritura total inmediata. Primero debe asegurarse la gobernanza y la publicación; después, construir una base Docker mínima y un modo demo pequeño; a continuación, implementar ingesta idempotente, dbt Silver/Gold, ML y Superset.

## 2. Fuentes normativas y alcance

Se contrastó el estado actual con:

- `AGENTS.md`, suministrado como adjunto para esta auditoría.
- `docs/context/TFM_CONTEXT.md`, suministrado como adjunto para esta auditoría.
- Todo el árbol versionado del commit indicado.
- El inventario local ignorado, únicamente para detectar riesgos de publicación y dependencias ocultas.
- El historial Git visible en todas las referencias locales, para localizar archivos retirados que siguen formando parte del repositorio publicable.

Los dos documentos normativos aún **no existen dentro del repositorio**. Deben materializarse en las rutas previstas durante la fase de saneamiento, tras confirmar que los adjuntos son sus versiones definitivas. Esta auditoría no los ha copiado para respetar la limitación de no realizar cambios distintos del propio diagnóstico.

No se leyó el contenido sustantivo de documentos administrativos o académicos privados ignorados, salvo la estructura mínima necesaria para confirmar la presencia de credenciales sin registrar sus valores en este informe.

## 3. Árbol actual

Árbol versionado relevante:

```text
TFM/
├── .gitignore
├── README.md
├── Codigo/
│   ├── Doc.md
│   ├── AnaPrevio/
│   │   └── AnalisisPrevio.ipynb
│   ├── AnaPredict/
│   │   └── AnalisisPredictivo.ipynb
│   └── ETL/
│       ├── dependencias.py
│       ├── funciones.py
│       ├── ingesta.py
│       ├── ETL.py
│       ├── Orquestador.py
│       ├── requirements.txt
│       ├── __pycache__/
│       │   └── *.pyc
│       └── Cuadernos/
│           ├── 00 Borrado.ipynb
│           ├── 01 Ingesta Datasets.ipynb
│           └── .ipynb_checkpoints/
├── Datasets/
│   ├── Bronze/Bronze.md
│   ├── Silver/Silver.md
│   └── Gold/Gold.md
└── Zonas/
    ├── taxi_zone_lookup.csv
    ├── taxi_zones.{shp,shx,dbf,prj,sbn,sbx}
    ├── taxi_zones.shp.xml
    └── taxi_zone_map_*.jpg
```

Elementos locales ignorados o no destinados a publicación:

- Un entorno virtual local de aproximadamente 244 MB y 8.427 archivos, autoignorado mediante `.venv/.gitignore`.
- Documentación oficial de TLC y referencias académicas locales.
- Documentos administrativos y formularios del TFM.
- Un archivo de conexión con usuarios y contraseñas en texto claro.
- Los directorios locales `Datasets/` están ignorados globalmente, aunque sus marcadores ya versionados continúan en Git.

El repositorio contiene 34 archivos versionados. Su historial ocupa aproximadamente 36,7 MiB como objetos sueltos, principalmente por PDF de referencias que ya no figuran en el árbol actual y por activos geográficos.

## 4. Componentes existentes

### 4.1 Ingesta y descarga

`Codigo/ETL/ingesta.py` implementa:

- Descubrimiento de enlaces `.parquet` desde la página de TLC mediante `requests` y BeautifulSoup.
- Extracción de año y mes desde el nombre del archivo.
- Filtrado por intervalo anual.
- Descarga en streaming y omisión de archivos cuyo nombre ya existe.
- Clasificación aproximada de Yellow, Green, FHV y FHVHV.
- Combinación en memoria por servicio y combinación global opcional.

La funcionalidad es una prueba de concepto, no una ingesta apta para el diseño objetivo. No hay timeouts, reintentos, descarga atómica, checksum, manifiesto, metadatos, códigos de salida ni control transaccional. La omisión por existencia no distingue un fichero completo de una descarga parcial. Además, los modos de combinación eliminan originales y contradicen la inmutabilidad de Bronze.

### 4.2 Configuración y dependencias

`Codigo/ETL/dependencias.py` calcula rutas relativas al repositorio y centraliza la URL de TLC. Ese cálculo es mejor que las rutas absolutas de los notebooks y puede inspirar la futura configuración.

El mismo módulo ejecuta `pip install -r requirements.txt` al importarse. Esto introduce efectos laterales, dependencia de Python local, acceso a red inesperado y falta de reproducibilidad. `tipoIngesta()` vuelve a invocar la instalación, por lo que el comportamiento se duplica.

`requirements.txt` declara `pandas`, `tqdm`, `beautifulsoup4`, `requests` y `pyarrow`, sin versiones, hashes ni separación entre ejecución y desarrollo. Todavía no incluye PostgreSQL/SQLAlchemy, dbt, ML, tests, calidad ni logging estructurado.

### 4.3 Orquestación

`Codigo/ETL/Orquestador.py` ofrece un menú interactivo para borrado, ingesta o ETL. No implementa un CLI automatizable, parámetros de modo demo/full, planificación, estados, reintentos, recuperación ni métricas. La opción ETL está comentada y no ejecuta transformaciones.

### 4.4 Transformaciones Silver y Gold

`Codigo/ETL/ETL.py` es un esqueleto. `silver()` no tiene cuerpo ejecutable y deja el módulo sintácticamente incompleto; `gold()` tampoco implementa lógica. Los archivos `Datasets/Silver/Silver.md` y `Datasets/Gold/Gold.md` son marcadores sin definición de esquema ni procesos.

No existen transformaciones homologadas por servicio, reglas de limpieza, deduplicación, cuarentena, dimensiones, hechos ni marts.

### 4.5 Borrado

`Codigo/ETL/funciones.py` y `Codigo/ETL/Cuadernos/00 Borrado.ipynb` contienen borrado físico de archivos. El notebook usa una ruta absoluta de Windows. La función Python no es recursiva, carece de confirmación no interactiva y presenta un defecto en la obtención de Gold (`dependencias[3]` intenta indexar la función en lugar de su resultado).

Este código no debe integrarse en el pipeline productivo. Si se conserva alguna operación de limpieza, debe limitarse a artefactos regenerables, validar rutas explícitas y estar separada del flujo normal.

### 4.6 Análisis exploratorio

`Codigo/AnaPrevio/AnalisisPrevio.ipynb` carga un mes de 2025 para los cuatro tipos de servicio y realiza inspecciones básicas sobre Yellow: columnas, muestra, estadísticos, nulos y duplicados. Sus salidas guardadas demuestran que se trabajó con volúmenes relevantes y ya muestran anomalías importantes, como fechas de 2008 dentro de un fichero de 2025 y distancias extremas.

El notebook depende del directorio de ejecución, usa año/mes codificados y conserva salidas voluminosas. La sección PCA está vacía. Es reutilizable como catálogo inicial de comprobaciones, no como pipeline de calidad ni como análisis reproducible.

### 4.7 Modelado predictivo

`Codigo/AnaPredict/AnalisisPredictivo.ipynb` solo contiene una división aleatoria 90/10 sobre una variable `data` no definida. No hay variable objetivo construida, features, modelos, evaluación, persistencia ni experimentos reproducibles. La división aleatoria incumple el requisito de validación temporal y podría producir fuga de información.

### 4.8 Geografía

`Zonas/` contiene el lookup de 265 zonas, el shapefile y mapas JPG por borough. Son activos valiosos para `dim_taxi_zone`, controles de integridad y visualización. El XML adjunto conserva metadatos técnicos parciales, pero no se ha encontrado en el repositorio una ficha de procedencia, URL, fecha de descarga, licencia, hash o transformaciones aplicadas.

### 4.9 Documentación

`README.md` tiene únicamente el título y una mención a conexión SSH. `Codigo/Doc.md` describe de forma preliminar las carpetas, pero no permite instalar, ejecutar ni reproducir el sistema. Parte del texto del código, notebooks y documentación presenta mojibake en caracteres españoles y emojis, que debe normalizarse a UTF-8.

Existen localmente diccionarios de datos TLC y guías oficiales ignoradas. Son referencias útiles, pero la documentación técnica del repositorio debería enlazar a sus fuentes oficiales en vez de depender de copias locales no versionadas.

## 5. Código y activos reutilizables

| Elemento | Reutilización recomendada | Condición |
|---|---|---|
| Descubrimiento de enlaces TLC | Conservar la idea y casos de prueba derivados | Encapsular cliente HTTP, validar URL/esquema, añadir timeout, retry y tests |
| Regex de año/mes | Reutilizable | Ampliar pruebas para nombres y servicios históricos |
| Filtro temporal | Reutilizable como regla de dominio | Sustituir menú por parámetros de CLI y usar fechas completas configurables |
| Descarga por chunks | Reutilizable conceptualmente | Escribir a temporal, validar Parquet/hash/tamaño y renombrar atómicamente |
| Clasificación de servicios | Reutilizable como prototipo | Corregir nomenclatura FHVHV/HVFHV, centralizar enum y probar esquemas |
| Cálculo de rutas desde la raíz | Reutilizable | Migrar a configuración por entorno/YAML y rutas internas de contenedor |
| Perfilado del notebook | Reutilizable como lista inicial de controles | Convertir a funciones/tests y persistir resultados |
| Lookup y geometrías TLC | Reutilizables | Documentar fuente/licencia, validar integridad y preparar seed/carga geográfica |
| Resultados exploratorios guardados | Útiles como evidencia de anomalías | No usarlos como datos de prueba; crear muestras deterministas y pequeñas |

No merece la pena restaurar `combinarCategoria.py` y `combinarYear.py`, eliminados en el historial: su lógica está duplicada en `ingesta.py` y conserva rutas absolutas y procesamiento completo en memoria.

## 6. Código que requiere refactorización o sustitución

### Refactorización necesaria

- `ingesta.py`: separar descubrimiento, planificación, descarga, validación y registro; eliminar globales y menús; impedir la eliminación de Bronze.
- `dependencias.py`: convertirlo en configuración sin efectos laterales; retirar toda instalación en tiempo de ejecución.
- `Orquestador.py`: sustituir el bucle interactivo por un CLI tipado con subcomandos y códigos de salida.
- `AnalisisPrevio.ipynb`: parametrizarlo y convertir controles repetibles en código de producción/tests.
- Activos geográficos: integrarlos como referencia gobernada, con procedencia y validación.

### Sustitución justificada o elementos prescindibles

- `ETL.py`: el esqueleto actual puede sustituirse por módulos de pipeline y modelos dbt, conservando únicamente el objetivo funcional documentado.
- `AnalisisPredictivo.ipynb`: la división aleatoria aislada no debe conservarse como base metodológica.
- Notebook y menú de borrado: retirar del flujo operativo; cualquier utilidad futura debe ser segura y explícita.
- `__pycache__/*.pyc`: artefactos generados que no deben versionarse.
- `.ipynb_checkpoints/`: duplicados automáticos que no deben versionarse.
- Marcadores `Datasets/*/*.md`: reemplazarlos por una única documentación clara de política de datos, manteniendo directorios mediante archivos apropiados si fueran necesarios.

La eliminación física de estos elementos debe realizarse en una tarea posterior, con un commit específico y justificando su sustitución, tal como exige `AGENTS.md`.

## 7. Carencias respecto a la arquitectura objetivo

| Área | Estado actual | Diferencia principal | Prioridad |
|---|---|---|---|
| Gobierno del repositorio | Faltan `AGENTS.md`, contexto, licencia y documentación operativa | No hay fuente normativa dentro del clon | Crítica |
| Docker Compose | Inexistente | No se puede levantar ningún servicio desde la raíz | Crítica |
| Pipeline contenerizado | Inexistente | Depende de Python/venv local y de instalación dinámica | Crítica |
| Bronze | Descarga básica a una carpeta | Sin estructura por servicio, manifiesto, metadatos, integridad ni inmutabilidad | Crítica |
| Control e idempotencia | Solo omisión por nombre de fichero | Faltan `pipeline_runs`, `pipeline_tasks`, `ingestion_files` y estados | Crítica |
| PostgreSQL | Inexistente | No hay almacenamiento analítico, esquemas ni inicialización | Crítica |
| dbt | Inexistente | No hay staging, Silver, Gold, marts, macros ni tests | Crítica |
| Calidad/cuarentena | Perfilado manual parcial | Sin reglas ejecutables, persistencia, razones de rechazo ni auditoría | Alta |
| Modelo dimensional | Inexistente | Faltan todas las dimensiones, hechos y marts previstos | Alta |
| Orquestación/scheduler | Menú Python | Sin ejecución manual automatizable, cron, retries o recuperación | Alta |
| Machine learning | Una división aleatoria aislada | Sin dataset de features, validación temporal, modelos o métricas | Alta |
| Superset/Redis | Inexistentes | Sin servicios, assets exportables ni dashboards | Alta |
| Tests/CI | Inexistentes | Sin unitarios, integración, dbt, Compose smoke ni E2E demo | Crítica |
| Seguridad/configuración | `.gitignore` mínimo | Faltan `.env.example`, `.dockerignore`, secret scanning y política de publicación | Crítica |
| Demo/full | Inexistentes | No existen comandos objetivo ni una muestra controlada | Crítica |
| Observabilidad | `print()` | Sin logs JSON, run ID, contadores, duración o versión del código | Alta |

## 8. Riesgos técnicos

### Críticos

- **Pérdida de Bronze:** `ingestaCateg()` borra cada Parquet original tras leerlo y `ingestaComb()` borra agregados intermedios. Esto impide trazabilidad y recuperación.
- **Escalabilidad:** la concatenación de todos los meses y servicios mediante listas de DataFrames puede agotar memoria. Un único mes FHVHV guardado en las salidas del notebook supera 20 millones de filas.
- **Módulo ETL no ejecutable:** `silver()` carece de cuerpo y no hay transformación real.
- **Ausencia de pruebas:** no existe protección frente a regresiones, cambios de esquema o duplicados.

### Altos

- **Descargas no recuperables:** sin timeout, retry, fichero temporal ni validación; un parcial puede quedar aceptado por mera existencia.
- **No idempotencia real:** no hay identidad estable, hash, estado ni control en base de datos.
- **Esquemas heterogéneos:** concatenar servicios por unión implícita de columnas genera nulos y semánticas incompatibles sin contrato común.
- **Dependencias no reproducibles:** versiones abiertas e instalación durante el import.
- **Fechas rígidas:** menús limitados a 2025 y notebooks fijados a noviembre de 2025; no cumplen una fecha final configurable.
- **Fuga temporal en ML:** la muestra aleatoria no es válida para predicción de demanda futura.
- **Errores de nomenclatura:** aparecen `fhvhv` y `hvfhv`, lo que puede omitir o duplicar la categoría de high-volume FHV.
- **Ausencia de contratos de datos:** no hay esquema esperado por servicio/periodo ni estrategia documentada para cambios históricos.

### Medios

- Código con globales, entradas interactivas, imports sin paquete, funciones sin tipado y excepciones demasiado generales.
- Ausencia de time zone explícita y de definición de límites de mes para fechas anómalas.
- Mojibake y salidas guardadas en notebooks, que dificultan revisión y aumentan ruido en Git.
- README insuficiente y nombre remoto con errata (`Anlysis`), que afecta presentación pero no funcionalidad.

## 9. Riesgos de seguridad y publicación

1. **Credenciales locales en texto claro — crítico.** Existe un archivo ignorado con dos conjuntos de usuario/contraseña. El escaneo se realizó sin copiar valores. Debe sacarse del árbol de trabajo, reemplazarse por un gestor seguro y rotarse si las credenciales siguen activas. No debe añadirse nunca a Git.
2. **PDF de terceros en el historial — alto.** El historial contiene al menos siete trabajos académicos completos, con blobs individuales de hasta unos 7,5 MB. Aunque hoy estén eliminados e ignorados, seguirían descargándose al clonar. Deben revisarse derechos de redistribución y, si procede, eliminarse del historial mediante una operación autorizada y coordinada.
3. **Material administrativo y acuerdos locales — alto.** Están ignorados actualmente. Debe mantenerse esa separación y verificarse que nunca hayan sido incluidos en ninguna referencia remota.
4. **Rutas y usuario local — medio.** Hay rutas absolutas en notebooks versionados y en scripts históricos. Deben eliminarse del árbol actual; una eventual limpieza de historial dependerá del nivel de privacidad requerido.
5. **Activos TLC sin ficha de licencia/procedencia — medio.** CSV, shapefile y mapas están versionados. Antes de mantenerlos en un repositorio público hay que documentar fuente y condiciones de redistribución; si no son redistribuibles, usar descarga automatizada o seeds permitidos.
6. **Binarios generados — bajo/medio.** Los `.pyc` versionados no aportan valor, pueden revelar rutas/metadatos de compilación y deben excluirse.
7. **Faltan protecciones básicas — alto.** No hay `.env.example`, `.dockerignore`, plantilla de secretos ficticios, escaneo automatizado ni guía de respuesta ante exposición.

El escaneo estático de nombres/rutas no encontró tokens GitHub, claves privadas, URL de base de datos con credenciales ni claves cloud en el árbol versionado. Esto reduce el riesgo inmediato, pero no sustituye un escaneo especializado de todo el historial antes de publicar.

## 10. Dependencias y reproducibilidad

La lista actual es mínima y no está fijada por versión. Además:

- `pyarrow` se importa mediante `pyarrow` y `pyarrow.parquet`, pero esos alias no se usan directamente en `ingesta.py`.
- La plataforma objetivo necesitará separar dependencias del pipeline, dbt, ML, notebooks y tests para evitar imágenes excesivas.
- Debe seleccionarse una estrategia de bloqueo reproducible compatible con Docker (por ejemplo, `pyproject.toml` y lock/constraints), sin instalar paquetes al importar módulos.
- El modo demo no debe depender de los millones de filas cuyos resultados quedaron guardados en notebooks; necesita una muestra pequeña, estable, documentada y legalmente publicable o descargable.

No se validó la instalación local ni se ejecutó el código porque la primera tarea prohíbe cambiar dependencias y la solución final no debe depender del entorno Python del host.

## 11. Propuesta de refactorización por fases

### Fase 0 — Gobernanza y saneamiento de publicación

- Incorporar las versiones aprobadas de `AGENTS.md` y `docs/context/TFM_CONTEXT.md`.
- Crear `.env.example`, ampliar `.gitignore`, añadir `.dockerignore` y decidir licencia del código y los activos.
- Retirar del árbol futuro caches, checkpoints y salidas pesadas de notebooks.
- Documentar fuentes/licencias de zonas y muestras.
- Rotar/trasladar credenciales locales.
- Auditar el historial con una herramienta de secretos y decidir la retirada autorizada de PDF de terceros.

**Salida:** repositorio seguro para continuar y publicar, sin modificar aún la lógica de datos.

### Fase 1 — Fundación reproducible y modo demo mínimo

- Crear estructura modular `pipeline/`, `docker/`, `configs/`, `sql/`, `tests/` y `docs/`.
- Añadir Compose con `postgres` y `pipeline` primero, healthchecks y volúmenes; reservar perfiles/servicios para dbt, scheduler, Superset, Redis y Jupyter.
- Implementar un CLI `pipeline run --mode demo` que inicialmente solo verifique configuración y coordinación.
- Fijar versiones y ejecutar todo dentro de contenedores.

**Salida:** `docker compose up -d` y un smoke test reproducible de la base.

### Fase 2 — Bronze idempotente y control operacional

- Modelar `control.pipeline_runs`, `control.pipeline_tasks`, `control.ingestion_files` y `control.data_quality_results`.
- Separar discovery/download/validate/register con contratos por servicio.
- Descargar a temporal, validar, calcular hash y promover atómicamente a `data/bronze/tlc/<service>/<year>/<month>/`.
- Implementar demo pequeño, ejecución full parametrizada, logs JSON, retries y recuperación.

**Salida:** ingesta de los cuatro servicios sin duplicar ni destruir originales.

### Fase 3 — PostgreSQL y dbt Silver

- Crear proyecto dbt, staging por servicio y modelo común homologado.
- Aplicar tipado, deduplicación, límites temporales, validación de zonas y cuarentena con motivo.
- Cargar referencias de zona, calendario/festivos y preparar integración meteorológica documentada.
- Añadir tests dbt de esquema, unicidad, nulos, relaciones y reglas de dominio.

**Salida:** Silver auditable para el modo demo.

### Fase 4 — Gold, modelo dimensional e indicadores

- Implementar dimensiones, `fact_trip`, agregados zona/hora y zona/día.
- Construir marts de movilidad, comparación de servicios, oportunidad, congestión aproximada y rentabilidad simulada.
- Documentar semántica observada/derivada/estimada y diagrama dimensional.

**Salida:** tablas Gold estables, probadas y consumibles.

### Fase 5 — Machine learning reproducible

- Crear dataset de features por servicio, zona y hora sin fuga temporal.
- Comparar baseline, modelo de árboles y boosting con particiones temporales.
- Evaluar horizontes de 1 h y 24 h, persistir predicciones/métricas y versionar artefactos ligeros/metadatos.
- Convertir notebooks en consumidores exploratorios del código, no en la única implementación.

**Salida:** comparación defendible y reproducible de tres modelos.

### Fase 6 — Superset y scheduler

- Añadir Redis, Superset, inicialización reproducible y scheduler basado en cron/Python.
- Construir/exportar datasets, charts y cuatro dashboards en español sin credenciales reales.
- Validar refresco desde Gold y predicciones.

**Salida:** visualización y ejecución programada reproducibles.

### Fase 7 — End-to-end, rendimiento y documentación

- Añadir unitarios, integración, dbt, Compose smoke y E2E demo a CI.
- Medir memoria/tiempos y ajustar DuckDB/Polars/pandas según evidencia.
- Completar runbooks, troubleshooting, arquitectura, catálogo y evidencias de resultados.
- Ejecutar revisión final de secretos, licencias, archivos grandes e historial.

**Salida:** entrega práctica candidata a aprobación; la memoria académica no comienza hasta aprobación expresa.

## 12. Primer conjunto de tareas ejecutables

Orden recomendado para el primer milestone:

| ID | Tarea | Criterio de aceptación | Dependencia |
|---|---|---|---|
| T0-01 | Crear rama temática para la fundación | Rama separada de `main`, sin reescribir historial | Aprobación del diagnóstico |
| T0-02 | Incorporar documentos normativos | `AGENTS.md` y `docs/context/TFM_CONTEXT.md` versionados y legibles en UTF-8 | Confirmar adjuntos definitivos |
| T0-03 | Saneamiento del árbol actual | Caches/checkpoints fuera de Git, ignores completos y ninguna credencial dentro del árbol publicable | Justificar eliminaciones |
| T0-04 | Resolver credenciales locales | Valores rotados si procede y almacenados fuera del repositorio; solo nombres ficticios en `.env.example` | Acción manual/segura del propietario |
| T0-05 | Decisión sobre historial y licencias | Inventario de PDF/activos, evidencia de licencia o plan autorizado de limpieza | No reescribir sin autorización |
| T1-01 | Crear esqueleto de proyecto | Directorios y `pyproject.toml` mínimos, paquete importable dentro del contenedor | T0 completada |
| T1-02 | Crear Compose base | `postgres` y `pipeline` con healthchecks; arranque desde raíz | T1-01 |
| T1-03 | Definir configuración demo/full | Fechas, servicios, rutas y límites en YAML/entorno, sin rutas absolutas | T1-01 |
| T1-04 | Crear CLI del pipeline | `run --mode demo` y `run --mode full --start-date --end-date`, validación y códigos de salida | T1-03 |
| T1-05 | Crear esquema de control | Migración SQL de las cuatro tablas de control y prueba de inicialización | T1-02 |
| T2-01 | Extraer cliente TLC | Discovery testeado para Yellow, Green, FHV y FHVHV sin descargar masivamente | T1-04 |
| T2-02 | Implementar descarga segura | Temporal + timeout + retry + validación + hash + promoción atómica | T2-01, T1-05 |
| T2-03 | Definir muestra demo | Periodo/servicios pequeños, tamaño documentado y ejecución repetible | Confirmar alcance demo |
| T2-04 | Prueba de idempotencia Bronze | Dos ejecuciones demo dejan un fichero físico y dos ejecuciones auditables, sin duplicados | T2-02, T2-03 |

El primer milestone debería terminar en T2-04. Aporta una base demostrable y reduce los riesgos principales antes de invertir en dbt, Gold, ML o dashboards.

## 13. Decisiones que requieren confirmación antes de fases posteriores

No bloquean esta auditoría ni el saneamiento inicial, pero sí trabajos posteriores:

- Fecha final exacta y cobertura real por servicio para la ejecución full.
- Periodo y tamaño del modo demo.
- Estado de WSL2, espacio libre y ubicación del disco virtual de Docker.
- Fuente meteorológica y licencia.
- Licencia del repositorio y redistribución de activos TLC.
- Autorización para rotar credenciales y, en su caso, reescribir el historial Git.
- Confirmación de que no existe código empresarial/confidencial dentro de elementos que se pretendan publicar.

## 14. Diagnóstico final

La base existente debe **conservarse como prototipo y evidencia exploratoria**, pero no extenderse en su forma actual. La estrategia de menor riesgo es extraer sus ideas válidas hacia módulos nuevos, testeables y contenerizados, manteniendo el código antiguo temporalmente hasta que cada sustitución tenga cobertura y aceptación.

La prioridad inmediata es asegurar el repositorio y construir una vertical demo muy estrecha: Compose + PostgreSQL + CLI + control + una descarga Bronze idempotente. Esa vertical validará las decisiones de arquitectura y permitirá continuar con Silver/Gold sin arrastrar los efectos laterales, rutas locales, borrados y problemas de memoria del prototipo.

