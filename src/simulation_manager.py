"""
Módulo de gestión de simulaciones moleculares.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class SimulationManager:
    """Gestor de simulaciones en el sistema de archivos."""

    # Extensiones comunes de archivos de simulaciones
    TRAJECTORY_EXTENSIONS = {".dcd", ".xtc", ".trr", ".tng", ".nc", ".h5"}
    INPUT_EXTENSIONS = {".in", ".inp", ".input", ".conf", ".mdin", ".gau"}
    OUTPUT_EXTENSIONS = {".out", ".log", ".o", ".mdout", ".mdinfo"}
    ENERGY_EXTENSIONS = {".en", ".ene", ".ener"}
    STRUCTURE_EXTENSIONS = {".pdb", ".gro", ".xyz", ".mol2", ".psf"}

    KNOWN_PROGRAMS = ["AMBER", "GAMESS", "Gaussian", "Travis", "GROMACS", "LAMMPS"]

    @staticmethod
    def scan_directory(directory: str) -> List[Dict]:
        """
        Escanea un directorio para identificar posibles simulaciones.

        Args:
            directory: Ruta del directorio a escanear

        Returns:
            Lista de diccionarios con información de directorios que parecen simulaciones
        """
        simulations = []
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            return simulations

        for item in dir_path.iterdir():
            if item.is_dir():
                sim_info = SimulationManager.analyze_directory(str(item))
                if sim_info:
                    simulations.append(sim_info)

        return simulations

    @staticmethod
    def analyze_directory(directory: str) -> Dict:
        """
        Analiza un directorio para determinar si contiene una simulación.

        Args:
            directory: Ruta del directorio a analizar

        Returns:
            Diccionario con información de la simulación o None
        """
        dir_path = Path(directory)

        # Obtener información del directorio
        try:
            files = list(dir_path.rglob("*"))
            size_bytes = SimulationManager.get_directory_size(directory)

            # Detectar programa basado en archivos presentes
            program = SimulationManager._detect_program(files)

            if not program:
                return None

            # Crear información de la simulación
            sim_info = {
                "title": dir_path.name,
                "program": program,
                "path": str(dir_path),
                "date": datetime.fromtimestamp(dir_path.stat().st_mtime).isoformat(),
                "size_bytes": size_bytes,
                "description": "",
                "files": [
                    {
                        "filename": f.name,
                        "file_path": str(f),
                        "size_bytes": f.stat().st_size if f.is_file() else 0,
                        "file_type": f.suffix.lower(),
                    }
                    for f in files
                    if f.is_file()
                ],
            }

            return sim_info
        except Exception as e:
            print(f"Error analizando directorio {directory}: {e}")
            return None

    @staticmethod
    def _detect_program(files: List[Path]) -> str:
        """
        Detecta el programa de simulación basado en los archivos presentes.

        Args:
            files: Lista de rutas de archivos

        Returns:
            Nombre del programa detectado o vacío
        """
        extensions = set()
        filenames_lower = []

        for f in files:
            if f.is_file():
                extensions.add(f.suffix.lower())
                filenames_lower.append(f.name.lower())

        # Heurística para detectar programa
        if any(ext in SimulationManager.TRAJECTORY_EXTENSIONS for ext in extensions):
            if any(".gro" in f or ".pdb" in f for f in filenames_lower):
                return "GROMACS"
            if any(".dcd" in ext for ext in extensions):
                return "AMBER"

        # Buscar por extensiones específicas
        if any(".gau" in f for f in filenames_lower) or ".gjf" in extensions:
            return "Gaussian"
        if any(".gms" in f or ".gamess" in f for f in filenames_lower):
            return "GAMESS"
        if any("travis" in f for f in filenames_lower):
            return "Travis"

        # Si no se detecta específicamente, pero hay archivos de simulación
        if extensions & (
            SimulationManager.TRAJECTORY_EXTENSIONS
            | SimulationManager.OUTPUT_EXTENSIONS
        ):
            return "Simulación"

        return ""

    @staticmethod
    def get_directory_size(directory: str) -> int:
        """
        Calcula el tamaño total de un directorio.

        Args:
            directory: Ruta del directorio

        Returns:
            Tamaño total en bytes
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            print(f"Error calculando tamaño: {e}")

        return total_size

    @staticmethod
    def get_file_size_readable(size_bytes: int) -> str:
        """
        Convierte bytes a formato legible.

        Args:
            size_bytes: Tamaño en bytes

        Returns:
            Tamaño en formato legible (B, KB, MB, GB, TB)
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Elimina un archivo del sistema.

        Args:
            file_path: Ruta del archivo

        Returns:
            True si se eliminó exitosamente, False si hubo error
        """
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                if file_path_obj.is_file():
                    file_path_obj.unlink()
                elif file_path_obj.is_dir():
                    shutil.rmtree(file_path_obj)
                return True
        except Exception as e:
            print(f"Error eliminando archivo: {e}")

        return False

    @staticmethod
    def get_file_type_category(file_extension: str) -> str:
        """
        Categoriza un tipo de archivo.

        Args:
            file_extension: Extensión del archivo

        Returns:
            Categoría del archivo
        """
        ext = file_extension.lower()

        if ext in SimulationManager.TRAJECTORY_EXTENSIONS:
            return "Trayectoria"
        elif ext in SimulationManager.INPUT_EXTENSIONS:
            return "Entrada"
        elif ext in SimulationManager.OUTPUT_EXTENSIONS:
            return "Salida"
        elif ext in SimulationManager.ENERGY_EXTENSIONS:
            return "Energía"
        elif ext in SimulationManager.STRUCTURE_EXTENSIONS:
            return "Estructura"
        elif ext in {".xlsx", ".xls", ".csv", ".txt", ".dat"}:
            return "Datos"
        elif ext in {".png", ".jpg", ".jpeg", ".pdf", ".tif"}:
            return "Visualización"
        else:
            return "Otro"
