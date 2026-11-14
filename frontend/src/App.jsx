
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom'

import Login from './pages/Login'
import Registro from './pages/Registro'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

import Menu from './pages/Menu'
import Analisis from './pages/Analisis'
import Riesgo from './pages/Riesgo'
import Ncbi from './pages/Ncbi'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas públicas */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Registro />} />

        {/* Rutas protegidas */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/menu" element={<Menu />} />
            <Route path="/analisis" element={<Analisis />} />
            <Route path="/riesgo" element={<Riesgo />} />
            <Route path="/ncbi" element={<Ncbi />} />
          </Route>
        </Route>

        {/* Ruta no encontrada */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
