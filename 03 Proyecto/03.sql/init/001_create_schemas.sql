-- Base mínima de PostgreSQL para la fase 1.
-- Las tablas de control y los modelos analíticos se añadirán en fases posteriores.

CREATE SCHEMA IF NOT EXISTS control;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

COMMENT ON SCHEMA control IS 'Auditoría y estado de ejecuciones del pipeline';
COMMENT ON SCHEMA silver IS 'Datos normalizados y validados';
COMMENT ON SCHEMA gold IS 'Modelo dimensional, marts y resultados analíticos';
