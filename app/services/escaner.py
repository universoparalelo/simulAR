import os
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.simulacion import Archivo, Simulacion

# ============================================================
# Clasificación de extensiones
# ============================================================

TRAJECTORY_EXTS = {".nc", ".dcd", ".mdcrd", ".trr", ".xtc", ".crd"}
INPUT_EXTS = {".prmtop", ".top", ".inpcrd", ".pdb", ".gro", ".gjf", ".inp", ".chk", ".fchk"}
OUTPUT_EXTS = {".log", ".out", ".txt", ".dat", ".travis"}
RESTART_EXTS = {".rst", ".rst7", ".ncrst"}


def classify_file_extension(ext: str) -> str:
    ext = ext.lower()
    if ext in TRAJECTORY_EXTS:
        return "trajectory"
    if ext in INPUT_EXTS:
        return "input"
    if ext in OUTPUT_EXTS:
        return "output"
    if ext in RESTART_EXTS:
        return "restart"
    return "other"


# ============================================================
# Detección de software
# ============================================================

# Extensiones que son señal fuerte de cada software
_AMBER_EXTS = {".prmtop", ".inpcrd", ".mdcrd", ".nc", ".rst7", ".ncrst"}
_GAMESS_EXTS = {".inp"}   # .log es compartido, se confirma por contenido
_GAUSSIAN_EXTS = {".gjf", ".chk", ".fchk"}
_TRAVIS_EXTS = {".travis"}
_GROMACS_EXTS = {".gro", ".top", ".tpr", ".xtc", ".trr", ".edr", ".ndx", ".mdp"}


def _read_first_bytes(path: str, n: int = 512) -> str:
    """Lee los primeros n bytes de un archivo como texto, ignorando errores."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(n)
    except OSError:
        return ""


def _detect_software_from_log(log_path: str) -> Optional[str]:
    """Inspecciona el contenido de un .log para distinguir AMBER/GAMESS/Gaussian."""
    header = _read_first_bytes(log_path, 1024)
    header_low = header.lower()
    if "gaussian" in header_low or "g16" in header_low or "g09" in header_low:
        return "Gaussian"
    if "gamess" in header_low:
        return "GAMESS"
    if "amber" in header_low or "sander" in header_low or "pmemd" in header_low:
        return "AMBER"
    return None


def detect_software(files: list[dict[str, Any]]) -> Optional[str]:
    """
    Determina el software de simulación a partir de la lista de archivos escaneados.
    Devuelve el nombre del software o None si no se puede determinar.
    """
    exts = {f["extension"].lower() for f in files if f["extension"]}
    paths_by_ext: dict[str, list[str]] = {}
    for f in files:
        ext = (f["extension"] or "").lower()
        paths_by_ext.setdefault(ext, []).append(f["ruta_completa"])

    # Señales exclusivas por extensión
    if exts & _GAUSSIAN_EXTS:
        return "Gaussian"
    if exts & _TRAVIS_EXTS:
        return "Travis"
    if exts & _AMBER_EXTS:
        return "AMBER"
    if exts & _GROMACS_EXTS:
        return "GROMACS"

    # .inp puede ser GAMESS o AMBER (mdin); intentamos leer el contenido
    if ".inp" in exts:
        for path in paths_by_ext.get(".inp", [])[:3]:
            content = _read_first_bytes(path, 512)
            if "gamess" in content.lower() or "$contrl" in content.lower():
                return "GAMESS"
            if "amber" in content.lower() or "&cntrl" in content.lower():
                return "AMBER"

    # .log puede ser de varios; inspeccionamos hasta 3 archivos
    if ".log" in exts:
        for path in paths_by_ext.get(".log", [])[:3]:
            detected = _detect_software_from_log(path)
            if detected:
                return detected

    return None


# ============================================================
# Validación de simulación
# ============================================================

# Una carpeta es una simulación si tiene al menos uno de estos
_SIMULATION_SIGNALS = (
    TRAJECTORY_EXTS
    | _AMBER_EXTS
    | _GAUSSIAN_EXTS
    | _GAMESS_EXTS
    | _TRAVIS_EXTS
    | _GROMACS_EXTS
    | {".log", ".out"}
)


def is_simulation_directory(files: list[dict[str, Any]]) -> bool:
    """Devuelve True si la lista de archivos tiene señales de ser una simulación."""
    if not files:
        return False
    exts = {f["extension"].lower() for f in files if f["extension"]}
    return bool(exts & _SIMULATION_SIGNALS)


# ============================================================
# Escaneo de archivos
# ============================================================

def scan_files_in_path(path: str) -> list[dict[str, Any]]:
    """Escanea recursivamente `path` y devuelve metadatos de cada archivo."""
    result: list[dict[str, Any]] = []
    for root, _, files in os.walk(path):
        for fname in files:
            full = os.path.join(root, fname)
            try:
                stat = os.stat(full)
                size = stat.st_size
                mtime = stat.st_mtime
            except OSError:
                size = None
                mtime = None
            _, ext = os.path.splitext(fname)
            tipo = classify_file_extension(ext)
            rel_path = os.path.relpath(full, path)
            result.append(
                {
                    "nombre_archivo": rel_path,
                    "extension": ext.lower() if ext else "",
                    "tamano_bytes": size,
                    "mtime": mtime,
                    "tipo": tipo,
                    "ruta_completa": full,
                }
            )
    return result


def build_metadata(path: str, files: list[dict[str, Any]], software: Optional[str]) -> dict[str, Any]:
    """Construye el diccionario de metadata enriquecida para una simulación."""
    by_type: dict[str, int] = {}
    total_bytes = 0
    for f in files:
        by_type[f["tipo"]] = by_type.get(f["tipo"], 0) + 1
        total_bytes += f["tamano_bytes"] or 0

    mtimes = [f["mtime"] for f in files if f["mtime"] is not None]

    return {
        "software_detectado": software,
        "total_archivos": len(files),
        "total_bytes": total_bytes,
        "archivos_por_tipo": by_type,
        "fecha_modificacion_mas_reciente": max(mtimes) if mtimes else None,
        "fecha_modificacion_mas_antigua": min(mtimes) if mtimes else None,
    }


# ============================================================
# Registro de simulaciones
# ============================================================

def register_simulation(
    db: Session,
    ruta_absoluta: str,
    nombre: Optional[str] = None,
    software: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Simulacion:
    """
    Registra una simulación en la DB leyendo la carpeta `ruta_absoluta`.
    - Si la ruta ya fue registrada, devuelve el registro existente.
    - Detecta el software automáticamente si no se proporciona.
    - Construye metadata enriquecida si no se proporciona.
    """
    ruta_absoluta = os.path.abspath(ruta_absoluta)
    if not os.path.exists(ruta_absoluta):
        raise FileNotFoundError(f"La ruta no existe: {ruta_absoluta}")

    existing = db.query(Simulacion).filter_by(ruta_absoluta=ruta_absoluta).first()
    if existing:
        return existing

    nombre = nombre or os.path.basename(ruta_absoluta.rstrip(os.sep)) or ruta_absoluta
    files = scan_files_in_path(ruta_absoluta)

    # Detectar software si no fue provisto
    if software is None:
        software = detect_software(files)

    # Construir metadata si no fue provista
    if metadata is None:
        metadata = build_metadata(ruta_absoluta, files, software)

    sim = Simulacion(
        nombre=nombre,
        ruta_absoluta=ruta_absoluta,
        software=software,
        metadata_json=metadata,
    )
    db.add(sim)
    db.flush()

    for f in files:
        db.add(Archivo(
            nombre_archivo=f["nombre_archivo"],
            extension=f["extension"],
            tamano_bytes=f["tamano_bytes"],
            tipo=f["tipo"],
            simulacion_id=sim.id,
        ))

    db.commit()
    db.refresh(sim)
    return sim


def scan_directory_for_simulations(
    db: Session,
    ruta_raiz: str,
    registrar: bool = True,
) -> list[dict[str, Any]]:
    """
    Escanea una carpeta raíz buscando subcarpetas que parezcan simulaciones.

    - Cada subcarpeta directa se analiza como posible simulación.
    - Si `registrar=True`, las que pasan la validación se registran en la DB.
    - Devuelve una lista con el resultado de cada subcarpeta analizada.
    """
    ruta_raiz = os.path.abspath(ruta_raiz)
    if not os.path.isdir(ruta_raiz):
        raise FileNotFoundError(f"La ruta no existe o no es un directorio: {ruta_raiz}")

    resultados = []

    try:
        entries = [
            e for e in os.scandir(ruta_raiz)
            if e.is_dir(follow_symlinks=False)
        ]
    except PermissionError as exc:
        raise PermissionError(f"Sin permiso para leer: {ruta_raiz}") from exc

    for entry in sorted(entries, key=lambda e: e.name):
        files = scan_files_in_path(entry.path)
        es_sim = is_simulation_directory(files)
        software = detect_software(files) if es_sim else None
        metadata = build_metadata(entry.path, files, software) if es_sim else None

        resultado: dict[str, Any] = {
            "ruta": entry.path,
            "nombre": entry.name,
            "es_simulacion": es_sim,
            "software_detectado": software,
            "total_archivos": len(files),
            "simulacion_id": None,
            "ya_registrada": False,
            "error": None,
        }

        if es_sim and registrar:
            try:
                existing = db.query(Simulacion).filter_by(ruta_absoluta=entry.path).first()
                if existing:
                    resultado["ya_registrada"] = True
                    resultado["simulacion_id"] = existing.id
                else:
                    sim = register_simulation(
                        db,
                        entry.path,
                        nombre=entry.name,
                        software=software,
                        metadata=metadata,
                    )
                    resultado["simulacion_id"] = sim.id
            except Exception as exc:
                resultado["error"] = str(exc)

        resultados.append(resultado)

    return resultados


def list_simulations(db: Session) -> list[Simulacion]:
    return db.query(Simulacion).order_by(Simulacion.fecha_registro.desc()).all()


# ============================================================
# Análisis de almacenamiento
# ============================================================

_ESSENTIAL_EXTS = {".prmtop", ".pdb", ".gro", ".top", ".psf", ".mol2",
                   ".nc", ".xtc", ".trr", ".dcd",
                   ".mdin", ".mdp", ".gjf", ".inp", ".inpcrd"}

_DELETABLE_EXTS = {".mdinfo", ".mdvel", ".mdcrd",
                   ".edr", ".cpt",
                   ".chk",
                   ".bak", ".tmp"}

_DELETABLE_PATTERNS = {"#"}


def classify_deletability(archivo: Archivo, all_archivos: list[Archivo]) -> str:
    """Clasifica un archivo como 'essential', 'useful' o 'deletable'.

    Reglas:
      - Topologías, trayectorias principales e inputs → essential
      - Checkpoints (.chk), velocidades (.mdvel), energía binaria (.edr),
        backups, mdcrd duplicados cuando existe .nc → deletable
      - Restarts: solo el más reciente es useful, el resto deletable
      - Outputs (.out, .log): useful (contienen datos parseables)
      - Todo lo demás → useful
    """
    ext = (archivo.extension or "").lower()
    nombre = archivo.nombre_archivo or ""

    if ext in _ESSENTIAL_EXTS:
        return "essential"

    if ext in _DELETABLE_EXTS:
        return "deletable"

    if any(nombre.startswith(p) or nombre.endswith(p) for p in _DELETABLE_PATTERNS):
        return "deletable"

    # .mdcrd es deletable si ya existe .nc (formato binario más eficiente)
    if ext == ".mdcrd":
        has_nc = any((a.extension or "").lower() == ".nc" for a in all_archivos)
        return "deletable" if has_nc else "essential"

    # Restarts: solo el más grande (último) es useful, el resto deletable
    if ext in RESTART_EXTS:
        restarts = [a for a in all_archivos if (a.extension or "").lower() in RESTART_EXTS]
        if len(restarts) <= 1:
            return "useful"
        biggest = max(restarts, key=lambda a: a.tamano_bytes or 0)
        return "useful" if archivo.id == biggest.id else "deletable"

    return "useful"


def analyze_storage(archivos: list[Archivo]) -> dict[str, Any]:
    """Analiza el almacenamiento de una simulación y clasifica archivos."""
    categories: dict[str, list[dict]] = {"essential": [], "useful": [], "deletable": []}
    totals: dict[str, int] = {"essential": 0, "useful": 0, "deletable": 0}

    for archivo in archivos:
        cat = classify_deletability(archivo, archivos)
        entry = {
            "id": archivo.id,
            "nombre_archivo": archivo.nombre_archivo,
            "extension": archivo.extension,
            "tamano_bytes": archivo.tamano_bytes or 0,
            "tipo": archivo.tipo,
            "categoria": cat,
        }
        categories[cat].append(entry)
        totals[cat] += archivo.tamano_bytes or 0

    total = sum(totals.values())
    return {
        "total_bytes": total,
        "essential_bytes": totals["essential"],
        "useful_bytes": totals["useful"],
        "deletable_bytes": totals["deletable"],
        "deletable_files": sorted(categories["deletable"],
                                  key=lambda f: f["tamano_bytes"], reverse=True),
        "archivos": sorted(
            categories["essential"] + categories["useful"] + categories["deletable"],
            key=lambda f: f["tamano_bytes"], reverse=True,
        ),
    }
