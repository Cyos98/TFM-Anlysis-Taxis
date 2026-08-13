# Arquitectura de la fase 1

> Documento histórico de la implementación Python preservada en
> `Ingesta Python/`; la arquitectura principal actual usa NiFi.

## Objetivo

Establecer una base local reproducible antes de implementar la ingesta y las transformaciones.

```text
Usuario / Docker Compose
          |
          +--> pipeline (Python 3.11, usuario no privilegiado)
          |        |
          |        +--> configuración TOML
          |        +--> validación demo/full
          |        +--> logs JSON
          |
          +--> postgres (PostgreSQL 16)
                   |
                   +--> control
                   +--> silver
                   +--> gold
```

## Decisiones

- El host solo necesita Docker, Compose y Git.
- El pipeline es un contenedor de tareas y mantiene un proceso ligero en espera para que `docker compose up -d` deje el servicio saludable.
- Las ejecuciones manuales usan `docker compose run --rm pipeline ...`.
- La imagen del pipeline no instala dependencias en tiempo de ejecución y no incluye el directorio `old/`.
- La configuración no contiene contraseñas. Las credenciales locales llegan mediante variables de entorno y nunca se imprimen.
- El volumen PostgreSQL es persistente; `data/` y `logs/` se montan desde el workspace y están excluidos de Git.

## Límites de esta fase

La fase 1 no descarga TLC, no crea tablas de control, no ejecuta dbt y no implementa Silver/Gold. El SQL inicial crea únicamente los esquemas para comprobar la base técnica.
