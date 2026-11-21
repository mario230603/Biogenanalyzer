
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.models.user import User

from app.services.diabetes import predecir_diabetes


# ============================================================
# 1. CONFIGURACIÓN DEL ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/diabetes",
    tags=["Predicción de diabetes"]
)


# ============================================================
# 2. MODELO DE ENTRADA
# ============================================================

class SolicitudPrediccion(BaseModel):

    # Variables binarias
    HighBP: int = Field(ge=0, le=1)
    HighChol: int = Field(ge=0, le=1)
    CholCheck: int = Field(ge=0, le=1)
    Smoker: int = Field(ge=0, le=1)
    Stroke: int = Field(ge=0, le=1)
    HeartDiseaseorAttack: int = Field(ge=0, le=1)
    PhysActivity: int = Field(ge=0, le=1)
    Fruits: int = Field(ge=0, le=1)
    Veggies: int = Field(ge=0, le=1)
    HvyAlcoholConsump: int = Field(ge=0, le=1)
    AnyHealthcare: int = Field(ge=0, le=1)
    NoDocbcCost: int = Field(ge=0, le=1)
    DiffWalk: int = Field(ge=0, le=1)
    Sex: int = Field(ge=0, le=1)

    # Variables numéricas y ordinales
    BMI: int = Field(ge=12, le=98)
    GenHlth: int = Field(ge=1, le=5)
    MentHlth: int = Field(ge=0, le=30)
    PhysHlth: int = Field(ge=0, le=30)
    Age: int = Field(ge=1, le=13)
    Education: int = Field(ge=1, le=6)
    Income: int = Field(ge=1, le=8)

    # Selección del umbral
    tipo_umbral: Literal["principal", "alternativo"] = "principal"

    class Config:
        extra = "forbid"


# ============================================================
# 3. ENDPOINT DE PREDICCIÓN
# ============================================================

@router.post("/predict")
def realizar_prediccion(
    consulta: SolicitudPrediccion,
    usuario: User = Depends(get_current_user)
):
    """
    Realiza una clasificación experimental relacionada
    con diabetes utilizando el modelo entrenado.

    Requiere autenticación mediante JWT.

    Permite utilizar el umbral principal o alternativo.
    """

    try:

        # Separar las variables del tipo de umbral.
        datos = consulta.dict(
            exclude={"tipo_umbral"}
        )

        # Ejecutar el servicio de machine learning.
        resultado = predecir_diabetes(
            datos=datos,
            tipo_umbral=consulta.tipo_umbral
        )

        return {
            "mensaje": "Predicción realizada correctamente.",
            "resultado": resultado
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        print(f"Error al realizar predicción de diabetes: {error}")

        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al realizar la predicción."
        )
