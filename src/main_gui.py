"""
Interfaz gráfica mejorada de simulAR con diseño moderno.
Basada en el diseño profesional de QuITEx.
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from analysis import AnalysisModule
from database import SimulationDatabase
from excel_export import ExcelExporter
from simulation_manager import SimulationManager


class ModernButton(QPushButton):
    """Botón con estilos modernos."""

    def __init__(self, text, icon=None, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setup_style()

    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    color: #333;
                    border: 1px solid #ddd;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #ebebeb;
                    border: 1px solid #bbb;
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
            """)


class ModernFrame(QFrame):
    """Frame con diseño moderno."""

    def __init__(self, title=""):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # SIEMPRE crear el layout principal
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        # Agregar título si existe
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 5px;
                }
            """)
            self.main_layout.addWidget(title_label)

        self.setLayout(self.main_layout)


class SimulationWorker(QThread):
    """Worker thread para cargar simulaciones."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory

    def run(self):
        try:
            self.progress.emit("Escaneando directorio...")
            simulations = SimulationManager.scan_directory(self.directory)
            self.finished.emit(simulations)
        except Exception as e:
            self.error.emit(str(e))


class DetailWindow(QDialog):
    """Ventana de detalle mejorada."""

    def __init__(self, db: SimulationDatabase, sim_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.sim_id = sim_id
        self.simulation = None
        self.files = []
        self.metrics = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializa la interfaz."""
        self.setWindowTitle("Detalle de Simulación - simulAR")
        self.setGeometry(100, 100, 1000, 700)

        title_label = QLabel(title)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Información general
        info_frame = ModernFrame("Información General")
        info_title_label = QLabel(title)
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                color: #555;
                line-height: 1.6;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(self.info_label)
        info_frame.main_layout.addLayout(info_layout)
        layout.addWidget(info_frame)

        # Tabla de archivos
        files_frame = ModernFrame("Archivos de la Simulación")
        files_title_label = QLabel(title)
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(
            ["Nombre", "Tipo", "Tamaño (MB)", "Ruta"]
        )
        self.files_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.setup_table_style(self.files_table)
        files_layout.addWidget(self.files_table)
        files_frame.main_layout.addLayout(files_layout)
        layout.addWidget(files_frame)

        # Tabla de métricas
        metrics_frame = ModernFrame("Métricas Calculadas")
        metrics_title_label = QLabel(title)
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(4)
        self.metrics_table.setHorizontalHeaderLabels(
            ["Métrica", "Valor", "Unidad", "Fecha"]
        )
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.setup_table_style(self.metrics_table)
        metrics_layout.addWidget(self.metrics_table)
        metrics_frame.main_layout.addLayout(metrics_layout)
        layout.addWidget(metrics_frame)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        btn_export = ModernButton("📊 Exportar a Excel")
        btn_export.clicked.connect(self.export_to_excel)
        buttons_layout.addWidget(btn_export)

        btn_analyze = ModernButton("🔍 Ejecutar Análisis", primary=True)
        btn_analyze.clicked.connect(self.run_analysis)
        buttons_layout.addWidget(btn_analyze)

        btn_delete = ModernButton("🗑️ Limpiar Archivos")
        btn_delete.clicked.connect(self.delete_files)
        buttons_layout.addWidget(btn_delete)

        btn_close = ModernButton("Cerrar")
        btn_close.clicked.connect(self.close)
        buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def setup_table_style(self, table):
        """Configura estilos para tabla."""
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #e0e0e0;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        table.setMaximumHeight(200)

    def load_data(self):
        """Carga los datos de la simulación."""
        self.simulation = self.db.get_simulation_by_id(self.sim_id)

        if not self.simulation:
            QMessageBox.warning(self, "Error", "No se pudo cargar la simulación")
            return

        info_text = f"""
        <b>Título:</b> {self.simulation["title"]}<br>
        <b>Programa:</b> {self.simulation["program"]}<br>
        <b>Fecha:</b> {self.simulation["date"]}<br>
        <b>Tamaño:</b> {SimulationManager.get_file_size_readable(self.simulation["size_bytes"])}<br>
        <b>Descripción:</b> {self.simulation["description"] or "N/A"}<br>
        <b>Creado:</b> {self.simulation["created_at"][:10]}
        """
        self.info_label.setText(info_text)

        self.files = self.db.get_simulation_files(self.sim_id)
        self.populate_files_table()

        self.metrics = self.db.get_metrics(self.sim_id)
        self.populate_metrics_table()

    def populate_files_table(self):
        """Llena la tabla de archivos."""
        self.files_table.setRowCount(len(self.files))

        for row, file_info in enumerate(self.files):
            self.files_table.setItem(row, 0, QTableWidgetItem(file_info["filename"]))
            self.files_table.setItem(row, 1, QTableWidgetItem(file_info["file_type"]))

            size_mb = file_info["size_bytes"] / (1024 * 1024)
            self.files_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f}"))
            self.files_table.setItem(row, 3, QTableWidgetItem(file_info["file_path"]))

    def populate_metrics_table(self):
        """Llena la tabla de métricas."""
        self.metrics_table.setRowCount(len(self.metrics))

        for row, metric in enumerate(self.metrics):
            self.metrics_table.setItem(row, 0, QTableWidgetItem(metric["metric_name"]))
            self.metrics_table.setItem(
                row, 1, QTableWidgetItem(str(metric["metric_value"]))
            )
            self.metrics_table.setItem(row, 2, QTableWidgetItem(metric["metric_unit"]))
            self.metrics_table.setItem(
                row, 3, QTableWidgetItem(metric["calculated_at"][:10])
            )

    def export_to_excel(self):
        """Exporta la simulación a Excel."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self, "Seleccionar directorio de salida"
            )
            if directory:
                sim_data = {
                    **self.simulation,
                    "files": self.files,
                    "metrics": self.metrics,
                }
                filepath = ExcelExporter.export_simulation(sim_data, directory)
                QMessageBox.information(
                    self, "✅ Éxito", f"Simulación exportada a:\n{filepath}"
                )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al exportar: {str(e)}")

    def run_analysis(self):
        """Ejecuta análisis."""
        try:
            redundant = AnalysisModule.identify_redundant_files(self.files)
            report = AnalysisModule.generate_analysis_report(
                {**self.simulation, "files": self.files}
            )

            QMessageBox.information(
                self,
                "📊 Análisis Completado",
                f"{report}\n\nArchivos redundantes: {len(redundant)}",
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al analizar: {str(e)}")

    def delete_files(self):
        """Elimina archivos innecesarios."""
        try:
            redundant = AnalysisModule.identify_redundant_files(self.files)

            if not redundant:
                QMessageBox.information(
                    self, "ℹ️ Información", "No hay archivos para limpiar"
                )
                return

            msg = f"Se encontraron {len(redundant)} archivos redundantes:\n\n"
            for f in redundant[:5]:
                msg += f"• {f['filename']} ({f['reason']})\n"
            if len(redundant) > 5:
                msg += f"... y {len(redundant) - 5} más"

            reply = QMessageBox.question(
                self, "⚠️ Confirmar", f"{msg}\n\n¿Continuar con la limpieza?"
            )
            if reply == QMessageBox.StandardButton.Yes:
                deleted_count = 0
                for file_info in redundant:
                    if SimulationManager.delete_file(file_info["file_path"]):
                        deleted_count += 1
                        self.db.delete_files([file_info["id"]])

                QMessageBox.information(
                    self, "✅ Éxito", f"Se eliminaron {deleted_count} archivos"
                )
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error: {str(e)}")


class MainWindow(QMainWindow):
    """Ventana principal mejorada."""

    def __init__(self):
        super().__init__()
        self.db = SimulationDatabase("data/simulations.db")
        self.simulations = []
        self.init_ui()
        self.setup_styles()

    def setup_styles(self):
        """Configura estilos globales."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #333;
            }
        """)

    def init_ui(self):
        """Inicializa la interfaz."""
        self.setWindowTitle("simulAR - Gestor de Simulaciones Moleculares")
        self.setGeometry(50, 50, 1400, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("📊 simulAR")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Información del sistema
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.date_label)

        self.disk_label = QLabel()
        self.disk_label.setStyleSheet(
            "color: #666; font-size: 12px; margin-left: 20px;"
        )
        header_layout.addWidget(self.disk_label)

        self.update_date()
        self.update_disk_info()

        main_layout.addLayout(header_layout)

        # Línea divisoria
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator)

        # Panel de acciones
        actions_frame = ModernFrame()
        actions_layout = QHBoxLayout()

        btn_load = ModernButton("➕ Cargar Nueva Simulación", primary=True)
        btn_load.setMinimumHeight(40)
        btn_load.clicked.connect(self.load_simulation)
        actions_layout.addWidget(btn_load)

        actions_layout.addStretch()

        # Filtros
        search_input = QLineEdit()
        search_input.setPlaceholderText("🔍 Buscar simulación...")
        search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        search_input.setMaximumWidth(250)
        actions_layout.addWidget(search_input)

        actions_frame.main_layout.addLayout(actions_layout)
        main_layout.addWidget(actions_frame)

        # Tabla de simulaciones
        table_frame = ModernFrame("Simulaciones Cargadas")
        # table title placeholder - omitted

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Título", "Programa", "Fecha", "Tamaño", "Acciones"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #c8e6c9;
            }
        """)
        self.table.doubleClicked.connect(self.open_simulation_detail)
        self.table.setMinimumHeight(300)

        table_frame.main_layout.addWidget(self.table)
        main_layout.addWidget(table_frame, 1)

        # Footer con estadísticas
        footer_frame = ModernFrame()
        footer_layout = QHBoxLayout()

        self.stats_label = QLabel("Cargando...")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px;")
        footer_layout.addWidget(self.stats_label)

        footer_layout.addStretch()

        footer_frame.main_layout.addLayout(footer_layout)
        main_layout.addWidget(footer_frame)

        central_widget.setLayout(main_layout)

        self.refresh_simulations()

    def update_date(self):
        """Actualiza la fecha."""
        now = datetime.now()
        self.date_label.setText(f"📅 {now.strftime('%d/%m/%Y %H:%M')}")

    def update_disk_info(self):
        """Actualiza info de disco."""
        try:
            _, _, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)
            self.disk_label.setText(f"💾 Disponible: {free_gb:.2f} GB")
        except:
            self.disk_label.setText("💾 N/A")

    def load_simulation(self):
        """Carga nueva simulación."""
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de simulación"
        )

        if directory:
            self.worker = SimulationWorker(directory)
            self.worker.progress.connect(self.on_progress)
            self.worker.finished.connect(self.on_simulations_loaded)
            self.worker.error.connect(self.on_error)
            self.worker.start()

    def on_progress(self, message: str):
        """Maneja el progreso."""
        self.statusBar().showMessage(message)

    def on_simulations_loaded(self, simulations: List[Dict]):
        """Maneja simulaciones cargadas."""
        if not simulations:
            QMessageBox.warning(
                self, "Sin resultados", "No se encontraron simulaciones"
            )
            return

        for sim in simulations:
            try:
                sim_id = self.db.add_simulation(
                    title=sim["title"],
                    program=sim["program"],
                    path=sim["path"],
                    date=sim["date"],
                    size_bytes=sim["size_bytes"],
                    description=sim.get("description", ""),
                )

                self.db.add_simulation_files(sim_id, sim["files"])

                QMessageBox.information(
                    self, "✅ Éxito", f"Simulación '{sim['title']}' cargada"
                )
            except ValueError as e:
                QMessageBox.warning(self, "⚠️ Duplicada", str(e))
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Error: {str(e)}")

        self.refresh_simulations()

    def on_error(self, error: str):
        """Maneja errores."""
        QMessageBox.critical(self, "❌ Error", f"Error: {error}")

    def refresh_simulations(self):
        """Actualiza la tabla."""
        self.simulations = self.db.get_all_simulations()

        self.table.setRowCount(len(self.simulations))

        for row, sim in enumerate(self.simulations):
            self.table.setItem(row, 0, QTableWidgetItem(sim["title"]))
            self.table.setItem(row, 1, QTableWidgetItem(sim["program"]))
            self.table.setItem(row, 2, QTableWidgetItem(sim["date"][:10]))

            size_readable = SimulationManager.get_file_size_readable(sim["size_bytes"])
            self.table.setItem(row, 3, QTableWidgetItem(size_readable))

            btn = ModernButton("Ver Detalle")
            btn.clicked.connect(
                lambda checked, sim_id=sim["id"]: self.open_simulation_detail_by_id(
                    sim_id
                )
            )
            self.table.setCellWidget(row, 4, btn)

        # Actualizar estadísticas
        total_size = self.db.get_total_size()
        total_readable = SimulationManager.get_file_size_readable(total_size)
        self.stats_label.setText(
            f"Total: {len(self.simulations)} simulaciones | Tamaño: {total_readable}"
        )

    def open_simulation_detail(self):
        """Abre detalle (doble clic)."""
        if self.table.currentRow() >= 0:
            sim = self.simulations[self.table.currentRow()]
            self.open_simulation_detail_by_id(sim["id"])

    def open_simulation_detail_by_id(self, sim_id: int):
        """Abre detalle por ID."""
        detail_window = DetailWindow(self.db, sim_id, self)
        detail_window.exec()


def main():
    """Función principal."""
    app = QApplication(sys.argv)
    app.setApplicationName("simulAR")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
