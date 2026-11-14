
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def registrar_usuario(
    datos: UserCreate,
    db: Session = Depends(get_db)
):
    # Comprobar si el correo ya está registrado
    usuario_existente = db.query(User).filter(
        User.correo == datos.correo
    ).first()

    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este correo electrónico ya está registrado"
        )

    # Crear el usuario con la contraseña protegida
    nuevo_usuario = User(
        nombre=datos.nombre,
        apellido=datos.apellido,
        correo=datos.correo,
        password=hash_password(datos.password)
    )

    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible registrar el usuario. Comprueba si el correo ya existe."
        )

    return nuevo_usuario


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK
)
def iniciar_sesion(
    datos: UserLogin,
    db: Session = Depends(get_db)
):
    # Buscar al usuario por su correo
    usuario = db.query(User).filter(
        User.correo == datos.correo
    ).first()

    # Verificar que exista y que su contraseña sea correcta
    if usuario is None or not verify_password(
        datos.password,
        usuario.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Generar el token de acceso
    access_token = create_access_token(usuario.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
