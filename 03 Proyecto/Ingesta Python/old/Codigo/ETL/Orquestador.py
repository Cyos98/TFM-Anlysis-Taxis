#Previo

from funciones import borrado
from ingesta import tipoIngesta
#3from ETL import ETL


while True:
    try:
        numero = int(input(
            "¿Qué deseas hacer?\n"
            "\t0: Nada - Salir del sistema\n"
            "\t1: Borrado - Borrar los datasets de las BBDDs\n"
            "\t2: Ingesta - Ingesta de datos en las BBDDs\n"
            "\t3: ETL - Trasformar y limpiar los datos\n"
        ))
        if numero == 0:
            print("Bye")
            exit()
            break   
        if numero == 1:
            print("Borrado")
            borrado()
            break
        elif numero == 2:
            print("Ingesta")
            tipoIngesta()
            break
        elif numero == 3:
            print("ETL")
            #ETL()
            break
        else:
            print("Número inválido. Debe ser del 1 al 3. Intenta de nuevo.")
    except ValueError:
        print("Entrada no válida. Debes ingresar un número entero.")
