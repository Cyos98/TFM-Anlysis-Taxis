# 00 Previo/dependencias.py

import subprocess
import sys
import os

"""
Definimos las rutas de nuestro sistema.
"""
def dependencias ():
    # Obtiene la ruta absoluta del directorio raíz del proyecto
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print ("La ruta principal es " + ROOT_DIR)

    # Obtiene la ruta absoluta para el alojamiento de datos
    BRONZE = os.path.abspath(os.path.join(ROOT_DIR, "Datasets", "Bronze"))
    SILVER = os.path.abspath(os.path.join(ROOT_DIR, "Datasets", "Silver"))
    GOLD = os.path.abspath(os.path.join(ROOT_DIR, "Datasets", "Gold"))

    # Obtenemos la ruta de los datos 
    URL = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"

    # ...

    #Return: con _, ignoramos aquellas variables que no quisieramos
    return ROOT_DIR, BRONZE, SILVER, GOLD, URL

"""
Instala los paquetes listados en requirements.txt
"""
def instalar():
    ruta_requirements = os.path.join(
        os.path.dirname(__file__),
        "requirements.txt"
    )
    
    print(f"Comprobando dependencias desde requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", ruta_requirements])
    print("Instalación completada.")

instalar()