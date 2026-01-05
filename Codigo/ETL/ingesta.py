# 01 Ingesta y ETL/borrado.py

"""
Descarga todos los datasets que le indiquemos
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Propias
from dependencias import dependencias
from funciones import anos
from dependencias import instalar

def tipoIngesta():
    #Comprobación todo esta instalado
    instalar()
    #Importamos las rutas del dependencias
    PATHS = dependencias()  # obtenemos las rutas
    global url
    url = PATHS[4] #Url donde obtenemos los datos
    global BRONZE 
    BRONZE = PATHS[1] # Destino donde aterrizaran los datos

    #Lanzamos años de inicio y fin:
    global ST_YEAR 
    global END_YEAR
    ST_YEAR, END_YEAR = anos()  

    #Lanzamos la ingesta que necesitemos:
    while True:
        try:
            numero = int(input(
                "¿Qué deseas hacer?\n"
                "\t1: Ingesta simple - Solo importamos los .parquet\n"
                "\t2: Ingesta por categorias - Se importan los .parquet y se guardan por tipo de vehiculo\n"
                "\t3: Ingesta Combinada - Se Combinan todos los .parquet en un unico dataset\n"
            ))
            
            if numero == 1:
                print("Ingesta simple")
                ingestaSimp()
                break
            elif numero == 2:
                print("Ingesta por categorias")
                ingestaCateg()
                break
            elif numero == 3:
                print("Ingesta Combinada")
                ingestaComb()
                break
            else:
                print("Número inválido. Debe ser del 1 al 3. Intenta de nuevo.")
        except ValueError:
            print("Entrada no válida. Debes ingresar un número entero.")
    

"""
Ingesta simple, sin modificaciones.
"""
def ingestaSimp():
    # Obtener HTML de la página
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los enlaces a archivos .parquet
    links = soup.find_all("a", href=True)
    parquet_links = [
        a["href"] for a in links
        if ".parquet" in a["href"].lower()
    ]

    # Filtrar solo los años deseados
    pattern = re.compile(r"(\d{4})-(\d{2})\.parquet", re.IGNORECASE)
    filtered_links = []

    for link in parquet_links:
        match = pattern.search(link)
        if match:
            year = int(match.group(1))
            if ST_YEAR <= year <= END_YEAR:
                # Asegurar URL completa
                if link.startswith("/"):
                    full_url = "https://www.nyc.gov" + link
                else:
                    full_url = link
                filtered_links.append(full_url)

    # Descargar archivos
    print(f"Se encontraron {len(filtered_links)} archivos. Iniciando descarga...\n")

    for file_url in tqdm(filtered_links):
        # Strip any trailing whitespace from the URL
        clean_file_url = file_url.strip()
        filename = os.path.basename(clean_file_url)
        dest_path = os.path.join(BRONZE, filename)

        if not os.path.exists(dest_path):
            # Use the cleaned URL for the request
            with requests.get(clean_file_url, stream=True) as r:
                r.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        else:
            print(f"{filename} ya existe, se omite.")

    print("\n✅ Descarga completada.")

"""
Ingesta combinando por tipos las distintas categorias. Esta borra todo lo que no sea el dataset final.
"""
def ingestaCateg():
    #Ejecutamos la ingesta simple primero para obtener el dato en crudo
    ingestaSimp()

    #rutas de origen y destino (En este caso la misma)
    input_dir = BRONZE
    output_dir = BRONZE

    # Formato de salida
    output_format = "parquet"

    # Categorías y sus archivos
    categories = {
        "yellow": [],   # Yellow Taxies
        "green": [],    # Green Trips
        "fhv": [],      # For hire vehicles
        "fhvhv": []     # High volume FHV companies (e.g., Uber, Lyft, Juno and Via) 
    }

    # Clasificar los archivos por tipo
    for file in os.listdir(input_dir):
        lower = file.lower()
        path = os.path.join(input_dir, file)

        if "yellow" in lower:
            categories["yellow"].append(path)
        elif "green" in lower:
            categories["green"].append(path)
        elif "fhv" in lower and "fhvhv" not in lower:
            categories["fhv"].append(path)
        elif "fhvhv" in lower:
            categories["fhvhv"].append(path)

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

            # FILTRO POR RANGO DE AÑOS
            if not (ST_YEAR <= year <= END_YEAR):
                continue

            try:
                df = pd.read_parquet(file)
                df["year"] = year
                df["month"] = month
                dfs.append(df)
                os.remove(file) # Eliminar el archivo original

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
            print(f"⚠️ No hay datos dentro del rango {ST_YEAR}–{END_YEAR} para {cat}")

"""
Ingesta combinando por tipos los distintos archivos por años. Esta borra todo lo que no sea el dataset final.
"""
def ingestaComb():
    #Ejecutamos la ingesta categorizada primero para obtener el dato por categorias
    ingestaCateg()

    #rutas de origen y destino (En este caso la misma)
    input_dir = BRONZE
    output_dir = BRONZE
    #os.makedirs(output_dir, exist_ok=True) #Comprobacion que existe BRONZE

    # 📄 Nombre del archivo final
    output_file = os.path.join(output_dir, "all_dataset.parquet")

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

        # Borrado los archivos individuales
        for filename in categories.values():
            path = os.path.join(input_dir, filename)
            try:
                os.remove(path)
                print(f"🗑️ Borrado: {filename}")
            except Exception as e:
                print(f"⚠️ No se pudo borrar {filename}: {e}")
    else:
        print("⚠️ No se cargaron datos. Verifica los archivos.")

tipoIngesta()