
import { Form, InputGroup, Button } from 'react-bootstrap'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

export default function Layout() {
  const navigate = useNavigate()

  // Cerrar sesión: por ahora regresa al login.
  // Más adelante conectaremos esta acción con la autenticación.
  const handleLogout = () => {
    navigate('/login')
  }

  // Estilos para identificar la opción activa de la barra lateral.
  const getNavLinkStyle = ({ isActive }) => ({
    display: 'block',
    padding: '14px 16px',
    marginBottom: '8px',
    borderRadius: '8px',
    color: '#ffffff',
    textDecoration: 'none',
    backgroundColor: isActive ? '#2563eb' : 'transparent',
    transition: 'background-color 0.2s ease',
  })

  return (
    <div className="min-vh-100 d-flex flex-column">

      {/* ENCABEZADO */}
      <header
        className="d-flex justify-content-between align-items-center
                   flex-wrap gap-3 p-3 text-white shadow-sm"
        style={{ backgroundColor: '#0b0f2f' }}
      >
        {/* Nombre de la plataforma */}
        <div className="d-flex align-items-center">
          <h2 className="m-0 fw-bold fs-4">
            BioGenAnalyzer
          </h2>
        </div>

        {/* Buscador visual: su funcionalidad se implementará después */}
        <Form
          className="d-none d-md-flex"
          style={{ width: '300px' }}
          onSubmit={(event) => event.preventDefault()}
        >
          <InputGroup>
            <Form.Control
              type="search"
              placeholder="Buscar..."
              aria-label="Buscar"
              style={{
                borderRadius: '20px 0 0 20px',
              }}
            />

            <Button
              type="submit"
              variant="light"
              style={{
                borderRadius: '0 20px 20px 0',
              }}
            >
              <i className="fas fa-search"></i>
            </Button>
          </InputGroup>
        </Form>

        {/* Usuario y cierre de sesión */}
        <div className="d-flex align-items-center gap-3">
          <span className="fw-bold">
            <i className="fas fa-user me-2"></i>
            Usuario de Prueba
          </span>

          <Button
            variant="primary"
            onClick={handleLogout}
            className="fw-bold px-3"
          >
            Cerrar sesión
          </Button>
        </div>
      </header>

      {/* CUERPO: BARRA LATERAL Y CONTENIDO */}
      <div className="d-flex flex-grow-1">

        {/* BARRA LATERAL */}
        <aside
          className="text-white p-3 d-none d-md-block flex-shrink-0"
          style={{
            width: '250px',
            backgroundColor: '#0b1b4d',
          }}
        >
          <h6 className="text-uppercase text-white-50 mb-3 px-3">
            Navegación
          </h6>

          <nav className="d-flex flex-column">

            <NavLink
              to="/menu"
              style={getNavLinkStyle}
            >
              <i
                className="fas fa-bars me-2"
                style={{ width: '20px' }}
              ></i>
              Menú principal
            </NavLink>

            <NavLink
              to="/analisis"
              style={getNavLinkStyle}
            >
              <i
                className="fas fa-dna me-2"
                style={{ width: '20px' }}
              ></i>
              Análisis de secuencias
            </NavLink>

            <NavLink
              to="/riesgo"
              style={getNavLinkStyle}
            >
              <i
                className="fas fa-heart-pulse me-2"
                style={{ width: '20px' }}
              ></i>
              Predicción de riesgo
            </NavLink>

            <NavLink
              to="/ncbi"
              style={getNavLinkStyle}
            >
              <i
                className="fas fa-database me-2"
                style={{ width: '20px' }}
              ></i>
              Consulta NCBI
            </NavLink>

          </nav>
        </aside>

        {/* CONTENIDO PRINCIPAL DINÁMICO */}
        <main
          className="flex-grow-1 p-3 p-md-4"
          style={{
            minWidth: 0,
            backgroundColor: '#f4f6f9',
          }}
        >
          <Outlet />
        </main>

      </div>
    </div>
  )
}
