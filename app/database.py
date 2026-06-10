import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Leer la URL de la base de datos desde la variable de entorno (por defecto SQLite local)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./simular_local.db")

# Engine y Session configurados para SQLAlchemy 2.0
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


# Declarative Base moderno
class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency de FastAPI: obtiene una sesión DB y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea las tablas definidas en los modelos registrados en Base.metadata.

    Nota: los módulos que definen modelos deben importarse antes de llamar a
    esta función (por ejemplo, desde el evento `startup` de la aplicación).
    """
    Base.metadata.create_all(bind=engine)
