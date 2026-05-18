"""
Módulo de análisis de simulaciones moleculares.
Cálculo de métricas y análisis de archivos.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AnalysisModule:
    """Módulo para análisis de simulaciones moleculares."""

    @staticmethod
    def calculate_rmsd(trajectory_file: str) -> Optional[float]:
        """
        Intenta extraer RMSD de un archivo de trayectoria.

        Args:
            trajectory_file: Ruta al archivo de trayectoria

        Returns:
            Valor de RMSD si se encuentra, None si no
        """
        try:
            with open(trajectory_file, "r", errors="ignore") as f:
                content = f.read()

            # Buscar patrones comunes de RMSD
            patterns = [
                r"RMSD\s*[=:]\s*([\d.]+)",
                r"rmsd\s*[=:]\s*([\d.]+)",
                r"R\s*M\s*S\s*D\s*[=:]\s*([\d.]+)",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    return float(matches[-1])
        except Exception as e:
            print(f"Error calculando RMSD: {e}")

        return None

    @staticmethod
    def calculate_gyration_radius(structure_file: str) -> Optional[float]:
        """
        Intenta extraer radio de giro de un archivo de estructura.

        Args:
            structure_file: Ruta al archivo de estructura

        Returns:
            Valor del radio de giro si se encuentra, None si no
        """
        try:
            with open(structure_file, "r", errors="ignore") as f:
                content = f.read()

            # Buscar patrones comunes de radio de giro
            patterns = [
                r"[Rr]adio\s+de\s+[Gg]iro\s*[=:]\s*([\d.]+)",
                r"[Gg]yration\s+[Rr]adius\s*[=:]\s*([\d.]+)",
                r"Rg\s*[=:]\s*([\d.]+)",
                r"rg\s*[=:]\s*([\d.]+)",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    return float(matches[-1])
        except Exception as e:
            print(f"Error calculando radio de giro: {e}")

        return None

    @staticmethod
    def analyze_output_file(file_path: str) -> Dict:
        """
        Analiza un archivo de salida y extrae información relevante.

        Args:
            file_path: Ruta al archivo de salida

        Returns:
            Diccionario con información extraída
        """
        analysis = {
            "file": Path(file_path).name,
            "size_mb": Path(file_path).stat().st_size / (1024 * 1024),
            "metrics": {},
            "convergence": None,
            "status": "unknown",
        }

        try:
            with open(file_path, "r", errors="ignore") as f:
                content = f.read().lower()

            # Detectar estado de finalización
            if "error" in content or "fail" in content:
                analysis["status"] = "error"
            elif "success" in content or "complete" in content or "finished" in content:
                analysis["status"] = "success"
            elif "converge" in content:
                analysis["status"] = "converged"
            else:
                analysis["status"] = "running"

            # Extraer métricas
            rmsd = AnalysisModule.calculate_rmsd(file_path)
            if rmsd:
                analysis["metrics"]["RMSD"] = rmsd

            rg = AnalysisModule.calculate_gyration_radius(file_path)
            if rg:
                analysis["metrics"]["Rg"] = rg

        except Exception as e:
            print(f"Error analizando archivo: {e}")

        return analysis

    @staticmethod
    def identify_redundant_files(files: List[Dict]) -> List[Dict]:
        """
        Identifica archivos potencialmente redundantes.

        Args:
            files: Lista de diccionarios de archivos

        Returns:
            Lista de archivos potencialmente redundantes
        """
        redundant = []

        # Archivos de backup comunes
        backup_patterns = [".bak", ".backup", ".old", ".~", "#", ".tmp"]

        for file_info in files:
            filename = file_info.get("filename", "").lower()

            # Detectar archivos de backup
            if any(pattern in filename for pattern in backup_patterns):
                redundant.append(
                    {**file_info, "reason": "Archivo de backup", "severity": "low"}
                )

            # Detectar archivos de log duplicados
            if filename.endswith(".log") and filename.count("log") > 1:
                redundant.append(
                    {**file_info, "reason": "Log duplicado", "severity": "low"}
                )

        return redundant

    @staticmethod
    def calculate_file_statistics(files: List[Dict]) -> Dict:
        """
        Calcula estadísticas sobre los archivos de una simulación.

        Args:
            files: Lista de diccionarios de archivos

        Returns:
            Diccionario con estadísticas
        """
        if not files:
            return {}

        stats = {
            "total_files": len(files),
            "total_size_mb": sum(f.get("size_bytes", 0) for f in files) / (1024 * 1024),
            "largest_file": None,
            "file_types": {},
        }

        # Encontrar archivo más grande
        largest = max(files, key=lambda f: f.get("size_bytes", 0))
        stats["largest_file"] = {
            "name": largest.get("filename"),
            "size_mb": largest.get("size_bytes", 0) / (1024 * 1024),
        }

        # Contar tipos de archivos
        for file_info in files:
            file_type = file_info.get("file_type", "unknown")
            stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1

        return stats

    @staticmethod
    def generate_analysis_report(sim_info: Dict) -> str:
        """
        Genera un reporte de análisis de simulación.

        Args:
            sim_info: Información de la simulación

        Returns:
            Texto del reporte
        """
        from simulation_manager import SimulationManager

        report = f"""
=== REPORTE DE ANÁLISIS DE SIMULACIÓN ===

Título: {sim_info.get("title", "N/A")}
Programa: {sim_info.get("program", "N/A")}
Fecha: {sim_info.get("date", "N/A")}
Tamaño Total: {SimulationManager.get_file_size_readable(sim_info.get("size_bytes", 0))}

--- ESTADÍSTICAS DE ARCHIVOS ---
Total de archivos: {len(sim_info.get("files", []))}

--- TIPOS DE ARCHIVO ---
"""

        stats = AnalysisModule.calculate_file_statistics(sim_info.get("files", []))

        for file_type, count in stats.get("file_types", {}).items():
            report += f"{file_type}: {count} archivo(s)\n"

        if stats.get("largest_file"):
            report += f"\nArchivo más grande: {stats['largest_file']['name']} "
            report += f"({stats['largest_file']['size_mb']:.2f} MB)\n"

        return report
