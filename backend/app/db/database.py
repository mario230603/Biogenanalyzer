
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Cargar las variables del archivo .env
load_dotenv()


# Construir la dirección de conexión
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3308")),
    database=os.getenv("DB_NAME", "login"),
)


# Crear el motor de conexión
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)


# Función para comprobar la conexión
def verificar_conexion():
    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT 1"))
        return resultado.scalar()
