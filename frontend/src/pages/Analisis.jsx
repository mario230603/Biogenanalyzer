
export default function Analisis() {
  return (
    <div>
      <h2
        className="fw-bold mb-3"
        style={{ color: '#0b1b4d' }}
      >
        <i className="fas fa-dna me-2"></i>
        Análisis de Secuencias
      </h2>

      <p className="text-secondary">
        En este módulo podrás cargar secuencias en formato FASTA
        y realizar análisis bioinformáticos.
      </p>

      <div className="bg-white p-4 rounded shadow-sm">
        <h5 className="fw-bold">
          Funcionalidades del módulo
        </h5>

        <ul className="mb-0">
          <li>Análisis de composición nucleotídica.</li>
          <li>Cálculo del porcentaje GC.</li>
          <li>Identificación de marcos abiertos de lectura (ORFs).</li>
          <li>Traducción de secuencias a proteínas.</li>
          <li>Búsqueda de motivos funcionales.</li>
        </ul>

        <p className="text-muted mt-3 mb-0">
          Módulo en construcción.
        </p>
      </div>
    </div>
  )
}
