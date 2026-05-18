#!/usr/bin/env python3
"""
Script de verificación de la instalación de simulAR.
Ejecutar: python check_installation.py
"""

import os
import sys


def print_header(text):
    """Imprime un encabezado."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def check_python_version():
    """Verifica la versión de Python."""
    print("✓ Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  Python {version.major}.{version.minor}.{version.micro} - ✅ OK")
        return True
    else:
        print(
            f"  Python {version.major}.{version.minor}.{version.micro} - ❌ Se requiere Python 3.8+"
        )
        return False


def check_dependencies():
    """Verifica las dependencias."""
    print("\n✓ Verificando dependencias...")

    dependencies = [
        ("PyQt6", "PyQt6"),
        ("openpyxl", "openpyxl"),
        ("psutil", "psutil"),
    ]

    all_ok = True
    for name, package in dependencies:
        try:
            __import__(package)
            print(f"  {name} - ✅ OK")
        except ImportError:
            print(f"  {name} - ❌ No instalado")
            all_ok = False

    return all_ok


def check_project_structure():
    """Verifica la estructura del proyecto."""
    print("\n✓ Verificando estructura del proyecto...")

    files_required = [
        "run_app.py",
        "config.py",
        "examples.py",
        "requirements.txt",
        "README.md",
        "QUICKSTART.md",
        "DEVELOPMENT.md",
    ]

    dirs_required = [
        "src",
        "tests",
        "data",
    ]

    src_files = [
        "src/main_gui.py",
        "src/database.py",
        "src/simulation_manager.py",
        "src/analysis.py",
        "src/excel_export.py",
    ]

    all_ok = True

    print("  Archivos principales:")
    for f in files_required:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"    {f} ({size} bytes) - ✅")
        else:
            print(f"    {f} - ❌ NO ENCONTRADO")
            all_ok = False

    print("\n  Directorios:")
    for d in dirs_required:
        if os.path.isdir(d):
            print(f"    {d} - ✅")
        else:
            print(f"    {d} - ❌ NO ENCONTRADO")
            all_ok = False

    print("\n  Módulos de código:")
    for f in src_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"    {f} ({size} bytes) - ✅")
        else:
            print(f"    {f} - ❌ NO ENCONTRADO")
            all_ok = False

    return all_ok


def check_imports():
    """Verifica que los módulos se puedan importar."""
    print("\n✓ Verificando importaciones de módulos...")

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

    modules = [
        "database",
        "simulation_manager",
        "analysis",
        "excel_export",
    ]

    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"  {module}.py - ✅")
        except Exception as e:
            print(f"  {module}.py - ❌ Error: {str(e)}")
            all_ok = False

    return all_ok


def print_installation_instructions():
    """Imprime instrucciones de instalación."""
    print_header("INSTRUCCIONES DE INSTALACIÓN")

    print("""
Si las verificaciones anteriores muestran errores, sigue estos pasos:

1. CREAR ENTORNO VIRTUAL:

   En Linux/macOS:
   $ python3 -m venv venv
   $ source venv/bin/activate

   En Windows:
   > python -m venv venv
   > venv\\Scripts\\activate

2. INSTALAR DEPENDENCIAS:

   $ pip install -r requirements.txt

3. EJECUTAR LA APLICACIÓN:

   $ python run_app.py

4. EJECUTAR EJEMPLOS:

   $ python examples.py
""")


def main():
    """Ejecuta todas las verificaciones."""
    print_header("VERIFICACIÓN DE INSTALACIÓN - simulAR")

    checks = [
        ("Versión de Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Estructura del Proyecto", check_project_structure),
        ("Importaciones", check_imports),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error en {name}: {str(e)}")
            results.append((name, False))

    # Resumen
    print_header("RESUMEN DE VERIFICACIÓN")

    all_ok = True
    for name, result in results:
        status = "✅ OK" if result else "❌ FALLÓ"
        print(f"{name}: {status}")
        if not result:
            all_ok = False

    print()

    if all_ok:
        print("""
╔════════════════════════════════════════╗
║  ✅ TODO ESTÁ CONFIGURADO CORRECTAMENTE  ║
║                                        ║
║  Ejecuta: python run_app.py            ║
╚════════════════════════════════════════╝
""")
    else:
        print_installation_instructions()

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
