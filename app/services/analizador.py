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
    topologia_rel = _find_topology(archivos)
    trayectorias_rel = _find_trajectories(archivos)
    out_files = [
        a.nombre_archivo for a in archivos
        if (a.extension or "").lower() == ".out"
    ]

    if topologia_rel is None:
        raise ValueError(
            "No se encontró archivo de topología compatible "
            "(.prmtop, .pdb, .gro, .top, .psf)."
        )

    topologia = os.path.join(sim.ruta_absoluta, topologia_rel)

    # Detectar modo: con trayectoria (MD) o sin ella (minimización / estructura estática)
    tiene_trayectoria = bool(trayectorias_rel)
    trayectorias = [os.path.join(sim.ruta_absoluta, r) for r in trayectorias_rel]

    # Formatos explícitos por extensión para MDAnalysis
    _MDA_FORMAT: dict[str, str] = {
        ".inpcrd": "INPCRD",
        ".rst": "RESTRT",
        ".rst7": "RESTRT",
        ".ncrst": "RESTRT",
        ".gro": "GRO",
    }

    if tiene_trayectoria:
        universe = mda.Universe(topologia, *trayectorias)
    else:
        # Preferir inpcrd > rst7/ncrst > rst > gro (orden de confiabilidad)
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
                topologia,
                os.path.join(sim.ruta_absoluta, coord_rel),
                format=coord_fmt,
            )
        else:
            universe = mda.Universe(topologia)

    n_frames = len(universe.trajectory)
    n_atomos = len(universe.atoms)

    resultados: dict[str, Any] = {
        "simulacion_id": simulacion_id,
        "modo": "dinamica" if tiene_trayectoria else "minimizacion_o_estatico",
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
            "No se encontró trayectoria (.nc, .mdcrd, .xtc). "
            "RMSD y Rg temporal no están disponibles. "
            "Se calcularon propiedades estáticas y energía de minimización."
        )

    # --- Propiedades estáticas (siempre disponibles) ---
    try:
        props = calcular_propiedades_estaticas(universe)
        _save_metrica(db, simulacion_id, "propiedades_estaticas", props)
        resultados["metricas_calculadas"].append("propiedades_estaticas")
        resultados["propiedades_estaticas"] = props
    except Exception as exc:
        resultados["errores"].append(f"Propiedades estáticas: {exc}")

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
            resultados["errores"].append(f"Energía minimización: {exc}")

    # --- RMSD (solo con trayectoria) ---
    if tiene_trayectoria and "rmsd" in metricas:
        try:
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
