#!/usr/bin/env python3
"""
Script de configuración e instalación de simulAR.
Ejecutar: python setup.py
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Ejecuta un comando del sistema."""
    if description:
        print(f"\n▶ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_python_version():
    """Verifica que Python sea 3.8+"""
    print("\n" + "=" * 60)
    print("  VERIFICACIÓN DE INSTALACIÓN - simulAR")
    print("=" * 60)

    version = sys.version_info
    print(f"\n✓ Versión de Python: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Se requiere Python 3.8 o superior")
        return False

    print("✓ Versión de Python OK")
    return True


def check_dependencies():
    """Verifica las dependencias instaladas."""
    print("\n▶ Verificando dependencias...")

    required = ["PyQt6", "openpyxl", "psutil"]
    missing = []

    for package in required:
        try:
            __import__(package.lower().replace("pyqt6", "PyQt6"))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ❌ {package} (falta)")
            missing.append(package)

    return len(missing) == 0, missing


def install_requirements():
    """Instala los requisitos."""
    print("\n▶ Instalando requisitos...")

    if not os.path.exists("requirements.txt"):
        print("❌ No se encontró requirements.txt")
        return False

    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Instalando dependencias",
    )


def create_directories():
    """Crea los directorios necesarios."""
    print("\n▶ Creando directorios...")

    dirs = ["data", "logs", "exports"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print(f"  ✓ {d}/")

    return True


def test_imports():
    """Prueba que se pueden importar todos los módulos."""
    print("\n▶ Probando importaciones...")

    # Agregar src al path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

    try:
        from database import SimulationDatabase

        print("  ✓ database")
    except Exception as e:
        print(f"  ❌ database: {e}")
        return False

    try:
        from simulation_manager import SimulationManager

        print("  ✓ simulation_manager")
    except Exception as e:
        print(f"  ❌ simulation_manager: {e}")
        return False

    try:
        from analysis import AnalysisModule

        print("  ✓ analysis")
    except Exception as e:
        print(f"  ❌ analysis: {e}")
        return False

    try:
        from excel_export import ExcelExporter

        print("  ✓ excel_export")
    except Exception as e:
        print(f"  ❌ excel_export: {e}")
        return False

    return True


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("  INSTALADOR DE SIMULACIÓN MOLECULAR - simulAR")
    print("=" * 60)

    # Paso 1: Verificar Python
    if not check_python_version():
        print("\n❌ INSTALACIÓN FALLIDA")
        return 1

    # Paso 2: Verificar dependencias
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"\n⚠️  Dependencias faltantes: {', '.join(missing)}")
        print("\n▶ Procediendo a instalar dependencias...")

        if not install_requirements():
            print("❌ No se pudieron instalar las dependencias")
            print("\nIntenta manualmente:")
            print(f"  {sys.executable} -m pip install -r requirements.txt")
            return 1

    # Paso 3: Crear directorios
    if not create_directories():
        print("❌ No se pudieron crear los directorios")
        return 1

    # Paso 4: Probar importaciones
    if not test_imports():
        print("❌ No se pudieron importar los módulos")
        return 1

    # Éxito
    print("\n" + "=" * 60)
    print("✅ INSTALACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("\n▶ Para ejecutar la aplicación:")
    print("   python run_app.py")
    print("\n▶ Para ver ejemplos de uso:")
    print("   python examples.py")
    print("\n▶ Para diagnosticar problemas:")
    print("   python diagnose_errors.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
