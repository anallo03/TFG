# -*- coding: utf-8 -*-
"""
Trabajo de fin de grado. (Ingeniería Matemática UCM)

Título: El problema de la dieta y su aplicación en escaladores de competición
Autor: Ana Llorente García


Este script resuelve el Modelo 3 con alimentos con Gurobi.

El Modelo 3 con alimentos es una ampliación del Modelo 2. Es un modelo semanal. Se incluye el
índice d (días) por lo que todas las variables y restricciones del Modelo 2 se
mantienen pero se modifican para incluir este nuevo índice.
"""

import json
import gurobipy as gp
from gurobipy import GRB

# Cargar datos desde el archivo JSON
with open("alimentos.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Crear modelo
model = gp.Model("Modelo3_alimentos")

# Índices
dias = ["1","2","3","4","5","6", "7"]
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

#Creamos el subconjunto de alimentos que pueden ser postre
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

# Variable de decisión: cantidad en gramos de cada alimento i en la franja j el día d
X = {(i, j, d): model.addVar(lb=0, vtype=GRB.CONTINUOUS) for i in data for j in franjas for d in dias}

# Variable de decisión binaria: 1 si esta presente el alimento i en la franja j el día d
Y = {(i, j, d): model.addVar(vtype=GRB.BINARY) for i in data for j in franjas for d in dias}

# Variable de decisión binaria: 1 si esta presente el alimento i  el día d
Z = {(i, d): model.addVar(vtype=GRB.BINARY) for i in data for d in dias}

# Variable de decisión binaria: 1 si esta presente el tipo de alimento en la franja j el día d
F = {(j, d): model.addVar(vtype=GRB.BINARY) for j in franjas for d in dias}  # frutas
V = {(j, d): model.addVar(vtype=GRB.BINARY) for j in franjas for d in dias}  # verduras
L = {(j, d): model.addVar(vtype=GRB.BINARY) for j in franjas for d in dias}  # legumbres
C = {(j, d): model.addVar(vtype=GRB.BINARY) for j in franjas for d in dias}  # carne
P = {(j, d): model.addVar(vtype=GRB.BINARY) for j in franjas for d in dias}  # pescado
LC = {(j, d): model.addVar(vtype=GRB.BINARY) for j in franjas for d in dias}  # leche y lácteos
A = {(j, d): model.addVar(vtype=GRB.BINARY) for j in franjas for d in dias}  # azúcares y dulces

# Función objetivo
model.setObjective(gp.quicksum(precio[i]/100 * X[i, j, d] for i in data for j in franjas for d in dias), GRB.MINIMIZE)

# Restricciones por franja horaria y día
for d in dias:
    for j in franjas:
        d_j = distr_calorica[j]
        # Restricción de calorías
        model.addConstr(gp.quicksum(energia[i]/100 * X[i, j, d] for i in data) >= d_j * 2900)
        model.addConstr(gp.quicksum(energia[i]/100 * X[i, j, d] for i in data) <= d_j * 3100)
        # Restricción de macronutrientes
        model.addConstr(gp.quicksum(carbohidratos[i]*4/100 * X[i, j, d] for i in data) >= distr_macros["carbohidratos"][j] * d_j * 2900)
        model.addConstr(gp.quicksum(carbohidratos[i]*4/100 * X[i, j, d] for i in data) <= distr_macros["carbohidratos"][j] * d_j * 3100)
        model.addConstr(gp.quicksum(proteina[i]*4/100 * X[i, j, d] for i in data) >= distr_macros["proteina"][j] * d_j * 2900)
        model.addConstr(gp.quicksum(proteina[i]*4/100 * X[i, j, d] for i in data) <= distr_macros["proteina"][j] * d_j * 3100)
        model.addConstr(gp.quicksum(grasa[i]*9/100 * X[i, j, d] for i in data) >= distr_macros["grasa"][j] * d_j * 2900)
        model.addConstr(gp.quicksum(grasa[i]*9/100 * X[i, j, d] for i in data) <= distr_macros["grasa"][j] * d_j * 3100)
        # Restricción de categorías permitidas (cambiar a X)
        for i in data:
            if categorias[i] not in categorias_permitidas[j]:
                model.addConstr(X[i, j, d] == 0)
        # Restricción de gramos mínimo y máximo por alimento
            model.addConstr(X[i, j, d] >= 20 * Y[i, j, d])
            model.addConstr(X[i, j, d] <= maximo[i] * Y[i, j, d])
        # Restriccion al menos 150g de frutas
        model.addConstr(gp.quicksum(X[i, j, d] for i in frutas) >= 150 * F[j, d])
        # Restriccion al menos 80g de verduras y máximo 250g
        model.addConstr(gp.quicksum(X[i, j, d] for i in verduras) >= 80 * V[j, d])
        model.addConstr(gp.quicksum(X[i, j, d] for i in verduras) <= 250 * V[j, d])
        # Restriccion máximo 100g de legumbres
        model.addConstr(gp.quicksum(X[i, j, d] for i in legumbres) <= 100 * L[j, d])
        # Restriccion máximo 250g de carne
        model.addConstr(gp.quicksum(X[i, j, d] for i in carnes) <= 250 * C[j, d])
        # Restriccion máximo 200g de pescado
        model.addConstr(gp.quicksum(X[i, j, d] for i in pescados) <= 200 * P[j, d])
        # Restriccion en una misma franja solo puede haber carne o pescado, no ambos
        model.addConstr(C[j, d] + P[j, d] <= 1)
        # Restriccion máximo 200g de leche o lácteos
        model.addConstr(gp.quicksum(X[i, j, d] for i in lacteos) <= 200 * LC[j, d])
        # Restriccion máximo 35g de azúcares o dulces
        model.addConstr(gp.quicksum(X[i, j, d] for i in azúcares) <= 35 * A[j, d])

    # Restricción no repetir alimentos en el día d     
    for i in data:
        model.addConstr(gp.quicksum(Y[i, j, d] for j in franjas) <= 1)
        
    # Restricciones adicionales (frutas en 3 franjas al menos, verduras en 2 franjas al menos, legumbres como mucho en 1 franja)
    model.addConstr(gp.quicksum(F[j, d] for j in franjas) >= 3)
    model.addConstr(gp.quicksum(V[j, d] for j in franjas) >= 2)
    model.addConstr(gp.quicksum(L[j, d] for j in franjas) <= 1)
    model.addConstr(gp.quicksum(A[j, d] for j in franjas) <= 1)
    
    # Restricción en el desayuno incluir leche o café o ambos
    if "leche desnatada" in data and "café" in data:
        model.addConstr(X["leche desnatada", "desayuno", d] + X["café", "desayuno", d] >= 200)

    # Restriccion de no incluir arroz y pasta en desayuno y merienda
    alimentos_prohibidos = ["arroz", "pasta", "quinoa"]
    for j in ["desayuno", "merienda"]:
        for i in alimentos_prohibidos:
            model.addConstr(X[i, j, d] == 0)
            
    # Restricción de incluir postres en comida y cena
    for j in ["comida", "cena"]:
        model.addConstr(gp.quicksum(X[i, j, d] for i in frutas + postre if i in data) >= 150)


# Restricciones para no repetir alimentos por día
for i in data:
    for d in dias:
        for j in franjas:
            model.addConstr(Y[i, j, d] <= Z[i, d])
        #model.addConstr(gp.quicksum(X[i,j,d] for j in franjas) <= maximo[i]*Z[i,d])
        model.addConstr(Z[i,d] <= gp.quicksum(Y[i, j, d] for j in franjas))

# Categorías de alimentos que no pueden repetirse más de 2 veces a la semana    
categorias_permitida= {6,7,8,10,12} #verduras, legumbres, frutas, pescados y carne
# Alimentos que sí se pueden repetir sin límite
alimentos_repetir={"leche desnatada","pasta","huevo", "yogur", "pan blanco", "pan integral"}

# Restricciones para controlar la repetición de alimentos
for i in data:
    if categorias[i]  in categorias_permitida: #Los alimentos dentro de "categorias_permitidas" se pueden repetir un máximo de 2 veces por semana
        model.addConstr(gp.quicksum(Z[i, d] for d in dias) <=2)
    if i not in alimentos_repetir: #El resto de alimentos se pueden repetir un máximo de 4 veces por semana excepto los de "alimentos_repetir" que se pueden consumir todos los días
        model.addConstr(gp.quicksum(Z[i, d] for d in dias) <=4)

# Restricciones adicionales: no repetir legumbres más de 3 días, no tomar azúcares más de 2 días         
model.addConstr(gp.quicksum(Z[i, d] for i in legumbres for d in dias) <=3)
model.addConstr(gp.quicksum(Z[i, d] for i in azúcares for d in dias) <=2)
    
# Restricciones para repetir alimentos en días separados
for i in data:
    # Debe de haber 2 días entre consumir el mismo tipo de carne, pescado , verdura , legumbre o fruta 
    if categorias[i]  in categorias_permitida:
        for idx in range(len(dias) - 2):
            d1 = dias[idx]
            d2 = dias[idx + 1]
            d3 = dias[idx + 2]
            model.addConstr(Z[i, d1] + Z[i, d2] + Z[i, d3]<= 1)
    # El resto de alimentos pueden aparecer como máximo en 2 días consecutivos     
    if i not in alimentos_repetir:
        for idx in range(len(dias) - 2):
            d1 = dias[idx]
            d2 = dias[idx + 1]
            d3 = dias[idx + 2]
            model.addConstr(Z[i, d1] + Z[i, d2] + Z[i, d3]<= 2)


# Parámetro para el valor de tolerancia de optimalidad             
model.setParam('MIPGap', 0.028)

# Resolver el modelo
model.optimize()

# Mostrar los resultados y guardarlos en un fichero
if model.status == GRB.OPTIMAL:
    output_lines = []
    output_lines.append("\nDieta óptima encontrada:")
    for d in dias:
        output_lines.append(f"\nDía: {d.capitalize()}")
        for j in franjas:
            output_lines.append(f"  {j.capitalize()}:")
            for i in data:
                cantidad = X[i, j, d].X
                if cantidad > 0:
                    output_lines.append(f"    {i}: {cantidad:.2f} g")

    output_lines.append(f"\nCoste total: {model.ObjVal:.2f} €")
    # Imprimir por pantalla
    for line in output_lines:
        print(line)
    # Guardar en fichero
    with open("Resultados/dieta_optima_Modelo3_alimentos.txt", "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")
    print("\nDieta óptima guardada en 'Resultados/dieta_optima_Modelo3_alimentos.txt'")
else:
    print("No se encontró una solución óptima.")

