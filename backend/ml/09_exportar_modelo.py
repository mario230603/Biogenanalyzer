
from pathlib import Path
from datetime import datetime, timezone
import json
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight, compute_class_weight


# ============================================================
# 1. RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

TRAIN_PATH = BASE_DIR / "data" / "processed" / "diabetes_train.csv"
TEST_PATH = BASE_DIR / "data" / "processed" / "diabetes_test.csv"

MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "diabetes_model.joblib"
METADATA_PATH = MODEL_DIR / "diabetes_metadata.json"

TARGET = "Diabetes_binary"


# ============================================================
# 2. HIPERPARÁMETROS DEL MODELO SELECCIONADO
# ============================================================

PARAMETROS = {
    "min_samples_leaf": 30,
    "max_leaf_nodes": 63,
    "max_iter": 150,
    "learning_rate": 0.1,
    "l2_regularization": 0.5,
    "random_state": 42
}


# ============================================================
# 3. UMBRALES SELECCIONADOS EN LA ETAPA 6
# ============================================================

UMBRALES = {
    "principal": {
        "valor": 0.71,
        "criterio": "F1_macro",
        "descripcion": (
            "Umbral seleccionado para equilibrar el rendimiento "
            "entre las dos clases."
        )
    },
    "alternativo": {
        "valor": 0.65,
        "criterio": "F1_clase_1",
        "descripcion": (
            "Umbral alternativo que favorece la detección "
            "de la clase positiva."
        )
    }
}


# ============================================================
# 4. MÉTRICAS DE LA EVALUACIÓN FINAL (ETAPA 7)
# ============================================================

METRICAS_TEST = {
    "roc_auc": 0.8303646629,
    "average_precision": 0.4354470943,
    "log_loss": 0.5039345731,
    "brier_score": 0.1728648618,

    "umbral_0.71": {
        "accuracy": 0.835130,
        "f1_macro": 0.685377,
        "f1_clase_1": 0.468315,
        "precision_clase_1": 0.425257,
        "recall_clase_1": 0.521075,
        "balanced_accuracy": 0.703526,
        "especificidad": 0.885978,
        "mcc": 0.374625
    },

    "umbral_0.65": {
        "accuracy": 0.806354,
        "f1_macro": 0.676408,
        "f1_clase_1": 0.471348,
        "precision_clase_1": 0.380373,
        "recall_clase_1": 0.619519,
        "balanced_accuracy": 0.728062,
        "especificidad": 0.836604,
        "mcc": 0.377113
    }
}


# ============================================================
# 5. VALIDAR EXISTENCIA DE ARCHIVOS
# ============================================================

print("\n" + "=" * 65)
print("ETAPA 9: EXPORTACIÓN DEL MODELO")
print("=" * 65)

for ruta in [TRAIN_PATH, TEST_PATH]:

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}"
        )

    print(f"Archivo encontrado: {ruta.name}")


# ============================================================
# 6. CARGAR LOS CONJUNTOS DE DATOS
# ============================================================

print("\nCargando conjuntos de datos...")

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)

if TARGET not in train.columns:
    raise ValueError(
        f"No se encontró la variable objetivo {TARGET} en entrenamiento."
    )

if TARGET not in test.columns:
    raise ValueError(
        f"No se encontró la variable objetivo {TARGET} en prueba."
    )

X_train = train.drop(columns=[TARGET])
y_train = train[TARGET]

X_test = test.drop(columns=[TARGET])
y_test = test[TARGET]


# ============================================================
# 7. VALIDACIONES DE ESTRUCTURA Y CALIDAD
# ============================================================

print("\nValidando estructura de los datos...")

if list(X_train.columns) != list(X_test.columns):
    raise ValueError(
        "Las variables o su orden no coinciden entre entrenamiento y prueba."
    )

if X_train.isnull().any().any() or X_test.isnull().any().any():
    raise ValueError(
        "Se encontraron valores faltantes en las variables predictoras."
    )

if y_train.isnull().any() or y_test.isnull().any():
    raise ValueError(
        "Se encontraron valores faltantes en la variable objetivo."
    )

if set(y_train.unique()) != {0, 1}:
    raise ValueError(
        "El conjunto de entrenamiento debe contener las clases 0 y 1."
    )

if set(y_test.unique()) != {0, 1}:
    raise ValueError(
        "El conjunto de prueba debe contener las clases 0 y 1."
    )

if not all(
    pd.api.types.is_numeric_dtype(X_train[col])
    for col in X_train.columns
):
    raise TypeError(
        "Todas las variables predictoras deben ser numéricas."
    )

if len(X_train.columns) != 21:
    raise ValueError(
        f"Se esperaban 21 variables predictoras, "
        f"pero se encontraron {len(X_train.columns)}."
    )

if not np.isfinite(X_train.to_numpy(dtype=float)).all():
    raise ValueError(
        "Se encontraron valores infinitos o no válidos en entrenamiento."
    )

if not np.isfinite(X_test.to_numpy(dtype=float)).all():
    raise ValueError(
        "Se encontraron valores infinitos o no válidos en prueba."
    )

print("Validaciones correctas.")
print(f"Registros de entrenamiento: {len(X_train):,}")
print(f"Registros de prueba: {len(X_test):,}")
print(f"Variables predictoras: {len(X_train.columns)}")


# ============================================================
# 8. CALCULAR PESOS PARA LAS CLASES
# ============================================================

print("\nCalculando pesos de las clases...")

pesos = compute_sample_weight(
    class_weight="balanced",
    y=y_train
)

clases = np.array([0, 1])

pesos_clases = compute_class_weight(
    class_weight="balanced",
    classes=clases,
    y=y_train
)

informacion_pesos = {
    str(int(clase)): float(peso)
    for clase, peso in zip(clases, pesos_clases)
}

distribucion_clases = {
    str(int(clase)): int(cantidad)
    for clase, cantidad in y_train.value_counts().sort_index().items()
}

print("Distribución de clases:")
print(distribucion_clases)

print("Pesos calculados:")
print(informacion_pesos)


# ============================================================
# 9. ENTRENAR EL MODELO FINAL
# ============================================================

print("\nEntrenando HistGradientBoostingClassifier...")

modelo = HistGradientBoostingClassifier(**PARAMETROS)

modelo.fit(
    X_train,
    y_train,
    sample_weight=pesos
)

print("Entrenamiento completado.")

if list(modelo.classes_) != [0, 1]:
    raise ValueError(
        "Las clases aprendidas por el modelo no son las esperadas."
    )

if list(modelo.feature_names_in_) != list(X_train.columns):
    raise ValueError(
        "El orden de las variables aprendidas no coincide."
    )


# ============================================================
# 10. COMPROBAR PREDICCIONES DEL MODELO ORIGINAL
# ============================================================

print("\nComprobando predicciones del modelo original...")

probabilidades = modelo.predict_proba(X_test)[:, 1]

if not np.isfinite(probabilidades).all():
    raise ValueError(
        "El modelo produjo probabilidades no válidas."
    )

if not ((probabilidades >= 0) & (probabilidades <= 1)).all():
    raise ValueError(
        "El modelo produjo probabilidades fuera del intervalo [0, 1]."
    )

print("Predicciones originales correctas.")


# ============================================================
# 11. CREAR DIRECTORIO Y EXPORTAR MODELO
# ============================================================

MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("\nExportando modelo...")

joblib.dump(
    modelo,
    MODEL_PATH,
    compress=3
)

print(f"Modelo guardado en: {MODEL_PATH}")


# ============================================================
# 12. CONSTRUIR ESQUEMA DE LAS VARIABLES
# ============================================================

print("\nConstruyendo esquema de variables...")

esquema_variables = {}

for columna in X_train.columns:

    valores = X_train[columna].dropna().unique().tolist()

    # Convertir tipos de NumPy a tipos nativos de Python
    valores = [
        valor.item() if isinstance(valor, np.generic) else valor
        for valor in valores
    ]

    esquema_variables[columna] = {
        "tipo": str(X_train[columna].dtype),
        "valores_observados_entrenamiento": sorted(valores)
    }


# ============================================================
# 13. CONSTRUIR METADATOS
# ============================================================

print("\nConstruyendo metadatos...")

metadatos = {

    "nombre": "BioGenAnalyzer Diabetes Model",

    "version": "1.0.0",

    "fecha_entrenamiento_utc": datetime.now(
        timezone.utc
    ).isoformat(),

    "entorno": {
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__
    },

    "algoritmo": {
        "nombre": "HistGradientBoostingClassifier",
        "hiperparametros": PARAMETROS
    },

    "variable_objetivo": TARGET,

    "clases": {
        "0": "Sin diabetes reportada",
        "1": "Prediabetes o diabetes reportada"
    },

    "variables_predictoras": list(X_train.columns),

    "numero_variables": len(X_train.columns),

    "orden_variables": list(X_train.columns),

    "esquema_variables": esquema_variables,

    "ponderacion_clases": {
        "metodo": "balanced",
        "distribucion_entrenamiento": distribucion_clases,
        "pesos": informacion_pesos
    },

    "umbrales": UMBRALES,

    "metricas_evaluacion_test": METRICAS_TEST,

    "dataset": {
        "nombre": "CDC Diabetes Health Indicators",
        "repositorio": "UCI Machine Learning Repository",
        "uci_id": 891,
        "anio": 2015,
        "registros_entrenamiento": int(len(X_train)),
        "registros_prueba": int(len(X_test)),
        "total_registros": int(len(X_train) + len(X_test))
    },

    "limitaciones": [
        (
            "Este modelo es una herramienta experimental de "
            "clasificación y no constituye un diagnóstico médico."
        ),
        (
            "La clase positiva combina prediabetes y diabetes reportadas "
            "en el conjunto de datos."
        ),
        (
            "El conjunto de datos procede de encuestas realizadas "
            "en Estados Unidos en 2015."
        ),
        (
            "No se ha validado el rendimiento del modelo en la "
            "población colombiana."
        ),
        (
            "Las probabilidades generadas no deben interpretarse "
            "como riesgo clínico individual ni como probabilidades "
            "clínicas calibradas."
        ),
        (
            "Los valores observados en entrenamiento no representan "
            "necesariamente todos los valores válidos de cada variable."
        )
    ],

    "archivo_modelo": MODEL_PATH.name
}


# ============================================================
# 14. GUARDAR METADATOS EN JSON
# ============================================================

with open(
    METADATA_PATH,
    "w",
    encoding="utf-8"
) as archivo:

    json.dump(
        metadatos,
        archivo,
        ensure_ascii=False,
        indent=4
    )

print(f"Metadatos guardados en: {METADATA_PATH}")


# ============================================================
# 15. RECARGAR Y VERIFICAR EL MODELO EXPORTADO
# ============================================================

print("\nRecargando modelo exportado...")

modelo_cargado = joblib.load(MODEL_PATH)

if list(modelo_cargado.classes_) != [0, 1]:
    raise ValueError(
        "Las clases del modelo cargado no coinciden."
    )

if list(modelo_cargado.feature_names_in_) != list(X_train.columns):
    raise ValueError(
        "Las variables del modelo cargado no coinciden."
    )

print("Clases y variables verificadas correctamente.")


# ============================================================
# 16. COMPROBAR EQUIVALENCIA DE PREDICCIONES
# ============================================================

print("\nVerificando equivalencia de predicciones...")

probabilidades_cargadas = modelo_cargado.predict_proba(X_test)[:, 1]

if not np.allclose(
    probabilidades,
    probabilidades_cargadas,
    rtol=1e-7,
    atol=1e-9
):
    raise ValueError(
        "Las predicciones del modelo cargado no coinciden "
        "con las del modelo original."
    )

print("Verificación de equivalencia de predicciones correcta.")


# ============================================================
# 17. RESUMEN FINAL
# ============================================================

print("\n" + "=" * 65)
print("EXPORTACIÓN COMPLETADA CORRECTAMENTE")
print("=" * 65)

print(f"\nModelo: {MODEL_PATH}")
print(f"Tamaño: {MODEL_PATH.stat().st_size / 1024:.2f} KB")

print(f"\nMetadatos: {METADATA_PATH}")
print(f"Tamaño: {METADATA_PATH.stat().st_size / 1024:.2f} KB")

print("\nModelo seleccionado: HistGradientBoostingClassifier")

print("\nUmbral principal:")
print(f"  Valor: {UMBRALES['principal']['valor']}")

print("\nUmbral alternativo:")
print(f"  Valor: {UMBRALES['alternativo']['valor']}")

print("\nROC-AUC en test:")
print(f"  {METRICAS_TEST['roc_auc']:.4f}")

print("\nF1 macro en test con umbral principal:")
print(f"  {METRICAS_TEST['umbral_0.71']['f1_macro']:.4f}")

print("\nF1 clase 1 en test con umbral alternativo:")
print(f"  {METRICAS_TEST['umbral_0.65']['f1_clase_1']:.4f}")

print("\nTodos los controles finalizaron correctamente.")
print("=" * 65)
