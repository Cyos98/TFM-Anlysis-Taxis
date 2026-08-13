# Fase 7: validación y cierre técnico

> Evidencia histórica de la vertical Python. La validación NiFi actual se
> documenta en `nifi_architecture.md`.

## Evidencias

- Docker Compose válido con PostgreSQL, pipeline, scheduler, Redis y Superset.
- Servicios persistentes saludables; Superset responde `200 /health`.
- 16 pruebas unitarias Python correctas.
- 99 nodos dbt correctos.
- Job programado completo ejecutado manualmente con código cero.
- Segunda ejecución ML con resultados exactamente reproducibles.
- Cuatro dashboards, ocho gráficos y siete datasets Superset publicados.
- CI de GitHub Actions con unitarios y E2E hasta ML.
- `git diff --check` sin errores.
- 32 archivos heredados conservados con hash idéntico.
- Bronze, modelos binarios, logs, `.env` y metadatos locales dbt excluidos de Git.
- Exports Superset revisados: URI con contraseña enmascarada, sin secretos en claro.

## Alcance validado

La vertical demo prueba de extremo a extremo infraestructura, contratos,
idempotencia, calidad, modelo dimensional, entrenamiento, persistencia,
programación y visualización. Bronze completo contiene 387 Parquet validados
desde 2018 hasta abril de 2026.

## Limitación pendiente antes de resultados académicos

Los 2.426.523.998 viajes del histórico no se han cargado crudos en PostgreSQL,
por decisión arquitectónica. Silver, Gold y ML actuales validan la vertical
demo; las métricas `synthetic_hourly_v1` no representan rendimiento sobre TLC.

El siguiente incremento funcional, si se aprueba, debe preagregar Bronze con
un motor columnar por mes/servicio, cargar demanda horaria real en PostgreSQL y
repetir dbt/ML/Superset en modo `full`. La memoria académica final no debe
iniciarse hasta que el usuario revise y apruebe la entrega práctica.
