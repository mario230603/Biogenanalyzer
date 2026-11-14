
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.core.security import JWT_SECRET_KEY, JWT_ALGORITHM


# Permite recibir el token JWT desde el encabezado Authorization
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    # Respuesta para tokens inválidos o ausentes
    error_autenticacion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la autenticación",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY no está configurada")

    try:
        # Extraer el token recibido
        token = credentials.credentials

        # Decodificar y verificar el JWT
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        # Recuperar el identificador del usuario
        user_id = payload.get("sub")

        if user_id is None:
            raise error_autenticacion

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error_autenticacion

    # Buscar al usuario en la base de datos
    usuario = db.query(User).filter(User.id == user_id).first()

    if usuario is None:
        raise error_autenticacion

    return usuario
