from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.simulacion import Simulacion


class ResultadoMetrica(Base):
    __tablename__ = "resultado_metricas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    simulacion_id: Mapped[int] = mapped_column(
        ForeignKey("simulaciones.id"), nullable=False
    )
    tipo_metrica: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    valores_tiempo_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    simulacion: Mapped["Simulacion"] = relationship(
        "Simulacion", back_populates="metricas"
    )

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"<ResultadoMetrica id={self.id} tipo={self.tipo_metrica} simulacion_id={self.simulacion_id}>"
