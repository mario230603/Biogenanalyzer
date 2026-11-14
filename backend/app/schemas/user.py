
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Esquema para recibir los datos del registro
class UserCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=128)


# Esquema para devolver información del usuario
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
    correo: EmailStr

# Datos recibidos durante el inicio de sesión
class UserLogin(BaseModel):
    correo: EmailStr
    password: str = Field(min_length=1, max_length=128)


# Respuesta que entrega el backend al iniciar sesión
class Token(BaseModel):
    access_token: str
    token_type: str