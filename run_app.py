#!/usr/bin/env python3
"""
simulAR - Gestor de Simulaciones Moleculares
Punto de entrada de la aplicación
"""

import os
import sys

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from main_gui import main

if __name__ == "__main__":
    main()
