
import { useState } from 'react'
import { Container, Card, Form, Button, Alert, Spinner } from 'react-bootstrap'
import { Link, useNavigate } from 'react-router-dom'
import { iniciarSesion } from '../services/api'

export default function Login() {
  const navigate = useNavigate()

  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()

    setError('')
    setCargando(true)

    const formulario = new FormData(event.currentTarget)

    const credenciales = {
      correo: formulario.get('correo'),
      password: formulario.get('password'),
    }

    try {
      const respuesta = await iniciarSesion(credenciales)

      // Guardar el token durante la sesión del navegador
      sessionStorage.setItem('access_token', respuesta.access_token)

      // Ir al menú principal
      navigate('/menu')
    } catch (error) {
      setError(error.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <Container className="d-flex justify-content-center align-items-center vh-100">
      <Card className="shadow-lg border-0" style={{ width: '450px', borderRadius: '20px' }}>
        <Card.Header
          className="text-white text-center py-4 border-0"
          style={{ backgroundColor: '#07105a', borderRadius: '20px 20px 0 0' }}
        >
          <h3 className="mb-0 fw-bold">BioGenAnalyzer</h3>
        </Card.Header>

        <Card.Body className="p-5">
          <h4
            className="text-center mb-4"
            style={{ color: '#10245f', fontWeight: 'bold' }}
          >
            Inicio de Sesión
          </h4>

          {error && (
            <Alert variant="danger">
              {error}
            </Alert>
          )}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Control
                type="email"
                name="correo"
                placeholder="Correo Electrónico"
                size="lg"
                required
                disabled={cargando}
              />
            </Form.Group>

            <Form.Group className="mb-4">
              <Form.Control
                type="password"
                name="password"
                placeholder="Contraseña"
                size="lg"
                required
                disabled={cargando}
              />
            </Form.Group>

            <Button
              type="submit"
              size="lg"
              className="w-100 fw-bold border-0"
              style={{ backgroundColor: '#0b5ad5' }}
              disabled={cargando}
            >
              {cargando ? (
                <>
                  <Spinner size="sm" className="me-2" />
                  Iniciando sesión...
                </>
              ) : (
                'Iniciar Sesión'
              )}
            </Button>
          </Form>

          <p className="text-center mt-4 text-muted mb-0">
            ¿No tienes cuenta?{' '}
            <Link
              to="/registro"
              style={{ color: '#0b5ad5', fontWeight: 'bold', textDecoration: 'none' }}
            >
              Regístrate aquí
            </Link>
          </p>
        </Card.Body>
      </Card>
    </Container>
  )
}
