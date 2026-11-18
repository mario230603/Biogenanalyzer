
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


UNIPROT_BASE_URL = "https://rest.uniprot.org"
TIMEOUT_UNIPROT = 30
MAX_INTENTOS_MAPEO = 30
ESPERA_MAPEO = 3


def _obtener_texto_posicion(posicion):
    """Obtiene el valor de una posición de una característica UniProt."""
    if isinstance(posicion, dict):
        return posicion.get("value")
    return posicion


def _normalizar_tipo_entrada(entry_type):
    """
    Identifica si una entrada pertenece a Swiss-Prot o TrEMBL.
    Devuelve una clasificación explícita y consistente.
    """
    texto = str(entry_type or "").strip().lower()

    # Comprobar primero 'unreviewed' para no confundirlo
    # con la palabra 'reviewed'.
    if "unreviewed" in texto or "trembl" in texto:
        return {
            "estado_revision": "No revisada",
            "tipo_entrada": "TrEMBL",
            "es_revisada": False,
        }

    if "reviewed" in texto or "swiss-prot" in texto or "swissprot" in texto:
        return {
            "estado_revision": "Revisada",
            "tipo_entrada": "Swiss-Prot",
            "es_revisada": True,
        }

    return {
        "estado_revision": "No especificado",
        "tipo_entrada": "No especificado",
        "es_revisada": None,
    }


def mapear_refseq_uniprot(accesiones: list[str]) -> dict:
    """
    Relaciona accesiones RefSeq Protein con entradas UniProtKB.
    Conserva las relaciones individuales y elimina pares duplicados.
    """
    accesiones = list(dict.fromkeys(
        acceso.strip()
        for acceso in accesiones
        if isinstance(acceso, str) and acceso.strip()
    ))

    if not accesiones:
        raise ValueError(
            "Debes proporcionar al menos una accesión RefSeq."
        )

    if len(accesiones) > 100000:
        raise ValueError(
            "No se pueden procesar más de 100000 accesiones."
        )

    try:
        # 1. Enviar el trabajo de mapeo.
        respuesta = requests.post(
            f"{UNIPROT_BASE_URL}/idmapping/run",
            data={
                "from": "RefSeq_Protein",
                "to": "UniProtKB",
                "ids": ",".join(accesiones),
            },
            timeout=TIMEOUT_UNIPROT,
        )
        respuesta.raise_for_status()

        job_id = respuesta.json().get("jobId")

        if not job_id:
            raise RuntimeError(
                "UniProt no devolvió un identificador de trabajo."
            )

        # 2. Esperar a que finalice el mapeo.
        url_estado = (
            f"{UNIPROT_BASE_URL}/idmapping/status/{job_id}"
        )
        url_resultados = None

        for _ in range(MAX_INTENTOS_MAPEO):
            estado_respuesta = requests.get(
                url_estado,
                timeout=TIMEOUT_UNIPROT,
                allow_redirects=False,
            )

            if estado_respuesta.status_code == 303:
                url_resultados = estado_respuesta.headers.get("Location")
                break

            estado_respuesta.raise_for_status()
            estado = estado_respuesta.json()

            if estado.get("jobStatus") == "FAILED":
                raise RuntimeError(
                    "UniProt no pudo completar el mapeo."
                )

            if estado.get("jobStatus") == "FINISHED":
                respuesta_detalle = requests.get(
                    f"{UNIPROT_BASE_URL}/idmapping/details/{job_id}",
                    timeout=TIMEOUT_UNIPROT,
                )
                respuesta_detalle.raise_for_status()

                url_resultados = (
                    respuesta_detalle.json().get("redirectURL")
                )
                break

            time.sleep(ESPERA_MAPEO)

        if not url_resultados:
            raise RuntimeError(
                "UniProt tardó demasiado o no proporcionó "
                "la dirección de los resultados."
            )

        # Solicitar el conjunto completo de resultados.
        url_resultados = url_resultados.replace(
            "/results/",
            "/results/stream/",
        )

        respuesta_resultados = requests.get(
            url_resultados,
            params={"format": "json"},
            timeout=60,
        )
        respuesta_resultados.raise_for_status()

        datos = respuesta_resultados.json()
        resultados = datos.get("results", [])

        # 3. Construir las correspondencias.
        correspondencias = []
        pares_unicos = set()

        for resultado in resultados:
            origen = resultado.get("from")
            destino = resultado.get("to", {})

            if isinstance(origen, dict):
                accession_refseq = (
                    origen.get("primaryAccession")
                    or origen.get("id")
                )
            else:
                accession_refseq = origen

            if isinstance(destino, dict):
                accession_uniprot = destino.get("primaryAccession")
                identificador = destino.get("uniProtkbId")
            else:
                accession_uniprot = destino
                identificador = None

            if not accession_refseq or not accession_uniprot:
                continue

            par = (accession_refseq, accession_uniprot)

            if par in pares_unicos:
                continue

            pares_unicos.add(par)

            correspondencias.append({
                "accesion_refseq": accession_refseq,
                "accesion_uniprot": accession_uniprot,
                "identificador_uniprot": identificador,
            })

        encontradas = {
            item["accesion_refseq"]
            for item in correspondencias
        }

        sin_correspondencia = [
            acceso
            for acceso in accesiones
            if acceso not in encontradas
        ]

        return {
            "total_accesiones_consultadas": len(accesiones),
            "total_correspondencias": len(correspondencias),
            "total_accesiones_con_correspondencia": len(encontradas),
            "total_sin_correspondencia": len(sin_correspondencia),
            "correspondencias": correspondencias,
            "accesiones_sin_correspondencia": sin_correspondencia,
            "fuente": "UniProtKB - ID Mapping",
        }

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "UniProt tardó demasiado en responder."
        )

    except requests.exceptions.RequestException:
        raise RuntimeError(
            "No fue posible conectar con UniProt."
        )

    except ValueError:
        raise RuntimeError(
            "UniProt devolvió una respuesta no válida."
        )


def _obtener_textos_comentario(comentario: dict) -> list[str]:
    """Extrae los textos de un comentario de UniProt."""
    textos = []

    for texto in comentario.get("texts", []):
        valor = texto.get("value")

        if valor:
            textos.append(valor)

    return textos


def _consultar_registro_uniprot(accession: str) -> dict:
    """
    Recupera la anotación funcional de una entrada UniProtKB.
    """
    time.sleep(0.15)  # Pausa preventiva para respetar límites de tasa de UniProt

    respuesta = requests.get(
        f"{UNIPROT_BASE_URL}/uniprotkb/{accession}.json",
        timeout=TIMEOUT_UNIPROT,
    )
    respuesta.raise_for_status()

    datos = respuesta.json()

    # 1. Nombre de la proteína.
    descripcion = datos.get("proteinDescription", {})

    nombre_recomendado = (
        descripcion.get("recommendedName", {})
        .get("fullName", {})
        .get("value")
    )

    if not nombre_recomendado:
        nombres_enviados = descripcion.get("submittedNames", [])

        if nombres_enviados:
            nombre_recomendado = (
                nombres_enviados[0]
                .get("fullName", {})
                .get("value")
            )

    # 2. Nombre del gen.
    genes = datos.get("genes", [])
    nombre_gen = None

    if genes:
        nombre_gen = (
            genes[0].get("geneName", {}).get("value")
        )

    # 3. Organismo y secuencia.
    organismo = datos.get("organism", {})
    secuencia = datos.get("sequence", {})

    # 4. Clasificación de la entrada.
    entry_type_original = datos.get("entryType")
    clasificacion = _normalizar_tipo_entrada(entry_type_original)

    # 5. Funciones y localizaciones subcelulares.
    funciones = []
    localizaciones = []

    for comentario in datos.get("comments", []):
        tipo = comentario.get("commentType")

        if tipo == "FUNCTION":
            funciones.extend(
                _obtener_textos_comentario(comentario)
            )

        elif tipo == "SUBCELLULAR LOCATION":
            for ubicacion in comentario.get(
                "subcellularLocations", []
            ):
                localizacion = (
                    ubicacion.get("location", {}).get("value")
                )

                if localizacion:
                    localizaciones.append(localizacion)

    funciones = list(dict.fromkeys(funciones))
    localizaciones = list(dict.fromkeys(localizaciones))

    # 6. Términos Gene Ontology.
    terminos_go = []

    categorias_go = {
        "F": "Función molecular",
        "P": "Proceso biológico",
        "C": "Componente celular",
    }

    for referencia in datos.get("uniProtKBCrossReferences", []):
        if referencia.get("database") != "GO":
            continue

        for propiedad in referencia.get("properties", []):
            if propiedad.get("key") != "GoTerm":
                continue

            valor = propiedad.get("value", "")
            prefijo = None
            termino = valor

            if ":" in valor:
                posible_prefijo, posible_termino = valor.split(":", 1)

                if posible_prefijo in categorias_go:
                    prefijo = posible_prefijo
                    termino = posible_termino.strip()

            terminos_go.append({
                "id": referencia.get("id"),
                "termino": termino,
                "categoria": categorias_go.get(
                    prefijo,
                    "Sin categoría especificada",
                ),
                "codigo_categoria": prefijo,
            })

    # Evitar términos GO duplicados.
    go_unicos = []
    go_vistos = set()

    for termino in terminos_go:
        clave = (
            termino["id"],
            termino["termino"],
            termino["categoria"],
        )

        if clave not in go_vistos:
            go_vistos.add(clave)
            go_unicos.append(termino)

    # 7. Dominios y otras características.
    caracteristicas = []

    tipos_interes = {
        "Domain",
        "Region",
        "Motif",
        "Active site",
        "Binding site",
        "Transmembrane",
        "Signal",
    }

    for caracteristica in datos.get("features", []):
        tipo = caracteristica.get("type")

        if tipo not in tipos_interes:
            continue

        ubicacion = caracteristica.get("location", {})

        inicio = _obtener_texto_posicion(
            ubicacion.get("start")
        )
        fin = _obtener_texto_posicion(
            ubicacion.get("end")
        )

        caracteristicas.append({
            "tipo": tipo,
            "nombre": caracteristica.get("description"),
            "inicio": inicio,
            "fin": fin,
        })

    return {
        "accesion_uniprot": datos.get("primaryAccession"),
        "identificador": datos.get("uniProtkbId"),
        "nombre_proteina": nombre_recomendado,
        "nombre_gen": nombre_gen,
        "organismo": organismo.get("scientificName"),
        "taxid": organismo.get("taxonId"),

        # Clasificación normalizada para la interfaz.
        "estado_revision": clasificacion["estado_revision"],
        "tipo_entrada": clasificacion["tipo_entrada"],
        "es_revisada": clasificacion["es_revisada"],

        # Conservamos también el valor original de UniProt.
        "entry_type_original": entry_type_original,

        "funciones": funciones,
        "localizacion_subcelular": localizaciones,
        "terminos_go": go_unicos,
        "caracteristicas": caracteristicas,
        "secuencia": secuencia.get("value"),
        "longitud": secuencia.get("length"),
        "fuente": "UniProtKB",
    }


def obtener_anotaciones_proteinas(accesiones_refseq: list[str]) -> dict:
    """
    Mapea accesiones RefSeq y recupera las anotaciones
    funcionales de las proteínas encontradas en UniProtKB.
    """
    mapeo = mapear_refseq_uniprot(accesiones_refseq)
    correspondencias = mapeo["correspondencias"]

    # Consultar cada entrada UniProt una sola vez.
    accesiones_uniprot = list(dict.fromkeys(
        item["accesion_uniprot"]
        for item in correspondencias
        if item.get("accesion_uniprot")
    ))

    anotaciones = []
    errores = []

    # Recuperar anotaciones con concurrencia limitada.
    with ThreadPoolExecutor(max_workers=3) as executor:
        tareas = {
            executor.submit(
                _consultar_registro_uniprot,
                accession,
            ): accession
            for accession in accesiones_uniprot
        }

        for tarea in as_completed(tareas):
            accession = tareas[tarea]

            try:
                anotaciones.append(tarea.result())

            except requests.exceptions.RequestException:
                errores.append({
                    "accesion_uniprot": accession,
                    "mensaje": "No fue posible recuperar este registro.",
                })

            except (ValueError, KeyError, TypeError):
                errores.append({
                    "accesion_uniprot": accession,
                    "mensaje": "No fue posible interpretar este registro.",
                })

    # Ordenar las anotaciones: primero las entradas revisadas.
    anotaciones.sort(
        key=lambda item: (
            item.get("es_revisada") is not True,
            item.get("accesion_uniprot") or "",
        )
    )

    # Relacionar cada entrada UniProt con sus accesiones RefSeq.
    correspondencias_por_uniprot = {}

    for item in correspondencias:
        accession = item.get("accesion_uniprot")
        refseq = item.get("accesion_refseq")

        if accession and refseq:
            lista = correspondencias_por_uniprot.setdefault(
                accession, []
            )

            if refseq not in lista:
                lista.append(refseq)

    for anotacion in anotaciones:
        anotacion["accesiones_refseq"] = (
            correspondencias_por_uniprot.get(
                anotacion["accesion_uniprot"], []
            )
        )

    total_revisadas = sum(
        1 for item in anotaciones
        if item.get("es_revisada") is True
    )

    total_no_revisadas = sum(
        1 for item in anotaciones
        if item.get("es_revisada") is False
    )

    return {
        "resumen": {
            "total_refseq": mapeo["total_accesiones_consultadas"],
            "total_correspondencias": mapeo["total_correspondencias"],
            "total_accesiones_refseq_con_correspondencia": (
                mapeo["total_accesiones_con_correspondencia"]
            ),
            "total_proteinas_anotadas": len(anotaciones),
            "total_proteinas_revisadas": total_revisadas,
            "total_proteinas_no_revisadas": total_no_revisadas,
            "total_sin_correspondencia": (
                mapeo["total_sin_correspondencia"]
            ),
            "total_errores_consulta": len(errores),
        },
        "anotaciones": anotaciones,
        "correspondencias": correspondencias,
        "accesiones_sin_correspondencia": (
            mapeo["accesiones_sin_correspondencia"]
        ),
        "errores": errores,
        "fuente": "NCBI RefSeq y UniProtKB",
    }
