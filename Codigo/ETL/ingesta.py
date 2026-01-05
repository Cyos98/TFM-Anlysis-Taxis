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

# Propias
from dependencias import dependencias
from funciones import anos
from dependencias import instalar

# Menú de selección de borrado
def ingesta():
    #Comprobación todo esta instalado
    instalar()

    #Importamos las rutas del dependencias
    PATHS = dependencias()  # obtenemos las rutas
    url = PATHS[4] #Url donde obtenemos los datos
    BRONZE = PATHS[1] # Destino donde aterrizaran los datos

    #Lanzamos años de inicio y fin:
    ST_YEAR, END_YEAR = anos()

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

ingesta()