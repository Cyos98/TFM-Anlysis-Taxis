# 01 Ingesta y ETL/borrado.py

"""
Modificaciones
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
from dependencias import instalar

def ETL():
    #Comprobación todo esta instalado
    instalar()

    #Importamos las rutas del dependencias
    _, BRONZE, SILVER, GOLD, _ = dependencias()  # obtenemos las rutas

    #Llamamos a la ETL
    silver(BRONZE,SILVER)
    gold(SILVER,GOLD)




##########################################    SILVER    ##########################################

"""
Limpieza
"""
def silver(input_Path, output_path):



##########################################    GOLD    ##########################################

"""
Dimensiones
"""

"""
Hechos
"""
def gold(input_Path, output_path):
    