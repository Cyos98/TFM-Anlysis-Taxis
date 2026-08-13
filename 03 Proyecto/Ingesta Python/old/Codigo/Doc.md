# Previo
Existen 3 documentos en esta carpeta, 2 .py y un .ipynb. Estos han de ser modificados para el correcto funcionamiento.
    * dependencias.py : Necesitamos especificar las rutas.
    * install.py : Instalará las dependencias.
    * instalador.ipynb : Mismo que los dos anteriores pero en formato cuaderno.
Una vez definido todo ya podemos comenzar.
# Ingesta y ETL
Se ha dividido el proceso en varios subprocesos
    * Borrado: Para que se pueda borrar los datasets y volver a ingestar.
    * Ingesta: Descarga de todos los parquets
    * ETL: Extracción de los datos ingestados para ser trasformados en las diferentes BBDDs del medallón
        * Bronze: 
        * Silver: 
        * Gold: 
Una vez definido todo ya podemos comenzar.
# Analisis Previo
Para el analisis previo se ha elegido que se examinen los 3 últimos meses para ver las variables más relevantes y así hacer un estudio para tratar nuestros datos. Consta de:
    * Borrado y Descarga de los 3 datasets más actuales de cada tipo.
    * Analisis PCA
    * Matriz de correlación

# Analisis Predictivo

# Orquestador