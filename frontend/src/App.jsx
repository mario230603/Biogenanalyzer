
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom'

import Login from './pages/Login'
import Registro from './pages/Registro'

import Layout from './components/Layout'

import Menu from './pages/Menu'
import Analisis from './pages/Analisis'
import Riesgo from './pages/Riesgo'
import Ncbi from './pages/Ncbi'

function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* RUTAS SIN ENCABEZADO NI BARRA LATERAL */}

        <Route
          path="/"
          element={<Navigate to="/login" replace />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/registro"
          element={<Registro />}
        />

        {/* RUTAS QUE COMPARTEN EL LAYOUT */}

        <Route element={<Layout />}>

          <Route
            path="/menu"
            element={<Menu />}
          />

          <Route
            path="/analisis"
            element={<Analisis />}
          />

          <Route
            path="/riesgo"
            element={<Riesgo />}
          />

          <Route
            path="/ncbi"
            element={<Ncbi />}
          />

        </Route>

        {/* RUTA PARA DIRECCIONES NO EXISTENTES */}

        <Route
          path="*"
          element={<Navigate to="/login" replace />}
        />

      </Routes>
    </BrowserRouter>
  )
}

export default App
