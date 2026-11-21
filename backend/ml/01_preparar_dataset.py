
from pathlib import Path

import pandas as pd
from ucimlrepo import fetch_ucirepo


# ==========================================
# 1. CONFIGURAR RUTAS
# ==========================================

RUTA_BACKEND = Path(__file__).resolve().parents[1]
RUTA_DATOS = RUTA_BACKEND / "data" / "raw"

RUTA_DATOS.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. DESCARGAR DATASET DESDE UCI
# ==========================================

print("\nDescargando CDC Diabetes Health Indicators...")

dataset = fetch_ucirepo(id=891)

X = dataset.data.features.copy()
y = dataset.data.targets.copy()

print("\nDescarga completada.")


# ==========================================
# 3. REVISAR DIMENSIONES
# ==========================================

print("\n========== DIMENSIONES ==========")

print("Registros:", X.shape[0])
print("Variables predictoras:", X.shape[1])
print("Dimensiones del objetivo:", y.shape)


# ==========================================
# 4. REVISAR COLUMNAS
# ==========================================

print("\n========== VARIABLES PREDICTORAS ==========")

print(X.columns.tolist())

print("\n========== VARIABLE OBJETIVO ==========")

print(y.columns.tolist())


# ==========================================
# 5. VERIFICAR VARIABLE OBJETIVO
# ==========================================

if "Diabetes_binary" not in y.columns:
    raise ValueError(
        "No se encontró Diabetes_binary. "
        f"Variables objetivo disponibles: {y.columns.tolist()}"
    )

y = y["Diabetes_binary"]

print("\n========== DISTRIBUCIÓN DE CLASES ==========")

print(y.value_counts().sort_index())

print("\nPorcentajes:")

print(
    (y.value_counts(normalize=True).sort_index() * 100).round(2)
)


# ==========================================
# 6. VERIFICAR VALORES FALTANTES
# ==========================================

print("\n========== VALORES FALTANTES ==========")

faltantes = X.isnull().sum()

print(faltantes[faltantes > 0])

print("Total de valores faltantes en X:", X.isnull().sum().sum())
print("Total de valores faltantes en y:", y.isnull().sum())


# ==========================================
# 7. VERIFICAR VALORES DEL OBJETIVO
# ==========================================

print("\n========== VALORES DEL OBJETIVO ==========")

print("Clases encontradas:", sorted(y.dropna().unique().tolist()))

if not set(y.dropna().unique()).issubset({0, 1}):
    raise ValueError("El objetivo no contiene únicamente las clases 0 y 1.")


# ==========================================
# 8. CONSTRUIR DATASET DE TRABAJO
# ==========================================

datos = X.copy()
datos["Diabetes_binary"] = y.values

print("\n========== DATASET DE TRABAJO ==========")

print("Dimensiones:", datos.shape)

print("\nPrimeros registros:")

print(datos.head())


# ==========================================
# 9. GUARDAR DATASET
# ==========================================

ruta_salida = RUTA_DATOS / "diabetes_binary.csv"

datos.to_csv(ruta_salida, index=False)

print("\nDataset guardado correctamente en:")
print(ruta_salida)


# ==========================================
# 10. RESUMEN FINAL
# ==========================================

print("\n========== RESUMEN ==========")

print("Registros:", datos.shape[0])
print("Columnas:", datos.shape[1])
print("Duplicados completos:", datos.duplicated().sum())
print("Valores faltantes:", datos.isnull().sum().sum())

print("\nPreparación inicial finalizada.")
