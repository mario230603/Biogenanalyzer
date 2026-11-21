
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier
)
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from sklearn.model_selection import StratifiedGroupKFold
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
    log_loss,
    confusion_matrix
)


# ==================================================
# 1. RUTAS Y CONFIGURACIÓN
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RUTA_TRAIN = BASE_DIR / "data" / "processed" / "diabetes_train.csv"

CARPETA_RESULTADOS = (
    BASE_DIR / "reports" / "model_comparison"
)

CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)

OBJETIVO = "Diabetes_binary"

N_SPLITS = 5
RANDOM_STATE = 42


# ==================================================
# 2. CARGAR DATOS DE ENTRENAMIENTO
# ==================================================

print("\nCargando conjunto de entrenamiento...")

datos = pd.read_csv(RUTA_TRAIN)

if OBJETIVO not in datos.columns:
    raise ValueError(
        f"No se encontró la columna objetivo: {OBJETIVO}"
    )

X_train = datos.drop(columns=[OBJETIVO])
y_train = datos[OBJETIVO].astype(int)

print("Dimensiones de X:", X_train.shape)
print("Dimensiones de y:", y_train.shape)

print("\nDistribución de clases:")
print(y_train.value_counts(normalize=True).sort_index())


# ==================================================
# 3. RECONSTRUIR GRUPOS
# ==================================================

# Las filas con predictores idénticos deben permanecer
# en la misma partición para evitar fuga de información.

grupos = pd.util.hash_pandas_object(
    X_train,
    index=False
).values


# ==================================================
# 4. DEFINIR LOS ALGORITMOS
# ==================================================

modelos = {

    "Dummy": DummyClassifier(
        strategy="most_frequent"
    ),

    "Regresion_Logistica": Pipeline([
        ("escalador", StandardScaler()),
        ("modelo", LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_STATE
        ))
    ]),

    "Arbol_Decision": DecisionTreeClassifier(
        min_samples_leaf=20,
        random_state=RANDOM_STATE
    ),

    "Random_Forest": RandomForestClassifier(
        n_estimators=150,
        min_samples_leaf=5,
        max_features="sqrt",
        n_jobs=-1,
        random_state=RANDOM_STATE
    ),

    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.1,
        l2_regularization=1.0,
        random_state=RANDOM_STATE
    )
}


# ==================================================
# 5. FUNCIÓN PARA CALCULAR MÉTRICAS
# ==================================================

def calcular_metricas(y_real, y_pred, y_prob):

    matriz = confusion_matrix(
        y_real,
        y_pred,
        labels=[0, 1]
    )

    tn, fp, fn, tp = matriz.ravel()

    especificidad = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0
    )

    metricas = {

        "verdaderos_negativos": int(tn),
        "falsos_positivos": int(fp),
        "falsos_negativos": int(fn),
        "verdaderos_positivos": int(tp),

        "accuracy": accuracy_score(
            y_real, y_pred
        ),

        "precision_clase_1": precision_score(
            y_real,
            y_pred,
            pos_label=1,
            zero_division=0
        ),

        "recall_clase_1": recall_score(
            y_real,
            y_pred,
            pos_label=1,
            zero_division=0
        ),

        "f1_clase_1": f1_score(
            y_real,
            y_pred,
            pos_label=1,
            zero_division=0
        ),

        "f1_macro": f1_score(
            y_real,
            y_pred,
            average="macro",
            zero_division=0
        ),

        "especificidad": especificidad,

        "balanced_accuracy": balanced_accuracy_score(
            y_real, y_pred
        ),

        "roc_auc": roc_auc_score(
            y_real, y_prob
        ),

        "average_precision": average_precision_score(
            y_real, y_prob
        ),

        "mcc": matthews_corrcoef(
            y_real, y_pred
        ),

        "log_loss": log_loss(
            y_real,
            y_prob,
            labels=[0, 1]
        )
    }

    return metricas


# ==================================================
# 6. VALIDACIÓN CRUZADA AGRUPADA Y ESTRATIFICADA
# ==================================================

validador = StratifiedGroupKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE
)

# Calculamos las particiones una sola vez para que
# todos los algoritmos utilicen exactamente los mismos folds.

particiones = list(
    validador.split(X_train, y_train, groups=grupos)
)


# ==================================================
# 7. ENTRENAR Y EVALUAR LOS MODELOS
# ==================================================

resultados = []

for nombre, modelo_base in modelos.items():

    print("\n" + "=" * 60)
    print(f"Evaluando modelo: {nombre}")
    print("=" * 60)

    for numero_fold, (indices_train, indices_val) in enumerate(
        particiones,
        start=1
    ):

        print(f"\nFold {numero_fold}/{N_SPLITS}")

        X_fold_train = X_train.iloc[indices_train]
        X_fold_val = X_train.iloc[indices_val]

        y_fold_train = y_train.iloc[indices_train]
        y_fold_val = y_train.iloc[indices_val]

        modelo = clone(modelo_base)

        # El baseline Dummy no utiliza ponderación.
        if nombre == "Dummy":

            modelo.fit(
                X_fold_train,
                y_fold_train
            )

        else:

            # Los pesos se calculan exclusivamente
            # con las etiquetas del fold de entrenamiento.

            pesos = compute_sample_weight(
                class_weight="balanced",
                y=y_fold_train
            )

            if nombre == "Regresion_Logistica":

                modelo.fit(
                    X_fold_train,
                    y_fold_train,
                    modelo__sample_weight=pesos
                )

            else:

                modelo.fit(
                    X_fold_train,
                    y_fold_train,
                    sample_weight=pesos
                )

        # ------------------------------------------
        # PREDICCIONES EN ENTRENAMIENTO
        # ------------------------------------------

        y_train_pred = modelo.predict(
            X_fold_train
        )

        y_train_prob = modelo.predict_proba(
            X_fold_train
        )[:, list(modelo.classes_).index(1)]

        # ------------------------------------------
        # PREDICCIONES EN VALIDACIÓN
        # ------------------------------------------

        y_val_pred = modelo.predict(
            X_fold_val
        )

        y_val_prob = modelo.predict_proba(
            X_fold_val
        )[:, list(modelo.classes_).index(1)]

        # ------------------------------------------
        # MÉTRICAS
        # ------------------------------------------

        metricas_train = calcular_metricas(
            y_fold_train,
            y_train_pred,
            y_train_prob
        )

        metricas_val = calcular_metricas(
            y_fold_val,
            y_val_pred,
            y_val_prob
        )

        # ------------------------------------------
        # GUARDAR RESULTADOS DEL FOLD
        # ------------------------------------------

        fila = {
            "modelo": nombre,
            "fold": numero_fold
        }

        for metrica in metricas_train:

            fila[f"{metrica}_train"] = (
                metricas_train[metrica]
            )

            fila[f"{metrica}_val"] = (
                metricas_val[metrica]
            )

            fila[f"brecha_{metrica}"] = (
                metricas_train[metrica]
                - metricas_val[metrica]
            )

        resultados.append(fila)

        print(
            f"F1 macro train: "
            f"{metricas_train['f1_macro']:.4f}"
        )

        print(
            f"F1 macro validación: "
            f"{metricas_val['f1_macro']:.4f}"
        )

        print(
            f"ROC-AUC validación: "
            f"{metricas_val['roc_auc']:.4f}"
        )

        print(
            f"Brecha F1 macro: "
            f"{metricas_train['f1_macro'] - metricas_val['f1_macro']:.4f}"
        )


# ==================================================
# 8. GUARDAR RESULTADOS POR FOLD
# ==================================================

df_resultados = pd.DataFrame(resultados)

ruta_folds = (
    CARPETA_RESULTADOS
    / "resultados_por_particion.csv"
)

df_resultados.to_csv(
    ruta_folds,
    index=False
)


# ==================================================
# 9. CALCULAR PROMEDIO Y DESVIACIÓN ESTÁNDAR
# ==================================================

columnas_metricas = [
    columna
    for columna in df_resultados.columns
    if columna not in ["modelo", "fold"]
]

resumen = df_resultados.groupby("modelo")[
    columnas_metricas
].agg(["mean", "std"])

# Aplanar nombres de columnas.
resumen.columns = [
    f"{metrica}_{estadistico}"
    for metrica, estadistico in resumen.columns
]

resumen = resumen.reset_index()

# Ordenar por F1 macro promedio de validación.
resumen = resumen.sort_values(
    by="f1_macro_val_mean",
    ascending=False
)

ruta_resumen = (
    CARPETA_RESULTADOS
    / "resumen_comparacion.csv"
)

resumen.to_csv(
    ruta_resumen,
    index=False
)


# ==================================================
# 10. MOSTRAR RESULTADOS
# ==================================================

columnas_mostrar = [
    "modelo",
    "f1_macro_train_mean",
    "f1_macro_val_mean",
    "f1_macro_val_std",
    "brecha_f1_macro_mean",
    "recall_clase_1_val_mean",
    "precision_clase_1_val_mean",
    "balanced_accuracy_val_mean",
    "roc_auc_val_mean",
    "average_precision_val_mean",
    "especificidad_val_mean",
    "mcc_val_mean",
    "log_loss_val_mean"
]

print("\n")
print("=" * 100)
print("RESULTADOS PROMEDIO DE VALIDACIÓN CRUZADA")
print("=" * 100)

print(
    resumen[columnas_mostrar].to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

print("\nArchivos guardados:")
print(ruta_folds)
print(ruta_resumen)

print("\nComparación de algoritmos finalizada.")
