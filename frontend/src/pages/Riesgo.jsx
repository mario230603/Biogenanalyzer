
export default function Riesgo() {
  return (
    <div>
      <h2
        className="fw-bold mb-3"
        style={{ color: '#0b1b4d' }}
      >
        <i className="fas fa-heart-pulse me-2"></i>
        Predicción de Riesgo de Diabetes
      </h2>

      <p className="text-secondary">
        En este módulo podrás ingresar información relacionada
        con características personales, hábitos y estilo de vida
        para estimar el riesgo de diabetes.
      </p>

      <div className="bg-white p-4 rounded shadow-sm">
        <h5 className="fw-bold">
          Funcionalidades del módulo
        </h5>

        <ul className="mb-0">
          <li>Formulario de variables personales y de salud.</li>
          <li>Procesamiento de datos.</li>
          <li>Predicción mediante Machine Learning.</li>
          <li>Visualización del nivel estimado de riesgo.</li>
        </ul>

        <p className="text-muted mt-3 mb-0">
          Módulo en construcción. La predicción será orientativa
          y no constituirá un diagnóstico médico.
        </p>
      </div>
    </div>
  )
}
