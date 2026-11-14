
from app.core.security import hash_password, verify_password

print("=== PRUEBA DE SEGURIDAD ARGON2 ===")

# Contraseña ficticia para realizar la prueba
password_original = "BioGen2026!"

# Generar el hash
password_encriptada = hash_password(password_original)

print("Hash generado correctamente.")

# Comprobar la contraseña correcta
resultado_correcto = verify_password(
    password_original,
    password_encriptada
)

print(
    "Verificación de contraseña correcta:",
    resultado_correcto
)

# Comprobar una contraseña incorrecta
resultado_incorrecto = verify_password(
    "ContraseñaIncorrecta",
    password_encriptada
)

print(
    "Verificación de contraseña incorrecta:",
    resultado_incorrecto
)

print("\nPrueba finalizada.")
