
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Cargar las variables del archivo .env
load_dotenv()

# Configuración de conexión a MariaDB
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3308")),
    database=os.getenv("DB_NAME", "biogenanalyzer"),
)

# Crear el motor de conexión
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Clase base para los modelos
class Base(DeclarativeBase):
    pass

# Crear sesiones para trabajar con la base de datos
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Función para verificar la conexión
def verificar_conexion():
    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT 1"))
        return resultado.scalar()


# Dependencia para proporcionar sesiones a los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
