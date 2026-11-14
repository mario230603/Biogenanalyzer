
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import verificar_conexion, engine
from app.api.auth import router as auth_router

app = FastAPI(
    title="BioGenAnalyzer API",
    description="Backend para la plataforma BioGenAnalyzer",
    version="1.0.0"
)


# Permitir comunicación con React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar las rutas de autenticación
app.include_router(auth_router)

# Endpoint principal
@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a la API de BioGenAnalyzer"
    }


# Comprobar estado del backend
@app.get("/health")
def verificar_estado():
    return {
        "estado": "activo"
    }


# Comprobar conexión con MariaDB
@app.get("/health/database")
def verificar_base_datos():
    try:
        resultado = verificar_conexion()

        return {
            "estado": "conectado",
            "base_de_datos": engine.url.database,
            "prueba": resultado
        }

    except Exception as error:
        print(f"Error de conexión con MariaDB: {error}")

        raise HTTPException(
            status_code=503,
            detail="No fue posible conectar con la base de datos"
        )
