import json
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.metrica import ResultadoMetrica


def create(
    db: Session,
    simulacion_id: int,
    tipo_metrica: str,
    valores: Any,
) -> ResultadoMetrica:
    """Guarda un resultado de métrica para una simulación.

    `valores` puede ser una lista, dict u otro objeto serializable a JSON.
    """
    metrica = ResultadoMetrica(
        simulacion_id=simulacion_id,
        tipo_metrica=tipo_metrica,
        valores_tiempo_json=json.dumps(valores),
    )
    db.add(metrica)
    db.commit()
    db.refresh(metrica)
    return metrica


def get_by_simulacion(db: Session, simulacion_id: int) -> List[ResultadoMetrica]:
    return (
        db.query(ResultadoMetrica)
        .filter(ResultadoMetrica.simulacion_id == simulacion_id)
        .all()
    )


def get_by_tipo(
    db: Session, simulacion_id: int, tipo_metrica: str
) -> Optional[ResultadoMetrica]:
    return (
        db.query(ResultadoMetrica)
        .filter(
            ResultadoMetrica.simulacion_id == simulacion_id,
            ResultadoMetrica.tipo_metrica == tipo_metrica,
        )
        .first()
    )


def delete_by_simulacion(db: Session, simulacion_id: int) -> int:
    """Borra todas las métricas de una simulación. Devuelve la cantidad eliminada."""
    deleted = (
        db.query(ResultadoMetrica)
        .filter(ResultadoMetrica.simulacion_id == simulacion_id)
        .delete()
    )
    db.commit()
    return deleted


def delete_by_id(db: Session, metrica_id: int) -> bool:
    metrica = db.query(ResultadoMetrica).filter(ResultadoMetrica.id == metrica_id).first()
    if metrica is None:
        return False
    db.delete(metrica)
    db.commit()
    return True
