# Comparación técnica: Python + cron frente a Apache NiFi

La comparación describe las implementaciones de este repositorio, no una regla
universal sobre ambas tecnologías.

| Criterio | Python + cron | Apache NiFi |
|---|---|---|
| Orquestación | Secuencia explícita en `orchestrator.py` | Grafo de Process Groups y conexiones |
| Scheduling | Expresión cron en contenedor separado | Scheduling por procesador o grupo |
| Observabilidad | Logs JSON y tablas de control | UI, colas, bulletins, métricas y logs |
| Provenance | Auditoría construida por la aplicación | Data Provenance nativo por FlowFile |
| Retry | Decoradores/bucles y estados propios | Relaciones Retry/Failure y `RetryFlowFile` |
| Configuración | TOML + entorno | Parameter Contexts + entorno sensible |
| Mantenibilidad | Cómodo para lógica algorítmica; exige conocer código | Flujo operacional visible; exige disciplina al versionarlo |
| Versionado | Git directo sobre Python | Especificación declarativa + bootstrap REST en Git |
| Complejidad | Menos servicios y menor coste inicial | Más componentes, repositorios y conceptos operativos |
| Consumo recursos | Bajo para la demo | JVM y repositorios persistentes; heap local de 512 MiB–2 GiB |
| Backpressure | Debe programarse | Capacidad nativa por conexión |
| Secretos | Variables de entorno | Variables de entorno y parámetros sensibles |
| Transformación analítica | No era su responsabilidad final | Tampoco: continúa en dbt |
| Machine Learning | Adecuado y se conserva | Solo dispara el servicio Python ML |

## Decisión

NiFi es la arquitectura principal para movimiento y coordinación de datos. dbt
sigue siendo el propietario de Silver/Gold y Python del ML. La versión anterior
permanece ejecutable en `Ingesta Python/` para comparar mantenibilidad,
observabilidad y reproducibilidad con la migración.

La ventaja prevista de NiFi en provenance y operación ya es verificable. La
vertical demo local e idempotente está implementada; la ingesta TLC remota
completa sigue **PARTIAL**, así que no se atribuyen todavía mejoras de tiempo,
fiabilidad ni volumen sobre el histórico real.
