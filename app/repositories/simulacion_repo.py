from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.simulacion import Simulacion


def get_by_id(db: Session, simulacion_id: int) -> Optional[Simulacion]:
    return db.query(Simulacion).filter(Simulacion.id == simulacion_id).first()


def get_all(db: Session) -> List[Simulacion]:
    return db.query(Simulacion).order_by(Simulacion.fecha_registro.desc()).all()


def update(
    db: Session,
    simulacion_id: int,
    nombre: Optional[str] = None,
    software: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[Simulacion]:
    sim = get_by_id(db, simulacion_id)
    if sim is None:
        return None
    if nombre is not None:
        sim.nombre = nombre
    if software is not None:
        sim.software = software
    if metadata is not None:
        sim.metadata_json = metadata
    db.commit()
    db.refresh(sim)
    return sim


def delete(db: Session, simulacion_id: int) -> bool:
    sim = get_by_id(db, simulacion_id)
    if sim is None:
        return False
    db.delete(sim)
    db.commit()
    return True
