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

#Si lo quiero desde drive
data_dir = r"C:\Users\carlo\Documents\TFM\01 Datasets\00 Raw Data"

#Si lo si quisiera acumular en drive:
output_dir = r"C:\Users\carlo\Documents\TFM\01 Datasets\01 Grouped Data"

os.makedirs(output_dir, exist_ok=True)

# 🗓️ Rango de años que quieres procesar
year_min = 2021
year_max = 2025

# 🔧 Formato de salida
output_format = "parquet"

# Categorías y sus archivos
categories = {
    "yellow": [],
    "green": [],
    "fhv": [],
    "hvfhv": []
}

# Clasificar los archivos por tipo
for file in os.listdir(data_dir):
    lower = file.lower()
    path = os.path.join(data_dir, file)

    if "yellow" in lower:
        categories["yellow"].append(path)
    elif "green" in lower:
        categories["green"].append(path)
    elif "fhv" in lower and "hvfhv" not in lower:
        categories["fhv"].append(path)
    elif "hvfhv" in lower:
        categories["hvfhv"].append(path)

# Regex para extraer año y mes
pattern = re.compile(r"(\d{4})-(\d{2})")

# Procesar cada categoría
for cat, files in categories.items():
    print(f"\n📦 Procesando categoría: {cat}")
    dfs = []

    for file in tqdm(sorted(files)):
        match = pattern.search(file)
        if not match:
            print(f"⚠️ Año y mes no encontrados en {file}")
            continue

        year, month = map(int, match.groups())

        # 👉 FILTRO POR RANGO DE AÑOS
        if not (year_min <= year <= year_max):
            continue

        try:
            df = pd.read_parquet(file)
            df["year"] = year
            df["month"] = month
            dfs.append(df)

            # Eliminar el archivo original
            ##os.remove(file)

        except Exception as e:
            print(f"❌ Error procesando {file}: {e}")

    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)
        output_path = os.path.join(output_dir, f"{cat}_tripdata.{output_format}")

        if output_format == "csv":
            full_df.to_csv(output_path, index=False)
        else:
            full_df.to_parquet(output_path, index=False)

        print(f"✅ Guardado: {output_path}")
    else:
        print(f"⚠️ No hay datos dentro del rango {year_min}–{year_max} para {cat}")