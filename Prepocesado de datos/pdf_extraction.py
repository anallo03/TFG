"""
Trabajo de fin de grado. (Ingeniería Matemática UCM)

Título: El problema de la dieta y su aplicación en escaladores de competición
Autor: Ana Llorente García


Este script crea un archivo JSON (food_data.json) con los datos nutricionales de alimentos extraídos de PDFs.
"""

import pdfplumber
import pandas as pd
from os import listdir
import unicodedata
import json

# Rutas de los directorios donde se encuentran los archivos CSV, PDF y donde se guardarán los datos extraídos
CSVS_PATH = "./csvs"
PDFS_PATH = "./pdfs"
DATA_PATH = "./data"

# Lista de categorías de alimentos que se buscarán en los PDFs
CATEGORIES = [
    "Cereales y derivados", "Leche y productos lácteos", "Huevos", "Azúcares y dulces", 
    "Aceites y grasas", "Carnes y productos cárnicos", "Pescados", "Verduras y hortalizas", 
    "Frutas", "Legumbres", "Frutos secos", "Condimentos y aperitivos", "Bebidas", "Crustáceos y moluscos"
]

# Obtiene la lista de todos los archivos PDF en el directorio especificado
allFiles = listdir(PDFS_PATH)

# Diccionario final donde se almacenarán los datos extraídos de todos los alimentos
finalJson = {}

def clean_text(text):
    """
    Limpia y normaliza el texto extraído de los PDFs.
    Reemplaza guiones largos por guiones normales y elimina espacios innecesarios.
    """
    if text is None:
        return ""
    text = text.strip()
    text = text.replace("\u2014", "-")  # Reemplaza guion largo por guion normal
    text = text.replace("\u2013", "-")  # Reemplaza otro tipo de guion
    return text

# Itera sobre cada archivo PDF encontrado en el directorio
for doc in allFiles:
    pdfPath = f"{PDFS_PATH}/{doc}"

    nutritionalData = []

    # Apertura del archivo PDF y extracción de los datos
    with pdfplumber.open(pdfPath) as pdf:
        for nPage, page in enumerate(pdf.pages):
            # Extracción de las tablas de la página (se asume que solo hay una tabla por página)
            tables = page.extract_tables()
            # Extracción del texto de la página
            text = page.extract_text()
            # Busca la categoría del alimento en el texto de la página
            for word in CATEGORIES:
                if word.title() in text.title():
                    nutritionalData.append(["Categoría", word])
                    break
            # Procesa cada tabla encontrada en la página
            for table in tables:
                for row in table:
                    # Filtra filas con al menos dos columnas y datos válidos
                    if row and len(row) >= 2 and row[0] is not None and row[1] is not None:
                        nutrient = clean_text(row[0])
                        value100g = clean_text(row[1])
                        value100g = str(value100g).replace(",", ".")
                        # Solo extrae los nutrientes de interés
                        if nutrient in ["Energía (Kcal)", "Proteínas (g)", "Hidratos de carbono (g)", "Lípidos totales (g)"]:
                            nutritionalData.append([nutrient, value100g])

    # Crea un DataFrame con los datos nutricionales extraídos
    df = pd.DataFrame(nutritionalData, columns=["Nutriente", "Valor por 100g"])

    # Extrae el nombre del alimento a partir del nombre del archivo PDF
    foodName = doc.split('.')[0]  # Se toma el nombre del archivo como nombre del alimento
    
    # Crea un diccionario con los nutrientes de este alimento
    nutrientsDic = dict(zip(df['Nutriente'], df['Valor por 100g']))
    
    # Añade el alimento y sus nutrientes al diccionario principal
    finalJson[foodName] = nutrientsDic

# Guarda el diccionario final en un archivo JSON codificado en ISO-8859-1
with open(f"{DATA_PATH}/food_data.json", "w", encoding="ISO-8859-1") as f:
    json.dump(finalJson, f, ensure_ascii=False, indent