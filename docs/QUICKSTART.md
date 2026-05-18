# INSTALACIÓN Y PRIMEROS PASOS - simulAR

## 🚀 Instalación Rápida

### 1. Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

Verifica tu versión de Python:
```bash
python --version
# o en algunos sistemas
python3 --version
```

### 2. Instalar Dependencias

Navega al directorio del proyecto:
```bash
cd simulAR
```

Crea un entorno virtual (recomendado):
```bash
# En Linux/macOS
python3 -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
venv\Scripts\activate
```

Instala las dependencias:
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la Aplicación

```bash
python run_app.py
```

O en Linux/macOS (si le asignaste permisos de ejecución):
```bash
./run_app.py
```

## 📋 Estructura del Proyecto

```
simulAR/
├── run_app.py                 # 🎬 Punto de entrada - ejecutar esto
├── examples.py                # 📚 Ejemplos de uso sin GUI
├── config.py                  # ⚙️ Configuración personalizable
├── requirements.txt           # 📦 Dependencias
├── README.md                  # 📖 Documentación completa
├── DEVELOPMENT.md             # 👨‍💻 Guía de desarrollo
├── QUICKSTART.md              # ⚡ Este archivo
│
├── src/
│   ├── main_gui.py           # 🖥️ Interfaz gráfica
│   ├── database.py           # 🗄️ Gestión de BD
│   ├── simulation_manager.py # 📁 Gestor de simulaciones
│   ├── analysis.py           # 📊 Análisis de datos
│   └── excel_export.py       # 📈 Exportación a Excel
│
├── data/
│   └── simulations.db        # 📋 BD (se crea automáticamente)
│
└── tests/
    └── test_modules.py       # ✅ Pruebas unitarias
```

## 🎯 Primer Uso

### Paso 1: Ejecutar la aplicación
```bash
python run_app.py
```

### Paso 2: Cargar simulaciones
1. Haz clic en **"Cargar Nueva Simulación"** (botón verde)
2. Selecciona la carpeta que contiene tus simulaciones
3. La aplicación escaneará automáticamente

### Paso 3: Ver detalles
- **Doble clic** en una simulación para ver detalles
- O haz clic en **"Ver Detalle"**

### Paso 4: Acciones disponibles
En la ventana de detalle puedes:
- **Exportar a Excel**: Genera un archivo .xlsx con toda la información
- **Ejecutar Análisis**: Genera un reporte con estadísticas
- **Limpiar Archivos**: Identifica y elimina archivos innecesarios

## 🧪 Ejemplos sin GUI

Si prefieres usar la aplicación sin interfaz gráfica:

```bash
python examples.py
```

Este script demuestra:
1. Crear simulaciones en la BD
2. Analizar archivos
3. Exportar a Excel
4. Escanear directorios

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'PyQt6'"
**Solución**: Instala las dependencias
```bash
pip install -r requirements.txt
```

### Error: "Could not connect to display"
**Solución** (Linux sin GUI):
```bash
export QT_QPA_PLATFORM=offscreen
python run_app.py
```

### Error: Permisos negados al eliminar archivos
**Solución**: Verifica que tengas permisos en el directorio
```bash
chmod 755 /ruta/del/directorio
```

### No se detectan simulaciones
**Solución**: Verifica que los archivos tengan extensiones reconocidas
- Ver `config.py` para ver extensiones soportadas
- Ver `simulation_manager.py` para agregar más tipos

## 📚 Archivos Importantes

- **README.md** - Documentación completa del proyecto
- **DEVELOPMENT.md** - Guía para desarrolladores
- **config.py** - Personaliza la aplicación aquí
- **examples.py** - Aprende cómo usar los módulos

## 🔗 Próximos Pasos

1. Lee **README.md** para entender todas las características
2. Consulta **DEVELOPMENT.md** para personalizaciones
3. Explora **examples.py** para ver casos de uso
4. Modifica **config.py** según tus necesidades

## 📞 Soporte

Si encuentras problemas:
1. Verifica los logs en `logs/simular.log`
2. Revisa la sección "Troubleshooting" en README.md
3. Consulta DEVELOPMENT.md para debugging

## ✨ Características Principales

✅ Gestión centralizada de simulaciones  
✅ Detección automática de programas (AMBER, GAMESS, Gaussian, Travis, etc.)  
✅ Base de datos SQLite integrada  
✅ Análisis automático de resultados  
✅ Exportación a Excel con formato profesional  
✅ Limpieza de archivos redundantes  
✅ Interfaz gráfica intuitiva  
✅ Totalmente extensible  

## 🎓 Información del Proyecto

- **Carrera**: Ingeniería en Sistemas de Información (ISI B)
- **Año**: 5to año
- **Tipo**: Práctica Supervisada (PS)
- **Grupo**: QuITEx - Química Teórica Experimental
- **Objetivo**: Gestión y análisis de simulaciones moleculares

---

**¡Listo para empezar! 🚀**

Ejecuta `python run_app.py` y disfruta de simulAR.
