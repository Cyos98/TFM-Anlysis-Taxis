# 00 Previo/Install.py

"""
Instala los paquetes listados en requirements.txt
"""

import subprocess
import sys

def instalar():

    print(f"Comprobando dependencias desde requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Instalación completada.")