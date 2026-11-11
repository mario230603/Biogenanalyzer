import { Container, Card, Form, Button } from 'react-bootstrap'
import { Link } from 'react-router-dom'

export default function Login() {
  const handleSubmit = (event) => {
    event.preventDefault()
  }

  return (
    <Container className="d-flex justify-content-center align-items-center vh-100">
      <Card className="shadow-lg border-0" style={{ width: '450px', borderRadius: '20px' }}>
        <Card.Header className="text-white text-center py-4 border-0" style={{ backgroundColor: '#07105a', borderRadius: '20px 20px 0 0' }}>
          <h3 className="mb-0 fw-bold">BioGenAnalyzer</h3>
        </Card.Header>
        <Card.Body className="p-5">
          <h4 className="text-center mb-4" style={{ color: '#10245f', fontWeight: 'bold' }}>Inicio de Sesión</h4>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Control type="email" name="correo" placeholder="Correo Electrónico" size="lg" required />
            </Form.Group>
            
            <Form.Group className="mb-4">
              <Form.Control type="password" name="password" placeholder="Contraseña" size="lg" required />
            </Form.Group>
            
            <Button type="submit" size="lg" className="w-100 fw-bold border-0" style={{ backgroundColor: '#0b5ad5' }}>
              Iniciar Sesión
            </Button>
          </Form>
          
          <p className="text-center mt-4 text-muted mb-0">
            ¿No tienes cuenta? <Link to="/registro" style={{ color: '#0b5ad5', fontWeight: 'bold', textDecoration: 'none' }}>Regístrate aquí</Link>
          </p>
        </Card.Body>
      </Card>
    </Container>
  )
}