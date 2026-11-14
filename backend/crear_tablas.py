
from app.db.database import Base, engine
from app.models.user import User

print("=== CREACIÓN DE TABLAS ===")

try:
    # Crear las tablas que todavía no existan
    Base.metadata.create_all(bind=engine)

    print("Tablas creadas o verificadas correctamente.")

    # Consultar las tablas registradas en la base de datos
    tablas = Base.metadata.tables.keys()

    print("\nTablas reconocidas por SQLAlchemy:")

    for tabla in tablas:
        print("-", tabla)

    print("\nBase de datos:", engine.url.database)

except Exception as error:
    print("Error al crear las tablas:", error)
