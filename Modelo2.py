# -*- coding: utf-8 -*-
"""
Trabajo de fin de grado. (Ingeniería Matemática UCM)

Título: El problema de la dieta y su aplicación en escaladores de competición
Autor: Ana Llorente García


Este script resuelve el Modelo 2 con Gurobi.

El Modelo 2 es una ampliación del Modelo 1, incorporando una  división del día en
cuatro franjas horarias: desayuno, comida, merienda y cena. Aunque el objetivo sigue
siendo el mismo: decidir que alimentos debe comprar la escaladora para cumplir con
los requisitos de nutrientes, incluir la división de comidas permite distribuir los
nutrientes de una manera más realista.
"""

import json
import gurobipy as gp
from gurobipy import GRB

# Cargar datos desde el archivo JSON
with open("alimentos.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Crear modelo
model = gp.Model("Modelo2")

# Índices
franjas = ["desayuno", "comida", "merienda", "cena"]

# Mapear categorías a números
categorias_map = {
    "Cereales y derivados": 1, "Leche y productos lácteos": 2, "Huevos": 3, "Azúcares y dulces": 4,
    "Aceites y grasas": 5, "Verduras y hortalizas": 6, "Legumbres": 7, "Frutas": 8, "Frutos secos": 9,
    "Carnes": 10, "Productos cárnicos": 11, "Pescados": 12, "Crustáceos y moluscos": 13,
    "Condimentos y aperitivos": 14, "Bebidas": 15
}

# Parámetros nutricionales
precio = {i: float(info["Precio (€/100g)"]) for i, info in data.items()}
energia = {i: float(info["Energía (Kcal)"]) for i, info in data.items()}
carbohidratos = {i: float(info["Hidratos de carbono (g)"]) for i, info in data.items()}
proteina = {i: float(info["Proteínas (g)"]) for i, info in data.items()}
grasa = {i: float(info["Lípidos totales (g)"]) for i, info in data.items()}
categorias = {i: categorias_map[info["Categoría"]] for i, info in data.items()}
maximo = {i: float(info["Máximo (g/día)"]) for i, info in data.items()}

# Crear subconjuntos por categoría
frutas = [i for i in data if data[i]["Categoría"] == "Frutas"]
legumbres = [i for i in data if data[i]["Categoría"] == "Legumbres"]
carnes = [i for i in data if data[i]["Categoría"] == "Carnes"]
pescados = [i for i in data if data[i]["Categoría"] == "Pescados"]
lacteos = [i for i in data if data[i]["Categoría"] == "Leche y productos lácteos"]
verduras = [i for i in data if data[i]["Categoría"] == "Verduras y hortalizas"]
azúcares = [i for i in data if data[i]["Categoría"] == "Azúcares y dulces"]

# Creamos el subconjunto de alimentos que pueden ser postre
postre = [i for i in data if data[i].get("Extra") == "Postre"]

# Distribución de calorías por franja horaria
distr_calorica = {"desayuno": 0.2, "comida": 0.4, "merienda": 0.1, "cena": 0.3}

# Distribución de macronutrientes por franja horaria
distr_macros = {
    "carbohidratos": {"desayuno": 0.5, "comida": 0.35, "merienda": 0.4, "cena": 0.4},
    "proteina": {"desayuno": 0.25, "comida": 0.4, "merienda": 0.3, "cena": 0.3},
    "grasa": {"desayuno": 0.25, "comida": 0.25, "merienda": 0.3, "cena": 0.3}
}

# Categorías permitidas por franja
categorias_permitidas = {
    "desayuno": {1, 2, 3, 4, 5, 8, 11},
    "comida": {1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 15},
    "merienda": {1, 2, 3, 4, 5, 8, 9, 11},
    "cena": {1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 15}
}

# Variable de decisión: cantidad en gramos de cada alimento i en la franja j
X = {(i, j): model.addVar(lb=0, vtype=GRB.CONTINUOUS) for i in data for j in franjas} #categorias no permitidas aqui

# Variable de decisión binaria: 1 si esta presente el alimento i en la franja j
Y = {(i, j): model.addVar(vtype=GRB.BINARY) for i in data for j in franjas}

# Variable de decisión binaria: 1 si esta presente el tipo de alimento en la franja j
F = {(j): model.addVar(vtype=GRB.BINARY) for j in franjas}  # frutas
V = {(j): model.addVar(vtype=GRB.BINARY) for j in franjas}  # verduras
L = {(j): model.addVar(vtype=GRB.BINARY) for j in franjas}  # legumbres
C = {(j): model.addVar(vtype=GRB.BINARY) for j in franjas}  # carne
P = {(j): model.addVar(vtype=GRB.BINARY) for j in franjas}  # pescado
LC = {(j): model.addVar(vtype=GRB.BINARY) for j in franjas}  # leche y lácteos
A = {(j): model.addVar(vtype=GRB.BINARY) for j in franjas}  # azúcares y dulces

# Función objetivo
model.setObjective(gp.quicksum(precio[i]/100 * X[i, j] for i in data for j in franjas), GRB.MINIMIZE)

   
# Restricciones por franja
for j in franjas:
    d_j = distr_calorica[j]
    # Restricción de calorías
    model.addConstr(gp.quicksum(energia[i]/100 * X[i, j] for i in data) >= d_j * 2900)
    model.addConstr(gp.quicksum(energia[i]/100 * X[i, j] for i in data) <= d_j * 3100)
    # Restricción de macronutrientes
    model.addConstr(gp.quicksum(carbohidratos[i]*4/100 * X[i, j] for i in data) >= distr_macros["carbohidratos"][j] * d_j * 2900)
    model.addConstr(gp.quicksum(carbohidratos[i]*4/100 * X[i, j] for i in data) <= distr_macros["carbohidratos"][j] * d_j * 3100)
    model.addConstr(gp.quicksum(proteina[i]*4/100 * X[i, j] for i in data) >= distr_macros["proteina"][j] * d_j * 2900)
    model.addConstr(gp.quicksum(proteina[i]*4/100 * X[i, j] for i in data) <= distr_macros["proteina"][j] * d_j * 3100)
    model.addConstr(gp.quicksum(grasa[i]*9/100 * X[i, j] for i in data) >= distr_macros["grasa"][j] * d_j * 2900)
    model.addConstr(gp.quicksum(grasa[i]*9/100 * X[i, j] for i in data) <= distr_macros["grasa"][j] * d_j * 3100)
    # Restricción de categorías permitidas
    for i in data:
        if categorias[i] not in categorias_permitidas[j]:
            model.addConstr(X[i, j] == 0)
    # Restricción de gramos mínimo y máximo por alimento
        model.addConstr(X[i, j] >= 20 * Y[i, j])
        model.addConstr(X[i, j] <= maximo[i] * Y[i, j])
    # Restriccion al menos 150g de frutas
    model.addConstr(gp.quicksum(X[i, j] for i in frutas) >= 150 * F[j])
    # Restriccion al menos 80g de verduras y máximo 250g
    model.addConstr(gp.quicksum(X[i, j] for i in verduras) >= 80 * V[j])
    model.addConstr(gp.quicksum(X[i, j] for i in verduras) <= 250 * V[j])
    # Restriccion máximo 100g de legumbres
    model.addConstr(gp.quicksum(X[i, j] for i in legumbres) <= 100 * L[j])
    # Restriccion máximo 250g de carne
    model.addConstr(gp.quicksum(X[i, j] for i in carnes) <= 250 * C[j])
    # Restriccion máximo 200g de pescado
    model.addConstr(gp.quicksum(X[i, j] for i in pescados) <= 200 * P[j])
    # Restriccion en una misma franja solo puede haber carne o pescado, no ambos
    model.addConstr(C[j] + P[j] <= 1)
    # Restriccion máximo 200g de leche o lácteos
    model.addConstr(gp.quicksum(X[i, j] for i in lacteos) <= 200 * LC[j])
    # Restriccion máximo 35g de azúcares o dulces
    model.addConstr(gp.quicksum(X[i, j] for i in azúcares) <= 35 * A[j])

# Restricción no repetir alimentos     
for i in data:
    model.addConstr(gp.quicksum(Y[i, j] for j in franjas) <= 1)
    
# Restricciones adicionales (frutas en 3 franjas al menos, verduras en 2 franjas al menos, legumbres como mucho en 1 franja)
model.addConstr(gp.quicksum(F[j] for j in franjas) >= 3)
model.addConstr(gp.quicksum(V[j] for j in franjas) >= 2)
model.addConstr(gp.quicksum(L[j] for j in franjas) <= 1)
model.addConstr(gp.quicksum(A[j] for j in franjas) <= 1)

# Restricción en el desayuno incluir leche o café o ambos
if "leche desnatada" in data and "café" in data:
    model.addConstr(X["leche desnatada", "desayuno"] + X["café", "desayuno"] >= 200)
    

# Restriccion de no incluir arroz y pasta en desayuno y merienda
alimentos_prohibidos = ["arroz", "pasta", "quinoa"]
for j in ["desayuno", "merienda"]:
    for i in alimentos_prohibidos:
        model.addConstr(X[i, j] == 0)

# Restricción de incluir postres en comida y cena
for j in ["comida", "cena"]:
    model.addConstr(gp.quicksum(X[i, j] for i in frutas + postre if i in data) >= 150)
    
# Resolver el modelo
model.optimize()

# Mostrar los resultados y guardarlos en un fichero
if model.status == GRB.OPTIMAL:
    output_lines = []
    output_lines.append("\nDieta óptima encontrada:")
    for j in franjas:
        output_lines.append(f"\n{j.capitalize()}:")
        for i in data:
            cantidad = X[i, j].X
            if cantidad > 0:
                output_lines.append(f"  {i}: {cantidad:.2f} g")
    output_lines.append(f"\nCoste total: {model.ObjVal:.2f} €")
    # Imprimir por pantalla
    for line in output_lines:
        print(line)
    # Guardar en fichero
    with open("Resultados/dieta_optima_Modelo2.txt", "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")
    print("\nDieta óptima guardada en 'Resultados/dieta_optima_Modelo2.txt'.")
else:
    print("No se encontró una solución óptima.")
