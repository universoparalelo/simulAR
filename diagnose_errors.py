#!/usr/bin/env python3
"""
Script de diagnóstico para identificar errores en simulAR.
Ejecutar: python diagnose_errors.py
"""

import os
import sys


def print_section(title):
    """Imprime un encabezado de sección."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_imports():
    """Prueba las importaciones de PyQt6."""
    print_section("Probando Importaciones de PyQt6")

    try:
        from PyQt6.QtCore import Qt, QThread, pyqtSignal

        print("✅ PyQt6.QtCore - OK")
    except ImportError as e:
        print(f"❌ PyQt6.QtCore - Error: {e}")
        return False

    try:
        from PyQt6.QtGui import QFont, QIcon, QPixmap

        print("✅ PyQt6.QtGui - OK")
    except ImportError as e:
        print(f"❌ PyQt6.QtGui - Error: {e}")
        return False

    try:
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

        print("✅ PyQt6.QtWidgets - OK")
    except ImportError as e:
        print(f"❌ PyQt6.QtWidgets - Error: {e}")
        return False

    return True


def test_local_modules():
    """Prueba los módulos locales."""
    print_section("Probando Módulos Locales")

    # Agregar src al path (directorio 'simulAR/src')
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

    try:
        from database import SimulationDatabase

        print("✅ database.py - OK")
    except Exception as e:
        print(f"❌ database.py - Error: {e}")
        return False

    try:
        from simulation_manager import SimulationManager

        print("✅ simulation_manager.py - OK")
    except Exception as e:
        print(f"❌ simulation_manager.py - Error: {e}")
        return False

    try:
        from analysis import AnalysisModule

        print("✅ analysis.py - OK")
    except Exception as e:
        print(f"❌ analysis.py - Error: {e}")
        return False

    try:
        from excel_export import ExcelExporter

        print("✅ excel_export.py - OK")
    except Exception as e:
        print(f"❌ excel_export.py - Error: {e}")
        return False

    return True


def test_dependencies():
    """Prueba las dependencias externas."""
    print_section("Probando Dependencias Externas")

    try:
        import psutil

        print("✅ psutil - OK")
    except ImportError:
        print("❌ psutil - No instalado")
        return False

    try:
        import openpyxl

        print("✅ openpyxl - OK")
    except ImportError:
        print("❌ openpyxl - No instalado")
        return False

    return True


def test_gui_initialization():
    """Prueba la inicialización de la GUI."""
    print_section("Probando Inicialización de GUI")

    try:
        # Agregar src al path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from main_gui import MainWindow, ModernButton, ModernFrame

        print("✅ Componentes GUI - OK")
        print("  - ModernButton: OK")
        print("  - ModernFrame: OK")
        print("  - MainWindow: OK")
        return True
    except Exception as e:
        print(f"❌ Componentes GUI - Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los diagnósticos."""
    print("\n" + "=" * 60)
    print("  DIAGNÓSTICO DE SIMULACIÓN MOLECULAR - simulAR")
    print("=" * 60)

    results = []

    # Pruebas
    results.append(("Importaciones PyQt6", test_imports()))
    results.append(("Dependencias Externas", test_dependencies()))
    results.append(("Módulos Locales", test_local_modules()))
    results.append(("Inicialización GUI", test_gui_initialization()))

    # Resumen
    print_section("RESUMEN DE DIAGNÓSTICO")

    all_ok = True
    for name, result in results:
        status = "✅ EXITOSO" if result else "❌ FALLÓ"
        print(f"{name}: {status}")
        if not result:
            all_ok = False

    print()

    if all_ok:
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("\nPuedes ejecutar: python run_app.py")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("\nSoluciones:")
        print("1. Verifica que Python 3.8+ está instalado")
        print("2. Crea entorno virtual: python -m venv venv")
        print(
            "3. Activa: source venv/bin/activate (o venv\\Scripts\\activate en Windows)"
        )

        print("4. Instala dependencias: pip install -r requirements.txt")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
