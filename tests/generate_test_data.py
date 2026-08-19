"""Genera simulaciones moleculares de prueba realistas para testear simulAR.

Crea 3 carpetas en simulaciones/:
  1. amber_md_alanina     — dinámica molecular AMBER con trayectoria .nc
  2. amber_min_proteina   — minimización de energía AMBER (sin trayectoria)
  3. gromacs_md_lisozima   — dinámica molecular GROMACS con trayectoria .xtc

Cada carpeta contiene archivos válidos que MDAnalysis puede leer, con tamaños
moderados (10-50 MB) para estresar el pipeline sin necesitar GB.
"""

import os
import struct
import sys
import textwrap

import numpy as np

try:
    import MDAnalysis as mda
except ImportError:
    print("ERROR: MDAnalysis no esta instalado. Activar el venv del proyecto.")
    sys.exit(1)


ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simulaciones")


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# 1. AMBER Dinámica Molecular — trayectoria .nc con muchos frames
# ---------------------------------------------------------------------------

def gen_amber_md():
    sim_dir = ensure_dir(os.path.join(ROOT, "amber_md_alanina"))
    n_atoms = 500
    n_frames = 2000
    n_residues = 50

    # Generar topología PDB (MDAnalysis la puede leer como topología)
    pdb_path = os.path.join(sim_dir, "sistema.pdb")
    _write_pdb(pdb_path, n_atoms, n_residues)

    # Generar prmtop vacío pero con extensión correcta para detección AMBER
    prmtop_path = os.path.join(sim_dir, "sistema.prmtop")
    _write_amber_prmtop(prmtop_path, n_atoms)

    # Generar trayectoria NetCDF (.nc)
    nc_path = os.path.join(sim_dir, "trayectoria.nc")
    _write_netcdf_trajectory(nc_path, n_atoms, n_frames, pdb_path)

    # Archivos auxiliares realistas
    _write_file(os.path.join(sim_dir, "md.mdin"), textwrap.dedent("""\
        Molecular dynamics production run
        &cntrl
          imin=0, irest=1, ntx=5,
          nstlim=500000, dt=0.002,
          ntc=2, ntf=2,
          cut=10.0,
          ntpr=500, ntwx=500, ntwr=5000,
          ntt=3, gamma_ln=2.0,
          temp0=300.0,
          ntp=1, barostat=2,
          iwrap=1,
        /
    """))

    _write_file(os.path.join(sim_dir, "md.out"), _gen_amber_md_output(n_frames))

    _write_file(os.path.join(sim_dir, "sistema.rst"), "restart file placeholder")

    size_mb = sum(
        os.path.getsize(os.path.join(sim_dir, f))
        for f in os.listdir(sim_dir)
    ) / (1024 * 1024)
    print(f"  amber_md_alanina: {n_atoms} atomos, {n_frames} frames, {size_mb:.1f} MB total")


# ---------------------------------------------------------------------------
# 2. AMBER Minimización — sin trayectoria, con curva de energía en .out
# ---------------------------------------------------------------------------

def gen_amber_min():
    sim_dir = ensure_dir(os.path.join(ROOT, "amber_min_proteina"))
    n_atoms = 800
    n_residues = 80

    pdb_path = os.path.join(sim_dir, "proteina.pdb")
    _write_pdb(pdb_path, n_atoms, n_residues)

    prmtop_path = os.path.join(sim_dir, "proteina.prmtop")
    _write_amber_prmtop(prmtop_path, n_atoms)

    # Coordenadas iniciales .inpcrd
    inpcrd_path = os.path.join(sim_dir, "proteina.inpcrd")
    _write_amber_inpcrd(inpcrd_path, n_atoms)

    # Archivo restart .rst
    rst_path = os.path.join(sim_dir, "minimizacion.rst")
    _write_amber_inpcrd(rst_path, n_atoms)

    _write_file(os.path.join(sim_dir, "min.mdin"), textwrap.dedent("""\
        Energy minimization
        &cntrl
          imin=1,
          maxcyc=5000, ncyc=2500,
          ntb=1,
          cut=10.0,
          ntpr=100,
          ntr=1, restraintmask='@CA',
          restraint_wt=2.0,
        /
    """))

    _write_file(os.path.join(sim_dir, "min.out"), _gen_amber_min_output())

    size_mb = sum(
        os.path.getsize(os.path.join(sim_dir, f))
        for f in os.listdir(sim_dir)
    ) / (1024 * 1024)
    print(f"  amber_min_proteina: {n_atoms} atomos, sin trayectoria, {size_mb:.1f} MB total")


# ---------------------------------------------------------------------------
# 3. GROMACS Dinámica Molecular — .gro + .xtc
# ---------------------------------------------------------------------------

def gen_gromacs_md():
    sim_dir = ensure_dir(os.path.join(ROOT, "gromacs_md_lisozima"))
    n_atoms = 600
    n_frames = 1500
    n_residues = 60

    gro_path = os.path.join(sim_dir, "sistema.gro")
    _write_gro(gro_path, n_atoms, n_residues)

    xtc_path = os.path.join(sim_dir, "trayectoria.xtc")
    _write_xtc_trajectory(xtc_path, n_atoms, n_frames, gro_path)

    _write_file(os.path.join(sim_dir, "topol.top"), textwrap.dedent("""\
        ; GROMACS topology file
        [ defaults ]
        1   2   yes   0.5   0.8333

        [ moleculetype ]
        Protein   3

        [ system ]
        Protein in water

        [ molecules ]
        Protein   1
        SOL       5000
    """))

    _write_file(os.path.join(sim_dir, "md.mdp"), textwrap.dedent("""\
        integrator  = md
        dt          = 0.002
        nsteps      = 500000
        nstxout-compressed = 500
        nstlog      = 1000
        nstenergy   = 1000
        tcoupl      = V-rescale
        ref-t       = 300
        pcoupl      = Parrinello-Rahman
        ref-p       = 1.0
        cutoff-scheme = Verlet
        coulombtype  = PME
        rcoulomb     = 1.0
        rvdw         = 1.0
    """))

    _write_file(os.path.join(sim_dir, "md.log"), _gen_gromacs_log())

    size_mb = sum(
        os.path.getsize(os.path.join(sim_dir, f))
        for f in os.listdir(sim_dir)
    ) / (1024 * 1024)
    print(f"  gromacs_md_lisozima: {n_atoms} atomos, {n_frames} frames, {size_mb:.1f} MB total")


# ===========================================================================
# Generadores de archivos
# ===========================================================================

def _write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_pdb(path: str, n_atoms: int, n_residues: int):
    """Genera un PDB sintético con coordenadas aleatorias pero formato válido."""
    rng = np.random.default_rng(42)
    res_names = ["ALA", "GLY", "LEU", "VAL", "ILE", "PRO", "PHE", "SER", "THR", "ASP"]
    atom_names = ["N", "CA", "C", "O", "CB"]

    with open(path, "w") as f:
        f.write("TITLE     Synthetic test system for simulAR\n")
        f.write("MODEL        1\n")
        for i in range(n_atoms):
            res_idx = (i // 5) % n_residues + 1
            res_name = res_names[res_idx % len(res_names)]
            atom_name = atom_names[i % len(atom_names)]
            x, y, z = rng.uniform(0, 50, 3)
            f.write(
                f"ATOM  {i+1:5d} {atom_name:<4s} {res_name:3s} A{res_idx:4d}    "
                f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           "
                f"{atom_name[0]:>2s}\n"
            )
        f.write("ENDMDL\nEND\n")


def _write_gro(path: str, n_atoms: int, n_residues: int):
    """Genera un archivo .gro (GROMACS) sintético."""
    rng = np.random.default_rng(123)
    res_names = ["ALA", "GLY", "LEU", "VAL", "ILE"]
    atom_names = ["N", "CA", "C", "O", "CB"]

    with open(path, "w") as f:
        f.write("Synthetic GROMACS system for simulAR\n")
        f.write(f"{n_atoms}\n")
        for i in range(n_atoms):
            res_idx = (i // 5) % n_residues + 1
            res_name = res_names[res_idx % len(res_names)]
            atom_name = atom_names[i % len(atom_names)]
            x, y, z = rng.uniform(0, 5.0, 3)
            f.write(
                f"{res_idx:5d}{res_name:<5s}{atom_name:>5s}{i+1:5d}"
                f"{x:8.3f}{y:8.3f}{z:8.3f}\n"
            )
        f.write("   5.00000   5.00000   5.00000\n")


def _write_amber_prmtop(path: str, n_atoms: int):
    """Genera un archivo .prmtop mínimo válido para detección de AMBER."""
    with open(path, "w") as f:
        f.write("%VERSION  VERSION_STAMP = V0001.000  DATE = 01/01/24\n")
        f.write("%FLAG TITLE\n")
        f.write("%FORMAT(20a4)\n")
        f.write("Synthetic AMBER topology\n")
        f.write("%FLAG POINTERS\n")
        f.write("%FORMAT(10I8)\n")
        f.write(f"{n_atoms:8d}" + "       0" * 9 + "\n")
        f.write("       0" * 10 + "\n")
        f.write("       0" * 10 + "\n")
        f.write("       0" * 1 + "\n")


def _write_amber_inpcrd(path: str, n_atoms: int):
    """Genera un archivo .inpcrd de AMBER con coordenadas aleatorias."""
    rng = np.random.default_rng(99)
    with open(path, "w") as f:
        f.write("Synthetic coordinates\n")
        f.write(f"{n_atoms:6d}\n")
        coords = rng.uniform(0, 50, n_atoms * 3)
        for i in range(0, len(coords), 6):
            chunk = coords[i:i+6]
            f.write("".join(f"{c:12.7f}" for c in chunk) + "\n")


def _write_netcdf_trajectory(nc_path: str, n_atoms: int, n_frames: int, pdb_path: str):
    """Genera una trayectoria NetCDF (.nc) de AMBER usando MDAnalysis."""
    u = mda.Universe(pdb_path)
    rng = np.random.default_rng(77)

    base_coords = u.atoms.positions.copy()

    with mda.Writer(nc_path, n_atoms=n_atoms, format="NCDF") as w:
        for frame_i in range(n_frames):
            drift = rng.normal(0, 0.1, base_coords.shape).astype(np.float32)
            u.atoms.positions = base_coords + drift * (frame_i * 0.01)
            u.trajectory.ts.time = frame_i * 2.0  # 2 ps per frame
            w.write(u.atoms)


def _write_xtc_trajectory(xtc_path: str, n_atoms: int, n_frames: int, gro_path: str):
    """Genera una trayectoria .xtc (GROMACS) usando MDAnalysis."""
    u = mda.Universe(gro_path)
    rng = np.random.default_rng(55)

    base_coords = u.atoms.positions.copy()

    with mda.Writer(xtc_path, n_atoms=n_atoms) as w:
        for frame_i in range(n_frames):
            drift = rng.normal(0, 0.05, base_coords.shape).astype(np.float32)
            u.atoms.positions = base_coords + drift * (frame_i * 0.005)
            u.trajectory.ts.time = frame_i * 2.0
            w.write(u.atoms)


# ---------------------------------------------------------------------------
# Generadores de archivos de salida (texto realista)
# ---------------------------------------------------------------------------

def _gen_amber_md_output(n_frames: int) -> str:
    """Genera un .out de MD de AMBER con datos realistas."""
    lines = []
    lines.append("          -------------------------------------------------------")
    lines.append("          Amber 22 SANDER                              2024")
    lines.append("          -------------------------------------------------------")
    lines.append("")
    lines.append("   NSTEP       ENERGY          RMS            GMAX")
    lines.append("")

    rng = np.random.default_rng(33)
    energy = -15000.0
    for step in range(0, n_frames * 250, 500):
        energy += rng.normal(-0.5, 2.0)
        temp = 300.0 + rng.normal(0, 5)
        lines.append(f" NSTEP = {step:8d}   TIME(PS) = {step*0.002:12.3f}")
        lines.append(f" Etot   = {energy:14.4f}  EKtot   = {temp*0.5:14.4f}")
        lines.append(f" TEMP(K) = {temp:8.2f}  PRESS = {rng.normal(1, 50):10.1f}")
        lines.append("")

    return "\n".join(lines)


def _gen_amber_min_output() -> str:
    """Genera un .out de minimización de AMBER con curva de energía parseeable."""
    lines = []
    lines.append("          -------------------------------------------------------")
    lines.append("          Amber 22 SANDER                              2024")
    lines.append("          -------------------------------------------------------")
    lines.append("")
    lines.append("   NSTEP       ENERGY          RMS            GMAX         NAME    NUMBER")
    lines.append("      1      -1.0000E+04      1.0000E+01      5.0000E+01     CA        123")
    lines.append("")
    lines.append("   FINAL RESULTS")
    lines.append("")

    rng = np.random.default_rng(44)
    energy = -8000.0
    rms_grad = 100.0

    for step in range(0, 5001, 100):
        energy -= rng.uniform(5, 50)
        rms_grad *= 0.92
        lines.append(f"   {step:5d}   {energy:15.4f}   {rms_grad:15.4f}")

    lines.append("")
    lines.append("   Maximum number of minimization cycles reached.")
    return "\n".join(lines)


def _gen_gromacs_log() -> str:
    """Genera un .log de GROMACS realista."""
    lines = []
    lines.append("                      :-) GROMACS - gmx mdrun, 2023.3 (-:")
    lines.append("")
    lines.append("Executable:   /usr/local/bin/gmx")
    lines.append("Data prefix:  /usr/local")
    lines.append("")
    lines.append("GROMACS version:    2023.3")
    lines.append("")

    rng = np.random.default_rng(66)
    for step in range(0, 500001, 1000):
        energy = -50000 + rng.normal(0, 100)
        temp = 300 + rng.normal(0, 3)
        lines.append(f"           Step           Time")
        lines.append(f"       {step:8d}    {step*0.002:12.5f}")
        lines.append(f"   Energies (kJ/mol)")
        lines.append(f"      Potential    Kinetic En.   Total Energy    Temperature")
        lines.append(f"  {energy:14.5e}  {temp*100:14.5e}  {energy+temp*100:14.5e}  {temp:14.5e}")
        lines.append("")

    return "\n".join(lines)


# ===========================================================================

if __name__ == "__main__":
    print(f"Generando simulaciones de prueba en: {ROOT}")
    print()
    gen_amber_md()
    gen_amber_min()
    gen_gromacs_md()
    print()
    print("Listo. Las 3 simulaciones estan en simulaciones/")
