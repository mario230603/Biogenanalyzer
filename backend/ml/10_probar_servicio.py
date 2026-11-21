
from app.services.diabetes import predecir_diabetes


# Datos ficticios de prueba.
datos_prueba = {
    "HighBP": 1,
    "HighChol": 1,
    "CholCheck": 1,
    "BMI": 28,
    "Smoker": 0,
    "Stroke": 0,
    "HeartDiseaseorAttack": 0,
    "PhysActivity": 1,
    "Fruits": 1,
    "Veggies": 1,
    "HvyAlcoholConsump": 0,
    "AnyHealthcare": 1,
    "NoDocbcCost": 0,
    "GenHlth": 3,
    "MentHlth": 2,
    "PhysHlth": 5,
    "DiffWalk": 0,
    "Sex": 1,
    "Age": 8,
    "Education": 5,
    "Income": 6
}


print("\nProbando umbral principal...")

resultado_principal = predecir_diabetes(
    datos_prueba,
    tipo_umbral="principal"
)

print(resultado_principal)


print("\nProbando umbral alternativo...")

resultado_alternativo = predecir_diabetes(
    datos_prueba,
    tipo_umbral="alternativo"
)

print(resultado_alternativo)


print("\nPruebas finalizadas.")
