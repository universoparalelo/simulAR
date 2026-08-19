"""Módulo de análisis de simulaciones moleculares.

Calcula métricas estándar (RMSD, radio de giro) a partir de archivos de
trayectoria usando MDAnalysis o cpptraj según el tamaño del archivo.

Criterio de selección:
  - Trayectoria < CPPTRAJ_THRESHOLD_BYTES  → MDAnalysis (más simple, integrado)
  - Trayectoria >= CPPTRAJ_THRESHOLD_BYTES → cpptraj si disponible (más rápido en
    archivos grandes), con fallback automático a MDAnalysis si no está instalado.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.metrica import ResultadoMetrica
from app.models.simulacion import Archivo, Simulacion

# Umbral a partir del cual se prefiere cpptraj (200 MB)
CPPTRAJ_THRESHOLD_BYTES = 200 * 1024 * 1024

# ---------------------------------------------------------------------------
# Verificación de disponibilidad de MDAnalysis y cpptraj
# ---------------------------------------------------------------------------

try:
    import MDAnalysis as mda
    from MDAnalysis.analysis import rms

    MDA_AVAILABLE = True
except ImportError:
    MDA_AVAILABLE = False


def _cpptraj_cmd() -> Optional[str]:
    """Devuelve el comando para ejecutar cpptraj, o None si no está disponible.

    Busca en orden: binario nativo → wsl cpptraj (Windows).
    """
    if shutil.which("cpptraj"):
        return "cpptraj"
    # Intento vía WSL en Windows
    try:
        result = subprocess.run(
            ["wsl", "which", "cpptraj"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return "wsl cpptraj"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


CPPTRAJ_CMD = _cpptraj_cmd()


# ---------------------------------------------------------------------------
# Detección de archivos de topología y trayectoria
# ---------------------------------------------------------------------------

# Extensiones de topología por software
_TOPOLOGY_EXTS = {".prmtop", ".pdb", ".gro", ".top", ".psf", ".mol2", ".fchk"}
# Extensiones de trayectoria
_TRAJECTORY_EXTS = {".nc", ".mdcrd", ".dcd", ".trr", ".xtc", ".crd"}


def _find_topology_candidates(archivos: list[Archivo]) -> list[str]:
    """Devuelve los archivos de topología ordenados por prioridad."""
    priority = [".prmtop", ".pdb", ".gro", ".top", ".psf"]
    candidates: dict[str, str] = {}
    for a in archivos:
        ext = (a.extension or "").lower()
        if ext in _TOPOLOGY_EXTS:
            candidates[ext] = a.nombre_archivo

    return [candidates[ext] for ext in priority if ext in candidates]


def _find_trajectories(archivos: list[Archivo]) -> list[str]:
    """Devuelve las rutas de los archivos de trayectoria encontrados."""
    return [
        a.nombre_archivo
        for a in archivos
        if (a.extension or "").lower() in _TRAJECTORY_EXTS
    ]


# ---------------------------------------------------------------------------
# Helpers para determinar qué motor usar
# ---------------------------------------------------------------------------

def _trayectoria_size_bytes(sim_ruta: str, trayectorias_rel: list[str]) -> int:
    """Suma de bytes de todos los archivos de trayectoria."""
    total = 0
    for rel in trayectorias_rel:
        try:
            total += os.path.getsize(os.path.join(sim_ruta, rel))
        except OSError:
            pass
    return total


def _usar_cpptraj(sim_ruta: str, trayectorias_rel: list[str]) -> bool:
    """True si cpptraj está disponible y la trayectoria supera el umbral."""
    if not CPPTRAJ_CMD:
        return False
    return _trayectoria_size_bytes(sim_ruta, trayectorias_rel) >= CPPTRAJ_THRESHOLD_BYTES


# ---------------------------------------------------------------------------
# Cálculo de métricas vía cpptraj
# ---------------------------------------------------------------------------

def _run_cpptraj(script: str) -> str:
    """Ejecuta un script cpptraj y devuelve stdout+stderr combinados."""
    cmd = CPPTRAJ_CMD.split()  # "wsl cpptraj" → ["wsl", "cpptraj"]
    result = subprocess.run(
        cmd + ["-i", "-"],
        input=script,
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"cpptraj falló (código {result.returncode}):\n{result.stderr}"
        )
    return result.stdout + result.stderr


def _parse_cpptraj_dat(path: str) -> tuple[list[float], list[float]]:
    """Parsea un archivo .dat de cpptraj con columnas: frame valor.

    Devuelve (frames, valores).
    """
    frames, valores = [], []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                frames.append(float(parts[0]))
                valores.append(float(parts[1]))
    return frames, valores


def calcular_rmsd_cpptraj(
    topologia: str,
    trayectorias: list[str],
    workdir: str,
) -> dict[str, Any]:
    """Calcula RMSD usando cpptraj (para trayectorias grandes).

    Devuelve el mismo formato que calcular_rmsd() de MDAnalysis.
    """
    out_file = os.path.join(workdir, "rmsd_cpptraj.dat")

    traj_lines = "\n".join(f"trajin {t}" for t in trayectorias)
    # Convierte rutas Windows a formato WSL si aplica
    if CPPTRAJ_CMD and CPPTRAJ_CMD.startswith("wsl"):
        topologia = topologia.replace("\\", "/").replace("C:", "/mnt/c")
        traj_lines = "\n".join(
            f"trajin {t.replace(chr(92), '/').replace('C:', '/mnt/c')}"
            for t in trayectorias
        )
        out_wsl = out_file.replace("\\", "/").replace("C:", "/mnt/c")
    else:
        out_wsl = out_file

    script = f"""parm {topologia}
{traj_lines}
rms first @CA,C,N out {out_wsl}
run
"""
    _run_cpptraj(script)

    frames, rmsd_vals = _parse_cpptraj_dat(out_file)
    return {
        "frames": frames,
        "tiempos_ps": frames,  # cpptraj reporta frame, no tiempo ps
        "rmsd_angstrom": rmsd_vals,
        "motor": "cpptraj",
    }


def calcular_rg_cpptraj(
    topologia: str,
    trayectorias: list[str],
    workdir: str,
) -> dict[str, Any]:
    """Calcula radio de giro usando cpptraj (para trayectorias grandes).

    Devuelve el mismo formato que calcular_radio_de_giro() de MDAnalysis.
    """
    out_file = os.path.join(workdir, "rg_cpptraj.dat")

    traj_lines = "\n".join(f"trajin {t}" for t in trayectorias)
    if CPPTRAJ_CMD and CPPTRAJ_CMD.startswith("wsl"):
        topologia = topologia.replace("\\", "/").replace("C:", "/mnt/c")
        traj_lines = "\n".join(
            f"trajin {t.replace(chr(92), '/').replace('C:', '/mnt/c')}"
            for t in trayectorias
        )
        out_wsl = out_file.replace("\\", "/").replace("C:", "/mnt/c")
    else:
        out_wsl = out_file

    script = f"""parm {topologia}
{traj_lines}
radgyr out {out_wsl} mass
run
"""
    _run_cpptraj(script)

    frames, rg_vals = _parse_cpptraj_dat(out_file)
    return {
        "frames": frames,
        "tiempos_ps": frames,
        "rg_angstrom": rg_vals,
        "motor": "cpptraj",
    }


# ---------------------------------------------------------------------------
# Cálculo de métricas vía MDAnalysis
# ---------------------------------------------------------------------------

def calcular_rmsd(
    universe: "mda.Universe",
    select: str = "backbone",
) -> dict[str, Any]:
    """Calcula RMSD cuadro a cuadro respecto al primer frame.

    Devuelve:
        {
            "frames": [...],   # índices de frame
            "tiempos_ps": [...],
            "rmsd_angstrom": [...]
        }
    """
    # Si la selección no tiene átomos, intenta con 'all'
    atoms = universe.select_atoms(select)
    if len(atoms) == 0:
        atoms = universe.select_atoms("all")
        select = "all"

    rmsd_analysis = rms.RMSD(atoms, select=select)
    rmsd_analysis.run()

    results = rmsd_analysis.results.rmsd  # shape (n_frames, 3): frame, time, rmsd
    return {
        "frames": results[:, 0].tolist(),
        "tiempos_ps": results[:, 1].tolist(),
        "rmsd_angstrom": results[:, 2].tolist(),
    }


def calcular_radio_de_giro(
    universe: "mda.Universe",
    select: str = "all",
) -> dict[str, Any]:
    """Calcula el radio de giro cuadro a cuadro.

    Devuelve:
        {
            "frames": [...],
            "tiempos_ps": [...],
            "rg_angstrom": [...]
        }
    """
    atoms = universe.select_atoms(select)
    if len(atoms) == 0:
        atoms = universe.select_atoms("all")

    frames, tiempos, rg_values = [], [], []
    for ts in universe.trajectory:
        frames.append(ts.frame)
        tiempos.append(float(ts.time))
        rg_values.append(float(atoms.radius_of_gyration()))

    return {
        "frames": frames,
        "tiempos_ps": tiempos,
        "rg_angstrom": rg_values,
    }


# ---------------------------------------------------------------------------
# Persistencia de métricas
# ---------------------------------------------------------------------------

def _save_metrica(
    db: Session,
    simulacion_id: int,
    tipo: str,
    valores: Any,
) -> ResultadoMetrica:
    """Sobreescribe la métrica si ya existe, o la crea."""
    existing = (
        db.query(ResultadoMetrica)
        .filter_by(simulacion_id=simulacion_id, tipo_metrica=tipo)
        .first()
    )
    if existing:
        existing.valores_tiempo_json = valores
        db.commit()
        db.refresh(existing)
        return existing

    metrica = ResultadoMetrica(
        simulacion_id=simulacion_id,
        tipo_metrica=tipo,
        valores_tiempo_json=valores,
    )
    db.add(metrica)
    db.commit()
    db.refresh(metrica)
    return metrica


# ---------------------------------------------------------------------------
# Parser de archivos de salida de minimización AMBER
# ---------------------------------------------------------------------------

def parsear_energia_minimizacion(out_path: str) -> dict[str, Any]:
    """Extrae la curva de energía de un archivo .out de minimización AMBER (sander/pmemd).

    Devuelve:
        {
            "pasos": [...],
            "energia_kcal_mol": [...],
            "rms_gradiente": [...]
        }
    """
    import re

    pattern = re.compile(
        r"^\s+(\d+)\s+([\-\d\.E+]+)\s+([\-\d\.E+]+)", re.MULTILINE
    )

    pasos, energias, rms_vals = [], [], []
    try:
        with open(out_path, encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
        for match in pattern.finditer(contenido):
            pasos.append(int(match.group(1)))
            energias.append(float(match.group(2)))
            rms_vals.append(float(match.group(3)))
    except OSError:
        pass

    return {
        "pasos": pasos,
        "energia_kcal_mol": energias,
        "rms_gradiente": rms_vals,
    }


def calcular_propiedades_estaticas(universe: "mda.Universe") -> dict[str, Any]:
    """Calcula propiedades estáticas de una estructura (sin trayectoria)."""
    atoms = universe.select_atoms("all")
    return {
        "n_atomos": len(atoms),
        "n_residuos": len(universe.residues),
        "rg_angstrom": float(atoms.radius_of_gyration()),
        "masa_total_uma": float(atoms.total_mass()),
    }


# ---------------------------------------------------------------------------
# Función principal de análisis
# ---------------------------------------------------------------------------

def analizar_simulacion(
    db: Session,
    simulacion_id: int,
    metricas: list[str] | None = None,
) -> dict[str, Any]:
    """
    Analiza una simulación y guarda las métricas en la DB.

    Args:
        db: Sesión de base de datos.
        simulacion_id: ID de la simulación a analizar.
        metricas: Lista de métricas a calcular. Por defecto: ["rmsd", "rg"].
                  Valores posibles: "rmsd", "rg".

    Returns:
        Diccionario con los resultados y metadatos del análisis.

    Raises:
        ValueError: Si MDAnalysis no está disponible o faltan archivos necesarios.
        FileNotFoundError: Si la ruta de la simulación no existe.
    """
    if not MDA_AVAILABLE:
        raise ValueError(
            "MDAnalysis no está instalado. "
            "Ejecutá: pip install MDAnalysis"
        )

    if metricas is None:
        metricas = ["rmsd", "rg"]

    sim: Optional[Simulacion] = db.query(Simulacion).filter_by(id=simulacion_id).first()
    if sim is None:
        raise ValueError(f"Simulación {simulacion_id} no encontrada en la DB.")

    if not os.path.isdir(sim.ruta_absoluta):
        raise FileNotFoundError(f"El directorio ya no existe: {sim.ruta_absoluta}")

    archivos: list[Archivo] = sim.archivos

    # Localizar archivos
    topologia_candidates = _find_topology_candidates(archivos)
    trayectorias_rel = _find_trajectories(archivos)
    out_files = [
        a.nombre_archivo for a in archivos
        if (a.extension or "").lower() == ".out"
    ]

    if not topologia_candidates:
        raise ValueError(
            "No se encontró archivo de topología compatible "
            "(.prmtop, .pdb, .gro, .top, .psf)."
        )

    # Detectar modo: con trayectoria (MD) o sin ella (minimización / estructura estática)
    tiene_trayectoria = bool(trayectorias_rel)
    trayectorias = [os.path.join(sim.ruta_absoluta, r) for r in trayectorias_rel]

    # Decidir motor de análisis para métricas temporales
    usar_cpp = tiene_trayectoria and _usar_cpptraj(sim.ruta_absoluta, trayectorias_rel)
    motor_label = "cpptraj" if usar_cpp else "MDAnalysis"

    # Formatos explícitos por extensión para MDAnalysis
    _MDA_FORMAT: dict[str, str] = {
        ".inpcrd": "INPCRD",
        ".rst": "RESTRT",
        ".rst7": "RESTRT",
        ".ncrst": "RESTRT",
        ".gro": "GRO",
    }

    # Cargar Universe probando cada topología en orden de prioridad
    universe = None
    topologia_rel = None
    for candidate_rel in topologia_candidates:
        candidate_path = os.path.join(sim.ruta_absoluta, candidate_rel)
        try:
            if tiene_trayectoria:
                universe = mda.Universe(candidate_path, *trayectorias)
            else:
                coord_priority = [".inpcrd", ".rst7", ".ncrst", ".rst", ".gro"]
                coord_rel = None
                for ext in coord_priority:
                    match = next(
                        (a.nombre_archivo for a in archivos if (a.extension or "").lower() == ext),
                        None,
                    )
                    if match:
                        coord_rel = match
                        coord_fmt = _MDA_FORMAT[ext]
                        break

                if coord_rel:
                    universe = mda.Universe(
                        candidate_path,
                        os.path.join(sim.ruta_absoluta, coord_rel),
                        format=coord_fmt,
                    )
                else:
                    universe = mda.Universe(candidate_path)
            topologia_rel = candidate_rel
            break
        except Exception:
            continue

    if universe is None:
        raise ValueError(
            f"No se pudo cargar ninguna topología. "
            f"Candidatos probados: {topologia_candidates}"
        )

    topologia = os.path.join(sim.ruta_absoluta, topologia_rel)

    n_frames = len(universe.trajectory)
    n_atomos = len(universe.atoms)
    traj_size_mb = round(
        _trayectoria_size_bytes(sim.ruta_absoluta, trayectorias_rel) / (1024 * 1024), 1
    )

    resultados: dict[str, Any] = {
        "simulacion_id": simulacion_id,
        "modo": "dinamica" if tiene_trayectoria else "minimizacion_o_estatico",
        "motor_analisis": motor_label,
        "trayectoria_size_mb": traj_size_mb,
        "n_frames": n_frames,
        "n_atomos": n_atomos,
        "topologia_usada": topologia_rel,
        "trayectorias_usadas": trayectorias_rel,
        "metricas_calculadas": [],
        "errores": [],
        "advertencias": [],
    }

    if not tiene_trayectoria:
        resultados["advertencias"].append(
            "No se encontro trayectoria (.nc, .mdcrd, .xtc). "
            "RMSD y Rg temporal no estan disponibles. "
            "Se calcularon propiedades estaticas y energia de minimizacion."
        )

    if usar_cpp:
        resultados["advertencias"].append(
            f"Trayectoria >= {CPPTRAJ_THRESHOLD_BYTES // (1024*1024)} MB "
            f"({traj_size_mb} MB): usando cpptraj."
        )
    elif tiene_trayectoria and CPPTRAJ_CMD:
        resultados["advertencias"].append(
            f"Trayectoria < {CPPTRAJ_THRESHOLD_BYTES // (1024*1024)} MB "
            f"({traj_size_mb} MB): usando MDAnalysis."
        )

    # --- Propiedades estáticas (siempre disponibles) ---
    try:
        props = calcular_propiedades_estaticas(universe)
        _save_metrica(db, simulacion_id, "propiedades_estaticas", props)
        resultados["metricas_calculadas"].append("propiedades_estaticas")
        resultados["propiedades_estaticas"] = props
    except Exception as exc:
        resultados["errores"].append(f"Propiedades estaticas: {exc}")

    # --- Energía de minimización (solo si hay .out y no hay trayectoria) ---
    if not tiene_trayectoria and out_files:
        try:
            out_path = os.path.join(sim.ruta_absoluta, out_files[0])
            energia_data = parsear_energia_minimizacion(out_path)
            if energia_data["pasos"]:
                _save_metrica(db, simulacion_id, "energia_minimizacion", energia_data)
                resultados["metricas_calculadas"].append("energia_minimizacion")
                energias = energia_data["energia_kcal_mol"]
                resultados["energia_resumen"] = {
                    "n_pasos": len(energias),
                    "energia_inicial_kcal_mol": energias[0],
                    "energia_final_kcal_mol": energias[-1],
                    "reduccion_kcal_mol": energias[0] - energias[-1],
                }
        except Exception as exc:
            resultados["errores"].append(f"Energia minimizacion: {exc}")

    # --- RMSD (solo con trayectoria) ---
    if tiene_trayectoria and "rmsd" in metricas:
        try:
            if usar_cpp:
                with tempfile.TemporaryDirectory() as tmpdir:
                    rmsd_data = calcular_rmsd_cpptraj(topologia, trayectorias, tmpdir)
            else:
                rmsd_data = calcular_rmsd(universe)
            _save_metrica(db, simulacion_id, "rmsd", rmsd_data)
            resultados["metricas_calculadas"].append("rmsd")
            vals = rmsd_data["rmsd_angstrom"]
            resultados["rmsd_resumen"] = {
                "min": min(vals),
                "max": max(vals),
                "promedio": sum(vals) / len(vals),
            }
        except Exception as exc:
            resultados["errores"].append(f"RMSD: {exc}")

    # --- Radio de giro temporal (solo con trayectoria) ---
    if tiene_trayectoria and "rg" in metricas:
        try:
            if usar_cpp:
                with tempfile.TemporaryDirectory() as tmpdir:
                    rg_data = calcular_rg_cpptraj(topologia, trayectorias, tmpdir)
            else:
                rg_data = calcular_radio_de_giro(universe)
            _save_metrica(db, simulacion_id, "rg", rg_data)
            resultados["metricas_calculadas"].append("rg")
            vals = rg_data["rg_angstrom"]
            resultados["rg_resumen"] = {
                "min": min(vals),
                "max": max(vals),
                "promedio": sum(vals) / len(vals),
            }
        except Exception as exc:
            resultados["errores"].append(f"Radio de giro: {exc}")

    return resultados


# ---------------------------------------------------------------------------
# Wrapper para ejecución en segundo plano (FastAPI BackgroundTasks)
# ---------------------------------------------------------------------------

def analizar_simulacion_background(
    simulacion_id: int,
    metricas: list[str] | None = None,
) -> None:
    """Corre `analizar_simulacion` en background con sesión propia.

    Se usa desde un BackgroundTask de FastAPI, que se ejecuta después de que
    la request ya respondió: la sesión inyectada por `Depends(get_db)` está
    cerrada para entonces, así que acá se abre y cierra una sesión nueva.
    Actualiza `estado_analisis`/`analisis_error` en la simulación al terminar.
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        analizar_simulacion(db, simulacion_id, metricas=metricas)
        sim = db.query(Simulacion).filter_by(id=simulacion_id).first()
        if sim is not None:
            sim.estado_analisis = "completado"
            sim.analisis_error = None
            db.commit()
    except Exception as exc:
        db.rollback()
        sim = db.query(Simulacion).filter_by(id=simulacion_id).first()
        if sim is not None:
            sim.estado_analisis = "error"
            error_msg = str(exc) or f"{type(exc).__name__}: {repr(exc)}"
            sim.analisis_error = error_msg
            db.commit()
    finally:
        db.close()
