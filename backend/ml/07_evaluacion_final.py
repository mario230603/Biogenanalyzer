
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    roc_auc_score,
    average_precision_score,
    matthews_corrcoef,
    confusion_matrix,
    log_loss,
    brier_score_loss
)


# ============================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

TRAIN_PATH = BASE_DIR / "data" / "processed" / "diabetes_train.csv"
TEST_PATH = BASE_DIR / "data" / "processed" / "diabetes_test.csv"

OUTPUT_DIR = BASE_DIR / "reports" / "final_evaluation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Diabetes_binary"


# ============================================================
# 2. CARGAR Y VALIDAR LOS DATOS
# ============================================================

print("=" * 70)
print("ETAPA 7: EVALUACIÓN FINAL DE MODELOS")
print("=" * 70)

if not TRAIN_PATH.exists():
    raise FileNotFoundError(f"No se encontró: {TRAIN_PATH}")

if not TEST_PATH.exists():
    raise FileNotFoundError(f"No se encontró: {TEST_PATH}")

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)

if TARGET not in train.columns or TARGET not in test.columns:
    raise ValueError(f"No se encontró la columna objetivo: {TARGET}")

# Verificar que ambos conjuntos tengan las mismas columnas
if set(train.columns) != set(test.columns):
    columnas_faltantes = set(train.columns) - set(test.columns)
    columnas_adicionales = set(test.columns) - set(train.columns)

    raise ValueError(
        "Las columnas de entrenamiento y prueba no coinciden.\n"
        f"Faltantes en test: {columnas_faltantes}\n"
        f"Adicionales en test: {columnas_adicionales}"
    )

# Alinear el orden de las columnas
test = test[train.columns]

# Verificar valores faltantes
if train.isnull().any().any() or test.isnull().any().any():
    raise ValueError("Se encontraron valores faltantes en los datos.")

# Separar variables predictoras y objetivo
X_train = train.drop(columns=[TARGET])
y_train = train[TARGET].astype(int)

X_test = test.drop(columns=[TARGET])
y_test = test[TARGET].astype(int)

# Verificar que las clases sean binarias
if set(y_train.unique()) != {0, 1}:
    raise ValueError(
        "El conjunto de entrenamiento debe contener las clases 0 y 1."
    )

if set(y_test.unique()) != {0, 1}:
    raise ValueError(
        "El conjunto de prueba debe contener las clases 0 y 1."
    )

# Verificar tipos de datos
if not X_train.dtypes.equals(X_test.dtypes):
    raise ValueError(
        "Los tipos de datos de las variables predictoras no coinciden."
    )

print("\nDimensiones:")
print("X_train:", X_train.shape)
print("X_test:", X_test.shape)

print("\nDistribución de clases en entrenamiento:")
print(y_train.value_counts(normalize=True).sort_index())

print("\nDistribución de clases en prueba:")
print(y_test.value_counts(normalize=True).sort_index())


# ============================================================
# 3. DEFINIR LOS MODELOS
# ============================================================

modelos = {
    "Regresion_Logistica": Pipeline([
        ("scaler", StandardScaler()),
        ("modelo", LogisticRegression(
            C=0.01,
            max_iter=2000,
            random_state=42
        ))
    ]),

    "Random_Forest": RandomForestClassifier(
        n_estimators=200,
        min_samples_split=10,
        min_samples_leaf=20,
        max_features=0.5,
        max_depth=15,
        random_state=42,
        n_jobs=2
    ),

    "HistGradientBoosting": HistGradientBoostingClassifier(
        min_samples_leaf=30,
        max_leaf_nodes=63,
        max_iter=150,
        learning_rate=0.1,
        l2_regularization=0.5,
        random_state=42
    )
}


# ============================================================
# 4. UMBRALES SELECCIONADOS EN LA ETAPA 6
# ============================================================

umbrales = {
    "Regresion_Logistica": {
        "F1_macro": 0.67,
        "F1_clase_1": 0.61
    },

    "Random_Forest": {
        "F1_macro": 0.68,
        "F1_clase_1": 0.62
    },

    "HistGradientBoosting": {
        "F1_macro": 0.71,
        "F1_clase_1": 0.65
    }
}


# ============================================================
# 5. CALCULAR PESOS DE CLASE
# ============================================================

# Los pesos se calculan exclusivamente con el conjunto de
# entrenamiento. El conjunto de prueba no interviene aquí.

pesos = compute_sample_weight(
    class_weight="balanced",
    y=y_train
)


# ============================================================
# 6. ENTRENAR LOS MODELOS Y OBTENER PROBABILIDADES
# ============================================================

resultados = []
matrices = []
metricas_modelos = []

# Almacenar predicciones individuales
predicciones_test = pd.DataFrame({
    "indice_registro": test.index,
    "clase_real": y_test.values
})

for nombre, modelo in modelos.items():

    print("\n" + "=" * 70)
    print(f"ENTRENANDO MODELO: {nombre}")
    print("=" * 70)

    # --------------------------------------------------------
    # 6.1 Entrenamiento
    # --------------------------------------------------------

    if nombre == "Regresion_Logistica":

        modelo.fit(
            X_train,
            y_train,
            modelo__sample_weight=pesos
        )

    else:

        modelo.fit(
            X_train,
            y_train,
            sample_weight=pesos
        )

    print("Entrenamiento completado.")

    # --------------------------------------------------------
    # 6.2 Obtener probabilidades de la clase positiva
    # --------------------------------------------------------

    indice_positivo = list(modelo.classes_).index(1)

    probabilidades = modelo.predict_proba(X_test)[:, indice_positivo]

    if not np.isfinite(probabilidades).all():
        raise ValueError(
            f"Probabilidades no válidas en {nombre}."
        )

    if ((probabilidades < 0) | (probabilidades > 1)).any():
        raise ValueError(
            f"Probabilidades fuera del rango [0, 1] en {nombre}."
        )

    # --------------------------------------------------------
    # 6.3 Métricas independientes del umbral
    # --------------------------------------------------------

    roc_auc = roc_auc_score(
        y_test,
        probabilidades
    )

    average_precision = average_precision_score(
        y_test,
        probabilidades
    )

    perdida_logaritmica = log_loss(
        y_test,
        probabilidades,
        labels=[0, 1]
    )

    brier = brier_score_loss(
        y_test,
        probabilidades
    )

    metricas_modelos.append({
        "modelo": nombre,
        "roc_auc": roc_auc,
        "average_precision": average_precision,
        "log_loss": perdida_logaritmica,
        "brier_score": brier
    })

    # Guardar probabilidades individuales
    columna_probabilidad = f"{nombre}_probabilidad"

    predicciones_test[columna_probabilidad] = probabilidades

    print("\nMétricas probabilísticas:")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"Average Precision: {average_precision:.4f}")
    print(f"Log Loss: {perdida_logaritmica:.4f}")
    print(f"Brier Score: {brier:.4f}")

    # --------------------------------------------------------
    # 6.4 Evaluar las dos estrategias de umbral
    # --------------------------------------------------------

    for estrategia, umbral in umbrales[nombre].items():

        predicciones = (
            probabilidades >= umbral
        ).astype(int)

        # Matriz de confusión
        tn, fp, fn, tp = confusion_matrix(
            y_test,
            predicciones,
            labels=[0, 1]
        ).ravel()

        # Especificidad
        especificidad = (
            tn / (tn + fp)
            if (tn + fp) > 0
            else 0
        )

        # Métricas de clasificación
        metricas = {
            "modelo": nombre,
            "estrategia": estrategia,
            "umbral": umbral,

            "accuracy": accuracy_score(
                y_test,
                predicciones
            ),

            "precision_clase_1": precision_score(
                y_test,
                predicciones,
                zero_division=0
            ),

            "recall_clase_1": recall_score(
                y_test,
                predicciones,
                zero_division=0
            ),

            "f1_clase_1": f1_score(
                y_test,
                predicciones,
                zero_division=0
            ),

            "f1_macro": f1_score(
                y_test,
                predicciones,
                average="macro",
                zero_division=0
            ),

            "balanced_accuracy": balanced_accuracy_score(
                y_test,
                predicciones
            ),

            "especificidad": especificidad,

            "roc_auc": roc_auc,

            "average_precision": average_precision,

            "mcc": matthews_corrcoef(
                y_test,
                predicciones
            ),

            "log_loss": perdida_logaritmica,

            "brier_score": brier,

            "TN": tn,
            "FP": fp,
            "FN": fn,
            "TP": tp
        }

        resultados.append(metricas)

        matrices.append({
            "modelo": nombre,
            "estrategia": estrategia,
            "umbral": umbral,
            "TN": tn,
            "FP": fp,
            "FN": fn,
            "TP": tp
        })

        # Guardar predicciones binarias individuales
        columna_prediccion = (
            f"{nombre}_prediccion_{estrategia}"
        )

        predicciones_test[columna_prediccion] = predicciones

        # ----------------------------------------------------
        # 6.5 Mostrar resultados
        # ----------------------------------------------------

        print("\n" + "-" * 55)
        print(f"Estrategia: {estrategia}")
        print(f"Umbral: {umbral}")

        print(f"F1 macro: {metricas['f1_macro']:.4f}")
        print(f"F1 clase 1: {metricas['f1_clase_1']:.4f}")

        print(
            f"Precisión clase 1: "
            f"{metricas['precision_clase_1']:.4f}"
        )

        print(
            f"Recall clase 1: "
            f"{metricas['recall_clase_1']:.4f}"
        )

        print(
            f"Balanced Accuracy: "
            f"{metricas['balanced_accuracy']:.4f}"
        )

        print(f"Especificidad: {especificidad:.4f}")
        print(f"MCC: {metricas['mcc']:.4f}")

        print(
            f"TN={tn}, FP={fp}, FN={fn}, TP={tp}"
        )


# ============================================================
# 7. GUARDAR RESULTADOS
# ============================================================

df_resultados = pd.DataFrame(resultados)
df_matrices = pd.DataFrame(matrices)
df_metricas_modelos = pd.DataFrame(metricas_modelos)

# Rutas de salida
ruta_resultados = OUTPUT_DIR / "resultados_finales.csv"
ruta_matrices = OUTPUT_DIR / "matrices_confusion.csv"
ruta_predicciones = OUTPUT_DIR / "predicciones_test.csv"
ruta_metricas_modelos = OUTPUT_DIR / "metricas_por_modelo.csv"

# Guardar archivos
df_resultados.to_csv(
    ruta_resultados,
    index=False
)

df_matrices.to_csv(
    ruta_matrices,
    index=False
)

predicciones_test.to_csv(
    ruta_predicciones,
    index=False
)

df_metricas_modelos.to_csv(
    ruta_metricas_modelos,
    index=False
)


# ============================================================
# 8. MOSTRAR RESUMEN FINAL
# ============================================================

print("\n" + "=" * 70)
print("RESUMEN DE EVALUACIÓN FINAL")
print("=" * 70)

columnas_resumen = [
    "modelo",
    "estrategia",
    "umbral",
    "f1_macro",
    "f1_clase_1",
    "precision_clase_1",
    "recall_clase_1",
    "balanced_accuracy",
    "roc_auc",
    "average_precision",
    "mcc",
    "especificidad",
    "brier_score"
]

print(
    df_resultados[columnas_resumen]
    .round(4)
    .to_string(index=False)
)

print("\n" + "=" * 70)
print("MÉTRICAS PROBABILÍSTICAS POR MODELO")
print("=" * 70)

print(
    df_metricas_modelos
    .round(4)
    .to_string(index=False)
)

print("\n" + "=" * 70)
print("ARCHIVOS GUARDADOS")
print("=" * 70)

print(ruta_resultados)
print(ruta_matrices)
print(ruta_predicciones)
print(ruta_metricas_modelos)

print("\nEtapa 7 completada correctamente.")
