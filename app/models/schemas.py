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

    model_config = {"from_attributes": True}


class ResultadoMetricaOut(BaseModel):
    id: int
    tipo_metrica: str
    valores_tiempo_json: Optional[str]

    model_config = {"from_attributes": True}


class SimulacionOut(BaseModel):
    id: int
    nombre: str
    ruta_absoluta: str
    software: Optional[str]
    fecha_registro: Optional[datetime]
    metadata_json: Optional[str]
    archivos: List[ArchivoOut] = Field(default_factory=list)
    metricas: List[ResultadoMetricaOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SimulacionCreate(BaseModel):
    ruta_absoluta: str
    nombre: Optional[str] = None
    software: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class SimulacionUpdate(BaseModel):
    nombre: Optional[str] = None
    software: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class MetricaCreate(BaseModel):
    tipo_metrica: str
    valores: Any


class MetricaOut(BaseModel):
    id: int
    simulacion_id: int
    tipo_metrica: str
    valores_tiempo_json: Optional[str]

    model_config = {"from_attributes": True}
