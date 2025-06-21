# -*- coding: utf-8 -*-
"""
Trabajo de fin de grado. (Ingeniería Matemática UCM)

Título: El problema de la dieta y su aplicación en escaladores de competición
Autor: Ana Llorente García


Este script resuelve el Modelo 3 con recetas con Gurobi.

El Modelo 3 con recetas es una ampliación de los modelos anteriores. 
Es un modelo semanal. Se incluye el índice d (días) y además, incorpora el uso
de recetas, manteniendo las mismas restricciones nutricionales y estructurales básicas.
"""

import gurobipy as gp
from gurobipy import GRB
import json

# Cargar datos desde el archivo JSON
with open("alimentos.json", "r", encoding="utf-8") as f:
    data = json.load(f)
with open("recetas.json", "r", encoding="utf-8") as f:
    recetas = json.load(f)

# Crear modelo
model = gp.Model("Modelo3_Recetas")

# Índices
dias = ["1","2","3","4","5","6", "7"]

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

X = {} # Variable de decisión binaria: 1 si se seleccion en la franja j la receta r el día d
Q = {} # Variable de decisión: cantidad en gramos de cada alimento i en la franja j de la receta r el día d
for d in dias:
    for j, lista in recetas.items():
        for r, receta in enumerate(lista):
            X[j, r, d] = model.addVar(vtype=GRB.BINARY)
            for i, (qmin, qmax) in receta["ingredientes"].items():
                Q[i, j, r, d] = model.addVar(lb=0, ub=float(qmax))

Y = {} # Variable de decisión binaria: 1 si se seleccion alimento extra i en la franja j el día d 
Q_extra = {} # Variable de decisión: cantidad en gramos de cada alimento extra i en la franja j el día d
for d in dias:
    for i in data:
        for j in recetas:
            Y[i, j, d] = model.addVar(vtype=GRB.BINARY)
            Q_extra[i, j, d] = model.addVar(lb=0)

# Variable de decisión binaria: 1 si esta presente el alimento i  el día d
Z = {(i, d): model.addVar(vtype=GRB.BINARY) for i in data for d in dias}

# Variable de decisión binaria: 1 si esta presente el tipo de alimento en la franja j el día d
F = {(j, d): model.addVar(vtype=GRB.BINARY) for j in recetas for d in dias}  # frutas
V = {(j, d): model.addVar(vtype=GRB.BINARY) for j in recetas for d in dias}  # verduras
L = {(j, d): model.addVar(vtype=GRB.BINARY) for j in recetas for d in dias}  # legumbres
C = {(j, d): model.addVar(vtype=GRB.BINARY) for j in recetas for d in dias}  # carne
P = {(j, d): model.addVar(vtype=GRB.BINARY) for j in recetas for d in dias}  # pescado
LC = {(j, d): model.addVar(vtype=GRB.BINARY) for j in recetas for d in dias}  # leche y lácteos
A = {(j, d): model.addVar(vtype=GRB.BINARY) for j in recetas for d in dias}  # azúcares y dulces

#Función objetivo:
model.setObjective(gp.quicksum( precio[i]/100 * Q[i, j, r, d] for (i, j, r, d) in Q
            ) + gp.quicksum(precio[i]/100 * Q_extra[i, j, d]  for (i, j, d) in Q_extra), GRB.MINIMIZE)

# Restricción gramos de alimento i de la receta r entre qmin y qmax 
for d in dias: 
    for j, lista in recetas.items():
        for r, receta in enumerate(lista):
            for i, (qmin, qmax) in receta["ingredientes"].items():
                model.addConstr(Q[i, j, r, d] <= float(qmax) * X[j, r, d])
                model.addConstr(Q[i, j, r, d] >= float(qmin) * X[j, r, d])
                
# Restricciones por franja y día                
for d in dias:
    for j in recetas:
        d_j = distr_calorica[j]
        # Restricción de calorías
        total_kcal = gp.quicksum((energia[i] / 100) * Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"]
                    ) + gp.quicksum((energia[i] / 100) * Q_extra[i, j, d] for i in data if (i, j, d) in Q_extra)
        model.addConstr(total_kcal >= d_j * 2900)
        model.addConstr(total_kcal <= d_j * 3100)

        # Restricción de carbohidratos
        expr_carbs = gp.quicksum((carbohidratos[i] * 4 / 100) * Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"]
                    ) + gp.quicksum((carbohidratos[i] * 4 / 100) * Q_extra[i, j, d] for i in data if (i, j, d) in Q_extra)
        model.addConstr(expr_carbs >= distr_macros["carbohidratos"][j] * d_j * 2900)
        model.addConstr(expr_carbs <= distr_macros["carbohidratos"][j] * d_j * 3100)

        # Restricción de proteínas
        expr_prot = gp.quicksum((proteina[i] * 4 / 100) * Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"]
                    ) + gp.quicksum((proteina[i] * 4 / 100) * Q_extra[i, j, d] for i in data if (i, j, d) in Q_extra)
        model.addConstr(expr_prot >= distr_macros["proteina"][j] * d_j * 2900)
        model.addConstr(expr_prot <= distr_macros["proteina"][j] * d_j * 3100)

        # Restricción de grasas
        expr_grasa = gp.quicksum((grasa[i] * 9 / 100) * Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"]
                    ) + gp.quicksum((grasa[i] * 9 / 100) * Q_extra[i, j, d] for i in data if (i, j, d) in Q_extra)
        model.addConstr(expr_grasa >= distr_macros["grasa"][j] * d_j * 2900)
        model.addConstr(expr_grasa <= distr_macros["grasa"][j] * d_j * 3100)

  
# Restricción alimento extra deben ser de categoría permitida en esa franja y como mínimo 20g y máximo 
for d in dias:
    for (i, j, d) in Q_extra:
        if categorias[i] not in categorias_permitidas[j]:
            model.addConstr(Q_extra[i, j, d] == 0)
        model.addConstr(Q_extra[i, j, d] >= 20 * Y[i, j, d])
        model.addConstr(Q_extra[i, j, d] <= maximo[i] * Y[i, j, d])

# Restricción máximo alimento por receta y de las categorías permitidas
for d in dias:
    for j, lista in recetas.items():
        for r, receta in enumerate(lista):
            for i in receta["ingredientes"]:
                model.addConstr(Q[i, j, r, d] <= maximo[i]* X[j, r, d])
                if categorias[i] not in categorias_permitidas[j]:
                    model.addConstr(Q[i, j, r, d] == 0)
                 
# Restricciones por franja horaria y día
for d in dias:       
    for j in recetas:
        # Restriccion al menos 150g de frutas
        expr_frutas = gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in frutas
        ) + gp.quicksum(Q_extra[i, j, d] for i in frutas if (i, j, d) in Q_extra)
        model.addConstr(expr_frutas >= 150 * F[j, d])
        # Restriccion al menos 80g de verduras y máximo 250g
        expr_verduras = gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in verduras
        ) + gp.quicksum(Q_extra[i, j, d] for i in verduras if (i, j, d) in Q_extra)
        model.addConstr(expr_verduras >= 80 * V[j, d])
        model.addConstr(expr_verduras <= 250 * V[j, d])
        # Restriccion máximo 100g de legumbres
        expr_legumbres = gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in legumbres
        ) + gp.quicksum(Q_extra[i, j, d] for i in legumbres if (i, j, d) in Q_extra)
        model.addConstr(expr_legumbres <= 100 * L[j, d])
        # Restriccion máximo 250g de carne
        expr_carne = gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in carnes
        ) + gp.quicksum(Q_extra[i, j, d] for i in carnes if (i, j, d) in Q_extra)
        model.addConstr(expr_carne <= 250 * C[j, d])
        # Restriccion máximo 200g de pescado
        expr_pescado = gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in pescados
        ) + gp.quicksum(Q_extra[i, j, d] for i in pescados if (i, j, d) in Q_extra)
        model.addConstr(expr_pescado <= 200 * P[j, d])
        # Restriccion en una misma franja solo puede haber carne o pescado, no ambos
        model.addConstr(C[j, d] + P[j, d] <= 1)
        # Restriccion máximo 200g de leche o lácteos
        expr_lacteos = gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in lacteos
        ) + gp.quicksum(Q_extra[i, j, d] for i in lacteos if (i, j, d) in Q_extra)
        model.addConstr(expr_lacteos <= 200 * LC[j, d])
        # Restriccion máximo 35g de azúcares o dulces
        expr_azúcares = gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in azúcares
        ) + gp.quicksum(Q_extra[i, j, d] for i in azúcares if (i, j, d) in Q_extra)
        model.addConstr(expr_azúcares <= 35 * A[j, d])

# Restricciones adicionales (frutas en 3 franjas al menos, verduras en 2 franjas al menos, legumbres como mucho en 1 franja)
for d in dias:
    model.addConstr(gp.quicksum(F[j, d] for j in recetas) >= 3)
    model.addConstr(gp.quicksum(V[j, d] for j in recetas) >= 2)
    model.addConstr(gp.quicksum(L[j, d] for j in recetas) <= 1)
    model.addConstr(gp.quicksum(A[j, d] for j in recetas) <= 1)
          
# Restricción al menos una receta por franja
for d in dias:
    for j in recetas:
        model.addConstr(gp.quicksum(X[j, r, d] for r in range(len(recetas[j]))) >= 1)


# Restricción si un alimento está en una receta seleccionada, no puede usarse como extra en ninguna franja
for d in dias:
    for i in data:
        recetas_con_ingrediente = []
        for j, lista in recetas.items():
            for r, receta in enumerate(lista):
                if i in receta["ingredientes"]:
                    recetas_con_ingrediente.append(X[j, r, d])
        if recetas_con_ingrediente:
            for franja in recetas:
                model.addConstr(Q_extra[i, franja, d] <= maximo[i] * (1.0 - gp.quicksum(recetas_con_ingrediente)))

# Restricción se selecciona alimento extra si es necesario y como mucho en una franja
for d in dias:
    for i in data:
        for j in recetas:
            model.addConstr(Q_extra[i, j, d] <= maximo[i] * Y[i, j, d])
        model.addConstr(gp.quicksum(Y[i, j, d] for j in recetas) <= 1)

# Restricción de incluir 200g de leche o café en el desayuno
for d in dias:
    leche_cafe_recetas = gp.quicksum(Q[i, "desayuno", r, d] for r, receta in enumerate(recetas["desayuno"])
        for i in receta["ingredientes"] if i in ["leche desnatada", "café"])

    leche_cafe_extra = gp.quicksum(Q_extra[i, "desayuno", d] for i in ["leche desnatada", "café"]
        if (i, "desayuno", d) in Q_extra)
    model.addConstr(leche_cafe_recetas + leche_cafe_extra >= 200)

# Restriccion de no incluir arroz y pasta en desayuno y merienda
for d in dias:
    alimentos_prohibidos = ["arroz", "pasta", "quinoa"]
    for j in ["desayuno", "merienda"]:
        for i in alimentos_prohibidos:
            model.addConstr(Q_extra[i, j, d] == 0)

# Restricción de incluir postres en comida y cena
for d in dias:
    for j in ["comida", "cena"]:
        model.addConstr(
            gp.quicksum(Q[i, j, r, d] for r, receta in enumerate(recetas[j]) for i in receta["ingredientes"] if i in frutas + postre
            ) + gp.quicksum(Q_extra[i, j, d] for i in frutas + postre if (i, j, d) in Q_extra) >= 150)

# Restricciones para no repetir alimentos por día
for i in data:
    for d in dias:
        usos_alimento = []
        # Si el alimento se usa como extra
        for j in recetas:
            usos_alimento.append(Y[i, j, d])
        # Si el alimento se usa dentro de alguna receta
        for j in recetas:
            for r, receta in enumerate(recetas[j]):
                if i in receta["ingredientes"]:
                    usos_alimento.append(X[j, r, d])
        for uso in usos_alimento:
            model.addConstr(uso <= Z[i, d])
        model.addConstr(Z[i, d] <= gp.quicksum(usos_alimento))

# Categorías de alimentos que no pueden repetirse más de 2 veces a la semana
categorias_permitida= {6,7,8,10,12}   # verduras, legumbres, frutas, carne, pescado
# Alimentos que sí se pueden repetir sin límite
alimentos_repetir = {"leche desnatada", "pasta", "huevo", "yogur", "pan blanco", "pan integral"}

# Restricción para controlar la repetición de alimentos
for i in data:
    if categorias[i] in categorias_permitida:
        model.addConstr(gp.quicksum(Z[i, d] for d in dias) <= 2)
    elif i not in alimentos_repetir:
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

# Restricción no repetir la misma receta más de dos veces a la semana
for j, lista in recetas.items():
    for r, receta in enumerate(lista):
        model.addConstr(gp.quicksum(X[j, r, d] for d in dias) <= 2)
        
#Restricción para dejar al menos 2 días entre en el consumo de la misma receta
for j, lista in recetas.items():
    for r, receta in enumerate(lista):
        for idx in range(len(dias) - 2):
            d1 = dias[idx]
            d2 = dias[idx + 1]
            d3 = dias[idx + 2]
            model.addConstr(X[j, r, d1] + X[j, r, d2] + X[j, r, d3] <=1)


# Parámetro para el valor de tolerancia de optimalidad   
model.setParam('MIPGap', 0.03)

# Resolver el modelo
model.optimize()

# Mostrar los resultados y escribir en fichero
if model.status == GRB.OPTIMAL:
    with open("Resultados/dieta_optima_Modelo3_recetas", "w", encoding="utf-8") as f:
        def escribir(linea):
            print(linea)
            f.write(linea + "\n")

        escribir("\nDieta óptima encontrada:")
        for d in dias:
            escribir(f"\nDía: {d.capitalize()}")

            for j in recetas:
                for r, receta in enumerate(recetas[j]):
                    if X[j, r, d].X > 0.5:
                        escribir(f"\n{j.capitalize()}: {receta.get('receta', 'Receta sin nombre')}")
                        for i, (qmin, qmax) in receta["ingredientes"].items():
                            cantidad = Q[i, j, r, d].X
                            if cantidad > 0.1:
                                escribir(f"  - {i}: {cantidad:.2f}g")
            # Ingredientes fuera de recetas (extras)
            for j in recetas:
                impresos = False
                for i in data:
                    cantidad = Q_extra[i, j, d].X
                    if cantidad > 0.1:
                        if not impresos:
                            escribir(f"\n{j.capitalize()} extra:")
                            impresos = True
                        escribir(f"  - {i}: {cantidad:.2f}g")

        escribir(f"\nCoste total: {model.objVal:.2f} €")
    print("\nDieta óptima guardada en 'Resultados/dieta_optima_Modelo3_recetas'.")
else:
    print("No se encontró solución óptima.")

