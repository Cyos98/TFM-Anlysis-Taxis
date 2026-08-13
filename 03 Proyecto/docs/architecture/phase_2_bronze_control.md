# Arquitectura de la fase 2: Bronze y control

> Documento histórico de la implementación Python. Consulte
> `nifi_architecture.md` para el estado principal actual.

## Flujo

```text
demo sintética                    índice oficial TLC
      |                                  |
      +------------- discovery ---------+
                        |
                        v
              control.ingestion_files
                        |
              temporal + SHA-256
                        |
                  validación Parquet
                        |
          +-------------+--------------+
          |                            |
       válido                       inválido
          |                            |
   promoción Bronze              quarantine/bronze
          |                            |
          +------ resultados de calidad+
                        |
             control.pipeline_runs/tasks
```

## Idempotencia

La identidad lógica incluye fuente, servicio, año, mes y nombre. El fichero físico se comprueba con SHA-256 antes de reutilizarse. Una segunda ejecución:

- Crea una nueva fila en `pipeline_runs` para preservar la auditoría.
- Reutiliza las cuatro filas de `ingestion_files`.
- Revalida los Parquet y persiste nuevos resultados de calidad.
- Marca las tareas de fichero como `SKIPPED`.
- No crea copias ni concatena datos.

## Seguridad frente a fallos

- Las descargas se escriben con extensión temporal única.
- Se comprueba `Content-Length` cuando el servidor lo proporciona.
- El fichero temporal se sincroniza y se promociona mediante rename atómico.
- Se aplican timeout y reintentos limitados con backoff.
- Un fichero existente con hash inesperado o Parquet inválido se traslada a cuarentena; no desaparece silenciosamente.
- Demo y TLC real usan namespaces físicos y claves lógicas diferentes.

## Modos

### Demo

Genera localmente dos filas sintéticas por servicio. Permite probar control, Parquet, calidad e idempotencia sin descargar datos TLC.

### Full

Consulta el índice oficial, filtra por mes y servicio y descarga cada Parquet original. La fecha final es obligatoria. Antes de ejecutarlo debe usarse `discover` y confirmarse el volumen.
