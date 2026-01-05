# 01 Ingesta y ETL/borrado.py

"""
Borra los datasets existentes dentro de "Datasets" en la carpeta que le indiquemos
"""

import os
from dependencias import dependencias

# Función que borra los archivos de una carpeta
def borrar(ruta):
    """
    Borra todos los archivos dentro de la carpeta especificada.
    """
    if not os.path.exists(ruta):
        print(f"⚠️ La carpeta {ruta} no existe.")
        return

    for archivo in os.listdir(ruta):
        ruta_archivo = os.path.join(ruta, archivo)
        if os.path.isfile(ruta_archivo):
            os.remove(ruta_archivo)
            print(f"🗑️ Borrado: {ruta_archivo}")

# Menú de selección de borrado
def borrado():
    ROOT_DIR, BRONZE, SILVER, GOLD = dependencias()  # obtenemos las rutas

    while True:
        try:
            numero = int(input(
                "¿Qué deseas Borrar?\n"
                "\t1: Bronze\n"
                "\t2: Silver\n"
                "\t3: Gold\n"
                "\t4: Todas las anteriores\n"
            ))
            
            if numero == 1:
                print("Borrado de Bronze")
                borrar(BRONZE)
                break
            elif numero == 2:
                print("Borrado de Silver")
                borrar(SILVER)
                break
            elif numero == 3:
                print("Borrado de Gold")
                borrar(GOLD)
                break
            elif numero == 4:
                print("Borrado Total")
                borrar(BRONZE)
                borrar(SILVER)
                borrar(GOLD)
                break
            else:
                print("Número inválido. Debe ser del 1 al 4. Intenta de nuevo.")
        except ValueError:
            print("Entrada no válida. Debes ingresar un número entero.")
