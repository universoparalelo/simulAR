from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.metrica import ResultadoMetrica

# JSON genérico en SQLite (TEXT), JSONB nativo en PostgreSQL/Supabase (indexable)
_JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Simulacion(Base):
    __tablename__ = "simulaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ruta_absoluta: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    software: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fecha_registro: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(_JSON_TYPE, nullable=True)
    estado_analisis: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pendiente", server_default="pendiente"
    )
    analisis_error: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Relaciones
    archivos: Mapped[List["Archivo"]] = relationship(
        "Archivo", back_populates="simulacion", cascade="all, delete-orphan"
    )
    metricas: Mapped[List["ResultadoMetrica"]] = relationship(
        "ResultadoMetrica", back_populates="simulacion", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - helper
        return (
            f"<Simulacion id={self.id} nombre={self.nombre} ruta={self.ruta_absoluta}>"
        )


class Archivo(Base):
    __tablename__ = "archivos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    simulacion_id: Mapped[int] = mapped_column(
        ForeignKey("simulaciones.id"), nullable=False
    )
    nombre_archivo: Mapped[str] = mapped_column(String(1024), nullable=False)
    extension: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tamano_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    simulacion: Mapped["Simulacion"] = relationship(
        "Simulacion", back_populates="archivos"
    )

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"<Archivo id={self.id} nombre={self.nombre_archivo} simulacion_id={self.simulacion_id}>"
