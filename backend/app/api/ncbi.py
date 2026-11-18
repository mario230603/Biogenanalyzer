from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.ncbi import (
    buscar_genes,
    obtener_detalle_genomico,
    obtener_secuencias_proteinas
)

from app.core.dependencies import get_current_user
from app.models.user import User

from app.services.uniprot import obtener_anotaciones_proteinas

router = APIRouter(
    prefix="/ncbi",
    tags=["Consulta NCBI"]
)


class ConsultaGenes(BaseModel):
    termino: str = Field(
        min_length=1,
        max_length=100,
        description="GeneID, símbolo o nombre del gen"
    )

    taxid: str = Field(
        default="9606",
        description="Identificador taxonómico del organismo"
    )

    max_resultados: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Cantidad máxima de coincidencias"
    )


@router.post("/genes")
def buscar_informacion_genetica(
    consulta: ConsultaGenes,
    usuario: User = Depends(get_current_user)
):
    """
    Busca genes por identificador, símbolo o nombre.
    Homo sapiens es el organismo predeterminado.
    Requiere autenticación JWT.
    """

    try:
        resultados = buscar_genes(
            termino=consulta.termino,
            taxid=consulta.taxid,
            max_resultados=consulta.max_resultados
        )

        return {
            "mensaje": (
                "Consulta realizada correctamente."
                if resultados
                else "No se encontraron genes para la búsqueda."
            ),
            "termino_busqueda": consulta.termino,
            "taxid": consulta.taxid,
            "total_encontrados": len(resultados),
            "resultados": resultados
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    
@router.get("/genes/{gene_id}/detalle")
def consultar_detalle_gen(
    gene_id: str,
    usuario: User = Depends(get_current_user)
):
    """
    Recupera información genómica ampliada de un gen.
    Requiere autenticación mediante JWT.
    """

    try:
        resultado = obtener_detalle_genomico(gene_id)

        return {
            "mensaje": "Detalle genómico recuperado correctamente.",
            "resultado": resultado
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

@router.get("/genes/{gene_id}/proteinas/secuencias")
def consultar_secuencias_proteinas(
    gene_id: str,
    usuario: User = Depends(get_current_user)
):
    try:
        resultado = obtener_secuencias_proteinas(gene_id)

        return {
            "mensaje": "Secuencias proteicas recuperadas correctamente.",
            "resultado": resultado
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )


@router.get("/genes/{gene_id}/proteinas/anotaciones")
def consultar_anotaciones_proteinas(
    gene_id: str,
    usuario: User = Depends(get_current_user)
):
    try:
        # Recuperar las proteínas RefSeq vinculadas al gen
        detalle = obtener_detalle_genomico(gene_id)

        proteinas = detalle.get(
            "proteinas_refseq_vinculadas", []
        )

        accesiones = [
            proteina["accesion"]
            for proteina in proteinas
        ]

        # Consultar UniProt
        resultado = obtener_anotaciones_proteinas(accesiones)

        return {
            "mensaje": "Anotaciones proteicas recuperadas correctamente.",
            "gene_id": gene_id,
            "simbolo": detalle.get("simbolo"),
            "resultado": resultado
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )