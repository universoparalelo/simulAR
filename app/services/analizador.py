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
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict[str, Any]:
    """Calcula RMSD cuadro a cuadro respecto al primer frame del rango."""
    atoms = universe.select_atoms(select)
    if len(atoms) == 0:
        atoms = universe.select_atoms("all")
        select = "all"

    start = frame_start or 0
    stop = frame_end if frame_end is not None else len(universe.trajectory)

    rmsd_analysis = rms.RMSD(atoms, select=select)
    rmsd_analysis.run(start=start, stop=stop)

    results = rmsd_analysis.results.rmsd
    return {
        "frames": results[:, 0].tolist(),
        "tiempos_ps": results[:, 1].tolist(),
        "rmsd_angstrom": results[:, 2].tolist(),
    }


def calcular_radio_de_giro(
    universe: "mda.Universe",
    select: str = "all",
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict[str, Any]:
    """Calcula el radio de giro cuadro a cuadro."""
    atoms = universe.select_atoms(select)
    if len(atoms) == 0:
        atoms = universe.select_atoms("all")

    start = frame_start or 0
    stop = frame_end if frame_end is not None else len(universe.trajectory)

    frames, tiempos, rg_values = [], [], []
    for ts in universe.trajectory[start:stop]:
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
    """Crea un nuevo registro de métrica (permite múltiples del mismo tipo)."""
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

def parsear_gaussian_log(log_path: str) -> dict[str, Any]:
    """Extrae métricas de un archivo .log de Gaussian (g09/g16).

    Extrae: energía SCF, método/base, convergencia de optimización,
    frecuencias vibracionales, termodinámica y datos de counterpoise.
    """
    import re

    result: dict[str, Any] = {
        "software": "Gaussian",
        "metodo": None,
        "base": None,
        "energia_hartree": None,
        "energia_kcal_mol": None,
        "convergencia": None,
        "n_pasos_opt": 0,
        "frecuencias_cm1": [],
        "freq_imaginarias": 0,
        "termodinamica": {},
        "counterpoise": {},
        "normal_termination": False,
        "errores_gaussian": [],
    }

    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
    except OSError:
        return result

    if re.search(r"Normal termination of Gaussian", contenido):
        result["normal_termination"] = True

    route_match = re.search(r"#\s*(.+?)(?:\n -+\n)", contenido, re.DOTALL)
    if route_match:
        route_line = route_match.group(1).replace("\n ", " ").strip()
        parts = route_line.split("/", 1)
        if len(parts) == 2:
            method_part = parts[0].split()[-1] if parts[0].split() else parts[0]
            result["metodo"] = method_part.strip()
            base_part = parts[1].split()[0] if parts[1].split() else parts[1]
            result["base"] = base_part.strip()

    scf_matches = re.findall(
        r"SCF Done:\s+E\(\S+\)\s*=\s*([-\d.E+]+)", contenido
    )
    if scf_matches:
        last_energy = float(scf_matches[-1])
        result["energia_hartree"] = last_energy
        result["energia_kcal_mol"] = round(last_energy * 627.5095, 4)
        result["n_pasos_opt"] = len(scf_matches)

    if "Optimization completed" in contenido:
        result["convergencia"] = "completada"
    elif "Optimization stopped" in contenido:
        result["convergencia"] = "no_convergió"
    elif result["n_pasos_opt"] == 1:
        result["convergencia"] = "single_point"

    freq_matches = re.findall(r"Frequencies\s+--\s+([\s\d.-]+)", contenido)
    all_freqs = []
    for match in freq_matches:
        for val in match.split():
            try:
                all_freqs.append(float(val))
            except ValueError:
                pass
    if all_freqs:
        result["frecuencias_cm1"] = all_freqs
        result["freq_imaginarias"] = sum(1 for f in all_freqs if f < 0)

    zpe_match = re.search(r"Zero-point correction=\s+([-\d.]+)", contenido)
    thermal_match = re.search(
        r"Thermal correction to Energy=\s+([-\d.]+)", contenido
    )
    enthalpy_match = re.search(
        r"Thermal correction to Enthalpy=\s+([-\d.]+)", contenido
    )
    gibbs_match = re.search(
        r"Thermal correction to Gibbs Free Energy=\s+([-\d.]+)", contenido
    )
    sum_elec_zpe = re.search(
        r"Sum of electronic and zero-point Energies=\s+([-\d.]+)", contenido
    )
    sum_elec_thermal = re.search(
        r"Sum of electronic and thermal Energies=\s+([-\d.]+)", contenido
    )
    sum_elec_enthalpy = re.search(
        r"Sum of electronic and thermal Enthalpies=\s+([-\d.]+)", contenido
    )
    sum_elec_gibbs = re.search(
        r"Sum of electronic and thermal Free Energies=\s+([-\d.]+)", contenido
    )

    thermo: dict[str, float] = {}
    if zpe_match:
        thermo["zpe_hartree"] = float(zpe_match.group(1))
    if thermal_match:
        thermo["thermal_correction_hartree"] = float(thermal_match.group(1))
    if enthalpy_match:
        thermo["enthalpy_correction_hartree"] = float(enthalpy_match.group(1))
    if gibbs_match:
        thermo["gibbs_correction_hartree"] = float(gibbs_match.group(1))
    if sum_elec_zpe:
        thermo["e_zpe_hartree"] = float(sum_elec_zpe.group(1))
    if sum_elec_thermal:
        thermo["e_thermal_hartree"] = float(sum_elec_thermal.group(1))
    if sum_elec_enthalpy:
        thermo["e_enthalpy_hartree"] = float(sum_elec_enthalpy.group(1))
    if sum_elec_gibbs:
        thermo["e_gibbs_hartree"] = float(sum_elec_gibbs.group(1))
    if thermo:
        result["termodinamica"] = thermo

    cp_corrected = re.search(
        r"Counterpoise corrected energy\s*=\s*([-\d.]+)", contenido
    )
    cp_bsse = re.search(r"BSSE energy\s*=\s*([-\d.]+)", contenido)
    if cp_corrected:
        result["counterpoise"]["energia_corregida_hartree"] = float(
            cp_corrected.group(1)
        )
    if cp_bsse:
        result["counterpoise"]["bsse_hartree"] = float(cp_bsse.group(1))

    dcbs_matches = re.findall(
        r"Counterpoise: doing DCBS calculation for fragment\s+(\d+)",
        contenido,
    )
    for frag_num in dcbs_matches:
        block_pattern = (
            rf"Counterpoise: doing DCBS calculation for fragment\s+{frag_num}"
            r".*?SCF Done:\s+E\(\S+\)\s*=\s*([-\d.E+]+)"
        )
        frag_match = re.search(block_pattern, contenido, re.DOTALL)
        if frag_match:
            result["counterpoise"][f"fragmento_{frag_num}_hartree"] = float(
                frag_match.group(1)
            )

    error_patterns = [
        (r"Convergence failure -- run terminated", "convergence_failure"),
        (r"FormBX had a problem", "formbx_error"),
        (r"Erroneous write", "write_error"),
        (r"galloc:.*could not allocate memory", "memory_error"),
    ]
    for pattern, label in error_patterns:
        if re.search(pattern, contenido):
            result["errores_gaussian"].append(label)

    return result


def parsear_gamess_log(log_path: str) -> dict[str, Any]:
    """Extrae métricas de un archivo .log de GAMESS.

    Extrae: energía SCF, método (DFT funcional), base, RUNTYP,
    descomposición LMOEDA (ES, EX, REP, POL, DISP, total),
    y estado de terminación.
    """
    import re

    result: dict[str, Any] = {
        "software": "GAMESS",
        "metodo": None,
        "base": None,
        "runtyp": None,
        "energia_hartree": None,
        "energia_kcal_mol": None,
        "lmoeda": {},
        "normal_termination": False,
        "errores_gamess": [],
        "n_atoms": None,
        "n_basis": None,
    }

    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
    except OSError:
        return result

    if re.search(r"EXECUTION OF GAMESS TERMINATED NORMALLY", contenido):
        result["normal_termination"] = True

    runtyp_match = re.search(r"RUNTYP=(\S+)", contenido)
    if runtyp_match:
        result["runtyp"] = runtyp_match.group(1)

    dft_match = re.search(r"DFTTYP=(\S+)", contenido)
    if dft_match and dft_match.group(1) != "NONE":
        result["metodo"] = dft_match.group(1)
    else:
        scftyp_match = re.search(r"SCFTYP=(\S+)", contenido)
        if scftyp_match:
            result["metodo"] = scftyp_match.group(1)

    gbasis_match = re.search(r"GBASIS=(\S+)", contenido)
    ngauss_match = re.search(r"IGAUSS=\s*(\d+)", contenido)
    if gbasis_match:
        base_parts = [gbasis_match.group(1)]
        if ngauss_match:
            base_parts.append(f"NGAUSS={ngauss_match.group(1)}")
        ndfunc = re.search(r"NDFUNC=\s*(\d+)", contenido)
        npfunc = re.search(r"NPFUNC=\s*(\d+)", contenido)
        diffsp = re.search(r"DIFFSP=\s*(\S+)", contenido)
        diffs = re.search(r"DIFFS\s*=\s*(\S+)", contenido)
        if ndfunc and int(ndfunc.group(1)) > 0:
            base_parts.append(f"NDFUNC={ndfunc.group(1)}")
        if npfunc and int(npfunc.group(1)) > 0:
            base_parts.append(f"NPFUNC={npfunc.group(1)}")
        if diffsp and diffsp.group(1) == "T":
            base_parts.append("DIFFSP")
        if diffs and diffs.group(1) == "T":
            base_parts.append("DIFFS")
        result["base"] = " ".join(base_parts)

    atoms_match = re.search(r"TOTAL NUMBER OF ATOMS\s*=\s*(\d+)", contenido)
    if atoms_match:
        result["n_atoms"] = int(atoms_match.group(1))

    basis_match = re.search(
        r"NUMBER OF CARTESIAN GAUSSIAN BASIS FUNCTIONS\s*=\s*(\d+)", contenido
    )
    if basis_match:
        result["n_basis"] = int(basis_match.group(1))

    energy_match = re.search(
        r"FINAL (?:RHF|UHF|ROHF|MCSCF|DFT) ENERGY IS\s+([-\d.]+)", contenido
    )
    if energy_match:
        e = float(energy_match.group(1))
        result["energia_hartree"] = e
        result["energia_kcal_mol"] = round(e * 627.5095, 4)

    eda_labels = {
        "ELECTROSTATIC ENERGY": "electrostatica",
        "EXCHANGE ENERGY": "intercambio",
        "REPULSION ENERGY": "repulsion",
        "POLARIZATION ENERGY": "polarizacion",
        "DISPERSION ENERGY": "dispersion",
        "TOTAL INTERACTION ENERGY": "interaccion_total",
    }
    for label, key in eda_labels.items():
        pattern = rf"{re.escape(label)}\s*\(\w+\)?\s*=\s*([-\d.]+)\s+([-\d.]+)"
        match = re.search(pattern, contenido)
        if not match:
            pattern_no_paren = rf"{re.escape(label)}\s*=\s*([-\d.]+)\s+([-\d.]+)"
            match = re.search(pattern_no_paren, contenido)
        if match:
            result["lmoeda"][key] = {
                "hartree": float(match.group(1)),
                "kcal_mol": float(match.group(2)),
            }

    error_patterns = [
        (r"EXECUTION OF GAMESS TERMINATED -ABNORMALLY-", "abnormal_termination"),
        (r"SCF IS UNCONVERGED", "scf_unconverged"),
        (r"ERROR.*MEMORY", "memory_error"),
        (r"THE GEOMETRY SEARCH IS NOT CONVERGED", "geometry_unconverged"),
    ]
    for pattern, label in error_patterns:
        if re.search(pattern, contenido, re.IGNORECASE):
            result["errores_gamess"].append(label)

    return result


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


def calcular_rmsf(
    universe: "mda.Universe",
    select: str = "name CA",
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict[str, Any]:
    """Calcula RMSF por átomo seleccionado (típicamente C-alpha → un valor por residuo)."""
    atoms = universe.select_atoms(select)
    if len(atoms) == 0:
        atoms = universe.select_atoms("name CA")
        if len(atoms) == 0:
            atoms = universe.select_atoms("all")

    start = frame_start or 0
    stop = frame_end if frame_end is not None else len(universe.trajectory)

    rmsf_analysis = rms.RMSF(atoms)
    rmsf_analysis.run(start=start, stop=stop)

    resids = atoms.resids.tolist()
    rmsf_vals = rmsf_analysis.results.rmsf.tolist()

    return {
        "residuos": resids,
        "rmsf_angstrom": rmsf_vals,
    }


def calcular_propiedades_estaticas(universe: "mda.Universe") -> dict[str, Any]:
    """Calcula propiedades estáticas de una estructura (sin trayectoria)."""
    atoms = universe.select_atoms("all")
    return {
        "n_moleculas": len(universe.residues),
        "rg_angstrom": float(atoms.radius_of_gyration()),
        "masa_total_uma": float(atoms.total_mass()),
    }


# ---------------------------------------------------------------------------
# Análisis de simulaciones Gaussian
# ---------------------------------------------------------------------------

def _analizar_gaussian(
    db: Session,
    sim: Simulacion,
    archivos: list[Archivo],
) -> dict[str, Any]:
    """Analiza archivos .log de Gaussian y persiste métricas."""
    log_files = [
        a.nombre_archivo for a in archivos
        if (a.extension or "").lower() == ".log"
    ]

    resultados: dict[str, Any] = {
        "simulacion_id": sim.id,
        "modo": "gaussian",
        "motor_analisis": "regex_parser",
        "metricas_calculadas": [],
        "errores": [],
        "advertencias": [],
        "logs_analizados": [],
    }

    if not log_files:
        raise ValueError(
            "No se encontraron archivos .log de Gaussian para analizar."
        )

    for log_rel in log_files:
        log_path = os.path.join(sim.ruta_absoluta, log_rel)
        try:
            datos = parsear_gaussian_log(log_path)
        except Exception as exc:
            resultados["errores"].append(f"{log_rel}: {exc}")
            continue

        if datos["energia_hartree"] is None:
            resultados["advertencias"].append(
                f"{log_rel}: no se encontró energía SCF"
            )
            continue

        datos["archivo"] = log_rel
        _save_metrica(db, sim.id, "gaussian_log", datos)
        resultados["metricas_calculadas"].append(f"gaussian_log:{log_rel}")
        resultados["logs_analizados"].append(log_rel)

    if not resultados["logs_analizados"]:
        raise ValueError(
            "No se pudo extraer energía de ningún archivo .log de Gaussian."
        )

    return resultados


# ---------------------------------------------------------------------------
# Análisis de simulaciones GAMESS
# ---------------------------------------------------------------------------

def _analizar_gamess(
    db: Session,
    sim: Simulacion,
    archivos: list[Archivo],
) -> dict[str, Any]:
    """Analiza archivos .log de GAMESS y persiste métricas."""
    log_files = [
        a.nombre_archivo for a in archivos
        if (a.extension or "").lower() in (".log", ".out")
    ]

    resultados: dict[str, Any] = {
        "simulacion_id": sim.id,
        "modo": "gamess",
        "motor_analisis": "regex_parser",
        "metricas_calculadas": [],
        "errores": [],
        "advertencias": [],
        "logs_analizados": [],
    }

    if not log_files:
        raise ValueError(
            "No se encontraron archivos .log/.out de GAMESS para analizar."
        )

    for log_rel in log_files:
        log_path = os.path.join(sim.ruta_absoluta, log_rel)
        try:
            datos = parsear_gamess_log(log_path)
        except Exception as exc:
            resultados["errores"].append(f"{log_rel}: {exc}")
            continue

        if datos["energia_hartree"] is None and not datos["lmoeda"]:
            resultados["advertencias"].append(
                f"{log_rel}: no se encontró energía ni datos EDA"
            )
            continue

        datos["archivo"] = log_rel
        _save_metrica(db, sim.id, "gamess_log", datos)
        resultados["metricas_calculadas"].append(f"gamess_log:{log_rel}")
        resultados["logs_analizados"].append(log_rel)

    if not resultados["logs_analizados"]:
        raise ValueError(
            "No se pudo extraer datos de ningún archivo .log de GAMESS."
        )

    return resultados


# ---------------------------------------------------------------------------
# Función principal de análisis
# ---------------------------------------------------------------------------

def analizar_simulacion(
    db: Session,
    simulacion_id: int,
    metricas: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """
    Analiza una simulación y guarda las métricas en la DB.

    Args:
        db: Sesión de base de datos.
        simulacion_id: ID de la simulación a analizar.
        metricas: Dict de métrica → config. Cada config puede tener:
                  atom_selection (str), frame_start (int|None), frame_end (int|None).
                  Default: {"rmsd": {"atom_selection": "backbone"}, "rg": {"atom_selection": "all"}}
    """
    if metricas is None:
        metricas = {
            "rmsf": {"atom_selection": "name CA"},
        }

    sim: Optional[Simulacion] = db.query(Simulacion).filter_by(id=simulacion_id).first()
    if sim is None:
        raise ValueError(f"Simulación {simulacion_id} no encontrada en la DB.")

    if not os.path.isdir(sim.ruta_absoluta):
        raise FileNotFoundError(f"El directorio ya no existe: {sim.ruta_absoluta}")

    archivos: list[Archivo] = sim.archivos

    # --- Gaussian: parsear .log directamente, no usa MDAnalysis ---
    if (sim.software or "").lower() == "gaussian":
        return _analizar_gaussian(db, sim, archivos)

    # --- GAMESS: parsear .log directamente, no usa MDAnalysis ---
    if (sim.software or "").lower() == "gamess":
        return _analizar_gamess(db, sim, archivos)

    if not MDA_AVAILABLE:
        raise ValueError(
            "MDAnalysis no está instalado. "
            "Ejecutá: pip install MDAnalysis"
        )

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

    # --- RMSF (solo con trayectoria) ---
    if tiene_trayectoria and "rmsf" in metricas:
        cfg = metricas["rmsf"]
        sel = cfg.get("atom_selection", "name CA")
        fs = cfg.get("frame_start")
        fe = cfg.get("frame_end")
        try:
            rmsf_data = calcular_rmsf(universe, select=sel, frame_start=fs, frame_end=fe)
            rmsf_data["config"] = {"atom_selection": sel, "frame_start": fs, "frame_end": fe}
            _save_metrica(db, simulacion_id, "rmsf", rmsf_data)
            resultados["metricas_calculadas"].append("rmsf")
            vals = rmsf_data["rmsf_angstrom"]
            resultados["rmsf_resumen"] = {
                "min": min(vals),
                "max": max(vals),
                "promedio": sum(vals) / len(vals),
            }
        except Exception as exc:
            resultados["errores"].append(f"RMSF: {exc}")

    # --- RMSD (solo con trayectoria) ---
    if tiene_trayectoria and "rmsd" in metricas:
        cfg = metricas["rmsd"]
        sel = cfg.get("atom_selection", "backbone")
        fs = cfg.get("frame_start")
        fe = cfg.get("frame_end")
        try:
            if usar_cpp:
                with tempfile.TemporaryDirectory() as tmpdir:
                    rmsd_data = calcular_rmsd_cpptraj(topologia, trayectorias, tmpdir)
            else:
                rmsd_data = calcular_rmsd(universe, select=sel, frame_start=fs, frame_end=fe)
            rmsd_data["config"] = {"atom_selection": sel, "frame_start": fs, "frame_end": fe}
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
        cfg = metricas["rg"]
        sel = cfg.get("atom_selection", "all")
        fs = cfg.get("frame_start")
        fe = cfg.get("frame_end")
        try:
            if usar_cpp:
                with tempfile.TemporaryDirectory() as tmpdir:
                    rg_data = calcular_rg_cpptraj(topologia, trayectorias, tmpdir)
            else:
                rg_data = calcular_radio_de_giro(universe, select=sel, frame_start=fs, frame_end=fe)
            rg_data["config"] = {"atom_selection": sel, "frame_start": fs, "frame_end": fe}
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
    metricas: dict[str, dict] | None = None,
) -> None:
    """Corre `analizar_simulacion` en background con sesión propia."""
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
