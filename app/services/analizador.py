"""Módulo de análisis de simulaciones moleculares.

Calcula métricas estándar (RMSD, radio de giro) a partir de archivos de
trayectoria usando MDAnalysis, y persiste los resultados en la DB.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.metrica import ResultadoMetrica
from app.models.simulacion import Archivo, Simulacion

# ---------------------------------------------------------------------------
# Verificación de disponibilidad de MDAnalysis
# ---------------------------------------------------------------------------

try:
    import MDAnalysis as mda
    from MDAnalysis.analysis import rms

    MDA_AVAILABLE = True
except ImportError:
    MDA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Detección de archivos de topología y trayectoria
# ---------------------------------------------------------------------------

# Extensiones de topología por software
_TOPOLOGY_EXTS = {".prmtop", ".pdb", ".gro", ".top", ".psf", ".mol2", ".fchk"}
# Extensiones de trayectoria
_TRAJECTORY_EXTS = {".nc", ".mdcrd", ".dcd", ".trr", ".xtc", ".crd"}


def _find_topology(archivos: list[Archivo]) -> Optional[str]:
    """Devuelve la ruta del archivo de topología más adecuado."""
    # Prioridad: prmtop > pdb > gro > resto
    priority = [".prmtop", ".pdb", ".gro", ".top", ".psf"]
    candidates: dict[str, str] = {}
    for a in archivos:
        ext = (a.extension or "").lower()
        if ext in _TOPOLOGY_EXTS:
            candidates[ext] = a.nombre_archivo

    for ext in priority:
        if ext in candidates:
            return candidates[ext]
    return None


def _find_trajectories(archivos: list[Archivo]) -> list[str]:
    """Devuelve las rutas de los archivos de trayectoria encontrados."""
    return [
        a.nombre_archivo
        for a in archivos
        if (a.extension or "").lower() in _TRAJECTORY_EXTS
    ]


# ---------------------------------------------------------------------------
# Cálculo de métricas
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
        existing.valores_tiempo_json = json.dumps(valores)
        db.commit()
        db.refresh(existing)
        return existing

    metrica = ResultadoMetrica(
        simulacion_id=simulacion_id,
        tipo_metrica=tipo,
        valores_tiempo_json=json.dumps(valores),
    )
    db.add(metrica)
    db.commit()
    db.refresh(metrica)
    return metrica


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

    # Localizar topología y trayectorias
    topologia_rel = _find_topology(archivos)
    trayectorias_rel = _find_trajectories(archivos)

    if topologia_rel is None:
        raise ValueError(
            "No se encontró archivo de topología compatible "
            "(.prmtop, .pdb, .gro, .top, .psf). "
            "Verificá que la simulación tenga los archivos correctos."
        )

    if not trayectorias_rel:
        raise ValueError(
            "No se encontraron archivos de trayectoria "
            "(.nc, .mdcrd, .dcd, .trr, .xtc). "
            "Verificá que la simulación tenga archivos de trayectoria."
        )

    topologia = os.path.join(sim.ruta_absoluta, topologia_rel)
    trayectorias = [os.path.join(sim.ruta_absoluta, r) for r in trayectorias_rel]

    # Cargar universo MDAnalysis
    universe = mda.Universe(topologia, *trayectorias)

    n_frames = len(universe.trajectory)
    n_atomos = len(universe.atoms)

    resultados: dict[str, Any] = {
        "simulacion_id": simulacion_id,
        "n_frames": n_frames,
        "n_atomos": n_atomos,
        "topologia_usada": topologia_rel,
        "trayectorias_usadas": trayectorias_rel,
        "metricas_calculadas": [],
        "errores": [],
    }

    # Calcular métricas solicitadas
    if "rmsd" in metricas:
        try:
            rmsd_data = calcular_rmsd(universe)
            _save_metrica(db, simulacion_id, "rmsd", rmsd_data)
            resultados["metricas_calculadas"].append("rmsd")
            resultados["rmsd_resumen"] = {
                "min": min(rmsd_data["rmsd_angstrom"]),
                "max": max(rmsd_data["rmsd_angstrom"]),
                "promedio": sum(rmsd_data["rmsd_angstrom"]) / len(rmsd_data["rmsd_angstrom"]),
            }
        except Exception as exc:
            resultados["errores"].append(f"RMSD: {exc}")

    if "rg" in metricas:
        try:
            rg_data = calcular_radio_de_giro(universe)
            _save_metrica(db, simulacion_id, "rg", rg_data)
            resultados["metricas_calculadas"].append("rg")
            resultados["rg_resumen"] = {
                "min": min(rg_data["rg_angstrom"]),
                "max": max(rg_data["rg_angstrom"]),
                "promedio": sum(rg_data["rg_angstrom"]) / len(rg_data["rg_angstrom"]),
            }
        except Exception as exc:
            resultados["errores"].append(f"Radio de giro: {exc}")

    return resultados
