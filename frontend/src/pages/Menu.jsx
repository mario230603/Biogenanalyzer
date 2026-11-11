import { Row, Col, Card, Button, Form, InputGroup } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'

export default function Menu() {
  const navigate = useNavigate()

  const handleLogout = () => {
    navigate('/login')
  }

  return (
    <div className="vh-100 d-flex flex-column">
      
      {/* HEADER */}
      <header className="d-flex justify-content-between align-items-center p-3 text-white shadow-sm" style={{ backgroundColor: '#0b0f2f' }}>
        <div className="d-flex align-items-center">
          <h2 className="m-0 fw-bold fs-4">BioGenAnalyzer</h2>
        </div>
        
        <Form className="d-none d-md-flex" style={{ width: '300px' }}>
          <InputGroup>
            <Form.Control type="search" placeholder="Buscar..." style={{ borderRadius: '20px 0 0 20px' }} />
            <Button variant="light" style={{ borderRadius: '0 20px 20px 0' }}>
              <i className="fas fa-search"></i>
            </Button>
          </InputGroup>
        </Form>

        <div className="d-flex align-items-center gap-3">
          <span className="fw-bold">
            <i className="fas fa-user me-2"></i>Usuario de Prueba
          </span>
          <Button variant="primary" onClick={handleLogout} className="fw-bold px-3">
            Cerrar sesión
          </Button>
        </div>
      </header>

      {/* CONTENEDOR PRINCIPAL */}
      <div className="d-flex flex-grow-1 overflow-hidden">
        
        {/* SIDEBAR (Barra lateral) */}
        <aside className="text-white p-3 d-none d-md-block" style={{ width: '250px', backgroundColor: '#0b1b4d' }}>
          <ul className="list-unstyled">
            <li className="p-3 mb-2 rounded" style={{ backgroundColor: '#2563eb', cursor: 'pointer' }}>
              <i className="fas fa-bars me-2" style={{ width: '20px' }}></i> Menú Principal
            </li>
            <li className="p-3 mb-2 rounded hover-sidebar" style={{ cursor: 'pointer' }}>
              <i className="fas fa-dna me-2" style={{ width: '20px' }}></i> Análisis de secuencias
            </li>
            <li className="p-3 mb-2 rounded hover-sidebar" style={{ cursor: 'pointer' }}>
              <i className="fas fa-heart-pulse me-2" style={{ width: '20px' }}></i> Predicción riesgo
            </li>
            <li className="p-3 mb-2 rounded hover-sidebar" style={{ cursor: 'pointer' }}>
              <i className="fas fa-database me-2" style={{ width: '20px' }}></i> Consulta NCBI
            </li>
          </ul>
        </aside>

        {/* CONTENIDO PRINCIPAL */}
        <main className="flex-grow-1 p-4 overflow-auto" style={{ backgroundColor: '#f4f6f9' }}>
          
          {/* SECCIÓN BIENVENIDA */}
          <Card className="border-0 mb-4" style={{ backgroundColor: '#e5e7eb', borderRadius: '15px' }}>
            <Card.Body className="d-flex flex-column flex-lg-row align-items-center gap-4 p-4">
              <img 
                src="https://pavlov.psyciencia.com/2017/06/genetic-trait.jpg" 
                alt="Imagen ADN" 
                style={{ width: '260px', height: '180px', objectFit: 'cover', borderRadius: '15px' }} 
              />
              <div>
                <h1 className="fw-bold mb-3" style={{ color: '#0b1b4d' }}>Bienvenido a BioGenAnalyzer</h1>
                <p className="fs-5 text-secondary mb-0">
                  Herramienta bioinformática de consulta, análisis de secuencias y predicción de riesgo en salud.
                </p>
              </div>
            </Card.Body>
          </Card>

          {/* SECCIÓN FUNCIONES */}
          <h2 className="mb-4 fw-bold" style={{ color: '#0b1b4d' }}>Funciones</h2>
          <Row className="g-4">
            
            {/* Tarjeta 1 */}
            <Col md={6} lg={4}>
              <Card className="h-100 border-0 p-3 hover-card" style={{ backgroundColor: '#e5e7eb', borderRadius: '15px' }}>
                <Card.Img variant="top" src="https://concepto.de/wp-content/uploads/2019/09/genes-genetica-adn-e1569535761396.jpg" style={{ height: '150px', objectFit: 'cover', borderRadius: '10px' }} />
                <Card.Body className="d-flex flex-column text-center px-0 pb-0">
                  <Card.Title className="fw-bold" style={{ color: '#0b1b4d' }}>Análisis de secuencias</Card.Title>
                  <Card.Text className="text-muted flex-grow-1">
                    Analiza secuencias en formato FASTA para obtener composición nucleotídica, ORFs y traducción proteica.
                  </Card.Text>
                  <Button variant="primary" className="w-100 fw-bold mt-2">Ir al módulo</Button>
                </Card.Body>
              </Card>
            </Col>

            {/* Tarjeta 2 */}
            <Col md={6} lg={4}>
              <Card className="h-100 border-0 p-3 hover-card" style={{ backgroundColor: '#e5e7eb', borderRadius: '15px' }}>
                <Card.Img variant="top" src="https://estaticos-cdn.prensaiberica.es/clip/7810338e-c27f-47d2-b67f-9328b534d56e_16-9-discover-aspect-ratio_320w_0.jpg" style={{ height: '150px', objectFit: 'cover', borderRadius: '10px' }} />
                <Card.Body className="d-flex flex-column text-center px-0 pb-0">
                  <Card.Title className="fw-bold" style={{ color: '#0b1b4d' }}>Riesgo de diabetes</Card.Title>
                  <Card.Text className="text-muted flex-grow-1">
                    Evalúa el riesgo de diabetes a partir de datos de hábitos mediante un modelo de Machine Learning.
                  </Card.Text>
                  <Button variant="primary" className="w-100 fw-bold mt-2">Ir al módulo</Button>
                </Card.Body>
              </Card>
            </Col>

            {/* Tarjeta 3 */}
            <Col md={6} lg={4}>
              <Card className="h-100 border-0 p-3 hover-card" style={{ backgroundColor: '#e5e7eb', borderRadius: '15px' }}>
                <Card.Img variant="top" src="https://avatars.githubusercontent.com/u/3812119?s=280&v=4" style={{ height: '150px', objectFit: 'cover', borderRadius: '10px' }} />
                <Card.Body className="d-flex flex-column text-center px-0 pb-0">
                  <Card.Title className="fw-bold" style={{ color: '#0b1b4d' }}>Consulta NCBI</Card.Title>
                  <Card.Text className="text-muted flex-grow-1">
                    Busca información genética directamente desde el API del NCBI de manera rápida.
                  </Card.Text>
                  <Button variant="primary" className="w-100 fw-bold mt-2">Ir al módulo</Button>
                </Card.Body>
              </Card>
            </Col>

          </Row>
        </main>
      </div>
    </div>
  )
}