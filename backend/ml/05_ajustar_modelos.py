
from pathlib import Path
import json

import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedGroupKFold, ParameterSampler
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
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
    confusion_matrix,
)


# --------------------------------------------------
# 1. RUTAS Y CONFIGURACIÓN
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

RUTA_TRAIN = BASE_DIR / "data" / "processed" / "diabetes_train.csv"
RUTA_REPORTES = BASE_DIR / "reports" / "model_tuning"

RUTA_REPORTES.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
N_SPLITS = 5
N_CONFIGURACIONES = 6


# --------------------------------------------------
# 2. CARGAR LOS DATOS DE ENTRENAMIENTO
# --------------------------------------------------

print("\nCargando conjunto de entrenamiento...")

if not RUTA_TRAIN.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo: {RUTA_TRAIN}"
    )

datos = pd.read_csv(RUTA_TRAIN)

if "Diabetes_binary" not in datos.columns:
    raise ValueError(
        "No se encontró la columna objetivo Diabetes_binary."
    )

X = datos.drop(columns=["Diabetes_binary"])
y = datos["Diabetes_binary"].astype(int)

if set(y.unique()) != {0, 1}:
    raise ValueError(
        "La variable objetivo debe contener las clases 0 y 1."
    )

print(f"Registros: {len(datos):,}")
print(f"Variables predictoras: {X.shape[1]}")
print(f"Distribución de clases:\n{y.value_counts().sort_index()}")


# --------------------------------------------------
# 3. CREAR GRUPOS Y PARTICIONES
# --------------------------------------------------

print("\nPreparando validación cruzada...")

# Los registros con predictores idénticos permanecen
# siempre dentro de la misma partición.
grupos = pd.util.hash_pandas_object(
    X,
    index=False
).values

cv = StratifiedGroupKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE
)

# Creamos las particiones una sola vez para que
# todos los modelos utilicen exactamente las mismas.
particiones = list(cv.split(X, y, groups=grupos))

print(f"Particiones creadas: {len(particiones)}")


# --------------------------------------------------
# 4. DEFINIR LOS MODELOS Y SUS CONFIGURACIONES
# --------------------------------------------------

espacios_parametros = {
    "Regresion_Logistica": {
        "C": [0.001, 0.01, 0.1, 1, 10],
    },

    "Random_Forest": {
        "n_estimators": [150, 200],
        "max_depth": [10, 12, 15, 18],
        "min_samples_split": [10, 20, 40],
        "min_samples_leaf": [10, 20, 30],
        "max_features": ["sqrt", 0.5],
    },

    "HistGradientBoosting": {
        "max_iter": [150, 200, 300],
        "learning_rate": [0.03, 0.05, 0.08, 0.1],
        "max_leaf_nodes": [15, 31, 45, 63],
        "min_samples_leaf": [20, 30, 50],
        "l2_regularization": [0.5, 1.0, 3.0, 5.0],
    },
}


def crear_modelo(nombre, parametros):
    """
    Construye el modelo correspondiente con los
    hiperparámetros de una configuración.
    """

    if nombre == "Regresion_Logistica":
        clasificador = LogisticRegression(
            penalty="l2",
            solver="lbfgs",
            max_iter=2000,
            random_state=RANDOM_STATE,
            C=parametros["C"],
        )

        return Pipeline([
            ("escalador", StandardScaler()),
            ("modelo", clasificador),
        ])

    if nombre == "Random_Forest":
        return RandomForestClassifier(
            **parametros,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

    if nombre == "HistGradientBoosting":
        return HistGradientBoostingClassifier(
            **parametros,
            random_state=RANDOM_STATE,
        )

    raise ValueError(f"Modelo desconocido: {nombre}")


# --------------------------------------------------
# 5. FUNCIÓN PARA CALCULAR MÉTRICAS
# --------------------------------------------------

def calcular_metricas(y_real, predicciones, probabilidades):
    tn, fp, fn, tp = confusion_matrix(
        y_real,
        predicciones,
        labels=[0, 1]
    ).ravel()

    especificidad = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0
    )

    return {
        "accuracy": accuracy_score(y_real, predicciones),
        "precision_clase_1": precision_score(
            y_real, predicciones, zero_division=0
        ),
        "recall_clase_1": recall_score(
            y_real, predicciones, zero_division=0
        ),
        "f1_clase_1": f1_score(
            y_real, predicciones, zero_division=0
        ),
        "f1_macro": f1_score(
            y_real, predicciones, average="macro", zero_division=0
        ),
        "balanced_accuracy": balanced_accuracy_score(
            y_real, predicciones
        ),
        "specificity": especificidad,
        "roc_auc": roc_auc_score(
            y_real, probabilidades
        ),
        "average_precision": average_precision_score(
            y_real, probabilidades
        ),
        "mcc": matthews_corrcoef(
            y_real, predicciones
        ),
        "log_loss": log_loss(
            y_real,
            probabilidades,
            labels=[0, 1]
        ),
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "TP": tp,
    }


# --------------------------------------------------
# 6. AJUSTE Y VALIDACIÓN DE LOS MODELOS
# --------------------------------------------------

resultados = []
mejores_configuraciones = {}

for nombre_modelo, espacio in espacios_parametros.items():

    print("\n" + "=" * 65)
    print(f"AJUSTANDO: {nombre_modelo}")
    print("=" * 65)

    configuraciones = list(
        ParameterSampler(
            espacio,
            n_iter=N_CONFIGURACIONES,
            random_state=RANDOM_STATE,
        )
    )

    mejor_f1 = -np.inf
    mejor_parametro = None

    for numero_config, parametros in enumerate(
        configuraciones,
        start=1
    ):

        print(
            f"\nConfiguración {numero_config}/"
            f"{N_CONFIGURACIONES}"
        )
        print(f"Hiperparámetros: {parametros}")

        for numero_fold, (indices_train, indices_val) in enumerate(
            particiones,
            start=1
        ):

            X_train = X.iloc[indices_train]
            X_val = X.iloc[indices_val]

            y_train = y.iloc[indices_train]
            y_val = y.iloc[indices_val]

            # Los pesos se calculan exclusivamente
            # con las etiquetas del fold de entrenamiento.
            pesos = compute_sample_weight(
                class_weight="balanced",
                y=y_train
            )

            modelo = crear_modelo(
                nombre_modelo,
                parametros
            )

            if nombre_modelo == "Regresion_Logistica":
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

            # Predicciones de entrenamiento
            pred_train = modelo.predict(X_train)

            prob_train = modelo.predict_proba(X_train)[:, 1]

            metricas_train = calcular_metricas(
                y_train,
                pred_train,
                prob_train
            )

            # Predicciones de validación
            pred_val = modelo.predict(X_val)

            prob_val = modelo.predict_proba(X_val)[:, 1]

            metricas_val = calcular_metricas(
                y_val,
                pred_val,
                prob_val
            )

            registro = {
                "modelo": nombre_modelo,
                "configuracion": numero_config,
                "fold": numero_fold,
                "hiperparametros": json.dumps(
                    parametros,
                    sort_keys=True
                ),
            }

            for metrica, valor in metricas_train.items():
                registro[f"train_{metrica}"] = valor

            for metrica, valor in metricas_val.items():
                registro[f"val_{metrica}"] = valor

            registro["brecha_f1_macro"] = (
                metricas_train["f1_macro"]
                - metricas_val["f1_macro"]
            )

            registro["brecha_roc_auc"] = (
                metricas_train["roc_auc"]
                - metricas_val["roc_auc"]
            )

            resultados.append(registro)

            print(
                f"Fold {numero_fold}/{N_SPLITS} | "
                f"F1 macro: {metricas_val['f1_macro']:.4f} | "
                f"Recall: {metricas_val['recall_clase_1']:.4f} | "
                f"ROC-AUC: {metricas_val['roc_auc']:.4f}"
            )

        # Evaluamos la media de F1 macro de esta configuración.
        registros_config = [
            r for r in resultados
            if r["modelo"] == nombre_modelo
            and r["configuracion"] == numero_config
        ]

        f1_promedio = np.mean([
            r["val_f1_macro"]
            for r in registros_config
        ])

        if f1_promedio > mejor_f1:
            mejor_f1 = f1_promedio
            mejor_parametro = parametros.copy()

        print(
            f"F1 macro promedio de la configuración: "
            f"{f1_promedio:.4f}"
        )

    mejores_configuraciones[nombre_modelo] = {
        "hiperparametros": mejor_parametro,
        "f1_macro_promedio": float(mejor_f1),
    }

    print(
        f"\nMejor configuración de {nombre_modelo}: "
        f"{mejor_parametro}"
    )
    print(f"Mejor F1 macro promedio: {mejor_f1:.4f}")


# --------------------------------------------------
# 7. GUARDAR RESULTADOS POR PARTICIÓN
# --------------------------------------------------

df_resultados = pd.DataFrame(resultados)

ruta_particiones = (
    RUTA_REPORTES / "resultados_por_particion.csv"
)

df_resultados.to_csv(
    ruta_particiones,
    index=False
)


# --------------------------------------------------
# 8. GENERAR RESUMEN POR CONFIGURACIÓN
# --------------------------------------------------

columnas_metricas = [
    "val_f1_macro",
    "val_f1_clase_1",
    "val_precision_clase_1",
    "val_recall_clase_1",
    "val_balanced_accuracy",
    "val_roc_auc",
    "val_average_precision",
    "val_mcc",
    "val_specificity",
    "val_log_loss",
    "brecha_f1_macro",
    "brecha_roc_auc",
]

resumen = (
    df_resultados
    .groupby(
        ["modelo", "configuracion", "hiperparametros"]
    )[columnas_metricas]
    .agg(["mean", "std"])
)

resumen.columns = [
    f"{metrica}_{estadistico}"
    for metrica, estadistico in resumen.columns
]

resumen = resumen.reset_index()

# Ordenar por F1 macro promedio, de mayor a menor.
resumen = resumen.sort_values(
    by="val_f1_macro_mean",
    ascending=False
)

ruta_resumen = (
    RUTA_REPORTES / "resumen_ajuste.csv"
)

resumen.to_csv(
    ruta_resumen,
    index=False
)


# --------------------------------------------------
# 9. GUARDAR LAS MEJORES CONFIGURACIONES
# --------------------------------------------------

ruta_mejores = (
    RUTA_REPORTES / "mejores_configuraciones.json"
)

with open(ruta_mejores, "w", encoding="utf-8") as archivo:
    json.dump(
        mejores_configuraciones,
        archivo,
        indent=4,
        ensure_ascii=False
    )


# --------------------------------------------------
# 10. MOSTRAR RESULTADOS FINALES
# --------------------------------------------------

print("\n" + "=" * 65)
print("RESUMEN FINAL DEL AJUSTE")
print("=" * 65)

columnas_mostrar = [
    "modelo",
    "configuracion",
    "val_f1_macro_mean",
    "val_f1_macro_std",
    "val_recall_clase_1_mean",
    "val_precision_clase_1_mean",
    "val_balanced_accuracy_mean",
    "val_roc_auc_mean",
    "val_average_precision_mean",
    "val_mcc_mean",
    "brecha_f1_macro_mean",
]

print(
    resumen[columnas_mostrar]
    .round(4)
    .to_string(index=False)
)

print("\nArchivos guardados correctamente:")
print(f"- {ruta_particiones}")
print(f"- {ruta_resumen}")
print(f"- {ruta_mejores}")

print("\nAjuste de hiperparámetros finalizado.")
