# simulAR - Gestor de Simulaciones Moleculares

## Descripción

**simulAR** es una aplicación de escritorio desarrollada en Python para la gestión, análisis y optimización del almacenamiento de simulaciones moleculares. Está diseñada para investigadores del grupo QuITEx y otros laboratorios que trabajan con herramientas como AMBER, GAMESS, Gaussian y Travis.

La aplicación ayuda a:
- 📁 **Organizar** simulaciones y sus archivos asociados
- 📊 **Analizar** resultados de manera automatizada y estandarizada
- 💾 **Optimizar** el almacenamiento identificando archivos innecesarios
- 📈 **Exportar** datos a Excel para análisis posterior
- 🗂️ **Centralizar** información en una base de datos local

## Características Principales

### 1. **Gestión de Simulaciones**
- Escaneo automático de directorios para detectar simulaciones
- Identificación del programa utilizado (AMBER, GAMESS, Gaussian, Travis, GROMACS, LAMMPS)
- Registro de metadata: título, fecha, tamaño, descripción
- Base de datos centralizada con SQLite

### 2. **Visualización de Información**
- Panel principal con todas las simulaciones cargadas
- Información del sistema: fecha actual y espacio disponible en disco
- Vista detallada de cada simulación con:
  - Lista completa de archivos
  - Métricas calculadas
  - Información del programa usado

### 3. **Análisis de Resultados**
- Cálculo automático de métricas (RMSD, radio de giro)
- Análisis de archivos de salida
- Generación de reportes
- Trazabilidad de cálculos realizados

### 4. **Optimización de Almacenamiento**
- Identificación de archivos redundantes
- Detección de archivos de backup y logs duplicados
- Recomendaciones de limpieza con estimación de espacio
- Eliminación controlada de archivos (siempre bajo control del usuario)

### 5. **Exportación de Datos**
- Exportar información de simulaciones a Excel
- Hojas separadas para información, archivos y métricas
- Exportación de múltiples simulaciones en un único archivo
- Formato profesional con estilos

## Requisitos del Sistema

- **Python 3.8 o superior**
- **Linux, macOS o Windows**
- **Dependencias** (ver `requirements.txt`):
  - PyQt6: Interfaz gráfica
  - openpyxl: Exportación a Excel
  - psutil: Información del sistema

## Instalación

### 1. Clonar o descargar el proyecto
```bash
cd simulAR
```

### 2. Crear un entorno virtual (recomendado)
```bash
# En Linux/macOS
python3 -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar la aplicación
```bash
python run_app.py
```

O en Linux/macOS:
```bash
./run_app.py
```

### Pasos iniciales

1. **Cargar simulaciones**:
   - Haz clic en el botón "Cargar Nueva Simulación"
   - Selecciona el directorio que contiene las simulaciones
   - La aplicación escaneará y detectará automáticamente las simulaciones

2. **Ver detalles de una simulación**:
   - Haz doble clic en una simulación de la tabla
   - O haz clic en el botón "Ver Detalle" de la fila

3. **Exportar a Excel**:
   - Abre el detalle de una simulación
   - Haz clic en "Exportar a Excel"
   - Selecciona el directorio de destino
   - Se creará un archivo .xlsx con toda la información

4. **Ejecutar análisis**:
   - Abre el detalle de una simulación
   - Haz clic en "Ejecutar Análisis"
   - Se mostrará un reporte con estadísticas y archivos redundantes

5. **Limpiar archivos**:
   - Abre el detalle de una simulación
   - Haz clic en "Limpiar Archivos"
   - Revisa la lista de archivos potencialmente redundantes
   - Confirma para proceder con la eliminación

## Estructura del Proyecto

```
simulAR/
├── run_app.py                 # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias Python
├── README.md                  # Este archivo
├── src/
│   ├── main_gui.py           # Interfaz gráfica principal
│   ├── database.py           # Gestión de base de datos SQLite
│   ├── simulation_manager.py # Gestión de simulaciones y archivos
│   ├── analysis.py           # Módulo de análisis y métricas
│   └── excel_export.py       # Exportador a Excel
├── data/
│   └── simulations.db        # Base de datos SQLite (generada automáticamente)
└── tests/                     # Pruebas unitarias (opcional)
```

## Módulos Principales

### `database.py`
Gestor de base de datos SQLite que almacena:
- Información de simulaciones
- Lista de archivos asociados
- Métricas calculadas
- Trazabilidad de operaciones

### `simulation_manager.py`
Herramientas para:
- Escanear directorios
- Detectar programas de simulación
- Calcular tamaños de archivos
- Eliminar archivos de forma segura
- Clasificar tipos de archivos

### `analysis.py`
Módulo de análisis que:
- Extrae RMSD y radio de giro
- Analiza archivos de salida
- Identifica archivos redundantes
- Calcula estadísticas
- Genera reportes

### `excel_export.py`
Exportador que genera:
- Hojas de información general
- Tablas de archivos
- Tablas de métricas
- Resúmenes de múltiples simulaciones

### `main_gui.py`
Interfaz gráfica con:
- Ventana principal con lista de simulaciones
- Ventana de detalle con información completa
- Diálogos de confirmación
- Threads para operaciones asincrónicas

## Flujo de Trabajo Típico

1. **Adquisición de Datos**: El usuario selecciona un directorio con simulaciones
2. **Detección Automática**: La aplicación identifica qué programas se utilizaron
3. **Almacenamiento**: La información se guarda en la base de datos local
4. **Análisis**: Se ejecutan análisis automáticos sobre los archivos
5. **Visualización**: El usuario puede ver resultados en la interfaz
6. **Exportación**: Se pueden exportar datos a Excel para análisis posterior
7. **Limpieza**: Se pueden eliminar archivos innecesarios de forma controlada

## Extensibilidad

La aplicación está diseñada para ser extensible. Para agregar nuevas funcionalidades:

### Agregar un nuevo programa de simulación
En `simulation_manager.py`, agregar la detección en el método `_detect_program()`:
```python
if any("mi_programa" in f for f in filenames_lower):
    return "Mi Programa"
```

### Agregar nuevas métricas
En `analysis.py`, agregar métodos similares a `calculate_rmsd()`:
```python
@staticmethod
def calculate_nueva_metrica(file_path: str) -> Optional[float]:
    # Implementar extracción de métrica
    pass
```

### Agregar nuevas columnas a Excel
En `excel_export.py`, modificar los métodos `_add_*_sheet()` para incluir nuevas columnas.

## Limitaciones y Consideraciones

- La aplicación no modifica los archivos de simulación, solo los lee y analiza
- Los archivos solo se eliminan cuando el usuario lo confirma explícitamente
- El análisis de métricas utiliza patrones regex; puede requerir ajustes según el formato específico de los archivos
- La base de datos SQLite funciona bien para miles de simulaciones; para volúmenes muy grandes, considerar PostgreSQL

## Troubleshooting

### La aplicación no inicia
- Verifica que tengas Python 3.8 o superior: `python --version`
- Instala las dependencias: `pip install -r requirements.txt`
- En sistemas Linux, podría necesitarse: `sudo apt-get install python3-pyqt6`

### No se detectan simulaciones
- Verifica que el directorio contenga archivos de simulación reconocidos
- Revisa `simulation_manager.py` para ver las extensiones soportadas
- Agrega más patrones de detección según sea necesario

### Errores de permisos al eliminar archivos
- Verifica que tengas permisos de lectura/escritura en el directorio
- En Linux/macOS, podría ser necesario `chmod` los archivos

### Problema con PyQt6 en Linux
- Algunos sistemas requieren instalación adicional:
  ```bash
  sudo apt-get install python3-pyqt6 libxkbcommon-x11-0
  ```

## Desarrollo Futuro

Mejoras previstas:
- [ ] Soporte para más formatos de simulación
- [ ] Gráficos interactivos de métricas
- [ ] Integración con Travis para análisis de trayectorias
- [ ] Sistema de reportes automáticos
- [ ] Historial de cambios y recuperación
- [ ] Búsqueda avanzada y filtrado
- [ ] Comparación entre simulaciones
- [ ] Cálculo de RMSD y radio de giro usando MDAnalysis

## Contribuir

Si deseas mejorar simulAR:
1. Haz un fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está disponible bajo la licencia MIT.

## Autores

Desarrollado como práctica supervisada para la carrera de Ingeniería en Sistemas de Información, ISI B, 5to año.

## Contacto

Para preguntas o sugerencias, contacta al equipo de desarrollo.

## Agradecimientos

- Grupo QuITEx - Por proporcionar los requerimientos y contexto del proyecto
- PyQt6 - Framework para la interfaz gráfica
- openpyxl - Librería para exportación a Excel
- Python - Lenguaje de programación utilizado

---

**Última actualización**: Octubre 2024
