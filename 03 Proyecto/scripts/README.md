# Scripts operativos

- `e2e_demo.sh`: ejecuta la vertical local NiFi → Bronze → PostgreSQL → dbt →
  Silver/Gold → ML y comprueba las dos filas deterministas.

El script no descarga TLC ni elimina volúmenes o datos locales. La eliminación
de volúmenes solo aparece en la limpieza del runner efímero de CI.
