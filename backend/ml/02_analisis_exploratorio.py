
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

RUTA_BACKEND = Path(__file__).resolve().parents[1]

RUTA_DATASET = RUTA_BACKEND / "data" / "raw" / "diabetes_binary.csv"

RUTA_RESULTADOS = RUTA_BACKEND / "reports" / "eda"

RUTA_RESULTADOS.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")

# Cargar dataset
datos = pd.read_csv(RUTA_DATASET)

print("\nDataset cargado correctamente.")
print("Dimensiones:", datos.shape)


# ==========================================
# 2. INFORMACIÓN GENERAL
# ==========================================

print("\n========== INFORMACIÓN GENERAL ==========")

print(datos.info())

print("\nEstadísticas descriptivas:")

print(datos.describe().T)

datos.describe().T.to_csv(
    RUTA_RESULTADOS / "estadisticas_descriptivas.csv"
)


# ==========================================
# 3. DISTRIBUCIÓN DE LA VARIABLE OBJETIVO
# ==========================================

print("\n========== DISTRIBUCIÓN DEL OBJETIVO ==========")

conteo = datos["Diabetes_binary"].value_counts().sort_index()

porcentaje = (
    datos["Diabetes_binary"]
    .value_counts(normalize=True)
    .sort_index() * 100
)

print(pd.DataFrame({
    "Cantidad": conteo,
    "Porcentaje": porcentaje.round(2)
}))

plt.figure(figsize=(7, 5))

sns.countplot(
    data=datos,
    x="Diabetes_binary"
)

plt.title("Distribución de la variable objetivo")
plt.xlabel("Diabetes (0 = No, 1 = Sí)")
plt.ylabel("Cantidad de registros")

plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "01_distribucion_objetivo.png",
    dpi=300
)

plt.close()


# ==========================================
# 4. ANÁLISIS DE REGISTROS DUPLICADOS
# ==========================================

print("\n========== REGISTROS DUPLICADOS ==========")

duplicados = datos.duplicated().sum()

print("Registros duplicados completos:", duplicados)

print(
    "Porcentaje de duplicados:",
    round(duplicados / len(datos) * 100, 2),
    "%"
)

# Comparar duplicados incluyendo y excluyendo el objetivo
duplicados_sin_objetivo = datos.drop(
    columns=["Diabetes_binary"]
).duplicated().sum()

print(
    "Duplicados considerando solamente predictores:",
    duplicados_sin_objetivo
)

# Revisar si existen patrones idénticos con diferentes etiquetas
duplicados_conflictivos = (
    datos.groupby(list(datos.columns[:-1]))["Diabetes_binary"]
    .nunique()
    .gt(1)
    .sum()
)

print(
    "Combinaciones de predictores con etiquetas diferentes:",
    duplicados_conflictivos
)


# ==========================================
# 5. DISTRIBUCIÓN DEL IMC
# ==========================================

plt.figure(figsize=(9, 5))

sns.histplot(
    data=datos,
    x="BMI",
    bins=40,
    kde=True
)

plt.title("Distribución del índice de masa corporal (BMI)")
plt.xlabel("BMI")
plt.ylabel("Frecuencia")

plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "02_distribucion_bmi.png",
    dpi=300
)

plt.close()


# ==========================================
# 6. BMI SEGÚN LA CLASE
# ==========================================

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=datos,
    x="Diabetes_binary",
    y="BMI"
)

plt.title("Distribución del BMI según la clase")
plt.xlabel("Diabetes (0 = No, 1 = Sí)")
plt.ylabel("BMI")

plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "03_bmi_por_clase.png",
    dpi=300
)

plt.close()


# ==========================================
# 7. VARIABLES BINARIAS
# ==========================================

variables_binarias = [
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

# Calcular porcentaje de valor 1 por clase
resumen_binarias = []

for variable in variables_binarias:

    tabla = pd.crosstab(
        datos["Diabetes_binary"],
        datos[variable],
        normalize="index"
    ) * 100

    for clase in tabla.index:

        porcentaje_uno = (
            tabla.loc[clase, 1]
            if 1 in tabla.columns
            else 0
        )

        resumen_binarias.append({
            "Variable": variable,
            "Clase": clase,
            "Porcentaje_valor_1": porcentaje_uno
        })

resumen_binarias = pd.DataFrame(resumen_binarias)

print("\n========== VARIABLES BINARIAS ==========")

print(resumen_binarias)

resumen_binarias.to_csv(
    RUTA_RESULTADOS / "resumen_variables_binarias.csv",
    index=False
)

plt.figure(figsize=(13, 7))

sns.barplot(
    data=resumen_binarias,
    x="Variable",
    y="Porcentaje_valor_1",
    hue="Clase"
)

plt.title("Porcentaje de respuestas afirmativas por clase")
plt.xlabel("Variable")
plt.ylabel("Porcentaje de valor 1 (%)")

plt.xticks(rotation=65, ha="right")

plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "04_variables_binarias.png",
    dpi=300
)

plt.close()


# ==========================================
# 8. VARIABLES ORDINALES
# ==========================================

variables_ordinales = [
    "GenHlth",
    "MentHlth",
    "PhysHlth",
    "Age",
    "Education",
    "Income"
]

print("\n========== VARIABLES ORDINALES ==========")

resumen_ordinales = (
    datos.groupby("Diabetes_binary")[variables_ordinales]
    .mean()
    .T
)

print(resumen_ordinales.round(2))

resumen_ordinales.to_csv(
    RUTA_RESULTADOS / "resumen_variables_ordinales.csv"
)


# ==========================================
# 9. MATRIZ DE CORRELACIÓN
# ==========================================

correlaciones = datos.corr(numeric_only=True)

correlaciones.to_csv(
    RUTA_RESULTADOS / "matriz_correlaciones.csv"
)

plt.figure(figsize=(16, 13))

sns.heatmap(
    correlaciones,
    cmap="coolwarm",
    center=0,
    annot=True,
    fmt=".2f",
    annot_kws={"size": 7}
)

plt.title("Matriz de correlación de las variables")

plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "05_matriz_correlacion.png",
    dpi=300
)

plt.close()


# ==========================================
# 10. RESUMEN FINAL
# ==========================================

print("\n========== RESUMEN DEL EDA ==========")

print("Registros:", datos.shape[0])
print("Variables predictoras:", datos.shape[1] - 1)
print("Registros duplicados:", duplicados)
print("Valores faltantes:", datos.isnull().sum().sum())

print("\nResultados guardados en:")
print(RUTA_RESULTADOS)

print("\nAnálisis exploratorio finalizado.")
