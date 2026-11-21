
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd


# ============================================================
# 1. RUTAS DE LOS ARCHIVOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "models" / "diabetes_model.joblib"
METADATA_PATH = BASE_DIR / "models" / "diabetes_metadata.json"


# ============================================================
# 2. REGLAS DE VALIDACIÓN DE LAS VARIABLES
# ============================================================

# Variables binarias: solamente aceptan 0 o 1.
VARIABLES_BINARIAS = [
    "HighBP",
    "HighChol",
    "CholCheck",
    "Smoker",
    "Stroke",
    "HeartDiseaseorAttack",
    "PhysActivity",
    "Fruits",
    "Veggies",
    "HvyAlcoholConsump",
    "AnyHealthcare",
    "NoDocbcCost",
    "DiffWalk",
    "Sex"
]

# Rangos de las variables ordinales y cuantitativas.
RANGOS_VARIABLES = {
    "BMI": (12, 98),
    "GenHlth": (1, 5),
    "MentHlth": (0, 30),
    "PhysHlth": (0, 30),
    "Age": (1, 13),
    "Education": (1, 6),
    "Income": (1, 8)
}


# ============================================================
# 3. CARGAR MODELO Y METADATOS
# ============================================================

def cargar_recursos():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo: {MODEL_PATH}"
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontraron los metadatos: {METADATA_PATH}"
        )

    modelo = joblib.load(MODEL_PATH)

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as archivo:

        metadatos = json.load(archivo)

    # Verificar que el modelo tenga las clases esperadas.
    if list(modelo.classes_) != [0, 1]:
        raise ValueError(
            "El modelo no contiene las clases esperadas: 0 y 1."
        )

    # Verificar las variables y su orden.
    variables = metadatos["orden_variables"]

    if list(modelo.feature_names_in_) != variables:
        raise ValueError(
            "El orden de variables de los metadatos "
            "no coincide con el modelo."
        )

    if len(variables) != 21:
        raise ValueError(
            "El modelo debe recibir exactamente 21 variables."
        )

    return modelo, metadatos


# Los recursos se cargan una sola vez al importar el servicio.
modelo, metadatos = cargar_recursos()

VARIABLES = metadatos["orden_variables"]

print(
    f"Modelo de diabetes cargado correctamente: "
    f"{metadatos['nombre']} v{metadatos['version']}"
)


# ============================================================
# 4. VALIDAR LOS DATOS RECIBIDOS
# ============================================================

def validar_datos(datos):

    if not isinstance(datos, dict):
        raise ValueError(
            "Los datos deben enviarse en formato de diccionario."
        )

    # Comprobar variables faltantes.
    faltantes = [
        variable
        for variable in VARIABLES
        if variable not in datos
    ]

    if faltantes:
        raise ValueError(
            f"Faltan las siguientes variables: {faltantes}"
        )

    # Comprobar variables adicionales.
    adicionales = [
        variable
        for variable in datos
        if variable not in VARIABLES
    ]

    if adicionales:
        raise ValueError(
            f"Se recibieron variables no reconocidas: {adicionales}"
        )

    datos_validados = {}

    for variable in VARIABLES:

        valor = datos[variable]

        # Evitar valores vacíos y booleanos.
        if valor is None or isinstance(valor, bool):
            raise ValueError(
                f"El valor de {variable} no es válido."
            )

        # Convertir a número.
        try:
            valor = float(valor)

        except (TypeError, ValueError):
            raise ValueError(
                f"La variable {variable} debe ser numérica."
            )

        # Rechazar NaN e infinitos.
        if not np.isfinite(valor):
            raise ValueError(
                f"La variable {variable} contiene un valor no válido."
            )

        # Todas las variables del conjunto utilizado son enteras.
        if not valor.is_integer():
            raise ValueError(
                f"La variable {variable} debe ser un número entero."
            )

        valor = int(valor)

        # Validar variables binarias.
        if variable in VARIABLES_BINARIAS:

            if valor not in [0, 1]:
                raise ValueError(
                    f"{variable} solamente acepta 0 o 1."
                )

        # Validar rangos de las demás variables.
        elif variable in RANGOS_VARIABLES:

            minimo, maximo = RANGOS_VARIABLES[variable]

            if not minimo <= valor <= maximo:
                raise ValueError(
                    f"{variable} debe estar entre "
                    f"{minimo} y {maximo}."
                )

        else:
            raise ValueError(
                f"No existe una regla de validación para {variable}."
            )

        datos_validados[variable] = valor

    return datos_validados


# ============================================================
# 5. GENERAR PREDICCIÓN
# ============================================================

def predecir_diabetes(
    datos,
    tipo_umbral="principal"
):

    # Validar datos recibidos.
    datos_validados = validar_datos(datos)

    # Seleccionar umbral.
    if tipo_umbral not in metadatos["umbrales"]:
        raise ValueError(
            "El umbral seleccionado no es válido. "
            "Utilice 'principal' o 'alternativo'."
        )

    informacion_umbral = metadatos["umbrales"][tipo_umbral]

    umbral = informacion_umbral["valor"]

    # Crear DataFrame respetando el orden original.
    entrada = pd.DataFrame(
        [datos_validados],
        columns=VARIABLES
    )

    # Obtener probabilidades.
    probabilidades = modelo.predict_proba(entrada)[0]

    probabilidad_0 = float(probabilidades[0])
    probabilidad_1 = float(probabilidades[1])

    # Clasificar utilizando el umbral seleccionado.
    clase_predicha = int(probabilidad_1 >= umbral)

    # Descripción de la clase.
    resultado = metadatos["clases"][str(clase_predicha)]

    return {
        "modelo": metadatos["nombre"],
        "version_modelo": metadatos["version"],

        "clase_predicha": clase_predicha,
        "resultado": resultado,

        "probabilidad_modelo_clase_0": round(
            probabilidad_0, 6
        ),

        "probabilidad_modelo_clase_1": round(
            probabilidad_1, 6
        ),

        "umbral_utilizado": umbral,
        "criterio_umbral": informacion_umbral["criterio"],

        "tipo_umbral": tipo_umbral,

        "advertencia": (
            "Este resultado es una clasificación experimental basada "
            "en datos de encuesta. No constituye un diagnóstico médico "
            "ni una estimación de riesgo clínico individual."
        )
    }
