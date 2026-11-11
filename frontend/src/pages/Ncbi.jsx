
export default function Ncbi() {
  return (
    <div>
      <h2
        className="fw-bold mb-3"
        style={{ color: '#0b1b4d' }}
      >
        <i className="fas fa-database me-2"></i>
        Consulta NCBI
      </h2>

      <p className="text-secondary">
        En este módulo podrás consultar información genética
        utilizando identificadores de genes de NCBI.
      </p>

      <div className="bg-white p-4 rounded shadow-sm">
        <h5 className="fw-bold">
          Funcionalidades del módulo
        </h5>

        <ul className="mb-0">
          <li>Ingreso de uno o varios identificadores de genes.</li>
          <li>Consulta de información mediante la API de NCBI.</li>
          <li>Visualización del nombre y descripción del gen.</li>
          <li>Consulta del cromosoma y organismo.</li>
          <li>Identificación del tipo de gen.</li>
        </ul>

        <p className="text-muted mt-3 mb-0">
          Módulo en construcción.
        </p>
      </div>
    </div>
  )
}
