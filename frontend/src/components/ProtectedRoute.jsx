import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { Alert, Spinner } from 'react-bootstrap'
import { obtenerUsuarioActual } from '../services/api'

export default function ProtectedRoute() {
  const [cargando, setCargando] = useState(true)
  const [autorizado, setAutorizado] = useState(false)
  const [error, setError] = useState('')
  const [intento, setIntento] = useState(0)
  
  // 1. Agregamos el estado para guardar los datos del usuario
  const [usuario, setUsuario] = useState(null)

  useEffect(() => {
    let activo = true

    const verificarSesion = async () => {
      const token = sessionStorage.getItem('access_token')

      if (!token) {
        if (activo) {
          setAutorizado(false)
          setCargando(false)
        }
        return
      }

      try {
        // 2. Obtenemos los datos y los guardamos en el estado
        const datosUsuario = await obtenerUsuarioActual(token)

        if (activo) {
            setUsuario(datosUsuario)
            setAutorizado(true)
            setError('')
        }
        
      } catch (error) {
        if (!activo) return

        if (error.status === 401) {
          sessionStorage.removeItem('access_token')
          setAutorizado(false)
        } else {
          setError('No fue posible verificar la sesión. Comprueba que el servidor esté funcionando.')
        }
      } finally {
        if (activo) {
          setCargando(false)
        }
      }
    }

    setCargando(true)
    verificarSesion()

    return () => {
      activo = false
    }
  }, [intento])

  if (cargando) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="text-center">
          <Spinner animation="border" variant="primary" />
          <p className="mt-3">Verificando sesión...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mt-5">
        <Alert variant="warning">
          {error}
        </Alert>
        <button
          className="btn btn-primary"
          onClick={() => setIntento((actual) => actual + 1)}
        >
          Reintentar
        </button>
      </div>
    )
  }

  if (!autorizado) {
    return <Navigate to="/login" replace />
  }

  // 3. Pasamos los datos del usuario hacia las páginas internas mediante el context
  return <Outlet context={usuario} />
}