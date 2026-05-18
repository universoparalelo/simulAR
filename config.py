"""
Archivo de configuración de simulAR.
Personalizables según necesidades del usuario.
"""

# Configuración de Base de Datos
DATABASE = {
    "path": "data/simulations.db",
    "timeout": 30,
}

# Configuración de la Interfaz Gráfica
GUI = {
    "window_width": 1200,
    "window_height": 700,
    "theme": "default",  # 'dark' o 'light'
}

# Configuración de Análisis
ANALYSIS = {
    "auto_analyze": False,  # Analizar automáticamente al cargar
    "detect_redundant_files": True,
    "min_file_size_mb": 1,  # Tamaño mínimo para considerar redundante
}

# Configuración de Archivos
FILES = {
    "excluded_extensions": [".tmp", ".temp", ".bak"],
    "excluded_folders": ["__pycache__", ".git", ".venv"],
    "max_directory_depth": 5,  # Profundidad máxima de escaneo
}

# Programas de Simulación Soportados
SUPPORTED_PROGRAMS = [
    "AMBER",
    "GAMESS",
    "Gaussian",
    "Travis",
    "GROMACS",
    "LAMMPS",
    "NAMD",
    "CHARMM",
]

# Extensiones de Archivo por Tipo
FILE_EXTENSIONS = {
    "trajectory": {".dcd", ".xtc", ".trr", ".tng", ".nc", ".h5", ".trj"},
    "input": {".in", ".inp", ".input", ".conf", ".mdin", ".gau", ".gjf"},
    "output": {".out", ".log", ".o", ".mdout", ".mdinfo", ".stdout"},
    "energy": {".en", ".ene", ".ener", ".ener.gz"},
    "structure": {".pdb", ".gro", ".xyz", ".mol2", ".psf", ".top"},
    "data": {".xlsx", ".xls", ".csv", ".txt", ".dat", ".json"},
    "visualization": {".png", ".jpg", ".jpeg", ".pdf", ".tif", ".gif"},
}

# Extensiones de Archivo Redundantes
REDUNDANT_PATTERNS = {
    "backup": [".bak", ".backup", ".old"],
    "temporary": [".tmp", ".temp", ".~"],
    "duplicate": ["#", ".dup", "_old"],
}

# Configuración de Exportación
EXPORT = {
    "excel_sheet_max_rows": 1000000,
    "include_timestamps": True,
    "auto_fit_columns": True,
}

# Configuración de Logging
LOGGING = {
    "enabled": True,
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "file": "logs/simular.log",
    "max_file_size": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5,
}

# Configuración de Rendimiento
PERFORMANCE = {
    "batch_size": 100,  # Tamaño de lote para operaciones BD
    "thread_pool_size": 4,  # Número de threads
    "cache_enabled": True,
    "cache_ttl": 3600,  # Tiempo de vida del caché en segundos
}

# Configuración de Validación
VALIDATION = {
    "min_title_length": 1,
    "max_title_length": 255,
    "require_description": False,
    "max_file_size_gb": 100,
}
