"""
Crea una simulación sintética con trayectoria para testear RMSD y Rg.
Genera: peptido_test.pdb (topología) + trayectoria.dcd (50 frames)
Registra la simulación en la DB y ejecuta el análisis.
"""

import os
import sys
import shutil
import numpy as np

# Asegurar que el path de la app esté disponible
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.models.simulacion
import app.models.metrica

import MDAnalysis as mda
from MDAnalysis.analysis import rms

from app.database import SessionLocal, init_db
from app.models.simulacion import Simulacion, Archivo
from app.services.analizador import analizar_simulacion

# ---------------------------------------------------------------------------
# 1. Crear carpeta de destino
# ---------------------------------------------------------------------------
DEST = os.path.join(
    os.path.dirname(__file__), "..", "data", "uploads", "sim_test_trayectoria"
)
DEST = os.path.abspath(DEST)
os.makedirs(DEST, exist_ok=True)
print(f"Carpeta de simulación: {DEST}")

# ---------------------------------------------------------------------------
# 2. Generar PDB de topología (péptido de 10 aminoácidos ~80 átomos backbone)
# ---------------------------------------------------------------------------
N_RESIDUES = 10
N_ATOMS_PER_RES = 4  # N, CA, C, O
N_ATOMS = N_RESIDUES * N_ATOMS_PER_RES

pdb_path = os.path.join(DEST, "peptido_test.pdb")

rng = np.random.default_rng(42)

# Coordenadas iniciales en hélice alpha simplificada
coords_init = []
for i in range(N_ATOMS):
    angle = i * 0.4
    x = 2.0 * np.cos(angle)
    y = 2.0 * np.sin(angle)
    z = i * 1.5
    coords_init.append([x, y, z])
coords_init = np.array(coords_init, dtype=np.float32)

atom_names = ["N", "CA", "C", "O"] * N_RESIDUES
resnames = ["ALA"] * N_ATOMS

with open(pdb_path, "w") as f:
    for i, (name, resname, xyz) in enumerate(zip(atom_names, resnames, coords_init)):
        res_id = i // N_ATOMS_PER_RES + 1
        f.write(
            f"ATOM  {i+1:5d} {name:<4s} {resname:3s} A{res_id:4d}    "
            f"{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00  0.00           C\n"
        )
    f.write("END\n")

print(f"PDB generado: {pdb_path} ({N_ATOMS} átomos, {N_RESIDUES} residuos)")

# ---------------------------------------------------------------------------
# 3. Generar trayectoria DCD (50 frames con movimiento aleatorio acumulado)
# ---------------------------------------------------------------------------
N_FRAMES = 50
dcd_path = os.path.join(DEST, "trayectoria.dcd")

u = mda.Universe(pdb_path)
all_atoms = u.select_atoms("all")

with mda.Writer(dcd_path, n_atoms=N_ATOMS) as writer:
    displacement = np.zeros((N_ATOMS, 3), dtype=np.float32)
    for frame in range(N_FRAMES):
        # Movimiento browniano acumulado (simula fluctuaciones térmicas)
        displacement += rng.normal(0, 0.1, (N_ATOMS, 3)).astype(np.float32)
        # Deriva lenta (simula cambio conformacional)
        drift = np.sin(frame * 0.1) * 0.3
        all_atoms.positions = coords_init + displacement + drift
        writer.write(all_atoms)

print(f"Trayectoria DCD generada: {dcd_path} ({N_FRAMES} frames)")

# ---------------------------------------------------------------------------
# 4. Registrar en la DB
# ---------------------------------------------------------------------------
init_db()
db = SessionLocal()

# Eliminar simulación anterior del mismo test si existe
existing = db.query(Simulacion).filter_by(ruta_absoluta=DEST).first()
if existing:
    db.query(app.models.metrica.ResultadoMetrica).filter_by(
        simulacion_id=existing.id
    ).delete()
    db.query(Archivo).filter_by(simulacion_id=existing.id).delete()
    db.delete(existing)
    db.commit()
    print("Simulación anterior eliminada de la DB")

import json, time

sim = Simulacion(
    nombre="sim_test_trayectoria",
    ruta_absoluta=DEST,
    software="AMBER",
    metadata_json=json.dumps({"total_bytes": 0, "nota": "simulación sintética para testing"}),
)
db.add(sim)
db.commit()
db.refresh(sim)
print(f"Simulación registrada con id={sim.id}")

archivos = [
    Archivo(
        nombre_archivo="peptido_test.pdb",
        extension=".pdb",
        tamano_bytes=os.path.getsize(pdb_path),
        tipo="topologia",
        simulacion_id=sim.id,
    ),
    Archivo(
        nombre_archivo="trayectoria.dcd",
        extension=".dcd",
        tamano_bytes=os.path.getsize(dcd_path),
        tipo="trayectoria",
        simulacion_id=sim.id,
    ),
]
for a in archivos:
    db.add(a)
db.commit()
print(f"Archivos registrados: peptido_test.pdb, trayectoria.dcd")

# ---------------------------------------------------------------------------
# 5. Ejecutar análisis (RMSD + Rg)
# ---------------------------------------------------------------------------
print("\n--- Ejecutando análisis ---")
resultado = analizar_simulacion(db, sim.id, metricas=["rmsd", "rg"])

print(f"Modo: {resultado['modo']}")
print(f"Frames: {resultado['n_frames']}")
print(f"Átomos: {resultado['n_atomos']}")
print(f"Métricas calculadas: {resultado['metricas_calculadas']}")
print(f"Errores: {resultado['errores']}")

if "rmsd_resumen" in resultado:
    r = resultado["rmsd_resumen"]
    print(f"\nRMSD:")
    print(f"  min:      {r['min']:.4f} Å")
    print(f"  max:      {r['max']:.4f} Å")
    print(f"  promedio: {r['promedio']:.4f} Å")

if "rg_resumen" in resultado:
    r = resultado["rg_resumen"]
    print(f"\nRadio de giro:")
    print(f"  min:      {r['min']:.4f} Å")
    print(f"  max:      {r['max']:.4f} Å")
    print(f"  promedio: {r['promedio']:.4f} Å")

# ---------------------------------------------------------------------------
# 6. Verificar en DB
# ---------------------------------------------------------------------------
metricas_db = (
    db.query(app.models.metrica.ResultadoMetrica)
    .filter_by(simulacion_id=sim.id)
    .all()
)
print(f"\nMétricas almacenadas en DB: {[m.tipo_metrica for m in metricas_db]}")
for m in metricas_db:
    datos = json.loads(m.valores_tiempo_json)
    if "frames" in datos:
        print(f"  {m.tipo_metrica}: {len(datos['frames'])} frames registrados")

db.close()
print(f"\nSimulación de test disponible con id={sim.id}")
print("Podés consultarla en: http://127.0.0.1:8000/simulaciones/" + str(sim.id))
