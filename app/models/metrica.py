from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ResultadoMetrica(Base):
    __tablename__ = "resultado_metricas"

    id = Column(Integer, primary_key=True, index=True)
    simulacion_id = Column(Integer, ForeignKey("simulaciones.id"), nullable=False)
    tipo_metrica = Column(String(100), nullable=False, index=True)
    valores_tiempo_json = Column(
        Text, nullable=True
    )  # Guardamos el vector como JSON serializado

    simulacion = relationship("Simulacion", back_populates="metricas")

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"<ResultadoMetrica id={self.id} tipo={self.tipo_metrica} simulacion_id={self.simulacion_id}>"
