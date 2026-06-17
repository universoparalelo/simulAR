from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.simulacion import Archivo


def get_by_simulacion(db: Session, simulacion_id: int) -> List[Archivo]:
    return db.query(Archivo).filter(Archivo.simulacion_id == simulacion_id).all()


def get_by_id(db: Session, archivo_id: int) -> Optional[Archivo]:
    return db.query(Archivo).filter(Archivo.id == archivo_id).first()


def delete(db: Session, archivo_id: int) -> bool:
    archivo = get_by_id(db, archivo_id)
    if archivo is None:
        return False
    db.delete(archivo)
    db.commit()
    return True
