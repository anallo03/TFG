# -*- coding: utf-8 -*-
"""
Trabajo de fin de grado. (Ingeniería Matemática UCM)

Título: El problema de la dieta y su aplicación en escaladores de competición
Autor: Ana Llorente García


Este script resuelve el Modelo 1 con Gurobi.

El objetivo es determinar qué alimentos debe adquirir la escaladora para satisfacer
los requerimientos nutricionales diarios, considerando únicamente las restricciones 
globales del día y sin distinguir entre diferentes franjas horarias.
"""

import json
import gurobipy as gp
from gurobipy import GRB

# Cargar datos desde el archivo JSON
with open("alimentos.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Crear modelo
model = gp.Model("Modelo1")

# Parámetros nutricionales
precio = {i: float(info["Precio (€/100g)"]) for i, info in data.items()}
energia = {i: float(info["Energía (Kcal)"]) for i, info in data.items()}
carbohidratos = {i: float(info["Hidratos de carbono (g)"]) for i, info in data.items()}
proteina = {i: float(info["Proteínas (g)"]) for i, info in data.items()}
grasa = {i: float(info["Lípidos totales (g)"]) for i, info in data.items()}

# Variable de decisión: cantidad de cada alimento en gramos
X = {i: model.addVar(lb=0, vtype=GRB.CONTINUOUS) for i in data}

# Función objetivo
model.setObjective(gp.quicksum(precio[i]/100 * X[i] for i in data), GRB.MINIMIZE)

# Restricción de calorías
model.addConstr(gp.quicksum(energia[i]/100 * X[i] for i in data) >= 2900)
model.addConstr(gp.quicksum(energia[i]/100 * X[i] for i in data) <= 3100)

# Restricción de carbohidratos (40% de calorías)
model.addConstr(gp.quicksum(carbohidratos[i]*4/100 * X[i] for i in data) >= 0.4 * 2900)
model.addConstr(gp.quicksum(carbohidratos[i]*4/100 * X[i] for i in data) <= 0.4 * 3100)

# Restricción de proteínas (30% de calorías)
model.addConstr(gp.quicksum(proteina[i]*4/100 * X[i] for i in data) >= 0.3 * 2900)
model.addConstr(gp.quicksum(proteina[i]*4/100 * X[i] for i in data) <= 0.3 * 3100)

# Restricción de grasas (30% de calorías)
model.addConstr(gp.quicksum(grasa[i]*9/100 * X[i] for i in data) >= 0.3 * 2900)
model.addConstr(gp.quicksum(grasa[i]*9/100 * X[i] for i in data) <= 0.3 * 3100)

# Resolver el modelo
model.optimize()

# Mostrar los resultados
if model.status == GRB.OPTIMAL:
    output_lines = []
    output_lines.append("\nDieta óptima encontrada:")
    for i in data:
        cantidad = X[i].X
        if cantidad > 0:
            output_lines.append(f"  {i}: {cantidad:.2f} g")
    output_lines.append(f"\nCoste total: {model.ObjVal:.2f} €")
    # Imprimir por pantalla
    for line in output_lines:
        print(line)
    # Guardar en fichero
    with open("Resultados/dieta_optima_Modelo1.txt", "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")
    print("\nDieta óptima guardada en 'Resultados/dieta_optima_Modelo1.txt'.")
else:
    print("No se encontró una solución óptima.")