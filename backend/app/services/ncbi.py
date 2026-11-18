import os
import time
import xml.etree.ElementTree as ET
from threading import Lock

import requests
from dotenv import load_dotenv


# Cargar variables del archivo .env
load_dotenv()

# Configuración de NCBI
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

NCBI_TOOL = os.getenv("NCBI_TOOL", "BioGenAnalyzer")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

# Control de velocidad: una solicitud cada 0.36 segundos como mínimo
INTERVALO_NCBI = 0.36

_bloqueo_ncbI = Lock()
_ultima_solicitud = 0.0


def _consultar_ncbi(servicio: str, parametros: dict) -> dict:
    """
    Realiza una petición a NCBI respetando el intervalo mínimo
    entre solicitudes.
    """

    global _ultima_solicitud

    url = f"{NCBI_BASE_URL}{servicio}.fcgi"

    parametros = {
        **parametros,
        "tool": NCBI_TOOL,
        "email": NCBI_EMAIL,
        "retmode": "json",
    }

    if NCBI_API_KEY:
        parametros["api_key"] = NCBI_API_KEY

    # El bloqueo evita que varias solicitudes de esta aplicación
    # salgan simultáneamente y superen el límite previsto.
    with _bloqueo_ncbI:

        tiempo_actual = time.monotonic()
        tiempo_transcurrido = tiempo_actual - _ultima_solicitud

        if tiempo_transcurrido < INTERVALO_NCBI:
            time.sleep(INTERVALO_NCBI - tiempo_transcurrido)

        _ultima_solicitud = time.monotonic()

        try:
            respuesta = requests.get(
                url,
                params=parametros,
                timeout=20
            )

            if respuesta.status_code == 429:
                raise RuntimeError(
                    "NCBI limitó temporalmente las solicitudes. "
                    "Espera un momento antes de intentarlo nuevamente."
                )

            respuesta.raise_for_status()

            return respuesta.json()

        except requests.exceptions.Timeout:
            raise RuntimeError("NCBI tardó demasiado en responder.")

        except requests.exceptions.RequestException:
            raise RuntimeError("No fue posible conectar con NCBI.")

        except ValueError:
            raise RuntimeError("NCBI devolvió una respuesta no válida.")


def buscar_genes(
    termino: str,
    taxid: str = "9606",
    max_resultados: int = 10
) -> list[dict]:
    """
    Busca genes por GeneID, símbolo o nombre.

    Homo sapiens (TaxID 9606) es el organismo predeterminado.
    """

    termino = termino.strip()

    if not termino:
        raise ValueError("Debes escribir un ID o nombre de gen.")

    if not taxid.isdigit():
        raise ValueError("El TaxID del organismo no es válido.")

    if not 1 <= max_resultados <= 20:
        raise ValueError("El máximo de resultados debe estar entre 1 y 20.")

    # Caso 1: el usuario introdujo un GeneID numérico.
    if termino.isdigit():
        gene_ids = [termino]

    # Caso 2: el usuario introdujo un símbolo o nombre.
    else:
        parametros_busqueda = {
            "db": "gene",
            "term": f'("{termino}"[All Fields]) AND {taxid}[Taxonomy ID]',
            "retmax": max_resultados,
            "sort": "relevance",
        }

        datos_busqueda = _consultar_ncbi(
            "esearch",
            parametros_busqueda
        )

        resultados_busqueda = datos_busqueda.get("esearchresult", {})

        if resultados_busqueda.get("error"):
            raise RuntimeError("NCBI no pudo completar la búsqueda.")

        gene_ids = resultados_busqueda.get("idlist", [])

    if not gene_ids:
        return []

    # Recuperar los resúmenes de todos los genes encontrados
    parametros_resumen = {
        "db": "gene",
        "id": ",".join(gene_ids),
        "version": "2.0",
    }

    datos_resumen = _consultar_ncbi(
        "esummary",
        parametros_resumen
    )

    resultados = datos_resumen.get("result", {})
    genes = []

    for gene_id in gene_ids:

        info = resultados.get(gene_id)

        if not info or info.get("error"):
            genes.append({
                "gene_id": gene_id,
                "encontrado": False,
                "mensaje": "No se encontró información para este gen."
            })
            continue

        organismo = info.get("organism") or {}

        genes.append({
            "gene_id": gene_id,
            "encontrado": True,
            "nombre": info.get("name"),
            "descripcion": info.get("description"),
            "organismo": organismo.get("scientificname"),
            "taxid": organismo.get("taxid"),
            "cromosoma": info.get("chromosome"),
            "ubicacion_citogenetica": info.get("maplocation"),
            "sinonimos": info.get("otheraliases"),
            "resumen": info.get("summary"),
            "genomicinfo": info.get("genomicinfo", []),
            "fuente": "NCBI Gene"
        })

    return genes


def _consultar_ncbi_xml(servicio: str, parametros: dict) -> ET.Element:
    """
    Realiza una consulta XML a NCBI respetando el límite
    de velocidad configurado para el servicio.
    """

    global _ultima_solicitud

    url = f"{NCBI_BASE_URL}{servicio}.fcgi"

    parametros = {
        **parametros,
        "tool": NCBI_TOOL,
        "email": NCBI_EMAIL,
        "retmode": "xml",
    }

    if NCBI_API_KEY:
        parametros["api_key"] = NCBI_API_KEY

    with _bloqueo_ncbI:

        tiempo_actual = time.monotonic()
        tiempo_transcurrido = tiempo_actual - _ultima_solicitud

        if tiempo_transcurrido < INTERVALO_NCBI:
            time.sleep(INTERVALO_NCBI - tiempo_transcurrido)

        _ultima_solicitud = time.monotonic()

        try:
            respuesta = requests.get(
                url,
                params=parametros,
                timeout=30
            )

            if respuesta.status_code == 429:
                raise RuntimeError(
                    "NCBI limitó temporalmente las solicitudes. "
                    "Espera antes de intentarlo nuevamente."
                )

            respuesta.raise_for_status()

            return ET.fromstring(respuesta.content)

        except requests.exceptions.Timeout:
            raise RuntimeError("NCBI tardó demasiado en responder.")

        except requests.exceptions.RequestException:
            raise RuntimeError("No fue posible conectar con NCBI.")

        except ET.ParseError:
            raise RuntimeError(
                "No fue posible interpretar el XML devuelto por NCBI."
            )


def _consultar_ncbi_texto(servicio: str, parametros: dict) -> str:
    """
    Realiza una petición a NCBI y devuelve texto plano.
    Respeta el intervalo mínimo entre solicitudes.
    """

    global _ultima_solicitud

    url = f"{NCBI_BASE_URL}{servicio}.fcgi"

    parametros = {
        **parametros,
        "tool": NCBI_TOOL,
        "email": NCBI_EMAIL,
        "retmode": "text",
    }

    if NCBI_API_KEY:
        parametros["api_key"] = NCBI_API_KEY

    with _bloqueo_ncbI:

        tiempo_actual = time.monotonic()
        tiempo_transcurrido = tiempo_actual - _ultima_solicitud

        if tiempo_transcurrido < INTERVALO_NCBI:
            time.sleep(INTERVALO_NCBI - tiempo_transcurrido)

        _ultima_solicitud = time.monotonic()

        try:
            respuesta = requests.get(
                url,
                params=parametros,
                timeout=30
            )

            if respuesta.status_code == 429:
                raise RuntimeError(
                    "NCBI limitó temporalmente las solicitudes."
                )

            respuesta.raise_for_status()

            return respuesta.text

        except requests.exceptions.Timeout:
            raise RuntimeError("NCBI tardó demasiado en responder.")

        except requests.exceptions.RequestException:
            raise RuntimeError("No fue posible conectar con NCBI.")


def obtener_detalle_genomico(gene_id: str) -> dict:
    """
    Recupera información ampliada de un gen mediante EFetch.

    Incluye tipo de gen, estado del registro, sinónimos,
    resumen, referencias genómicas, transcritos y proteínas.
    """

    if not gene_id.isdigit():
        raise ValueError("El GeneID debe ser numérico.")

    # Consultar el registro completo del gen en formato XML
    raiz = _consultar_ncbi_xml(
        "efetch",
        {
            "db": "gene",
            "id": gene_id,
        }
    )

    registro = raiz.find("Entrezgene")

    if registro is None:
        raise ValueError(
            f"NCBI no devolvió un registro para el GeneID {gene_id}."
        )

    # Función auxiliar para extraer texto de una etiqueta
    def obtener_texto(elemento, etiqueta):
        if elemento is None:
            return None

        nodo = elemento.find(etiqueta)

        if nodo is None or nodo.text is None:
            return None

        return nodo.text.strip()

    # Información básica del gen
    gen = registro.find("Entrezgene_gene/Gene-ref")

    simbolo = obtener_texto(gen, "Gene-ref_locus")
    descripcion = obtener_texto(gen, "Gene-ref_desc")
    ubicacion = obtener_texto(gen, "Gene-ref_maploc")

    # Sinónimos
    sinonimos = []

    if gen is not None:
        for nodo in gen.findall(
            "Gene-ref_syn/Gene-ref_syn_E"
        ):
            if nodo.text:
                sinonimos.append(nodo.text.strip())

    # Tipo de gen
    nodo_tipo = registro.find("Entrezgene_type")

    tipo_gen = None

    if nodo_tipo is not None:
        tipo_gen = nodo_tipo.get("value")

    # Estado del registro
    nodo_estado = registro.find(
        "Entrezgene_track-info/Gene-track/Gene-track_status"
    )

    estado = None

    if nodo_estado is not None:
        estado = nodo_estado.get("value")

    estados = {
        "live": "vigente",
        "secondary": "reemplazado",
        "discontinued": "discontinuado",
    }

    # Resumen funcional disponible en el registro
    resumen = obtener_texto(registro, "Entrezgene_summary")

    # Consultar coordenadas cromosómicas mediante ESummary
    datos_posicion = _consultar_ncbi(
        "esummary",
        {
            "db": "gene",
            "id": gene_id,
            "version": "2.0",
        }
    )

    informacion_gen = datos_posicion.get(
        "result", {}
    ).get(gene_id, {})

    datos_genomicos = informacion_gen.get(
        "genomicinfo", []
    )

    coordenadas_genomicas = []

    for ubicacion_genomica in datos_genomicos:

        chrstart = ubicacion_genomica.get("chrstart")
        chrstop = ubicacion_genomica.get("chrstop")

        if chrstart is None or chrstop is None:
            continue

        try:
            chrstart = int(chrstart)
            chrstop = int(chrstop)
        except (ValueError, TypeError):
            continue

        coordenadas_genomicas.append({
            "cromosoma": ubicacion_genomica.get("chrloc"),
            "accesion_referencia": ubicacion_genomica.get("chraccver"),

            # Coordenadas originales de NCBI (base cero)
            "inicio_ncbi": chrstart,
            "fin_ncbi": chrstop,

            # Coordenadas convertidas a base uno
            "inicio_1_based": min(chrstart, chrstop) + 1,
            "fin_1_based": max(chrstart, chrstop) + 1,

            # Orientación del gen
            "orientacion": (
                "directa" if chrstart <= chrstop else "reversa"
            ),

            "numero_exones": ubicacion_genomica.get("exoncount"),
        })

    # Diccionarios para organizar las referencias y evitar duplicados.
    # La accesión funciona como identificador único de cada secuencia.
    referencias_genomicas_dict = {}
    transcritos_dict = {}
    proteinas_dict = {}

    # Recorrer las anotaciones de secuencias del registro
    for comentario in registro.iter("Gene-commentary"):

        accession = obtener_texto(
            comentario,
            "Gene-commentary_accession"
        )

        if not accession:
            continue

        etiqueta = obtener_texto(
            comentario,
            "Gene-commentary_label"
        )

        tipo_comentario = comentario.find(
            "Gene-commentary_type"
        )

        tipo = (
            tipo_comentario.get("value")
            if tipo_comentario is not None
            else None
        )

        elemento = {
            "accesion": accession,
            "nombre": etiqueta,
            "tipo": tipo,
        }

        # Clasificar cada accesión
        if accession.startswith(
            ("NC_", "NG_", "NT_", "NW_", "NZ_")
        ):
            coleccion = referencias_genomicas_dict

        elif accession.startswith(
            ("NM_", "NR_", "XM_", "XR_")
        ):
            coleccion = transcritos_dict

        elif accession.startswith(
            ("NP_", "XP_", "YP_", "WP_")
        ):
            coleccion = proteinas_dict

        else:
            continue

        # Guardar solo una entrada por accesión.
        # Si la nueva entrada tiene nombre y la anterior no,
        # conservar la que tiene información más completa.
        anterior = coleccion.get(accession)

        if (
            anterior is None
            or (
                not anterior["nombre"]
                and elemento["nombre"]
            )
        ):
            coleccion[accession] = elemento

    # Convertir los diccionarios en listas para la respuesta JSON
    referencias_genomicas = list(
        referencias_genomicas_dict.values()
    )

    transcritos = list(
        transcritos_dict.values()
    )

    proteinas = list(
        proteinas_dict.values()
    )

    # Consultar proteínas RefSeq vinculadas directamente al gen
    datos_enlace = _consultar_ncbi(
        "elink",
        {
            "id": gene_id,
            "linkname": "gene_protein_refseq",
            "cmd": "neighbor",
            "retmode": "json",
            "idtype": "acc",
        }
    )

    proteinas_refseq_dict = {}

    linksets = datos_enlace.get("linksets", [])

    for linkset in linksets:
        bases_enlace = linkset.get("linksetdbs", [])

        for base_enlace in bases_enlace:

            if base_enlace.get("linkname") != "gene_protein_refseq":
                continue

            accesiones = base_enlace.get("links", [])

            for accession in accesiones:

                proteinas_refseq_dict[accession] = {
                    "accesion": accession,
                    "base_datos": "NCBI RefSeq Protein"
                }

    proteinas_refseq = list(proteinas_refseq_dict.values())

    return {
        "gene_id": gene_id,
        "encontrado": True,
        "simbolo": simbolo,
        "descripcion": descripcion,
        "tipo_gen": tipo_gen,
        "estado_registro": estados.get(estado, estado),
        "sinonimos": sinonimos,
        "resumen_funcional": resumen,
        "ubicacion_citogenetica": ubicacion,
        "coordenadas_genomicas": coordenadas_genomicas,
        "referencias_genomicas": referencias_genomicas,
        "transcritos": transcritos,
        "proteinas": proteinas,
        "proteinas_refseq_vinculadas": proteinas_refseq,
        "fuente": "NCBI Gene - EFetch, ESummary y ELink",
    }


def obtener_secuencias_proteinas(gene_id: str) -> dict:
    """
    Recupera las secuencias FASTA de las proteínas RefSeq
    vinculadas a un gen.
    """

    if not gene_id.isdigit():
        raise ValueError("El GeneID debe ser numérico.")

    # Obtener las proteínas vinculadas al gen
    detalle = obtener_detalle_genomico(gene_id)

    proteinas = detalle.get("proteinas_refseq_vinculadas", [])

    if not proteinas:
        return {
            "gene_id": gene_id,
            "simbolo": detalle.get("simbolo"),
            "total_proteinas": 0,
            "secuencias": []
        }

    # Extraer las accesiones RefSeq
    accesiones = [
        proteina["accesion"]
        for proteina in proteinas
    ]

    # Consultar todas las secuencias en una sola petición
    fasta = _consultar_ncbi_texto(
        "efetch",
        {
            "db": "protein",
            "id": ",".join(accesiones),
            "rettype": "fasta",
        }
    )

    # Interpretar el formato FASTA
    secuencias = []
    registro_actual = None

    for linea in fasta.splitlines():

        linea = linea.strip()

        if not linea:
            continue

        if linea.startswith(">"):

            if registro_actual is not None:
                registro_actual["secuencia"] = "".join(
                    registro_actual["fragmentos"]
                )
                registro_actual["longitud"] = len(
                    registro_actual["secuencia"]
                )
                del registro_actual["fragmentos"]

                secuencias.append(registro_actual)

            encabezado = linea[1:]
            partes = encabezado.split(maxsplit=1)

            registro_actual = {
                "accesion": partes[0],
                "descripcion": partes[1] if len(partes) > 1 else "",
                "fragmentos": []
            }

        elif registro_actual is not None:
            registro_actual["fragmentos"].append(linea)

    # Guardar el último registro
    if registro_actual is not None:

        registro_actual["secuencia"] = "".join(
            registro_actual["fragmentos"]
        )

        registro_actual["longitud"] = len(
            registro_actual["secuencia"]
        )

        del registro_actual["fragmentos"]

        secuencias.append(registro_actual)

    return {
        "gene_id": gene_id,
        "simbolo": detalle.get("simbolo"),
        "total_proteinas": len(secuencias),
        "secuencias": secuencias,
        "fuente": "NCBI Protein - EFetch FASTA"
    }