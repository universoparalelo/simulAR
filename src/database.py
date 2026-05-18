"""
Módulo de gestión de base de datos para simulaciones moleculares.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SimulationDatabase:
    """Gestor de base de datos SQLite para simulaciones."""

    def __init__(self, db_path: str = "data/simulations.db"):
        """
        Inicializa la conexión a la base de datos.

        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Inicializa las tablas de la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de simulaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                program TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                date TEXT NOT NULL,
                size_bytes INTEGER,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Tabla de archivos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size_bytes INTEGER,
                file_type TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
            )
        """)

        # Tabla de métricas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_unit TEXT,
                calculated_at TEXT NOT NULL,
                FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    def add_simulation(
        self,
        title: str,
        program: str,
        path: str,
        date: str,
        size_bytes: int,
        description: str = "",
    ) -> int:
        """
        Agrega una nueva simulación a la base de datos.

        Args:
            title: Título de la simulación
            program: Programa usado (AMBER, GAMESS, Gaussian, Travis)
            path: Ruta del directorio de la simulación
            date: Fecha de la simulación
            size_bytes: Tamaño total en bytes
            description: Descripción opcional

        Returns:
            ID de la simulación creada
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        try:
            cursor.execute(
                """
                INSERT INTO simulations
                (title, program, path, date, size_bytes, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (title, program, path, date, size_bytes, description, now, now),
            )

            conn.commit()
            sim_id = cursor.lastrowid
            return sim_id
        except sqlite3.IntegrityError:
            raise ValueError(f"La simulación '{title}' ya existe en la base de datos")
        finally:
            conn.close()

    def get_all_simulations(self) -> List[Dict]:
        """
        Obtiene todas las simulaciones registradas.

        Returns:
            Lista de diccionarios con información de simulaciones
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, program, path, date, size_bytes, description,
                   created_at, updated_at FROM simulations ORDER BY date DESC
        """)

        simulations = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return simulations

    def get_simulation_by_id(self, sim_id: int) -> Optional[Dict]:
        """
        Obtiene información de una simulación específica.

        Args:
            sim_id: ID de la simulación

        Returns:
            Diccionario con información de la simulación
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, program, path, date, size_bytes, description,
                   created_at, updated_at FROM simulations WHERE id = ?
        """,
            (sim_id,),
        )

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def add_simulation_files(self, sim_id: int, files: List[Dict]):
        """
        Agrega archivos asociados a una simulación.

        Args:
            sim_id: ID de la simulación
            files: Lista de diccionarios con información de archivos
                   {filename, file_path, size_bytes, file_type}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        for file_info in files:
            cursor.execute(
                """
                INSERT INTO simulation_files
                (simulation_id, filename, file_path, size_bytes, file_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    sim_id,
                    file_info["filename"],
                    file_info["file_path"],
                    file_info.get("size_bytes", 0),
                    file_info.get("file_type", ""),
                    now,
                ),
            )

        conn.commit()
        conn.close()

    def get_simulation_files(self, sim_id: int) -> List[Dict]:
        """
        Obtiene los archivos de una simulación.

        Args:
            sim_id: ID de la simulación

        Returns:
            Lista de diccionarios con información de archivos
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, filename, file_path, size_bytes, file_type, created_at
            FROM simulation_files WHERE simulation_id = ? ORDER BY filename
        """,
            (sim_id,),
        )

        files = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return files

    def add_metric(
        self, sim_id: int, metric_name: str, metric_value: float, metric_unit: str = ""
    ):
        """
        Agrega una métrica a una simulación.

        Args:
            sim_id: ID de la simulación
            metric_name: Nombre de la métrica (RMSD, radio de giro, etc.)
            metric_value: Valor de la métrica
            metric_unit: Unidad de medida
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO metrics
            (simulation_id, metric_name, metric_value, metric_unit, calculated_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (sim_id, metric_name, metric_value, metric_unit, now),
        )

        conn.commit()
        conn.close()

    def get_metrics(self, sim_id: int) -> List[Dict]:
        """
        Obtiene las métricas de una simulación.

        Args:
            sim_id: ID de la simulación

        Returns:
            Lista de diccionarios con información de métricas
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, metric_name, metric_value, metric_unit, calculated_at
            FROM metrics WHERE simulation_id = ? ORDER BY calculated_at DESC
        """,
            (sim_id,),
        )

        metrics = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return metrics

    def delete_simulation(self, sim_id: int):
        """
        Elimina una simulación y todos sus datos asociados.

        Args:
            sim_id: ID de la simulación
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM simulations WHERE id = ?", (sim_id,))

        conn.commit()
        conn.close()

    def delete_files(self, file_ids: List[int]):
        """
        Elimina archivos de la base de datos.

        Args:
            file_ids: Lista de IDs de archivos a eliminar
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for file_id in file_ids:
            cursor.execute("DELETE FROM simulation_files WHERE id = ?", (file_id,))

        conn.commit()
        conn.close()

    def get_total_size(self) -> int:
        """
        Calcula el tamaño total de todas las simulaciones.

        Returns:
            Tamaño total en bytes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(size_bytes) FROM simulations")
        result = cursor.fetchone()[0]
        conn.close()

        return result if result else 0
