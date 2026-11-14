
from app.db.database import Base, engine
from app.models.user import User

print("=== VERIFICACIÓN DEL MODELO USER ===")

# Comprobar que SQLAlchemy reconoce la tabla
print("Tabla reconocida:", User.__tablename__)

# Mostrar las columnas del modelo
print("\nColumnas registradas:")

for columna in User.__table__.columns:
    print(
        f"- {columna.name}: "
        f"{columna.type}"
    )

# Comprobar la base de datos configurada
print("\nBase de datos:", engine.url.database)

# Comprobar que el modelo está registrado en Base
print(
    "\nModelo registrado en Base:",
    "users" in Base.metadata.tables
)

print("\nVerificación finalizada.")
