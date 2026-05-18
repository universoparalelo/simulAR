"""
Script de ejemplo para usar los módulos de simulAR sin la interfaz gráfica.
Útil para testing y automatización.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from analysis import AnalysisModule
from database import SimulationDatabase
from excel_export import ExcelExporter
from simulation_manager import SimulationManager


def example_basic_workflow():
    """Ejemplo 1: Flujo básico de uso."""
    print("=== EJEMPLO 1: Flujo Básico ===\n")

    # Inicializar base de datos
    db = SimulationDatabase("data/simulations_example.db")
    print("✓ Base de datos inicializada")

    # Crear una simulación de ejemplo
    sim_id = db.add_simulation(
        title="Simulación de Prueba",
        program="AMBER",
        path="/path/to/simulation",
        date="2024-01-15T10:30:00",
        size_bytes=5 * 1024 * 1024,  # 5 MB
        description="Simulación de ejemplo para testing",
    )
    print(f"✓ Simulación agregada con ID: {sim_id}")

    # Agregar archivos
    files = [
        {
            "filename": "trajectory.dcd",
            "file_path": "/path/to/trajectory.dcd",
            "size_bytes": 3 * 1024 * 1024,
            "file_type": ".dcd",
        },
        {
            "filename": "output.log",
            "file_path": "/path/to/output.log",
            "size_bytes": 1 * 1024 * 1024,
            "file_type": ".log",
        },
        {
            "filename": "structure.pdb",
            "file_path": "/path/to/structure.pdb",
            "size_bytes": 500 * 1024,
            "file_type": ".pdb",
        },
    ]
    db.add_simulation_files(sim_id, files)
    print("✓ Archivos agregados")

    # Agregar métricas
    db.add_metric(sim_id, "RMSD", 2.5, "Å")
    db.add_metric(sim_id, "Rg", 15.3, "Å")
    print("✓ Métricas agregadas")

    # Recuperar simulaciones
    simulations = db.get_all_simulations()
    print(f"✓ Total de simulaciones: {len(simulations)}")

    # Obtener información de una simulación
    sim = db.get_simulation_by_id(sim_id)
    print(f"\nInformación de la simulación:")
    print(f"  Título: {sim['title']}")
    print(f"  Programa: {sim['program']}")
    print(f"  Tamaño: {SimulationManager.get_file_size_readable(sim['size_bytes'])}")

    return sim_id


def example_file_analysis(sim_id):
    """Ejemplo 2: Análisis de archivos."""
    print("\n=== EJEMPLO 2: Análisis de Archivos ===\n")

    db = SimulationDatabase("data/simulations_example.db")

    # Obtener archivos de la simulación
    files = db.get_simulation_files(sim_id)
    print(f"✓ Archivos encontrados: {len(files)}")

    # Calcular estadísticas
    stats = AnalysisModule.calculate_file_statistics(files)
    print(f"\nEstadísticas de archivos:")
    print(f"  Total de archivos: {stats['total_files']}")
    print(f"  Tamaño total: {stats['total_size_mb']:.2f} MB")
    print(
        f"  Archivo más grande: {stats['largest_file']['name']} ({stats['largest_file']['size_mb']:.2f} MB)"
    )

    # Identificar archivos redundantes
    redundant = AnalysisModule.identify_redundant_files(files)
    print(f"\nArchivos redundantes encontrados: {len(redundant)}")
    for f in redundant:
        print(f"  - {f['filename']}: {f['reason']}")


def example_excel_export(sim_id):
    """Ejemplo 3: Exportación a Excel."""
    print("\n=== EJEMPLO 3: Exportación a Excel ===\n")

    db = SimulationDatabase("data/simulations_example.db")

    # Obtener información completa de la simulación
    sim = db.get_simulation_by_id(sim_id)
    files = db.get_simulation_files(sim_id)
    metrics = db.get_metrics(sim_id)

    # Crear datos para exportar
    sim_data = {**sim, "files": files, "metrics": metrics}

    # Exportar a Excel
    filepath = ExcelExporter.export_simulation(sim_data, ".")
    print(f"✓ Simulación exportada a: {filepath}")


def example_directory_scan():
    """Ejemplo 4: Escanear directorio para simulaciones."""
    print("\n=== EJEMPLO 4: Escanear Directorio ===\n")

    # Escanear un directorio (cambiar ruta según sea necesario)
    directory = "."

    simulations = SimulationManager.scan_directory(directory)

    if simulations:
        print(f"✓ Simulaciones encontradas: {len(simulations)}\n")
        for sim in simulations[:3]:  # Mostrar las primeras 3
            print(f"  Título: {sim['title']}")
            print(f"  Programa: {sim['program']}")
            print(
                f"  Tamaño: {SimulationManager.get_file_size_readable(sim['size_bytes'])}"
            )
            print(f"  Archivos: {len(sim['files'])}\n")
    else:
        print("✗ No se encontraron simulaciones en el directorio")


def main():
    """Ejecutar ejemplos."""
    print("\n" + "=" * 50)
    print("  simulAR - Ejemplos de Uso")
    print("=" * 50 + "\n")

    try:
        # Ejecutar ejemplos
        sim_id = example_basic_workflow()
        example_file_analysis(sim_id)
        example_excel_export(sim_id)
        example_directory_scan()

        print("\n" + "=" * 50)
        print("  ✓ Todos los ejemplos completados exitosamente")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"\n✗ Error durante la ejecución: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
