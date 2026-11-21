import { useRef, useState } from 'react'
import { predecirDiabetes } from '../services/api'

// ============================================================
// 1. CONFIGURACIÓN DE VARIABLES DEL MODELO
// ============================================================

const secciones = [
  {
    titulo: '1. Características demográficas',
    descripcion: 'Información general de la persona.',
    campos: [
      {
        nombre: 'Sex',
        etiqueta: 'Sexo',
        tipo: 'select',
        opciones: [
          { valor: '0', texto: 'Femenino' },
          { valor: '1', texto: 'Masculino' },
        ],
      },
      {
        nombre: 'Age',
        etiqueta: 'Grupo de edad',
        tipo: 'select',
        opciones: [
          { valor: '1', texto: '18–24 años' },
          { valor: '2', texto: '25–29 años' },
          { valor: '3', texto: '30–34 años' },
          { valor: '4', texto: '35–39 años' },
          { valor: '5', texto: '40–44 años' },
          { valor: '6', texto: '45–49 años' },
          { valor: '7', texto: '50–54 años' },
          { valor: '8', texto: '55–59 años' },
          { valor: '9', texto: '60–64 años' },
          { valor: '10', texto: '65–69 años' },
          { valor: '11', texto: '70–74 años' },
          { valor: '12', texto: '75–79 años' },
          { valor: '13', texto: '80 años o más' },
        ],
      },
      {
        nombre: 'Education',
        etiqueta: 'Nivel educativo',
        tipo: 'select',
        opciones: [
          { valor: '1', texto: 'Sin escolaridad o jardín infantil' },
          { valor: '2', texto: 'Educación básica (grados 1 a 8)' },
          { valor: '3', texto: 'Educación secundaria incompleta (grados 9 a 11)' },
          { valor: '4', texto: 'Bachillerato completo o equivalente' },
          { valor: '5', texto: 'Entre 1 y 3 años de educación universitaria' },
          { valor: '6', texto: '4 o más años de educación universitaria' },
        ],
      },
      {
        nombre: 'Income',
        etiqueta: 'Nivel de ingresos anuales del hogar',
        tipo: 'select',
        opciones: [
          { valor: '1', texto: 'Menos de 10.000 USD' },
          { valor: '2', texto: '10.000 a menos de 15.000 USD' },
          { valor: '3', texto: '15.000 a menos de 20.000 USD' },
          { valor: '4', texto: '20.000 a menos de 25.000 USD' },
          { valor: '5', texto: '25.000 a menos de 35.000 USD' },
          { valor: '6', texto: '35.000 a menos de 50.000 USD' },
          { valor: '7', texto: '50.000 a menos de 75.000 USD' },
          { valor: '8', texto: '75.000 USD o más' },
        ],
      },
    ],
  },
  {
    titulo: '2. Antecedentes y condiciones de salud',
    descripcion: 'Información relacionada con antecedentes médicos y condiciones de salud.',
    campos: [
      {
        nombre: 'HighBP',
        etiqueta: '¿Alguna vez un profesional de la salud le ha informado que tiene presión arterial alta?',
        tipo: 'boolean',
      },
      {
        nombre: 'HighChol',
        etiqueta: '¿Alguna vez un profesional de la salud le ha informado que tiene colesterol alto?',
        tipo: 'boolean',
      },
      {
        nombre: 'CholCheck',
        etiqueta: '¿Se ha realizado un control de colesterol durante los últimos 5 años?',
        tipo: 'boolean',
      },
      {
        nombre: 'Stroke',
        etiqueta: '¿Alguna vez le han informado que sufrió un accidente cerebrovascular?',
        tipo: 'boolean',
      },
      {
        nombre: 'HeartDiseaseorAttack',
        etiqueta: '¿Alguna vez le han diagnosticado enfermedad coronaria o ha sufrido un infarto?',
        tipo: 'boolean',
      },
      {
        nombre: 'AnyHealthcare',
        etiqueta: '¿Cuenta con algún tipo de cobertura o servicio de atención médica?',
        tipo: 'boolean',
      },
      {
        nombre: 'NoDocbcCost',
        etiqueta: 'Durante los últimos 12 meses, ¿necesitó consultar a un médico, pero no pudo hacerlo debido al costo?',
        tipo: 'boolean',
      },
      {
        nombre: 'DiffWalk',
        etiqueta: '¿Tiene dificultad seria para caminar o subir escaleras?',
        tipo: 'boolean',
      },
    ],
  },
  {
    titulo: '3. Hábitos y estilo de vida',
    descripcion: 'Información sobre actividad física, alimentación y consumo de tabaco y alcohol.',
    campos: [
      {
        nombre: 'BMI',
        etiqueta: 'Índice de masa corporal (IMC)',
        tipo: 'number',
        min: 12,
        max: 98,
        ayuda: 'Ingrese su IMC como número entero (entre 12 y 98) o calcúlelo abajo con su peso y estatura.',
      },
      {
        nombre: 'Smoker',
        etiqueta: '¿Ha fumado al menos 100 cigarrillos durante toda su vida?',
        tipo: 'boolean',
      },
      {
        nombre: 'PhysActivity',
        etiqueta: '¿Realizó actividad física o ejercicio durante los últimos 30 días, sin contar la actividad laboral?',
        tipo: 'boolean',
      },
      {
        nombre: 'Fruits',
        etiqueta: '¿Consume frutas al menos una vez al día?',
        tipo: 'boolean',
      },
      {
        nombre: 'Veggies',
        etiqueta: '¿Consume verduras al menos una vez al día?',
        tipo: 'boolean',
      },
      {
        nombre: 'HvyAlcoholConsump',
        etiqueta: '¿Su consumo de alcohol supera los límites definidos por el estudio?',
        tipo: 'boolean',
        ayuda: 'Hombres: más de 14 bebidas por semana. Mujeres: más de 7 bebidas por semana.',
      },
    ],
  },
  {
    titulo: '4. Percepción del estado de salud',
    descripcion: 'Valoración general y número de días con dificultades de salud.',
    campos: [
      {
        nombre: 'GenHlth',
        etiqueta: 'En general, ¿cómo considera su estado de salud?',
        tipo: 'select',
        opciones: [
          { valor: '1', texto: 'Excelente' },
          { valor: '2', texto: 'Muy bueno' },
          { valor: '3', texto: 'Bueno' },
          { valor: '4', texto: 'Regular' },
          { valor: '5', texto: 'Malo' },
        ],
      },
      {
        nombre: 'MentHlth',
        etiqueta: '¿Cuántos días durante los últimos 30 días su salud mental no fue buena?',
        tipo: 'number',
        min: 0,
        max: 30,
        ayuda: 'Incluye estrés, depresión y problemas emocionales. Ingrese 0 si ningún día.',
      },
      {
        nombre: 'PhysHlth',
        etiqueta: '¿Cuántos días durante los últimos 30 días su salud física no fue buena?',
        tipo: 'number',
        min: 0,
        max: 30,
        ayuda: 'Incluye enfermedades físicas y lesiones. Ingrese 0 si ningún día.',
      },
    ],
  },
]

// ============================================================
// 2. VARIABLES, VALORES INICIALES Y PERFIL DE EJEMPLO
// ============================================================

const nombresVariables = secciones.flatMap((seccion) =>
  seccion.campos.map((campo) => campo.nombre)
)

const valoresIniciales = Object.fromEntries(
  nombresVariables.map((nombre) => [nombre, ''])
)

const perfilEjemplo = {
  Sex: '1',
  Age: '8',
  Education: '5',
  Income: '6',
  HighBP: '1',
  HighChol: '1',
  CholCheck: '1',
  Stroke: '0',
  HeartDiseaseorAttack: '0',
  AnyHealthcare: '1',
  NoDocbcCost: '0',
  DiffWalk: '0',
  BMI: '28',
  Smoker: '0',
  PhysActivity: '1',
  Fruits: '1',
  Veggies: '1',
  HvyAlcoholConsump: '0',
  GenHlth: '3',
  MentHlth: '2',
  PhysHlth: '5',
}

// ============================================================
// 3. COMPONENTE DE CADA CAMPO
// ============================================================

function CampoFormulario({ campo, valor, onChange, children }) {
  return (
    <div className="col-md-6 mb-3">
      <label htmlFor={campo.nombre} className="form-label fw-semibold">
        {campo.etiqueta}
        <span className="text-danger"> *</span>
      </label>

      {campo.tipo === 'boolean' && (
        <select
          id={campo.nombre}
          name={campo.nombre}
          className="form-select"
          value={valor}
          onChange={(e) => onChange(campo.nombre, e.target.value)}
          required
        >
          <option value="">Seleccione una opción</option>
          <option value="0">No</option>
          <option value="1">Sí</option>
        </select>
      )}

      {campo.tipo === 'select' && (
        <select
          id={campo.nombre}
          name={campo.nombre}
          className="form-select"
          value={valor}
          onChange={(e) => onChange(campo.nombre, e.target.value)}
          required
        >
          <option value="">Seleccione una opción</option>
          {campo.opciones.map((opcion) => (
            <option key={opcion.valor} value={opcion.valor}>
              {opcion.texto}
            </option>
          ))}
        </select>
      )}

      {campo.tipo === 'number' && (
        <input
          id={campo.nombre}
          name={campo.nombre}
          type="number"
          className="form-control"
          min={campo.min}
          max={campo.max}
          step="1"
          value={valor}
          onChange={(e) => onChange(campo.nombre, e.target.value)}
          required
        />
      )}

      {campo.ayuda && (
        <small className="text-muted d-block mt-1">
          {campo.ayuda}
        </small>
      )}

      {children}
    </div>
  )
}

// ============================================================
// 4. COMPONENTE PRINCIPAL
// ============================================================

export default function Riesgo() {
  const [datos, setDatos] = useState(valoresIniciales)
  const [tipoUmbral, setTipoUmbral] = useState('principal')
  const [resultado, setResultado] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  // Calculadora auxiliar de IMC
  const [mostrarCalcImc, setMostrarCalcImc] = useState(false)
  const [pesoKg, setPesoKg] = useState('')
  const [estaturaCm, setEstaturaCm] = useState('')

  const resultadoRef = useRef(null)

  const camposCompletos = nombresVariables.filter((k) => datos[k] !== '').length

  function actualizarCampo(nombre, valor) {
    setDatos((actuales) => ({
      ...actuales,
      [nombre]: valor,
    }))
    setResultado(null)
    setError('')
  }

  function calcularImcDesdeMedidas(nuevoPeso, nuevaEstatura) {
    const p = Number(nuevoPeso)
    const hCm = Number(nuevaEstatura)

    if (p >= 25 && p <= 350 && hCm >= 100 && hCm <= 250) {
      const hMetros = hCm / 100
      const imcEntero = Math.round(p / (hMetros * hMetros))
      const imcAcotado = Math.min(98, Math.max(12, imcEntero))
      actualizarCampo('BMI', String(imcAcotado))
    }
  }

  function cargarEjemplo() {
    setDatos({ ...perfilEjemplo })
    setResultado(null)
    setError('')
  }

  function validarDatos() {
    const datosNumericos = {}

    for (const campo of nombresVariables) {
      const valor = datos[campo]

      if (valor === '' || valor === undefined || valor === null) {
        throw new Error(`Debe completar el campo: ${campo}.`)
      }

      const numero = Number(valor)

      if (!Number.isFinite(numero) || !Number.isInteger(numero)) {
        throw new Error(`El campo ${campo} debe contener un número entero válido.`)
      }

      datosNumericos[campo] = numero
    }

    const rangos = {
      Sex: [0, 1],
      Age: [1, 13],
      Education: [1, 6],
      Income: [1, 8],
      BMI: [12, 98],
      GenHlth: [1, 5],
      MentHlth: [0, 30],
      PhysHlth: [0, 30],
    }

    const variablesBinarias = [
      'HighBP',
      'HighChol',
      'CholCheck',
      'Smoker',
      'Stroke',
      'HeartDiseaseorAttack',
      'PhysActivity',
      'Fruits',
      'Veggies',
      'HvyAlcoholConsump',
      'AnyHealthcare',
      'NoDocbcCost',
      'DiffWalk',
    ]

    for (const [nombre, [min, max]] of Object.entries(rangos)) {
      const valor = datosNumericos[nombre]
      if (valor < min || valor > max) {
        throw new Error(`El campo ${nombre} debe estar entre ${min} y ${max}.`)
      }
    }

    for (const nombre of variablesBinarias) {
      const valor = datosNumericos[nombre]
      if (![0, 1].includes(valor)) {
        throw new Error(`El campo ${nombre} solo admite 0 o 1.`)
      }
    }

    return datosNumericos
  }

  async function manejarPrediccion(e) {
    e.preventDefault()

    setCargando(true)
    setError('')
    setResultado(null)

    try {
      const datosNumericos = validarDatos()

      const respuesta = await predecirDiabetes({
        ...datosNumericos,
        tipo_umbral: tipoUmbral,
      })

      if (!respuesta || !respuesta.resultado) {
        throw new Error('El servidor devolvió una respuesta inesperada.')
      }

      setResultado(respuesta.resultado)

      setTimeout(() => {
        resultadoRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    } catch (err) {
      setError(err.message || 'No fue posible realizar la predicción.')
    } finally {
      setCargando(false)
    }
  }

  function limpiarFormulario() {
    setDatos({ ...valoresIniciales })
    setPesoKg('')
    setEstaturaCm('')
    setResultado(null)
    setError('')
    setTipoUmbral('principal')
  }

  const porcentajeNegativo = resultado
    ? Math.min(100, Math.max(0, resultado.probabilidad_modelo_clase_0 * 100))
    : 0
  const porcentajePositivo = resultado
    ? Math.min(100, Math.max(0, resultado.probabilidad_modelo_clase_1 * 100))
    : 0
  const porcentajeUmbral = resultado
    ? Math.min(100, Math.max(0, resultado.umbral_utilizado * 100))
    : 71

  // Detecta si cayó en la zona intermedia (entre 65% y 71%) con el modo estricto
  const enZonaObservacion =
    resultado &&
    resultado.clase_predicha === 0 &&
    resultado.probabilidad_modelo_clase_1 >= 0.65

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <h2 className="fw-bold mb-0" style={{ color: '#0b1b4d' }}>
          <i className="fas fa-heart-pulse me-2"></i>
          Evaluación Preventiva de Diabetes
        </h2>

        <div className="d-flex align-items-center gap-2">
          <span className="badge bg-light text-dark border px-3 py-2">
            Completados: {camposCompletos} / {nombresVariables.length}
          </span>
          <button
            type="button"
            className="btn btn-sm btn-outline-primary"
            onClick={cargarEjemplo}
          >
            Cargar datos de ejemplo
          </button>
        </div>
      </div>

      <p className="text-secondary mb-4">
        Complete el cuestionario sobre salud y hábitos para estimar la similitud de su perfil con patrones poblacionales mediante un modelo de Machine Learning.
      </p>

      <div className="alert alert-info">
        <strong>Aviso importante:</strong> esta herramienta realiza una estimación orientativa basada en patrones estadísticos. <strong>No constituye un diagnóstico médico</strong> ni reemplaza exámenes de laboratorio ni la consulta con un profesional de la salud.
      </div>

      <div className="alert alert-warning">
        <strong>Nota sobre las preguntas:</strong> las categorías de edad, educación e ingresos provienen de la encuesta poblacional CDC BRFSS (Estados Unidos). Los rangos económicos están en dólares estadounidenses como referencia del estudio original y no equivalen directamente a escalas salariales en Colombia.
      </div>

      <form onSubmit={manejarPrediccion}>
        {secciones.map((seccion) => (
          <div
            className="bg-white p-4 rounded shadow-sm mb-4"
            key={seccion.titulo}
          >
            <h5 className="fw-bold mb-1" style={{ color: '#0b1b4d' }}>
              {seccion.titulo}
            </h5>

            <p className="text-muted small mb-4">
              {seccion.descripcion}
            </p>

            <div className="row">
              {seccion.campos.map((campo) => (
                <CampoFormulario
                  key={campo.nombre}
                  campo={campo}
                  valor={datos[campo.nombre]}
                  onChange={actualizarCampo}
                >
                  {campo.nombre === 'BMI' && (
                    <div className="mt-2">
                      <button
                        type="button"
                        className="btn btn-link btn-sm p-0 text-decoration-none"
                        onClick={() => setMostrarCalcImc((v) => !v)}
                      >
                        {mostrarCalcImc
                          ? 'Ocultar calculadora de IMC'
                          : '¿No conoce su IMC? Calcular con peso y estatura'}
                      </button>

                      {mostrarCalcImc && (
                        <div className="row g-2 mt-1 p-2 bg-light rounded border">
                          <div className="col-6">
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="Peso (kg)"
                              min="25"
                              max="350"
                              value={pesoKg}
                              onChange={(e) => {
                                setPesoKg(e.target.value)
                                calcularImcDesdeMedidas(e.target.value, estaturaCm)
                              }}
                            />
                          </div>
                          <div className="col-6">
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              placeholder="Estatura (cm)"
                              min="100"
                              max="250"
                              value={estaturaCm}
                              onChange={(e) => {
                                setEstaturaCm(e.target.value)
                                calcularImcDesdeMedidas(pesoKg, e.target.value)
                              }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CampoFormulario>
              ))}
            </div>
          </div>
        ))}

        {/* SELECCIÓN DEL MODO DE ANÁLISIS (EN LENGUAJE CLARO) */}
        <div className="bg-white p-4 rounded shadow-sm mb-4">
          <h5 className="fw-bold mb-2" style={{ color: '#0b1b4d' }}>
            Nivel de sensibilidad del análisis
          </h5>

          <label htmlFor="tipoUmbral" className="form-label fw-semibold">
            ¿Qué tan estricto desea que sea el criterio de alerta?
          </label>

          <select
            id="tipoUmbral"
            className="form-select"
            value={tipoUmbral}
            onChange={(e) => {
              setTipoUmbral(e.target.value)
              setResultado(null)
            }}
          >
            <option value="principal">
              Modo estándar — Más estricto y equilibrado (exige al menos 71% de coincidencia)
            </option>
            <option value="alternativo">
              Modo preventivo — Más sensible para detección temprana (alerta desde 65% de coincidencia)
            </option>
          </select>

          <small className="text-muted d-block mt-2">
            El <strong>modo estándar</strong> evita alertas innecesarias exigiendo mayor certeza. El <strong>modo preventivo</strong> es más sensible para detectar posibles señales tempranas, aunque puede generar más avisos preventivos.
          </small>
        </div>

        {error && (
          <div className="alert alert-danger" role="alert">
            <strong>Error:</strong> {error}
          </div>
        )}

        <div className="d-flex flex-wrap gap-2 mb-4">
          <button
            type="submit"
            className="btn btn-primary px-4"
            disabled={cargando}
          >
            {cargando ? (
              <>
                <span className="spinner-border spinner-border-sm me-2"></span>
                Analizando perfil...
              </>
            ) : (
              <>
                <i className="fas fa-microscope me-2"></i>
                Analizar perfil
              </>
            )}
          </button>

          <button
            type="button"
            className="btn btn-outline-secondary px-4"
            onClick={limpiarFormulario}
            disabled={cargando}
          >
            Limpiar formulario
          </button>
        </div>
      </form>

      {/* ======================================================
          RESULTADOS EN LENGUAJE CLARO + FICHA TÉCNICA DEL MODELO
      ====================================================== */}
      {resultado && (
        <div
          ref={resultadoRef}
          className="bg-white p-4 rounded shadow-sm mb-4 border"
        >
          <h4 className="fw-bold mb-3" style={{ color: '#0b1b4d' }}>
            Resultado de la evaluación
          </h4>

          {/* VEREDICTO PRINCIPAL */}
          <div
            className={`alert ${
              resultado.clase_predicha === 1
                ? 'alert-warning'
                : enZonaObservacion
                ? 'alert-info'
                : 'alert-success'
            }`}
          >
            <h5 className="fw-bold mb-2">
              {resultado.clase_predicha === 1
                ? 'Perfil compatible con indicios de prediabetes o diabetes'
                : 'Perfil sin indicios suficientes de prediabetes o diabetes'}
            </h5>

            <p className="mb-0">
              {resultado.clase_predicha === 1
                ? `Según sus respuestas, el modelo calculó una afinidad del ${porcentajePositivo.toFixed(1)}% con perfiles de prediabetes o diabetes, superando el límite de alerta seleccionado (${porcentajeUmbral.toFixed(0)}%). Se recomienda consultar a un médico para una valoración clínica.`
                : `Según sus respuestas, el modelo calculó una afinidad del ${porcentajePositivo.toFixed(1)}% con perfiles de prediabetes o diabetes, por debajo del límite de alerta seleccionado (${porcentajeUmbral.toFixed(0)}%).`}
            </p>

            {enZonaObservacion && (
              <p className="mt-2 mb-0 small fw-semibold">
                Nota preventiva: su resultado ({porcentajePositivo.toFixed(1)}%) está muy cerca del límite estándar (71%). Si desea una evaluación más sensible, puede cambiar arriba al «Modo preventivo (65%)» o consultar con su médico.
              </p>
            )}
          </div>

          {/* BARRA VISUAL DE PROXIMIDAD AL LÍMITE */}
          <div className="border rounded p-3 mb-4 bg-light">
            <div className="d-flex justify-content-between small fw-semibold mb-1">
              <span>
                Índice estimado por el modelo: <strong>{porcentajePositivo.toFixed(1)}%</strong>
              </span>
              <span className="text-danger">
                Límite de alerta ({tipoUmbral === 'principal' ? 'Modo estándar' : 'Modo preventivo'}): <strong>{porcentajeUmbral.toFixed(0)}%</strong>
              </span>
            </div>

            <div className="position-relative" style={{ height: '24px' }}>
              <div className="progress h-100">
                <div
                  className={`progress-bar ${
                    resultado.clase_predicha === 1 ? 'bg-warning' : 'bg-primary'
                  }`}
                  role="progressbar"
                  style={{ width: `${porcentajePositivo}%` }}
                  aria-valuenow={porcentajePositivo}
                  aria-valuemin="0"
                  aria-valuemax="100"
                />
              </div>

              <div
                title={`Límite de alerta (${porcentajeUmbral.toFixed(0)}%)`}
                style={{
                  position: 'absolute',
                  left: `${porcentajeUmbral}%`,
                  top: '-4px',
                  bottom: '-4px',
                  width: '3px',
                  backgroundColor: '#dc3545',
                }}
              />
            </div>

            <small className="text-muted d-block mt-2">
              La línea roja marca el límite necesario para activar una alerta preventiva. Si la barra azul no cruza esa línea, el resultado se mantiene negativo.
            </small>
          </div>

          {/* TARJETAS EN LENGUAJE HUMANO (SIN "CLASE 0" NI "CLASE 1") */}
          <div className="row text-center mb-3">
            <div className="col-md-6 mb-3">
              <div className="border rounded p-3 h-100">
                <h6 className="text-muted mb-2">
                  Probabilidad estimada de clase sin diabetes reportada
                </h6>
                <h3 className="fw-bold text-success mb-1">
                  {porcentajeNegativo.toFixed(1)}%
                </h3>
                <small className="text-muted">
                  Estimación estadística según encuesta poblacional
                </small>
              </div>
            </div>

            <div className="col-md-6 mb-3">
              <div className="border rounded p-3 h-100">
                <h6 className="text-muted mb-2">
                   Probabilidad estimada de clase con prediabetes o diabetes reportada
                </h6>
                <h3 className={`fw-bold mb-1 ${resultado.clase_predicha === 1 ? 'text-warning' : 'text-primary'}`}>
                  {porcentajePositivo.toFixed(1)}%
                </h3>
                <small className="text-muted">
                  No equivale a un diagnóstico clínico individual
                </small>
              </div>
            </div>
          </div>

          {/* FICHA TRANSPARENTE DEL MODELO DE MACHINE LEARNING */}
          <div className="border-top pt-3 mt-2">
            <h6 className="fw-bold text-secondary mb-2">
              <i className="fas fa-robot me-2"></i>
              ¿Cómo se calculó este resultado?
            </h6>

            <div className="row small text-muted mb-2">
              <div className="col-md-4">
                <strong>Sistema:</strong> {resultado.modelo} (v{resultado.version_modelo})
              </div>
              <div className="col-md-4">
                <strong>Algoritmo:</strong> HistGradientBoostingClassifier (Scikit-learn)
              </div>
              <div className="col-md-4">
                <strong>Base de datos:</strong> 253.680 registros (CDC BRFSS)
              </div>
              <div className="col-md-4 mt-1">
                <strong>Modo aplicado:</strong> {tipoUmbral === 'principal' ? 'Estándar' : 'Preventivo'} (umbral {resultado.umbral_utilizado})
              </div>
              <div className="col-md-4 mt-1">
                <strong>Criterio de selección del umbral:</strong> {resultado.criterio_umbral}
              </div>
              <div className="col-md-4 mt-1">
                <strong>Variables analizadas:</strong> 21 indicadores de salud y hábitos
              </div>
            </div>

            <p className="text-muted small mb-0 fst-italic">
              {resultado.advertencia ||
                'Este resultado es una clasificación experimental generada por un modelo de Machine Learning entrenado con datos de encuesta poblacional. No constituye un diagnóstico médico ni sustituye pruebas clínicas como glucosa en ayunas o hemoglobina glicosilada (HbA1c).'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}