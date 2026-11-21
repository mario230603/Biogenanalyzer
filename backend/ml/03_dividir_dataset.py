
from pathlib import Path

import pandas as pd

from sklearn.model_selection import StratifiedGroupKFold


# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

RUTA_BACKEND = Path(__file__).resolve().parents[1]

RUTA_DATASET = (
    RUTA_BACKEND
    / "data"
    / "raw"
    / "diabetes_binary.csv"
)

RUTA_PROCESADOS = RUTA_BACKEND / "data" / "processed"

RUTA_PROCESADOS.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42


# ==========================================
# 2. CARGAR DATASET
# ==========================================

print("\nCargando dataset...")

datos = pd.read_csv(RUTA_DATASET)

print("Dimensiones:", datos.shape)


# ==========================================
# 3. SEPARAR PREDICTORES Y OBJETIVO
# ==========================================

X = datos.drop(columns=["Diabetes_binary"])

y = datos["Diabetes_binary"]

print("\nVariables predictoras:", X.shape[1])
print("Variable objetivo:", y.name)


# ==========================================
# 4. CREAR GRUPOS DE PREDICTORES IDÉNTICOS
# ==========================================

# Todas las filas con exactamente los mismos
# predictores reciben el mismo identificador.

grupos = pd.util.hash_pandas_object(
    X,
    index=False
).values

print("\n========== AGRUPACIÓN ==========")

print("Registros:", len(X))
print("Grupos únicos:", len(set(grupos)))


# ==========================================
# 5. DIVISIÓN ESTRATIFICADA POR GRUPOS
# ==========================================

divisor = StratifiedGroupKFold(
    n_splits=5,
    shuffle=True,
    random_state=RANDOM_STATE
)

indices_entrenamiento, indices_prueba = next(
    divisor.split(X, y, groups=grupos)
)

X_train = X.iloc[indices_entrenamiento].copy()
X_test = X.iloc[indices_prueba].copy()

y_train = y.iloc[indices_entrenamiento].copy()
y_test = y.iloc[indices_prueba].copy()


# ==========================================
# 6. REVISAR DIMENSIONES
# ==========================================

print("\n========== DIMENSIONES ==========")

print("X_train:", X_train.shape)
print("X_test:", X_test.shape)

print("y_train:", y_train.shape)
print("y_test:", y_test.shape)

print(
    "\nPorcentaje entrenamiento:",
    round(len(X_train) / len(datos) * 100, 2),
    "%"
)

print(
    "Porcentaje prueba:",
    round(len(X_test) / len(datos) * 100, 2),
    "%"
)


# ==========================================
# 7. COMPROBAR DISTRIBUCIÓN DE CLASES
# ==========================================

def mostrar_distribucion(nombre, objetivo):

    print(f"\n{nombre}")

    tabla = pd.DataFrame({
        "Cantidad": objetivo.value_counts().sort_index(),
        "Porcentaje": (
            objetivo.value_counts(normalize=True)
            .sort_index() * 100
        ).round(2)
    })

    print(tabla)


mostrar_distribucion(
    "Distribución original",
    y
)

mostrar_distribucion(
    "Distribución entrenamiento",
    y_train
)

mostrar_distribucion(
    "Distribución prueba",
    y_test
)


# ==========================================
# 8. VERIFICAR QUE NO HAYA GRUPOS COMPARTIDOS
# ==========================================

grupos_train = set(grupos[indices_entrenamiento])
grupos_test = set(grupos[indices_prueba])

grupos_compartidos = grupos_train.intersection(grupos_test)

print("\n========== CONTROL DE FUGA DE DATOS ==========")

print("Grupos en entrenamiento:", len(grupos_train))
print("Grupos en prueba:", len(grupos_test))
print("Grupos compartidos:", len(grupos_compartidos))

if grupos_compartidos:
    raise ValueError(
        "Error: existen grupos compartidos entre entrenamiento y prueba."
    )

print("Correcto: no existen grupos compartidos.")


# ==========================================
# 9. GUARDAR CONJUNTOS
# ==========================================

train = X_train.copy()
train["Diabetes_binary"] = y_train

test = X_test.copy()
test["Diabetes_binary"] = y_test

ruta_train = RUTA_PROCESADOS / "diabetes_train.csv"
ruta_test = RUTA_PROCESADOS / "diabetes_test.csv"

train.to_csv(ruta_train, index=False)
test.to_csv(ruta_test, index=False)

print("\n========== ARCHIVOS GUARDADOS ==========")

print(ruta_train)
print(ruta_test)


# ==========================================
# 10. RESUMEN FINAL
# ==========================================

print("\n========== RESUMEN FINAL ==========")

print("Registros originales:", len(datos))
print("Registros entrenamiento:", len(train))
print("Registros prueba:", len(test))

print("Variables predictoras:", X.shape[1])

print("\nDivisión finalizada correctamente.")
