"""
Pruebas básicas para los módulos de simulAR.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import unittest
from pathlib import Path

from analysis import AnalysisModule
from excel_export import ExcelExporter
from simulation_manager import SimulationManager


class TestSimulationManager(unittest.TestCase):
    """Pruebas del gestor de simulaciones."""

    def test_file_size_readable(self):
        """Prueba conversión de bytes a formato legible."""
        self.assertEqual(SimulationManager.get_file_size_readable(512), "512.00 B")
        self.assertEqual(SimulationManager.get_file_size_readable(1024), "1.00 KB")
        self.assertEqual(
            SimulationManager.get_file_size_readable(1024 * 1024), "1.00 MB"
        )
        self.assertEqual(
            SimulationManager.get_file_size_readable(1024 * 1024 * 1024), "1.00 GB"
        )

    def test_file_type_category(self):
        """Prueba categorización de tipos de archivo."""
        self.assertEqual(
            SimulationManager.get_file_type_category(".dcd"), "Trayectoria"
        )
        self.assertEqual(SimulationManager.get_file_type_category(".log"), "Salida")
        self.assertEqual(SimulationManager.get_file_type_category(".pdb"), "Estructura")
        self.assertEqual(SimulationManager.get_file_type_category(".xyz"), "Estructura")
        self.assertEqual(SimulationManager.get_file_type_category(".unknown"), "Otro")


class TestAnalysisModule(unittest.TestCase):
    """Pruebas del módulo de análisis."""

    def test_identify_redundant_files(self):
        """Prueba identificación de archivos redundantes."""
        files = [
            {"filename": "simulation.log", "file_path": "/path/to/log", "id": 1},
            {"filename": "backup.bak", "file_path": "/path/to/bak", "id": 2},
            {"filename": "data.csv", "file_path": "/path/to/csv", "id": 3},
        ]

        redundant = AnalysisModule.identify_redundant_files(files)

        self.assertGreater(len(redundant), 0)
        self.assertTrue(any(".bak" in f["filename"] for f in redundant))

    def test_calculate_file_statistics(self):
        """Prueba cálculo de estadísticas de archivos."""
        files = [
            {"filename": "file1.txt", "size_bytes": 1024, "file_type": ".txt"},
            {"filename": "file2.log", "size_bytes": 2048, "file_type": ".log"},
            {"filename": "file3.pdb", "size_bytes": 4096, "file_type": ".pdb"},
        ]

        stats = AnalysisModule.calculate_file_statistics(files)

        self.assertEqual(stats["total_files"], 3)
        self.assertGreater(stats["total_size_mb"], 0)
        self.assertIsNotNone(stats["largest_file"])


if __name__ == "__main__":
    unittest.main()
