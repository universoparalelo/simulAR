from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

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
    valores_tiempo_json: Optional[Union[Dict[str, Any], List[Any]]]

    model_config = {"from_attributes": True}


class SimulacionOut(BaseModel):
    id: int
    nombre: str
    ruta_absoluta: str
    software: Optional[str]
    fecha_registro: Optional[datetime]
    metadata_json: Optional[Dict[str, Any]]
    estado_analisis: str
    analisis_error: Optional[str]
    archivos: List[ArchivoOut] = Field(default_factory=list)
    metricas: List[ResultadoMetricaOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SimulacionCreate(BaseModel):
    ruta_absoluta: str
    nombre: Optional[str] = None
    software: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class AnalisisMetricaConfig(BaseModel):
    atom_selection: str = "backbone"
    frame_start: Optional[int] = None
    frame_end: Optional[int] = None


class AnalisisRequest(BaseModel):
    metricas: Dict[str, AnalisisMetricaConfig] = Field(default_factory=lambda: {
        "rmsd": AnalisisMetricaConfig(atom_selection="backbone"),
        "rg": AnalisisMetricaConfig(atom_selection="all"),
    })


class ScanDirectoryRequest(BaseModel):
    ruta_absoluta: str
    registrar: bool = True


class ScanDirectoryResult(BaseModel):
    ruta: str
    nombre: str
    es_simulacion: bool
    software_detectado: Optional[str]
    total_archivos: int
    simulacion_id: Optional[int]
    ya_registrada: bool
    error: Optional[str]


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
    valores_tiempo_json: Optional[Union[Dict[str, Any], List[Any]]]

    model_config = {"from_attributes": True}
