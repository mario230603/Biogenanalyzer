import { useState, useMemo, useRef } from 'react'
import {
  buscarGenes,
  obtenerSecuenciasProteinas,
  obtenerDetalleGenomico,
  obtenerAnotacionesProteinas,
} from '../services/api'

// --------------------------------------------------
// UTILIDADES
// --------------------------------------------------

function obtenerResultado(respuesta) {
  return respuesta?.resultado || respuesta
}

function obtenerMensajeError(error, mensajePredeterminado) {
  return error?.message || mensajePredeterminado
}

function esProteinaRevisada(proteina) {
  if (typeof proteina?.es_revisada === 'boolean') {
    return proteina.es_revisada
  }

  const tipo = String(proteina?.tipo_entrada || '').toLowerCase()
  const estado = String(proteina?.estado_revision || '').toLowerCase()

  return (
    tipo.includes('swiss-prot') ||
    (estado.includes('revisada') && !estado.includes('no revisada'))
  )
}

function descargarFasta(accesion, descripcion, secuencia) {
  const contenido = `>${accesion} ${descripcion || ''}\n${secuencia || ''}\n`
  const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)

  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = `${accesion}.fasta`

  document.body.appendChild(enlace)
  enlace.click()
  document.body.removeChild(enlace)

  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function normalizarCategoriaGO(termino) {
  const codigo = String(termino?.codigo_categoria || '').toUpperCase()

  if (codigo === 'F' || codigo === 'P' || codigo === 'C') {
    return codigo
  }

  const cat = String(termino?.categoria || '').toLowerCase()

  if (
    cat.includes('función') ||
    cat.includes('funcion') ||
    cat.includes('molecular')
  ) {
    return 'F'
  }

  if (cat.includes('proceso') || cat.includes('biological')) {
    return 'P'
  }

  if (cat.includes('componente') || cat.includes('cellular')) {
    return 'C'
  }

  return 'OTRO'
}

// --------------------------------------------------
// SUBCOMPONENTES
// --------------------------------------------------

function TextoConReferencias({ texto, limite = 360 }) {
  const [expandido, setExpandido] = useState(false)

  if (!texto) {
    return <span className="text-secondary small">No disponible.</span>
  }

  const str = String(texto)

  const idsPubmed = [
    ...new Set(
      (str.match(/PubMed:(\d+)/g) || []).map((m) => m.replace('PubMed:', ''))
    ),
  ]

  // Limpia paréntesis de PubMed en el cuerpo para lectura fluida, conservando los enlaces abajo
  const textoLimpio = str
    .replace(/\s*\(PubMed:[^)]+\)/g, '')
    .replace(/\s+\./g, '.')
    .trim()

  const esLargo = textoLimpio.length > limite

  const visible =
    expandido || !esLargo
      ? textoLimpio
      : `${textoLimpio.slice(0, limite).trim()}...`

  return (
    <div>
      <p className="mb-2 text-dark" style={{ lineHeight: '1.65' }}>
        {visible}
      </p>

      <div className="d-flex align-items-center flex-wrap gap-2">
        {esLargo && (
          <button
            type="button"
            className="btn btn-link btn-sm p-0 text-decoration-none fw-semibold me-2"
            onClick={() => setExpandido(!expandido)}
          >
            {expandido ? 'Mostrar menos' : 'Leer descripción completa'}
          </button>
        )}

        {idsPubmed.length > 0 && (
          <div className="d-flex align-items-center flex-wrap gap-1">
            <span className="small text-secondary me-1">Referencias:</span>

            {(expandido ? idsPubmed : idsPubmed.slice(0, 5)).map((pmid) => (
              <a
                key={pmid}
                href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`}
                target="_blank"
                rel="noopener noreferrer"
                className="badge bg-light text-primary border text-decoration-none"
                title={`Abrir PubMed:${pmid}`}
              >
                PMID:{pmid}
              </a>
            ))}

            {!expandido && idsPubmed.length > 5 && (
              <button
                type="button"
                className="btn btn-link btn-sm p-0 small text-decoration-none"
                onClick={() => setExpandido(true)}
              >
                +{idsPubmed.length - 5} más
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function SeccionGeneOntology({ terminos = [] }) {
  const [filtro, setFiltro] = useState('')

  const agrupados = useMemo(() => {
    const q = filtro.trim().toLowerCase()

    const filtrados = q
      ? terminos.filter(
          (t) =>
            String(t.termino || '').toLowerCase().includes(q) ||
            String(t.id || '').toLowerCase().includes(q)
        )
      : terminos

    return {
      funcion: filtrados.filter((t) => normalizarCategoriaGO(t) === 'F'),
      proceso: filtrados.filter((t) => normalizarCategoriaGO(t) === 'P'),
      componente: filtrados.filter((t) => normalizarCategoriaGO(t) === 'C'),
    }
  }, [terminos, filtro])

  if (!terminos.length) {
    return (
      <p className="text-secondary small mb-0">
        No hay términos Gene Ontology registrados.
      </p>
    )
  }

  const columnas = [
    {
      titulo: 'Función molecular (F)',
      items: agrupados.funcion,
      color: 'primary',
    },
    {
      titulo: 'Proceso biológico (P)',
      items: agrupados.proceso,
      color: 'success',
    },
    {
      titulo: 'Componente celular (C)',
      items: agrupados.componente,
      color: 'info',
    },
  ]

  return (
    <div>
      <div className="mb-3" style={{ maxWidth: '340px' }}>
        <input
          type="text"
          className="form-control form-control-sm"
          placeholder="Filtrar términos GO por nombre o código..."
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
        />
      </div>

      <div className="row g-3">
        {columnas.map((col) => (
          <div key={col.titulo} className="col-12 col-lg-4">
            <div className="border rounded p-3 h-100 bg-light">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="fw-bold small">{col.titulo}</span>
                <span className={`badge bg-${col.color}`}>
                  {col.items.length}
                </span>
              </div>

              <div style={{ maxHeight: '260px', overflowY: 'auto' }}>
                {col.items.length > 0 ? (
                  <ul className="list-unstyled mb-0 small">
                    {col.items.map((go, idx) => (
                      <li
                        key={`${go.id}-${idx}`}
                        className="py-1 border-bottom"
                      >
                        <span className="font-monospace text-secondary me-2">
                          {go.id}
                        </span>
                        <span>{go.termino}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-secondary small">
                    Sin coincidencias.
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function PanelAnotacionUniProt({ proteina }) {
  const [subTab, setSubTab] = useState('dominios')

  if (!proteina) return null

  const revisada = esProteinaRevisada(proteina)

  return (
    <div>
      {/* Encabezado de la entrada seleccionada */}
      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 border-bottom pb-3 mb-3">
        <div>
          <div className="d-flex align-items-center flex-wrap gap-2">
            <h5 className="fw-bold mb-0">{proteina.accesion_uniprot}</h5>

            <span className="text-secondary font-monospace small">
              ({proteina.identificador})
            </span>

            <span className="badge bg-light text-dark border">
              {proteina.longitud} aa
            </span>
          </div>

          <div className="text-dark fw-semibold mt-1">
            {proteina.nombre_proteina || 'Nombre no disponible'}
          </div>
        </div>

        <span
          className={`badge ${
            revisada ? 'bg-success' : 'bg-warning text-dark'
          } px-3 py-2`}
        >
          {revisada ? 'Swiss-Prot · Revisada' : 'TrEMBL · No revisada'}
        </span>
      </div>

      {/* Localización subcelular */}
      {Array.isArray(proteina.localizacion_subcelular) &&
        proteina.localizacion_subcelular.length > 0 && (
          <div className="mb-4">
            <div className="small fw-semibold text-secondary mb-2">
              Localización subcelular
            </div>

            <div className="d-flex flex-wrap gap-2">
              {proteina.localizacion_subcelular.map((loc, i) => (
                <span
                  key={i}
                  className="badge bg-light text-dark border fw-normal px-2 py-1"
                >
                  <i className="fas fa-map-marker-alt text-primary me-1"></i>
                  {loc}
                </span>
              ))}
            </div>
          </div>
        )}

      {/* Sub-pestañas */}
      <ul className="nav nav-tabs mb-3">
        <li className="nav-item">
          <button
            type="button"
            className={`nav-link ${
              subTab === 'dominios' ? 'active fw-semibold' : ''
            }`}
            onClick={() => setSubTab('dominios')}
          >
            Dominios y regiones ({proteina.caracteristicas?.length || 0})
          </button>
        </li>

        <li className="nav-item">
          <button
            type="button"
            className={`nav-link ${
              subTab === 'go' ? 'active fw-semibold' : ''
            }`}
            onClick={() => setSubTab('go')}
          >
            Gene Ontology ({proteina.terminos_go?.length || 0})
          </button>
        </li>

        <li className="nav-item">
          <button
            type="button"
            className={`nav-link ${
              subTab === 'funcion' ? 'active fw-semibold' : ''
            }`}
            onClick={() => setSubTab('funcion')}
          >
            Función bioquímica
          </button>
        </li>
      </ul>

      {subTab === 'dominios' && (
        <div
          className="table-responsive"
          style={{ maxHeight: '300px', overflowY: 'auto' }}
        >
          {proteina.caracteristicas?.length > 0 ? (
            <table className="table table-sm table-hover align-middle mb-0">
              <thead className="table-light sticky-top">
                <tr>
                  <th>Tipo</th>
                  <th>Descripción / Interacción</th>
                  <th className="text-end">Posición (aa)</th>
                </tr>
              </thead>

              <tbody>
                {proteina.caracteristicas.map((c, i) => (
                  <tr key={i}>
                    <td>
                      <span className="badge bg-primary-subtle text-primary border">
                        {c.tipo || 'N/D'}
                      </span>
                    </td>

                    <td className="small">{c.nombre || 'N/D'}</td>

                    <td className="text-end font-monospace small text-nowrap">
                      {c.inicio ?? c.start ?? '?'} – {c.fin ?? c.end ?? '?'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-secondary small mb-0">
              Sin características estructurales anotadas.
            </p>
          )}
        </div>
      )}

      {subTab === 'go' && (
        <SeccionGeneOntology terminos={proteina.terminos_go || []} />
      )}

      {subTab === 'funcion' && (
        <div>
          {proteina.funciones?.length > 0 ? (
            proteina.funciones.map((fn, i) => (
              <TextoConReferencias key={i} texto={fn} limite={450} />
            ))
          ) : (
            <p className="text-secondary small mb-0">
              No hay una función bioquímica anotada para esta entrada.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// --------------------------------------------------
// COMPONENTE PRINCIPAL
// --------------------------------------------------

export default function Ncbi() {
  const [termino, setTermino] = useState('')
  const [taxid, setTaxid] = useState('9606')

  const [resultados, setResultados] = useState([])
  const [genSeleccionado, setGenSeleccionado] = useState(null)

  // Identificador para evitar que respuestas tardías sobrescriban el gen activo
  const idConsulta = useRef(0)

  // Estados independientes para carga progresiva
  const [detalleGenomico, setDetalleGenomico] = useState(null)
  const [cargandoGenoma, setCargandoGenoma] = useState(false)
  const [errorGenoma, setErrorGenoma] = useState('')

  const [secuencias, setSecuencias] = useState([])
  const [cargandoSecuencias, setCargandoSecuencias] = useState(false)
  const [errorSecuencias, setErrorSecuencias] = useState('')
  const [accesionSecuenciaActiva, setAccesionSecuenciaActiva] = useState('')

  const [anotaciones, setAnotaciones] = useState(null)
  const [cargandoUniprot, setCargandoUniprot] = useState(false)
  const [errorUniprot, setErrorUniprot] = useState('')
  const [accesionUniprotActiva, setAccesionUniprotActiva] = useState('')

  const [cargandoBusqueda, setCargandoBusqueda] = useState(false)
  const [error, setError] = useState('')
  const [avisoCopia, setAvisoCopia] = useState('')

  async function manejarBusqueda(e) {
    e.preventDefault()

    const consultaActual = ++idConsulta.current

    setError('')
    setAvisoCopia('')
    setResultados([])
    setGenSeleccionado(null)

    setDetalleGenomico(null)
    setSecuencias([])
    setAnotaciones(null)

    setCargandoGenoma(false)
    setCargandoSecuencias(false)
    setCargandoUniprot(false)

    setErrorGenoma('')
    setErrorSecuencias('')
    setErrorUniprot('')

    if (!termino.trim()) {
      setError('Escribe un GeneID, símbolo o nombre de gen.')
      return
    }

    try {
      setCargandoBusqueda(true)

      const res = await buscarGenes({
        termino: termino.trim(),
        taxid,
        max_resultados: 10,
      })

      if (consultaActual !== idConsulta.current) return

      const lista = res?.resultados || []
      setResultados(lista)

      if (!lista.length) {
        setError('No se encontraron genes con ese término.')
      }
    } catch (err) {
      if (consultaActual === idConsulta.current) {
        setError(
          obtenerMensajeError(err, 'No fue posible realizar la búsqueda.')
        )
      }
    } finally {
      if (consultaActual === idConsulta.current) {
        setCargandoBusqueda(false)
      }
    }
  }

  // Carga progresiva e independiente: cada bloque aparece apenas responde su API
  function seleccionarGen(gen) {
    const consultaActual = ++idConsulta.current

    setError('')
    setAvisoCopia('')
    setGenSeleccionado(gen)

    setDetalleGenomico(null)
    setSecuencias([])
    setAccesionSecuenciaActiva('')
    setAnotaciones(null)
    setAccesionUniprotActiva('')

    setErrorGenoma('')
    setErrorSecuencias('')
    setErrorUniprot('')

    setCargandoGenoma(true)
    setCargandoSecuencias(true)
    setCargandoUniprot(true)

    // 1. Genómica (NCBI Gene)
    obtenerDetalleGenomico(gen.gene_id)
      .then((res) => {
        if (consultaActual !== idConsulta.current) return
        setDetalleGenomico(obtenerResultado(res))
      })
      .catch((err) => {
        if (consultaActual !== idConsulta.current) return
        setErrorGenoma(
          obtenerMensajeError(
            err,
            'No fue posible recuperar la información genómica de NCBI.'
          )
        )
      })
      .finally(() => {
        if (consultaActual === idConsulta.current) {
          setCargandoGenoma(false)
        }
      })

    // 2. Secuencias (NCBI RefSeq)
    obtenerSecuenciasProteinas(gen.gene_id)
      .then((res) => {
        if (consultaActual !== idConsulta.current) return
        const lista = obtenerResultado(res)?.secuencias || []
        setSecuencias(lista)
        if (lista.length > 0) {
          setAccesionSecuenciaActiva(lista[0].accesion)
        }
      })
      .catch((err) => {
        if (consultaActual !== idConsulta.current) return
        setErrorSecuencias(
          obtenerMensajeError(
            err,
            'No fue posible recuperar las secuencias proteicas de NCBI.'
          )
        )
      })
      .finally(() => {
        if (consultaActual === idConsulta.current) {
          setCargandoSecuencias(false)
        }
      })

    // 3. Anotación funcional (UniProtKB)
    obtenerAnotacionesProteinas(gen.gene_id)
      .then((res) => {
        if (consultaActual !== idConsulta.current) return
        const datos = obtenerResultado(res)
        setAnotaciones(datos)

        const listaProteinas = datos?.anotaciones || []
        if (listaProteinas.length > 0) {
          const revisada = listaProteinas.find(esProteinaRevisada)
          setAccesionUniprotActiva(
            (revisada || listaProteinas[0]).accesion_uniprot
          )
        }
      })
      .catch((err) => {
        if (consultaActual !== idConsulta.current) return
        setErrorUniprot(
          obtenerMensajeError(
            err,
            'No fue posible recuperar las anotaciones de UniProtKB.'
          )
        )
      })
      .finally(() => {
        if (consultaActual === idConsulta.current) {
          setCargandoUniprot(false)
        }
      })
  }

  function volverAResultados() {
    idConsulta.current += 1

    setGenSeleccionado(null)
    setCargandoGenoma(false)
    setCargandoSecuencias(false)
    setCargandoUniprot(false)

    setErrorGenoma('')
    setErrorSecuencias('')
    setErrorUniprot('')
    setAvisoCopia('')
  }

  async function copiarSecuencia() {
    const secuencia = secuenciaSeleccionada?.secuencia || ''

    if (!secuencia) {
      setAvisoCopia('No hay una secuencia disponible para copiar.')
      return
    }

    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error('El navegador no permite acceder al portapapeles.')
      }

      await navigator.clipboard.writeText(secuencia)
      setAvisoCopia(
        `Secuencia ${secuenciaSeleccionada.accesion} copiada al portapapeles.`
      )
      window.setTimeout(() => setAvisoCopia(''), 3000)
    } catch (err) {
      setAvisoCopia(
        obtenerMensajeError(
          err,
          'No fue posible copiar la secuencia. Puedes seleccionarla manualmente.'
        )
      )
    }
  }

  // Mapeo de correspondencias RefSeq <-> UniProt
  const mapaRefseqAUniprot = useMemo(() => {
    const mapa = {}

    for (const c of anotaciones?.correspondencias || []) {
      if (!mapa[c.accesion_refseq]) {
        mapa[c.accesion_refseq] = []
      }

      if (!mapa[c.accesion_refseq].includes(c.accesion_uniprot)) {
        mapa[c.accesion_refseq].push(c.accesion_uniprot)
      }
    }

    return mapa
  }, [anotaciones])

  const coordenadaPrincipal = detalleGenomico?.coordenadas_genomicas?.[0]

  const secuenciaSeleccionada =
    secuencias.find((s) => s.accesion === accesionSecuenciaActiva) ||
    secuencias[0]

  const listaUniprot = anotaciones?.anotaciones || []

  const proteinaSeleccionada =
    listaUniprot.find((p) => p.accesion_uniprot === accesionUniprotActiva) ||
    listaUniprot[0]

  const totalRevisadas = listaUniprot.filter(esProteinaRevisada).length
  const totalTrembl = listaUniprot.length - totalRevisadas

  return (
    <div>
      {/* CABECERA */}
      <div className="mb-4">
        <h2 className="fw-bold mb-1" style={{ color: '#0b1b4d' }}>
          <i className="fas fa-dna me-2"></i>
          Explorador Genómico y Proteico
        </h2>

        <p className="text-secondary mb-0">
          Consulta integrada de estructura génica (NCBI), secuencias RefSeq y
          anotación funcional (UniProtKB).
        </p>
      </div>

      {/* BUSCADOR */}
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body p-4">
          <form
            onSubmit={manejarBusqueda}
            className="row g-3 align-items-end"
          >
            <div className="col-12 col-md-6">
              <label className="form-label fw-semibold small">
                GeneID, símbolo o nombre del gen
              </label>

              <input
                type="text"
                className="form-control"
                placeholder="Ej: 7157, TP53, NOS2, BRCA1..."
                value={termino}
                onChange={(e) => setTermino(e.target.value)}
              />
            </div>

            <div className="col-12 col-md-4">
              <label className="form-label fw-semibold small">
                Organismo (TaxID)
              </label>

              <select
                className="form-select"
                value={taxid}
                onChange={(e) => setTaxid(e.target.value)}
              >
                <option value="9606">Homo sapiens (9606)</option>
                <option value="10090">Mus musculus (10090)</option>
                <option value="10116">Rattus norvegicus (10116)</option>
                <option value="7227">Drosophila melanogaster (7227)</option>
                <option value="4932">Saccharomyces cerevisiae (4932)</option>
              </select>
            </div>

            <div className="col-12 col-md-2">
              <button
                type="submit"
                className="btn btn-primary w-100"
                disabled={cargandoBusqueda}
              >
                {cargandoBusqueda ? 'Buscando...' : 'Buscar'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {avisoCopia && (
        <div className="alert alert-success py-2 small">{avisoCopia}</div>
      )}

      {/* TABLA DE RESULTADOS */}
      {resultados.length > 0 && !genSeleccionado && (
        <div className="card border-0 shadow-sm mb-4">
          <div className="card-body p-4">
            <h6 className="fw-bold mb-3">
              Resultados encontrados ({resultados.length})
            </h6>

            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>GeneID</th>
                    <th>Símbolo</th>
                    <th>Descripción</th>
                    <th>Organismo</th>
                    <th>Cromosoma</th>
                    <th></th>
                  </tr>
                </thead>

                <tbody>
                  {resultados.map((gen) => (
                    <tr key={gen.gene_id}>
                      <td className="font-monospace">{gen.gene_id}</td>
                      <td className="fw-bold">{gen.nombre}</td>
                      <td>{gen.descripcion}</td>
                      <td className="small">{gen.organismo}</td>
                      <td>{gen.cromosoma || 'N/D'}</td>
                      <td className="text-end">
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          onClick={() => seleccionarGen(gen)}
                        >
                          Analizar gen
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================
          FICHA MAESTRA PROGRESIVA DEL GEN
      ================================================== */}
      {genSeleccionado && (
        <div className="d-flex flex-column gap-4">
          {/* 1. BLOQUE GENÓMICO (NCBI GENE) */}
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 border-bottom pb-3 mb-3">
                <div>
                  <div className="d-flex align-items-center flex-wrap gap-2 mb-1">
                    <h3 className="fw-bold mb-0" style={{ color: '#0b1b4d' }}>
                      {detalleGenomico?.simbolo || genSeleccionado.nombre}
                    </h3>

                    <span className="badge bg-primary">
                      GeneID: {genSeleccionado.gene_id}
                    </span>

                    {detalleGenomico?.ubicacion_citogenetica && (
                      <span className="badge bg-light text-dark border">
                        Locus: {detalleGenomico.ubicacion_citogenetica}
                      </span>
                    )}

                    {detalleGenomico?.tipo_gen && (
                      <span className="badge bg-light text-secondary border">
                        {detalleGenomico.tipo_gen}
                      </span>
                    )}
                  </div>

                  <p className="text-secondary mb-0">
                    {detalleGenomico?.descripcion || genSeleccionado.descripcion}{' '}
                    · <em>{genSeleccionado.organismo}</em>
                  </p>
                </div>

                {resultados.length > 1 && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={volverAResultados}
                  >
                    <i className="fas fa-arrow-left me-1"></i>
                    Volver a resultados
                  </button>
                )}
              </div>

              {cargandoGenoma ? (
                <div className="d-flex align-items-center gap-2 text-secondary small py-2">
                  <div className="spinner-border spinner-border-sm text-primary"></div>
                  <span>
                    Cargando coordenadas y metadatos genómicos de NCBI...
                  </span>
                </div>
              ) : errorGenoma ? (
                <div className="alert alert-warning small mb-0">
                  <strong>Error en NCBI Gene:</strong> {errorGenoma}
                </div>
              ) : (
                <>
                  <div className="row g-3 mb-4">
                    <div className="col-6 col-lg-3">
                      <div className="border rounded p-3 bg-light h-100">
                        <div className="small text-secondary">
                          Ubicación genómica
                        </div>
                        <div className="fw-bold mt-1">
                          Chr{' '}
                          {coordenadaPrincipal?.cromosoma ||
                            genSeleccionado.cromosoma ||
                            'N/D'}
                        </div>
                        <div className="small text-secondary">
                          {coordenadaPrincipal
                            ? `${coordenadaPrincipal.inicio_1_based?.toLocaleString() ?? 'N/D'} – ${coordenadaPrincipal.fin_1_based?.toLocaleString() ?? 'N/D'} (${coordenadaPrincipal.orientacion || 'N/D'})`
                            : 'Coordenadas N/D'}
                        </div>
                      </div>
                    </div>

                    <div className="col-6 col-lg-3">
                      <div className="border rounded p-3 bg-light h-100">
                        <div className="small text-secondary">
                          Estructura génica
                        </div>
                        <div className="fw-bold mt-1">
                          {coordenadaPrincipal?.numero_exones ?? 'N/D'}{' '}
                          {coordenadaPrincipal?.numero_exones === 1
                            ? 'exón'
                            : 'exones'}
                        </div>
                        <div className="small text-secondary">
                          {detalleGenomico?.transcritos?.length || 0}{' '}
                          {detalleGenomico?.transcritos?.length === 1
                            ? 'transcrito RefSeq'
                            : 'transcritos RefSeq'}
                        </div>
                      </div>
                    </div>

                    <div className="col-6 col-lg-3">
                      <div className="border rounded p-3 bg-light h-100">
                        <div className="small text-secondary">
                          Secuencias RefSeq
                        </div>
                        <div className="fw-bold mt-1">
                          {cargandoSecuencias
                            ? 'Consultando...'
                            : `${secuencias.length} ${
                                secuencias.length === 1
                                  ? 'proteína'
                                  : 'proteínas'
                              }`}
                        </div>
                        <div className="small text-secondary">
                          {secuenciaSeleccionada
                            ? `Activa: ${secuenciaSeleccionada.longitud} aa`
                            : 'NCBI Protein'}
                        </div>
                      </div>
                    </div>

                    <div className="col-6 col-lg-3">
                      <div className="border rounded p-3 bg-light h-100">
                        <div className="small text-secondary">
                          Entradas UniProtKB
                        </div>
                        <div className="fw-bold mt-1">
                          {cargandoUniprot
                            ? 'Consultando...'
                            : proteinaSeleccionada?.accesion_uniprot ||
                              'Sin mapeo'}
                        </div>
                        <div className="small text-secondary">
                          {cargandoUniprot
                            ? 'Mapeando RefSeq...'
                            : `${totalRevisadas} Swiss-Prot · ${totalTrembl} TrEMBL`}
                        </div>
                      </div>
                    </div>
                  </div>

                  {detalleGenomico?.resumen_funcional && (
                    <div className="mb-3">
                      <div className="small fw-semibold text-secondary mb-1">
                        Resumen del gen (NCBI RefSeq)
                      </div>
                      <TextoConReferencias
                        texto={detalleGenomico.resumen_funcional}
                        limite={340}
                      />
                    </div>
                  )}

                  {Array.isArray(detalleGenomico?.sinonimos) &&
                    detalleGenomico.sinonimos.length > 0 && (
                      <div className="d-flex align-items-center flex-wrap gap-2 mt-3">
                        <span className="small text-secondary fw-semibold">
                          Sinónimos:
                        </span>
                        {detalleGenomico.sinonimos.map((sin, i) => (
                          <span
                            key={i}
                            className="badge bg-light text-dark border fw-normal"
                          >
                            {sin}
                          </span>
                        ))}
                      </div>
                    )}

                  <div className="d-flex flex-column gap-2 mt-4 pt-3 border-top">
                    {detalleGenomico?.transcritos?.length > 0 && (
                      <details>
                        <summary
                          className="small fw-semibold text-primary"
                          style={{ cursor: 'pointer' }}
                        >
                          Ver tabla de transcritos (
                          {detalleGenomico.transcritos.length})
                        </summary>
                        <div
                          className="table-responsive mt-2"
                          style={{ maxHeight: '240px', overflowY: 'auto' }}
                        >
                          <table className="table table-sm table-bordered mb-0">
                            <thead className="table-light">
                              <tr>
                                <th>Accesión</th>
                                <th>Variante</th>
                                <th>Tipo</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detalleGenomico.transcritos.map((t, i) => (
                                <tr key={i}>
                                  <td className="font-monospace small">
                                    {t.accesion}
                                  </td>
                                  <td className="small">{t.nombre}</td>
                                  <td className="small">{t.tipo}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    )}

                    {detalleGenomico?.referencias_genomicas?.length > 0 && (
                      <details>
                        <summary
                          className="small fw-semibold text-primary"
                          style={{ cursor: 'pointer' }}
                        >
                          Ver ensamblajes y referencias genómicas (
                          {detalleGenomico.referencias_genomicas.length})
                        </summary>
                        <div className="table-responsive mt-2">
                          <table className="table table-sm table-bordered mb-0">
                            <thead className="table-light">
                              <tr>
                                <th>Accesión</th>
                                <th>Ensamblaje</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detalleGenomico.referencias_genomicas.map(
                                (r, i) => (
                                  <tr key={i}>
                                    <td className="font-monospace small">
                                      {r.accesion}
                                    </td>
                                    <td className="small">{r.nombre}</td>
                                  </tr>
                                )
                              )}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 2. BLOQUE DE SECUENCIAS PROTEICAS (SELECTOR + RELACIÓN UNIPROT) */}
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                <div>
                  <h5 className="fw-bold mb-0">
                    <i className="fas fa-align-left me-2 text-primary"></i>
                    Secuencias proteicas (NCBI RefSeq)
                  </h5>
                  <div className="small text-secondary">
                    Selecciona una secuencia RefSeq para inspeccionar su FASTA y
                    su correspondencia con UniProtKB.
                  </div>
                </div>

                {secuencias.length > 1 && (
                  <div style={{ minWidth: '280px' }}>
                    <select
                      className="form-select form-select-sm"
                      value={accesionSecuenciaActiva}
                      onChange={(e) =>
                        setAccesionSecuenciaActiva(e.target.value)
                      }
                    >
                      {secuencias.map((s) => (
                        <option key={s.accesion} value={s.accesion}>
                          {s.accesion} ({s.longitud} aa) — {s.descripcion}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {cargandoSecuencias ? (
                <div className="d-flex align-items-center gap-2 text-secondary small py-2">
                  <div className="spinner-border spinner-border-sm text-primary"></div>
                  <span>Recuperando secuencias FASTA desde NCBI...</span>
                </div>
              ) : errorSecuencias ? (
                <div className="alert alert-warning small mb-0">
                  <strong>Error en NCBI RefSeq:</strong> {errorSecuencias}
                </div>
              ) : secuenciaSeleccionada ? (
                <>
                  <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 bg-light border rounded p-2 px-3 mb-2">
                    <div className="small">
                      <strong className="font-monospace text-primary me-2">
                        {secuenciaSeleccionada.accesion}
                      </strong>
                      <span>{secuenciaSeleccionada.descripcion}</span>
                      <span className="badge bg-secondary ms-2">
                        {secuenciaSeleccionada.longitud} aa
                      </span>

                      {mapaRefseqAUniprot[secuenciaSeleccionada.accesion]
                        ?.length > 0 && (
                        <span className="ms-2 text-secondary">
                          → UniProt:{' '}
                          {mapaRefseqAUniprot[
                            secuenciaSeleccionada.accesion
                          ].map((acc) => (
                            <button
                              key={acc}
                              type="button"
                              className="btn btn-link btn-sm p-0 ms-1 font-monospace text-decoration-none"
                              onClick={() => setAccesionUniprotActiva(acc)}
                            >
                              {acc}
                            </button>
                          ))}
                        </span>
                      )}
                    </div>

                    <div className="d-flex gap-2">
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-secondary"
                        onClick={copiarSecuencia}
                      >
                        <i className="fas fa-copy me-1"></i>
                        Copiar
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-primary"
                        onClick={() =>
                          descargarFasta(
                            secuenciaSeleccionada.accesion,
                            secuenciaSeleccionada.descripcion,
                            secuenciaSeleccionada.secuencia
                          )
                        }
                      >
                        <i className="fas fa-download me-1"></i>
                        Descargar .fasta
                      </button>
                    </div>
                  </div>

                  <pre
                    className="bg-dark text-light rounded p-3 mb-0 small font-monospace"
                    style={{
                      maxHeight: '190px',
                      overflowY: 'auto',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                    }}
                  >
                    {`>${secuenciaSeleccionada.accesion} ${secuenciaSeleccionada.descripcion}\n${secuenciaSeleccionada.secuencia}`}
                  </pre>
                </>
              ) : (
                <p className="text-secondary small mb-0">
                  No se encontraron secuencias proteicas RefSeq para este gen.
                </p>
              )}
            </div>
          </div>

          {/* 3. BLOQUE DE ANOTACIÓN FUNCIONAL (UNIPROTKB) */}
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                <div>
                  <h5 className="fw-bold mb-0">
                    <i className="fas fa-microscope me-2 text-primary"></i>
                    Anotación funcional y estructural (UniProtKB)
                  </h5>
                  <div className="small text-secondary">
                    {listaUniprot.length > 0
                      ? `${listaUniprot.length} ${
                          listaUniprot.length === 1
                            ? 'entrada asociada'
                            : 'entradas asociadas'
                        } (${totalRevisadas} Swiss-Prot · ${totalTrembl} TrEMBL)`
                      : 'Dominios, localización subcelular, Gene Ontology y función bioquímica.'}
                  </div>
                </div>

                {listaUniprot.length > 1 && (
                  <div style={{ minWidth: '280px' }}>
                    <select
                      className="form-select form-select-sm"
                      value={accesionUniprotActiva}
                      onChange={(e) => setAccesionUniprotActiva(e.target.value)}
                    >
                      {listaUniprot.map((p) => (
                        <option
                          key={p.accesion_uniprot}
                          value={p.accesion_uniprot}
                        >
                          {p.accesion_uniprot} —{' '}
                          {esProteinaRevisada(p) ? 'Swiss-Prot' : 'TrEMBL'} (
                          {p.longitud} aa)
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {cargandoUniprot ? (
                <div className="d-flex align-items-center gap-2 text-secondary small py-2">
                  <div className="spinner-border spinner-border-sm text-primary"></div>
                  <span>Consultando anotaciones en UniProtKB...</span>
                </div>
              ) : errorUniprot ? (
                <div className="alert alert-warning small mb-0">
                  <strong>Error en UniProtKB:</strong> {errorUniprot}
                </div>
              ) : proteinaSeleccionada ? (
                <PanelAnotacionUniProt proteina={proteinaSeleccionada} />
              ) : (
                <p className="text-secondary small mb-0">
                  No se encontraron anotaciones en UniProtKB para este gen.
                </p>
              )}
            </div>
          </div>

          {/* 4. ACCESO DIRECTO A ESTRUCTURAS MOLECULARES 3D */}
          {proteinaSeleccionada?.accesion_uniprot && (
            <div className="card border-0 shadow-sm">
              <div className="card-body p-4 d-flex flex-wrap justify-content-between align-items-center gap-3">
                <div>
                  <h6 className="fw-bold mb-1">
                    <i className="fas fa-cubes me-2 text-primary"></i>
                    Estructuras moleculares 3D (
                    {proteinaSeleccionada.accesion_uniprot})
                  </h6>
                  <p className="text-secondary small mb-0">
                    Explora el modelo estructural predicho o las estructuras
                    experimentales cristalográficas asociadas a esta proteína.
                  </p>
                </div>

                <div className="d-flex flex-wrap gap-2">
                  <a
                    href={`https://alphafold.ebi.ac.uk/entry/${proteinaSeleccionada.accesion_uniprot}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-sm btn-outline-primary"
                  >
                    <i className="fas fa-external-link-alt me-1"></i>
                    Ver en AlphaFold DB
                  </a>
                  <a
                    href={`https://www.rcsb.org/search?request=${encodeURIComponent(
                      JSON.stringify({
                        query: {
                          type: 'terminal',
                          service: 'text',
                          parameters: {
                            attribute:
                              'rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession',
                            operator: 'exact_match',
                            value: proteinaSeleccionada.accesion_uniprot,
                          },
                        },
                        return_type: 'entry',
                      })
                    )}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-sm btn-outline-secondary"
                  >
                    <i className="fas fa-external-link-alt me-1"></i>
                    Buscar en RCSB PDB
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* PIE DE PÁGINA DE ATRIBUCIÓN CIENTÍFICA */}
          <footer className="border-top pt-3 mt-2 text-secondary small d-flex flex-wrap justify-content-between align-items-center gap-2">
            <div>
              <strong>Fuentes de datos:</strong>{' '}
              <a
                href={`https://www.ncbi.nlm.nih.gov/gene/${genSeleccionado.gene_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-decoration-none"
              >
                NCBI Gene ({genSeleccionado.gene_id})
              </a>
              {proteinaSeleccionada?.accesion_uniprot && (
                <>
                  {' · '}
                  <a
                    href={`https://www.uniprot.org/uniprotkb/${proteinaSeleccionada.accesion_uniprot}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-decoration-none"
                  >
                    UniProtKB ({proteinaSeleccionada.accesion_uniprot})
                  </a>
                </>
              )}
              {' · '}RCSB PDB / AlphaFold DB (CC BY 4.0)
            </div>
            <span className="text-muted">
              BioGenAnalyzer · Uso académico y de investigación
            </span>
          </footer>
        </div>
      )}
    </div>
  )
}