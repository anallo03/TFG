"""
Trabajo de fin de grado. (Ingeniería Matemática UCM)

Título: El problema de la dieta y su aplicación en escaladores de competición
Autor: Ana Llorente García


Este script 
    1. Obtiene los enlaces de las subpáginas de productos.
    2. Extrae los enlaces de los PDFs.
    3. Descarga los PDFs.
"""

from time import sleep
import random
from bs4 import BeautifulSoup
import requests
import csv

# Data incial
DATA_PATH = "./data"
PDFS_PATH = "./pdfs"
DOMAIN_WEB = "https://www.mapa.gob.es"
MAIN_WEB = "https://www.mapa.gob.es/es/ministerio/servicios/informacion/plataforma-de-conocimiento-para-el-medio-rural-y-pesquero/observatorio-de-buenas-practicas/buenas-practicas-sobre-alimentacion/caract-nutricionales.aspx"


def get_urls():
    """
    Extrae los enlaces de las subpáginas de productos desde la página principal.
    Guarda los enlaces en un archivo CSV y los retorna como lista.
    """
    urlLinks = []
    response = requests.get(MAIN_WEB)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        div = soup.find("div", class_="panel-info") # Extraer la etiqueta <div> que contiene el listado de links de los PDFs
        li = div.find_all("li")[:-1] # Extraer las etiquetas <li> que contienen los links de interés
        
        for i in li:
            link = DOMAIN_WEB + i.find("a")["href"] # Extraer los links de las etiquetas <a>
            if link not in urlLinks:
                urlLinks.append(link)
            
        
    with open("./data/urls.csv", "w", newline="") as file: # Guardar los links en un archivo CSV
        writer = csv.writer(file)
        writer.writerow(["URL"])
        for url in urlLinks:
            writer.writerow([url])
            
    return urlLinks
    
def get_pdfs_links(urlLinks: list):
    """
    Extrae los enlaces directos a los PDFs desde las subpáginas de productos.
    Guarda los enlaces y nombres de los alimentos en un archivo CSV.
    Retorna una lista de diccionarios con 'food' y 'link'.
    """
    pdfLinks = []
    for url in urlLinks:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            div = soup.find("div", class_="panel-info") # Extraer la etiqueta <div> que contiene el listado de links de los PDFs
            li = div.find_all("li") # Extraer las etiquetas <li> que contienen los links de los PDFs
            
            for i in li:
                link = DOMAIN_WEB + i.find("a")["href"]
                food = i.find("a").text
                pdfLinks.append({"food": food, "link": link})
                
    with open("./data/pdfLinks.csv", "w", newline="") as file: # Guardar los links en un archivo CSV
        writer = csv.writer(file)
        writer.writerow(["PDF URL"])
        for pdf in pdfLinks:
            writer.writerow([pdf])
    
    return pdfLinks
            
def download_pdfs(pdfLinks: list):
    """
    Descarga los archivos PDF desde los enlaces proporcionados.
    Guarda cada PDF en la carpeta especificada con el nombre del alimento.
    """
    for pdf in pdfLinks:
        food = pdf["food"]
        link = pdf["link"]
        response = requests.get(link, stream=True)
        if response.status_code == 200:
            with open(f"{PDFS_PATH}/{food}.pdf", "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"PDF descargado correctamente como '{food}.pdf'")
        else:
            print(f"Error al descargar el PDF. Código de estado: {response.status_code}")
        
        
def main():
    '''
    Función principal que ejecuta el flujo completo:
    1. Obtiene los enlaces de las subpáginas de productos.
    2. Extrae los enlaces de los PDFs.
    3. Descarga los PDFs.
    '''
    urlLinks = get_urls()
    pdfLinks = get_pdfs_links(urlLinks)
    download_pdfs(pdfLinks)

if __name__ == "__main__":
    main()