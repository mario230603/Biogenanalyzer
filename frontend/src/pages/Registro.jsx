
import { useState } from 'react'
import { Container, Card, Form, Button, Alert, Spinner } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { registrarUsuario } from '../services/api'

export default function Registro() {
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const [exito, setExito] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()

    setError('')
    setExito(false)
    setCargando(true)

    const formularioElemento = event.currentTarget
    const formulario = new FormData(formularioElemento)

    const datosUsuario = {
      nombre: formulario.get('nombre').trim(),
      apellido: formulario.get('apellido').trim(),
      correo: formulario.get('correo').trim(),
      password: formulario.get('password'),
    }

    try {
      await registrarUsuario(datosUsuario)

      setExito(true)
      formularioElemento.reset()
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
            Registro de Usuario
          </h4>

          {error && (
            <Alert variant="danger">
              {error}
            </Alert>
          )}

          {exito && (
            <Alert variant="success">
              ¡Registro exitoso! Tu cuenta ha sido creada. Ahora puedes iniciar sesión.
            </Alert>
          )}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Control
                type="text"
                name="nombre"
                placeholder="Nombres"
                size="lg"
                required
                minLength={2}
                maxLength={100}
                disabled={cargando}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Control
                type="text"
                name="apellido"
                placeholder="Apellidos"
                size="lg"
                required
                minLength={2}
                maxLength={100}
                disabled={cargando}
              />
            </Form.Group>

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
                minLength={8}
                maxLength={128}
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
                  Registrando...
                </>
              ) : (
                'Registrar'
              )}
            </Button>
          </Form>

          <p className="text-center mt-4 text-muted mb-0">
            ¿Ya tienes cuenta?{' '}
            <Link
              to="/login"
              style={{ color: '#0b5ad5', fontWeight: 'bold', textDecoration: 'none' }}
            >
              Inicia sesión aquí
            </Link>
          </p>
        </Card.Body>
      </Card>
    </Container>
  )
}
