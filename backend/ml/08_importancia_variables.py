
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score


# ============================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

TRAIN_PATH = BASE_DIR / "data" / "processed" / "diabetes_train.csv"
TEST_PATH = BASE_DIR / "data" / "processed" / "diabetes_test.csv"

OUTPUT_DIR = BASE_DIR / "reports" / "feature_importance"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Diabetes_binary"


# ============================================================
# 2. CARGAR Y VALIDAR LOS DATOS
# ============================================================

print("=" * 70)
print("ETAPA 8: IMPORTANCIA DE VARIABLES")
print("=" * 70)

if not TRAIN_PATH.exists():
    raise FileNotFoundError(f"No se encontró: {TRAIN_PATH}")

if not TEST_PATH.exists():
    raise FileNotFoundError(f"No se encontró: {TEST_PATH}")

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)

if TARGET not in train.columns or TARGET not in test.columns:
    raise ValueError(f"No se encontró la variable objetivo: {TARGET}")

if list(train.columns) != list(test.columns):
    raise ValueError("Las columnas de entrenamiento y prueba no coinciden.")

if train.isnull().any().any() or test.isnull().any().any():
    raise ValueError("Se encontraron valores faltantes.")

X_train = train.drop(columns=[TARGET])
y_train = train[TARGET].astype(int)

X_test = test.drop(columns=[TARGET])
y_test = test[TARGET].astype(int)

if set(y_train.unique()) != {0, 1}:
    raise ValueError("El entrenamiento debe contener las clases 0 y 1.")

if set(y_test.unique()) != {0, 1}:
    raise ValueError("La prueba debe contener las clases 0 y 1.")

if not all(
    pd.api.types.is_numeric_dtype(dtype)
    for dtype in X_train.dtypes
):
    raise ValueError("Se encontraron variables no numéricas.")

print("\nDimensiones:")
print("X_train:", X_train.shape)
print("X_test:", X_test.shape)

print("\nNúmero de variables:", X_train.shape[1])


# ============================================================
# 3. DEFINIR HISTGRADIENTBOOSTING
# ============================================================

modelo = HistGradientBoostingClassifier(
    min_samples_leaf=30,
    max_leaf_nodes=63,
    max_iter=150,
    learning_rate=0.1,
    l2_regularization=0.5,
    random_state=42
)


# ============================================================
# 4. ENTRENAR EL MODELO
# ============================================================

print("\n" + "=" * 70)
print("ENTRENAMIENTO DE HISTGRADIENTBOOSTING")
print("=" * 70)

pesos = compute_sample_weight(
    class_weight="balanced",
    y=y_train
)

modelo.fit(
    X_train,
    y_train,
    sample_weight=pesos
)

print("Entrenamiento completado.")


# ============================================================
# 5. RENDIMIENTO BASE DEL MODELO
# ============================================================

probabilidades = modelo.predict_proba(X_test)[:, 1]

roc_auc_base = roc_auc_score(
    y_test,
    probabilidades
)

print("\nROC-AUC original:", round(roc_auc_base, 4))


# ============================================================
# 6. CALCULAR IMPORTANCIA POR PERMUTACIÓN
# ============================================================

print("\n" + "=" * 70)
print("CALCULANDO IMPORTANCIA POR PERMUTACIÓN")
print("=" * 70)

print("Métrica utilizada: ROC-AUC")
print("Número de repeticiones: 10")
print("Este proceso puede tardar algunos minutos.")

importancia = permutation_importance(
    estimator=modelo,
    X=X_test,
    y=y_test,
    scoring="roc_auc",
    n_repeats=10,
    random_state=42,
    n_jobs=2
)

print("Cálculo completado.")


# ============================================================
# 7. ORGANIZAR LOS RESULTADOS
# ============================================================

df_importancia = pd.DataFrame({
    "variable": X_test.columns,

    "importancia_media": importancia.importances_mean,

    "desviacion_estandar": importancia.importances_std,

    "importancia_minima": importancia.importances.min(axis=1),

    "importancia_maxima": importancia.importances.max(axis=1),

    "repeticiones_positivas": (
        importancia.importances > 0
    ).mean(axis=1)
})

df_importancia = df_importancia.sort_values(
    by="importancia_media",
    ascending=False
).reset_index(drop=True)

df_importancia.insert(
    0,
    "posicion",
    range(1, len(df_importancia) + 1)
)


# ============================================================
# 8. GUARDAR RESULTADOS
# ============================================================

ruta_csv = OUTPUT_DIR / "importancia_variables.csv"

df_importancia.to_csv(
    ruta_csv,
    index=False
)


# ============================================================
# 9. GENERAR GRÁFICO DE IMPORTANCIA
# ============================================================

top_n = min(15, len(df_importancia))

datos_grafico = df_importancia.head(top_n).sort_values(
    by="importancia_media",
    ascending=True
)

plt.figure(figsize=(11, 8))

plt.barh(
    datos_grafico["variable"],
    datos_grafico["importancia_media"],
    xerr=datos_grafico["desviacion_estandar"],
    capsize=3
)

plt.axvline(
    x=0,
    linestyle="--",
    linewidth=1
)

plt.xlabel("Disminución del ROC-AUC después de permutar la variable")
plt.ylabel("Variables")
plt.title(
    "Importancia de variables - HistGradientBoosting"
)

plt.tight_layout()

ruta_grafico = OUTPUT_DIR / "importancia_variables_top15.png"

plt.savefig(
    ruta_grafico,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 10. MOSTRAR RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("RANKING DE IMPORTANCIA DE VARIABLES")
print("=" * 70)

print(
    df_importancia[
        [
            "posicion",
            "variable",
            "importancia_media",
            "desviacion_estandar",
            "repeticiones_positivas"
        ]
    ].round(5).to_string(index=False)
)

print("\n" + "=" * 70)
print("ARCHIVOS GENERADOS")
print("=" * 70)

print(ruta_csv)
print(ruta_grafico)

print("\nEtapa 8 completada correctamente.")
