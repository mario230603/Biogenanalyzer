
from pathlib import Path
import json

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
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
    confusion_matrix
)


# ==================================================
# 1. RUTAS
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[1]

TRAIN_PATH = (
    BASE_DIR / "data" / "processed" / "diabetes_train.csv"
)

OUTPUT_DIR = (
    BASE_DIR / "reports" / "threshold_optimization"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. CONFIGURACIÓN
# ==================================================

RANDOM_STATE = 42
N_SPLITS = 5

UMBRAL_INICIAL = 0.50

UMBRALES = np.round(
    np.arange(0.10, 0.91, 0.01),
    2
)

# Objetivo experimental de precisión mínima.
# No representa un estándar clínico.
PRECISION_MINIMA = 0.35


# ==================================================
# 3. CARGAR DATOS DE ENTRENAMIENTO
# ==================================================

print("\nCargando datos de entrenamiento...")

df = pd.read_csv(TRAIN_PATH)

if "Diabetes_binary" not in df.columns:
    raise ValueError(
        "No se encontró la columna Diabetes_binary."
    )

X = df.drop(columns=["Diabetes_binary"])
y = df["Diabetes_binary"].astype(int)

if set(y.unique()) != {0, 1}:
    raise ValueError(
        "La variable objetivo debe contener las clases 0 y 1."
    )

if X.isnull().any().any():
    raise ValueError(
        "Se encontraron valores faltantes en X. "
        "Revisa el preprocesamiento antes de continuar."
    )

print(f"Registros: {len(X)}")
print(f"Variables predictoras: {X.shape[1]}")

print("\nDistribución de clases:")
print(y.value_counts())

print("\nProporción de clases:")
print(y.value_counts(normalize=True))


# ==================================================
# 4. CREAR GRUPOS Y PARTICIONES
# ==================================================

print("\nCreando particiones...")

grupos = pd.util.hash_pandas_object(
    X,
    index=False
).values

cv = StratifiedGroupKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE
)

particiones = list(
    cv.split(X, y, groups=grupos)
)

print("Particiones creadas:", len(particiones))


# ==================================================
# 5. DEFINIR MODELOS Y MEJORES HIPERPARÁMETROS
# ==================================================

modelos = {

    "Regresion_Logistica": Pipeline([
        ("escalador", StandardScaler()),
        ("modelo", LogisticRegression(
            C=0.01,
            max_iter=2000,
            random_state=RANDOM_STATE
        ))
    ]),

    "Random_Forest": RandomForestClassifier(
        n_estimators=200,
        min_samples_split=10,
        min_samples_leaf=20,
        max_features=0.5,
        max_depth=15,
        random_state=RANDOM_STATE,
        n_jobs=2
    ),

    "HistGradientBoosting": HistGradientBoostingClassifier(
        min_samples_leaf=30,
        max_leaf_nodes=63,
        max_iter=150,
        learning_rate=0.1,
        l2_regularization=0.5,
        random_state=RANDOM_STATE
    )
}


# ==================================================
# 6. GENERAR PROBABILIDADES OUT-OF-FOLD
# ==================================================

print("\nGenerando probabilidades OOF...")

resultados_oof = []

for nombre, modelo_base in modelos.items():

    print(f"\nProcesando: {nombre}")

    probabilidades = np.full(
        len(X),
        np.nan,
        dtype=float
    )

    fold_asignado = np.full(
        len(X),
        -1,
        dtype=int
    )

    for numero_fold, (idx_train, idx_val) in enumerate(
        particiones,
        start=1
    ):

        X_train = X.iloc[idx_train]
        X_val = X.iloc[idx_val]

        y_train = y.iloc[idx_train]

        # Pesos calculados únicamente con el fold de entrenamiento.
        pesos = compute_sample_weight(
            class_weight="balanced",
            y=y_train
        )

        modelo = clone(modelo_base)

        # Ajustar el modelo.
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

        # Obtener probabilidad de clase positiva.
        indice_positivo = list(modelo.classes_).index(1)

        probabilidades[idx_val] = modelo.predict_proba(
            X_val
        )[:, indice_positivo]

        fold_asignado[idx_val] = numero_fold

        print(
            f"  Fold {numero_fold}/{N_SPLITS} completado"
        )

    if np.isnan(probabilidades).any():
        raise ValueError(
            f"Hay registros sin predicción OOF en {nombre}."
        )

    if (fold_asignado == -1).any():
        raise ValueError(
            f"Hay registros sin fold asignado en {nombre}."
        )

    temporal = pd.DataFrame({
        "modelo": nombre,
        "indice": X.index,
        "fold": fold_asignado,
        "valor_real": y.values,
        "probabilidad_positiva": probabilidades
    })

    resultados_oof.append(temporal)


# ==================================================
# 7. UNIR Y GUARDAR PROBABILIDADES OOF
# ==================================================

df_oof = pd.concat(
    resultados_oof,
    ignore_index=True
)

df_oof.to_csv(
    OUTPUT_DIR / "probabilidades_oof.csv",
    index=False
)

print("\nProbabilidades OOF guardadas.")


# ==================================================
# 8. FUNCIÓN PARA CALCULAR MÉTRICAS
# ==================================================

def calcular_metricas(
    y_real,
    probabilidades,
    umbral
):

    y_real = np.asarray(y_real)
    probabilidades = np.asarray(probabilidades)

    y_pred = (
        probabilidades >= umbral
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_real,
        y_pred,
        labels=[0, 1]
    ).ravel()

    especificidad = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0
    )

    return {
        "umbral": float(umbral),

        "accuracy": accuracy_score(
            y_real,
            y_pred
        ),

        "precision_clase_1": precision_score(
            y_real,
            y_pred,
            zero_division=0
        ),

        "recall_clase_1": recall_score(
            y_real,
            y_pred,
            zero_division=0
        ),

        "f1_clase_1": f1_score(
            y_real,
            y_pred,
            zero_division=0
        ),

        "f1_macro": f1_score(
            y_real,
            y_pred,
            average="macro",
            zero_division=0
        ),

        "balanced_accuracy": balanced_accuracy_score(
            y_real,
            y_pred
        ),

        "especificidad": especificidad,

        "roc_auc": roc_auc_score(
            y_real,
            probabilidades
        ),

        "average_precision": average_precision_score(
            y_real,
            probabilidades
        ),

        "mcc": matthews_corrcoef(
            y_real,
            y_pred
        ),

        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp)
    }


# ==================================================
# 9. EVALUAR TODOS LOS UMBRALES
# ==================================================

print("\nEvaluando umbrales...")

resultados_umbrales = []

for nombre in modelos.keys():

    datos = df_oof[
        df_oof["modelo"] == nombre
    ]

    y_real = datos["valor_real"].to_numpy()

    probabilidades = datos[
        "probabilidad_positiva"
    ].to_numpy()

    for umbral in UMBRALES:

        metricas = calcular_metricas(
            y_real,
            probabilidades,
            umbral
        )

        metricas["modelo"] = nombre

        resultados_umbrales.append(metricas)


df_umbrales = pd.DataFrame(
    resultados_umbrales
)

df_umbrales.to_csv(
    OUTPUT_DIR / "resultados_por_umbral.csv",
    index=False
)


# ==================================================
# 10. FUNCIONES DE SELECCIÓN DE UMBRAL
# ==================================================

def seleccionar_umbral(
    datos,
    estrategia,
    precision_minima=PRECISION_MINIMA
):

    datos = datos.copy()

    datos["distancia_050"] = (
        datos["umbral"] - UMBRAL_INICIAL
    ).abs()

    if estrategia == "F1_macro":

        candidatos = datos.copy()

        columna_objetivo = "f1_macro"

    elif estrategia == "F1_clase_1":

        candidatos = datos.copy()

        columna_objetivo = "f1_clase_1"

    elif estrategia == "F1_macro_precision_minima":

        candidatos = datos[
            datos["precision_clase_1"] >= precision_minima
        ].copy()

        columna_objetivo = "f1_macro"

    else:

        raise ValueError(
            f"Estrategia desconocida: {estrategia}"
        )

    # No se encontró ningún umbral que cumpla
    # la restricción de precisión.
    if candidatos.empty:

        return None

    # Criterios de desempate:
    # 1. Métrica objetivo más alta.
    # 2. Mejor balanced accuracy.
    # 3. Umbral más cercano a 0.50.

    mejor = candidatos.sort_values(
        by=[
            columna_objetivo,
            "balanced_accuracy",
            "distancia_050"
        ],
        ascending=[
            False,
            False,
            True
        ]
    ).iloc[0]

    return mejor


# ==================================================
# 11. DEFINIR ESTRATEGIAS
# ==================================================

ESTRATEGIAS = [
    "F1_macro",
    "F1_clase_1",
    "F1_macro_precision_minima"
]


# ==================================================
# 12. SELECCIÓN GLOBAL DE UMBRALES
# ==================================================

print("\nSeleccionando umbrales globales...")

resumen_global = []

umbrales_seleccionados = {}

for nombre in modelos.keys():

    datos_modelo = df_umbrales[
        df_umbrales["modelo"] == nombre
    ].copy()

    resultado_050 = datos_modelo[
        np.isclose(
            datos_modelo["umbral"],
            UMBRAL_INICIAL
        )
    ].iloc[0]

    umbrales_seleccionados[nombre] = {}

    for estrategia in ESTRATEGIAS:

        mejor = seleccionar_umbral(
            datos_modelo,
            estrategia
        )

        if mejor is None:

            resumen_global.append({
                "modelo": nombre,
                "estrategia": estrategia,
                "estado": "Sin umbral que cumpla precision minima",
                "umbral": np.nan,
                "f1_macro": np.nan,
                "f1_clase_1": np.nan,
                "precision_clase_1": np.nan,
                "recall_clase_1": np.nan,
                "balanced_accuracy": np.nan,
                "especificidad": np.nan,
                "roc_auc": np.nan,
                "average_precision": np.nan,
                "mcc": np.nan,
                "tn": np.nan,
                "fp": np.nan,
                "fn": np.nan,
                "tp": np.nan
            })

            umbrales_seleccionados[nombre][estrategia] = None

            continue

        registro = mejor.to_dict()

        registro["modelo"] = nombre
        registro["estrategia"] = estrategia
        registro["estado"] = "Seleccionado"

        resumen_global.append(registro)

        umbrales_seleccionados[nombre][estrategia] = {
            "umbral": float(mejor["umbral"]),
            "f1_macro": float(mejor["f1_macro"]),
            "f1_clase_1": float(mejor["f1_clase_1"]),
            "precision_clase_1": float(
                mejor["precision_clase_1"]
            ),
            "recall_clase_1": float(
                mejor["recall_clase_1"]
            ),
            "balanced_accuracy": float(
                mejor["balanced_accuracy"]
            )
        }

    print(f"\nModelo: {nombre}")

    print(
        "  F1 macro con umbral 0.50:",
        round(resultado_050["f1_macro"], 4)
    )


df_resumen_global = pd.DataFrame(
    resumen_global
)

df_resumen_global.to_csv(
    OUTPUT_DIR / "resumen_estrategias_globales.csv",
    index=False
)


# ==================================================
# 13. ANÁLISIS DE ESTABILIDAD POR FOLD
# ==================================================

print("\nAnalizando estabilidad por fold...")

resultados_folds = []

for nombre in modelos.keys():

    datos_modelo = df_oof[
        df_oof["modelo"] == nombre
    ]

    for numero_fold in range(1, N_SPLITS + 1):

        datos_fold = datos_modelo[
            datos_modelo["fold"] == numero_fold
        ]

        y_real = datos_fold[
            "valor_real"
        ].to_numpy()

        probabilidades = datos_fold[
            "probabilidad_positiva"
        ].to_numpy()

        tabla_fold = []

        for umbral in UMBRALES:

            metricas = calcular_metricas(
                y_real,
                probabilidades,
                umbral
            )

            tabla_fold.append(metricas)

        df_fold = pd.DataFrame(tabla_fold)

        for estrategia in ESTRATEGIAS:

            mejor = seleccionar_umbral(
                df_fold,
                estrategia
            )

            if mejor is None:

                resultados_folds.append({
                    "modelo": nombre,
                    "fold": numero_fold,
                    "estrategia": estrategia,
                    "umbral": np.nan,
                    "estado": "Sin umbral factible"
                })

            else:

                registro = mejor.to_dict()

                registro["modelo"] = nombre
                registro["fold"] = numero_fold
                registro["estrategia"] = estrategia
                registro["estado"] = "Seleccionado"

                resultados_folds.append(registro)


df_estabilidad = pd.DataFrame(
    resultados_folds
)

df_estabilidad.to_csv(
    OUTPUT_DIR / "estabilidad_por_fold.csv",
    index=False
)


# ==================================================
# 14. RESUMEN DE ESTABILIDAD DE UMBRALES
# ==================================================

resumen_estabilidad = []

for (nombre, estrategia), grupo in df_estabilidad.groupby(
    ["modelo", "estrategia"]
):

    umbrales_validos = grupo[
        "umbral"
    ].dropna()

    resumen_estabilidad.append({

        "modelo": nombre,

        "estrategia": estrategia,

        "folds_con_umbral": len(umbrales_validos),

        "umbral_mean": (
            umbrales_validos.mean()
            if len(umbrales_validos) > 0
            else np.nan
        ),

        "umbral_std": (
            umbrales_validos.std(ddof=1)
            if len(umbrales_validos) > 1
            else np.nan
        ),

        "umbral_min": (
            umbrales_validos.min()
            if len(umbrales_validos) > 0
            else np.nan
        ),

        "umbral_max": (
            umbrales_validos.max()
            if len(umbrales_validos) > 0
            else np.nan
        )
    })


df_resumen_estabilidad = pd.DataFrame(
    resumen_estabilidad
)

df_resumen_estabilidad.to_csv(
    OUTPUT_DIR / "resumen_estabilidad.csv",
    index=False
)


# ==================================================
# 15. GUARDAR UMBRALES SELECCIONADOS
# ==================================================

with open(
    OUTPUT_DIR / "umbrales_seleccionados.json",
    "w",
    encoding="utf-8"
) as archivo:

    json.dump(
        umbrales_seleccionados,
        archivo,
        indent=4,
        ensure_ascii=False
    )


# ==================================================
# 16. MOSTRAR RESULTADOS
# ==================================================

print("\n" + "=" * 90)
print("RESUMEN DE ESTRATEGIAS DE OPTIMIZACIÓN")
print("=" * 90)

columnas_globales = [
    "modelo",
    "estrategia",
    "estado",
    "umbral",
    "f1_macro",
    "f1_clase_1",
    "precision_clase_1",
    "recall_clase_1",
    "balanced_accuracy",
    "especificidad"
]

print(
    df_resumen_global[columnas_globales].round(4).to_string(
        index=False
    )
)


print("\n" + "=" * 90)
print("RESUMEN DE ESTABILIDAD POR FOLD")
print("=" * 90)

print(
    df_resumen_estabilidad.round(4).to_string(
        index=False
    )
)


# ==================================================
# 17. ARCHIVOS GENERADOS
# ==================================================

print("\n" + "=" * 90)
print("ARCHIVOS GENERADOS")
print("=" * 90)

archivos = [
    "probabilidades_oof.csv",
    "resultados_por_umbral.csv",
    "resumen_estrategias_globales.csv",
    "estabilidad_por_fold.csv",
    "resumen_estabilidad.csv",
    "umbrales_seleccionados.json"
]

for archivo in archivos:
    print(f"  - {archivo}")

print("\nDirectorio:", OUTPUT_DIR)

print("\nETAPA 6 COMPLETADA")
