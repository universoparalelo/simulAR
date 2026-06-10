import json
import os
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.simulacion import Archivo, Simulacion

TRAJECTORY_EXTS = {".nc", ".dcd", ".mdcrd", ".trr"}
INPUT_EXTS = {".prmtop", ".top", ".inpcrd", ".pdb", ".gro"}
OUTPUT_EXTS = {".log", ".out", ".txt", ".dat"}


def classify_file_extension(ext: str) -> str:
    ext = ext.lower()
    if ext in TRAJECTORY_EXTS:
        return "trajectory"
    if ext in INPUT_EXTS:
        return "input"
    if ext in OUTPUT_EXTS:
        return "output"
    return "other"


def scan_files_in_path(path: str) -> List[dict[str, Any]]:
    """Escanea recursivamente `path` y devuelve una lista de metadatos de archivos."""
    result: List[dict[str, Any]] = []
    for root, _, files in os.walk(path):
        for fname in files:
            full = os.path.join(root, fname)
            try:
                size = os.path.getsize(full)
            except OSError:
                size = None
            _, ext = os.path.splitext(fname)
            tipo = classify_file_extension(ext)
            rel_path = os.path.relpath(full, path)
            result.append(
                {
                    "nombre_archivo": rel_path,
                    "extension": ext.lower(),
                    "tamano_bytes": size,
                    "tipo": tipo,
                    "ruta_completa": full,
                }
            )
    return result


def register_simulation(
    db: Session,
    ruta_absoluta: str,
    nombre: Optional[str] = None,
    software: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Simulacion:
    """Registra una simulacion en la DB leyendo la carpeta `ruta_absoluta`.

    - Si la ruta ya fue registrada, devuelve el registro existente.
    - Añade todos los archivos detectados a la tabla `Archivo`.
    """
    ruta_absoluta = os.path.abspath(ruta_absoluta)
    if not os.path.exists(ruta_absoluta):
        raise FileNotFoundError(f"La ruta no existe: {ruta_absoluta}")

    existing = db.query(Simulacion).filter_by(ruta_absoluta=ruta_absoluta).first()
    if existing:
        return existing

    nombre = nombre or os.path.basename(ruta_absoluta.rstrip(os.sep)) or ruta_absoluta

    # Construimos simulación; si metadata está presente, la serializamos y la pasamos al constructor
    metadata_json = None
    if metadata is not None:
        try:
            metadata_json = json.dumps(metadata)
        except Exception:
            metadata_json = None

    sim = Simulacion(
        nombre=nombre,
        ruta_absoluta=ruta_absoluta,
        software=software,
        metadata_json=metadata_json,
    )

    db.add(sim)
    db.flush()  # obtener id antes de agregar archivos

    files = scan_files_in_path(ruta_absoluta)

    for f in files:
        archivo = Archivo(
            nombre_archivo=f["nombre_archivo"],
            extension=f["extension"],
            tamano_bytes=f["tamano_bytes"],
            tipo=f["tipo"],
            simulacion_id=sim.id,
        )
        db.add(archivo)

    db.commit()
    db.refresh(sim)
    return sim


def list_simulations(db: Session) -> List[Simulacion]:
    return db.query(Simulacion).order_by(Simulacion.fecha_registro.desc()).all()
