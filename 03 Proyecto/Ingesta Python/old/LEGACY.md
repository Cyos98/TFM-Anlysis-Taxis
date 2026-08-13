# Proyecto legado

Esta carpeta conserva el prototipo existente antes de iniciar la nueva arquitectura.

No se ha eliminado contenido. Se han trasladado aquí:

- Scripts y notebooks de `Codigo/`.
- Marcadores Bronze/Silver/Gold de `Datasets/`.
- Lookup, shapefile y mapas de `Zonas/`.
- README original.

El código se mantiene como referencia y fuente de lógica reutilizable, pero no se copia a las imágenes Docker ni forma parte del pipeline nuevo. Consulte `docs/audit/initial_repository_audit.md` para conocer los motivos y el plan de sustitución.

No ejecute los scripts de borrado o combinación sobre datos que necesite conservar: algunos flujos antiguos eliminan archivos de origen.
