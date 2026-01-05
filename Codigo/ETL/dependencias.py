# 00 Previo/dependencias.py

"""
Definimos las rutas de nuestro sistema.
"""

import subprocess
import sys
import os

def dependencias ():
    # Obtiene la ruta absoluta del directorio raíz del proyecto
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print ("La ruta principal es " + ROOT_DIR)

    # Obtiene la ruta absoluta para el alojamiento de datos
    BRONZE = os.path.abspath(os.path.join(ROOT_DIR, "Datasets", "Bronze"))
    SILVER = os.path.abspath(os.path.join(ROOT_DIR, "Datasets", "Silver"))
    GOLD = os.path.abspath(os.path.join(ROOT_DIR, "Datasets", "Gold"))

    # ...

    #Return:
    return ROOT_DIR, BRONZE, SILVER, GOLD