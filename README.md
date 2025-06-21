# Trabajo de Fin de Grado - Ingeniería Matemática UCM

**Título:** El problema de la dieta y su aplicación en escaladores de competición  
**Autor:** Ana Llorente García

## Estructura del repositorio

1. **Carpeta:** `pdfs`  
   Datos de alimentos (PDFs descargados).

2. **Carpeta:** `prepocesado de datos`  
   - `pdf_downloader.py`: Script que descarga los PDFs de alimentos desde la web del gobierno de España.  
   - `pdf_extraction.py`: Script que convierte los PDFs descargados a un archivo JSON con los datos de alimentos.  
   - `food_data.json`: Archivo JSON con los datos de alimentos extraídos de los PDFs.

3. `alimentos.json`  
   Archivo JSON con los datos de alimentos procesados y listos para ser utilizados en los modelos.

4. `recetas.json`  
   Archivo JSON con las recetas por franja horaria, incluyendo ingredientes y cantidades.

5. `Modelo1.py`  
   Script que resuelve el Modelo 1 con Gurobi.

6. `Modelo2.py`  
   Script que resuelve el Modelo 2 con Gurobi.

7. `Modelo3_alimentos.py`  
   Script que resuelve el Modelo 3 con alimentos con Gurobi.

8. `Modelo3_recetas.py`  
   Script que resuelve el Modelo 3 con recetas con Gurobi.

9. `ModeloIA.py`  
   Script que utiliza la API de Google Gemini para generar menús diarios a partir del resultado del Modelo 3 con alimentos.
