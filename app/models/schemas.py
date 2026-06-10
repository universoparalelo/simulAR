from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ArchivoOut(BaseModel):
    id: int
    nombre_archivo: str
    extension: Optional[str]
    tamano_bytes: Optional[int]
    tipo: Optional[str]

    class Config:
        orm_mode = True


class ResultadoMetricaOut(BaseModel):
    id: int
    tipo_metrica: str
    valores_tiempo_json: Optional[str]

    class Config:
        orm_mode = True


class SimulacionOut(BaseModel):
    id: int
    nombre: str
    ruta_absoluta: str
    software: Optional[str]
    fecha_registro: Optional[datetime]
    metadata_json: Optional[str]
    archivos: List[ArchivoOut] = Field(default_factory=list)
    metricas: List[ResultadoMetricaOut] = Field(default_factory=list)

    class Config:
        orm_mode = True


class SimulacionCreate(BaseModel):
    ruta_absoluta: str
    nombre: Optional[str] = None
    software: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
