# -*- coding: utf-8 -*-
"""
Trabajo de fin de grado. (Ingeniería Matemática UCM)

Título: El problema de la dieta y su aplicación en escaladores de competición
Autor: Ana Llorente García


Este script determina la dieta óptima semanal para una escaladora de competición
usando la API de Google Gemini para generar menús diarios a partir de una dieta semanal.    
Utilizando los resultados del Modelo 3 con alimentos.
"""

import re
import google.generativeai as genai

# Configurar la API de Google Gemini (a rellenar por el usario)
genai.configure(api_key="")

# Inicializar el modelo de Gemini (asegúrate de haber configurado las credenciales antes)
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

# Función para cargar la dieta desde un archivo .txt 
def cargar_dieta_desde_txt(ruta_txt):
    """
    Carga una dieta semanal desde un archivo de texto con formato específico. (Facilita el análisis a la IA)
    El archivo debe contener días, franjas horarias y alimentos con cantidades.
    Devuelve un diccionario estructurado por día y franja horaria.
    """
    dieta = {}
    dia_actual = None
    franja_actual = None

    with open(ruta_txt, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            # Ignora líneas vacías o de encabezado
            if not linea or "Dieta óptima encontrada" in linea:
                continue

            # Detecta el inicio de un nuevo día
            match_dia = re.match(r"Día:\s*(\d+)", linea)
            if match_dia:
                dia_actual = f"Día {match_dia.group(1)}"
                dieta[dia_actual] = {}
                continue

            # Detecta la franja horaria (Desayuno, Comida, Merienda, Cena)
            if linea.endswith(":") and linea[:-1] in ["Desayuno", "Comida", "Merienda", "Cena"]:
                franja_actual = linea[:-1]
                dieta[dia_actual][franja_actual] = {}
                continue

            # Detecta alimentos y cantidades en gramos
            match_alimento = re.match(r"(.+?):\s*([\d.]+)\s*g", linea)
            if match_alimento and dia_actual and franja_actual:
                alimento = match_alimento.group(1).strip()
                cantidad = float(match_alimento.group(2))
                dieta[dia_actual][franja_actual][alimento] = cantidad
                continue

            # Detecta el coste total de la dieta
            match_coste = re.match(r"Coste total:\s*([\d.]+)\s*€", linea)
            if match_coste:
                dieta["Coste total"] = float(match_coste.group(1))

    return dieta

# Función para generar el prompt para Gemini
def generar_prompt_semanal(dieta_semanal):
    """
    Genera un prompt detallado para Gemini a partir de la dieta semanal.
    El prompt solicita la creación de menús diarios con nombres de platos y descripciones,
    usando únicamente los ingredientes y cantidades especificados.
    """
    prompt = (
        "Eres un chef profesional. A partir de los siguientes ingredientes por franja horaria y día,"
        "crea un menú completo diario elaborado con nombres de platos y descripciones que sea apetitoso."
        "No añadas ningún ingrediente extra  e incluye todos los alimentos disponibles en cada franja."
        "En la descripción indica los gramos de cada ingrediente."
        "En la comida y la cena siempre debe haber primer plato, segundo plato y postre. "
        "Da sugerencias de diferentes platos para cada día aunque los ingredientes sean los mismos"
    )

    for dia, dieta_diaria in dieta_semanal.items():
        if dia == "Coste total":
            continue
        prompt += f"--- {dia} ---\n"
        for franja, alimentos in dieta_diaria.items():
            prompt += f"{franja}:\n"
            for alimento, cantidad in alimentos.items():
                prompt += f"  - {alimento}: {cantidad:.2f} g\n"
            prompt += "\n"

    if "Coste total" in dieta_semanal:
        prompt += f"Coste total semanal: {dieta_semanal['Coste total']} €\n"

    return prompt

# Función que llama a Gemini
def generar_menu_con_gemini(dieta):
    """
    Llama al modelo Gemini con el prompt generado a partir de la dieta y devuelve el menú generado.
    """
    prompt = generar_prompt_semanal(dieta)
    response = model.generate_content(prompt)
    return response.text

# Función principal para ejecutar el script
if __name__ == "__main__":
    # Cargar la dieta desde el archivo .txt
    dieta_modelo = cargar_dieta_desde_txt("Resultados/dieta_optima_Modelo3_alimentos.txt")

    # Generar el menú con Gemini
    menu_generado = generar_menu_con_gemini(dieta_modelo)

    # Guardar el resultado en un archivo
    with open("Resultados/dieta_óptima_IA.txt", "w", encoding="utf-8") as f:
        f.write(menu_generado)

