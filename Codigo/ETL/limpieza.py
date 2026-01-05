# 01 Ingesta y ETL/borrado.py

"""
Borra los datasets existentes dentro de "01 Datasets" en la carpeta que le indiquemos
"""

import subprocess
import sys
from Codigo.ETL import dependencias

def instalar():

    print(f"Comprobando dependencias desde requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Instalación completada.")