# 01 Ingesta y ETL/borrado.py



import os
from dependencias import dependencias

"""
Borra los datasets existentes dentro de "Datasets" en la carpeta que le indiquemos
"""
# Función que borra los archivos de una carpeta
def borrar(ruta):
    """
    Borra todos los archivos dentro de la carpeta especificada.
    """
    for archivo in os.listdir(ruta):
        ruta_archivo = os.path.join(ruta, archivo)
        if os.path.isfile(ruta_archivo):
            os.remove(ruta_archivo)
            print(f"🗑️ Borrado: {ruta_archivo}")

# Menú de selección de borrado
def borrado():
    Dependencias = dependencias()  # obtenemos las rutas
    BRONZE = Dependencias[1]
    SILVER = Dependencias[2]
    GOLD = dependencias[3]
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

"""
Definimos años de inicio y de fin para la ingesta/combinación
"""
def anos():
    print("Teniendo en cuenta que el primer año en que disponemos de datos es 2009 y el último 2025")

    # Año inicio
    while True:
        try:
            ST_YEAR = int(input("¿Cuál quieres que sea el año de inicio? "))
            if 2009 <= ST_YEAR <= 2025:
                break
            else:
                print("Número inválido. Intenta de nuevo.")
        except ValueError:
            print("Entrada no válida. Debes ingresar un número entero.")

    # Año fin
    while True:
        try:
            END_YEAR = int(input("¿Cuál quieres que sea el año de fin? "))
            if not (2009 <= END_YEAR <= 2025):
                print("Número inválido. Intenta de nuevo.")
            elif END_YEAR < ST_YEAR:
                print("El año fin no puede ser menor que el año de inicio.")
            else:
                print(f"Las fechas elegidas son de {ST_YEAR} a {END_YEAR}")
                break
        except ValueError:
            print("Entrada no válida. Debes ingresar un número entero.")

    return ST_YEAR, END_YEAR

"""
Definimos 
"""