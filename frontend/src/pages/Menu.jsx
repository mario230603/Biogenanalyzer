import { Row, Col, Card, Button } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'

export default function Menu() {
  const navigate = useNavigate()

  // Información de las tarjetas del menú principal.
  const funciones = [
    {
      titulo: 'Análisis de secuencias',
      descripcion:
        'Analiza secuencias en formato FASTA para obtener composición nucleotídica, ORFs y traducción proteica.',
      imagen: '/analisis.jpg',
      ruta: '/analisis',
    },
    {
      titulo: 'Predicción de riesgo de diabetes',
      descripcion:
        'Estima el riesgo de diabetes a partir de variables personales, hábitos y un modelo de Machine Learning.',
      imagen: '/diabetes.jpg',
      ruta: '/riesgo',
    },
    {
      titulo: 'Consulta NCBI',
      descripcion:
        'Consulta información genética mediante identificadores de genes y la API de NCBI.',
      imagen: '/ncbi.webp',
      ruta: '/ncbi',
    },
  ]

  return (
    <>
      {/* TARJETA DE BIENVENIDA */}
      <Card
        className="border-0 mb-4"
        style={{
          backgroundColor: '#e5e7eb',
          borderRadius: '15px',
        }}
      >
        <Card.Body
          className="d-flex flex-column flex-lg-row
                     align-items-center gap-4 p-4"
        >
          <img
            src="https://pavlov.psyciencia.com/2017/06/genetic-trait.jpg"
            alt="Representación de información genética"
            style={{
              width: '260px',
              maxWidth: '100%',
              height: '180px',
              objectFit: 'cover',
              borderRadius: '15px',
            }}
          />

          <div>
            <h1
              className="fw-bold mb-3"
              style={{ color: '#0b1b4d' }}
            >
              Bienvenido a BioGenAnalyzer
            </h1>

            <p className="fs-5 text-secondary mb-0">
              Herramienta bioinformática de consulta, análisis
              de secuencias y predicción de riesgo en salud.
            </p>
          </div>
        </Card.Body>
      </Card>

      {/* SECCIÓN DE FUNCIONES */}
      <h2
        className="mb-4 fw-bold"
        style={{ color: '#0b1b4d' }}
      >
        Funciones
      </h2>

      <Row className="g-4">

        {funciones.map((funcion) => (
          <Col
            key={funcion.ruta}
            md={6}
            lg={4}
          >
            <Card
              className="h-100 border-0 p-3 hover-card"
              style={{
                backgroundColor: '#e5e7eb',
                borderRadius: '15px',
              }}
            >
              {/* IMAGEN DE LA FUNCIÓN */}
              <img
                src={funcion.imagen}
                alt={funcion.titulo}
                style={{
                  height: '150px',
                  width: '100%',
                  objectFit: 'cover',
                  borderRadius: '10px',
                }}
              />

              {/* INFORMACIÓN DE LA FUNCIÓN */}
              <Card.Body
                className="d-flex flex-column
                           text-center px-0 pb-0 pt-3"
              >
                <Card.Title
                  className="fw-bold"
                  style={{ color: '#0b1b4d' }}
                >
                  {funcion.titulo}
                </Card.Title>

                <Card.Text className="text-muted flex-grow-1">
                  {funcion.descripcion}
                </Card.Text>

                <Button
                  variant="primary"
                  className="w-100 fw-bold mt-2"
                  onClick={() => navigate(funcion.ruta)}
                >
                  Ir al módulo
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}

      </Row>
    </>
  )
}