from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Simulacion(Base):
    __tablename__ = "simulaciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    ruta_absoluta = Column(String(1024), nullable=False, unique=True)
    software = Column(String(100), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(
        Text, nullable=True
    )  # Guardamos JSON serializado como TEXT en SQLite

    # Relaciones
    archivos = relationship(
        "Archivo", back_populates="simulacion", cascade="all, delete-orphan"
    )
    metricas = relationship(
        "ResultadoMetrica", back_populates="simulacion", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - helper
        return (
            f"<Simulacion id={self.id} nombre={self.nombre} ruta={self.ruta_absoluta}>"
        )


class Archivo(Base):
    __tablename__ = "archivos"

    id = Column(Integer, primary_key=True, index=True)
    simulacion_id = Column(Integer, ForeignKey("simulaciones.id"), nullable=False)
    nombre_archivo = Column(String(1024), nullable=False)
    extension = Column(String(50), nullable=True)
    tamano_bytes = Column(Integer, nullable=True)
    tipo = Column(String(50), nullable=True)

    simulacion = relationship("Simulacion", back_populates="archivos")

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"<Archivo id={self.id} nombre={self.nombre_archivo} simulacion_id={self.simulacion_id}>"
