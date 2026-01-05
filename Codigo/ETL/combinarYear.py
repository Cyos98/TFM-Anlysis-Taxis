# 01 Ingesta y ETL/borrado.py

"""
Combina por tipos los distintos archivos
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
from dependencias import dependencias

# Menú de selección de borrado
def ingesta():
    #Importamos las rutas del dependencias
    dependencias = dependencias()  # obtenemos las rutas
    URL = dependencias[4] #Url donde obtenemos los datos
    BRONZE = dependencias[1] # Destino donde aterrizaran los datos

#📂 Carpeta de entrada (donde están los archivos individuales)
input_dir = r"C:\Users\carlo\Documents\TFM\01 Datasets\01 Grouped Data"

# 📂 Carpeta de salida (donde irá el archivo combinado final)
final_dir = r"C:\Users\carlo\Documents\TFM\01 Datasets\02 Full Dataset"
os.makedirs(final_dir, exist_ok=True)

# 📄 Nombre del archivo final
output_file = os.path.join(final_dir, "all_dataset.parquet")

# Categorías y nombres de archivos
categories = {
    "yellow": "yellow_tripdata.parquet",
    "green": "green_tripdata.parquet",
    "fhv": "fhv_tripdata.parquet",
    "hvfhv": "hvfhv_tripdata.parquet"
}

dfs = []

for cat, filename in categories.items():
    path = os.path.join(input_dir, filename)

    if not os.path.exists(path):
        print(f"⚠️ Archivo no encontrado: {path}")
        continue

    try:
        df = pd.read_parquet(path)
        df["categoria"] = cat
        dfs.append(df)
        print(f"✅ Cargado: {filename} ({len(df)} filas)")
    except Exception as e:
        print(f"❌ Error leyendo {filename}: {e}")

# Concatenar y guardar
if dfs:
    all_data = pd.concat(dfs, ignore_index=True)
    all_data.to_parquet(output_file, index=False)
    print(f"\n✅ Archivo combinado guardado en: {output_file}")

"""
    # Borrar los archivos individuales
    for filename in categories.values():
        path = os.path.join(input_dir, filename)
        try:
            os.remove(path)
            print(f"🗑️ Borrado: {filename}")
        except Exception as e:
            print(f"⚠️ No se pudo borrar {filename}: {e}")
"""
else:
    print("⚠️ No se cargaron datos. Verifica los archivos.")
