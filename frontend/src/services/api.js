
const API_URL = 'http://127.0.0.1:8000'

async function solicitar(endpoint, opciones = {}) {
  const respuesta = await fetch(`${API_URL}${endpoint}`, {
    ...opciones,
    headers: {
      'Content-Type': 'application/json',
      ...opciones.headers,
    },
  })

  const datos = await respuesta.json().catch(() => ({}))

  if (!respuesta.ok) {
    const mensaje = Array.isArray(datos.detail)
      ? datos.detail.map((error) => error.msg).join(', ')
      : datos.detail || 'Ocurrió un error al comunicarse con el servidor'

    const error = new Error(mensaje)
    error.status = respuesta.status
    throw error
  }

  return datos
}

export function registrarUsuario(datosUsuario) {
  return solicitar('/auth/register', {
    method: 'POST',
    body: JSON.stringify(datosUsuario),
  })
}

export function iniciarSesion(credenciales) {
  return solicitar('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credenciales),
  })
}

// Consultar los datos del usuario que inició sesión
export function obtenerUsuarioActual(token) {
  return solicitar('/auth/me', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}
