# Guía de Desarrollo - simulAR

## Estructura del Código

### Jerarquía de Módulos

```
main_gui.py (Interfaz gráfica)
    ↓
    ├── database.py (Acceso a datos)
    ├── simulation_manager.py (Lógica de simulaciones)
    ├── analysis.py (Análisis de datos)
    └── excel_export.py (Exportación)
```

## Cómo Agregar Funcionalidades

### 1. Agregar Soporte para un Nuevo Programa de Simulación

Edita `src/simulation_manager.py`:

```python
# En _detect_program():
if any("nuevo_programa" in f for f in filenames_lower):
    return "NuevoPrograma"

# En KNOWN_PROGRAMS (opcional):
KNOWN_PROGRAMS = [..., "NuevoPrograma"]
```

### 2. Agregar Una Nueva Métrica

Edita `src/analysis.py`:

```python
@staticmethod
def calculate_nueva_metrica(file_path: str) -> Optional[float]:
    """
    Calcula la nueva métrica.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        Valor de la métrica o None
    """
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
        
        # Implementar extracción de la métrica
        pattern = r'METRICA\s*[=:]\s*([\d.]+)'
        matches = re.findall(pattern, content)
        if matches:
            return float(matches[-1])
    except Exception as e:
        print(f"Error calculando métrica: {e}")
    
    return None
```

Y en el método `analyze_output_file()`:

```python
nueva_metrica = AnalysisModule.calculate_nueva_metrica(file_path)
if nueva_metrica:
    analysis['metrics']['NuevaMetrica'] = nueva_metrica
```

### 3. Agregar Nuevas Columnas en Excel

Edita `src/excel_export.py`:

```python
@staticmethod
def _add_info_sheet(worksheet, sim_info: Dict):
    # ... código existente ...
    
    # Agregar nueva fila de datos
    data = [
        # ... datos existentes ...
        ("Nueva Propiedad", sim_info.get('nueva_propiedad', 'N/A')),
    ]
```

### 4. Agregar Nuevos Botones en la GUI

Edita `src/main_gui.py`:

En la clase `DetailWindow.init_ui()`:

```python
# Agregar nuevo botón
btn_nueva_accion = QPushButton("Nueva Acción")
btn_nueva_accion.clicked.connect(self.nueva_accion)
buttons_layout.addWidget(btn_nueva_accion)

# Agregar método correspondiente
def nueva_accion(self):
    """Ejecuta la nueva acción."""
    try:
        # Implementar lógica
        result = hacer_algo()
        QMessageBox.information(self, "Éxito", f"Acción completada: {result}")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Error: {str(e)}")
```

## Patrones de Código

### Patrón de Base de Datos

```python
# Abrir conexión
conn = sqlite3.connect(self.db_path)
cursor = conn.cursor()

# Ejecutar query
cursor.execute("SELECT * FROM tabla WHERE id = ?", (id,))

# Procesar resultados
result = cursor.fetchone()

# Cerrar conexión
conn.close()
```

### Patrón de Manejo de Errores

```python
try:
    # Código que puede fallar
    resultado = hacer_algo()
except ValueError as e:
    # Error específico de validación
    QMessageBox.warning(self, "Advertencia", str(e))
except Exception as e:
    # Error genérico
    QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
```

### Patrón de Threading para Operaciones Largas

```python
class MyWorker(QThread):
    finished = pyqtSignal(result_type)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            result = operacion_larga()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# En la ventana principal:
worker = MyWorker()
worker.finished.connect(self.on_finished)
worker.error.connect(self.on_error)
worker.start()
```

## Convenciones de Código

### Nombres de Variables

- **Simulaciones**: `sim`, `simulation`, `sim_info`
- **Archivos**: `file`, `file_info`, `file_path`
- **Base de datos**: `db`, `conn`, `cursor`
- **IDs**: `sim_id`, `file_id`, `metric_id`

### Docstrings

```python
def mi_funcion(param1: str, param2: int) -> Dict:
    """
    Descripción breve de la función.
    
    Descripción detallada si es necesaria.
    
    Args:
        param1: Descripción del parámetro 1
        param2: Descripción del parámetro 2
        
    Returns:
        Descripción del valor retornado
        
    Raises:
        ValueError: Si ocurre alguna validación
    """
    pass
```

### Tipos de Datos

Siempre incluir type hints:

```python
from typing import Dict, List, Optional, Tuple

def procesar_archivos(archivos: List[Dict]) -> Tuple[int, float]:
    pass

def obtener_simulacion(sim_id: int) -> Optional[Dict]:
    pass
```

## Testing

### Ejecutar Pruebas

```bash
python -m pytest tests/
# o
python -m unittest tests.test_modules
```

### Agregar Nuevas Pruebas

Edita `tests/test_modules.py`:

```python
class TestNuevoModulo(unittest.TestCase):
    """Pruebas del nuevo módulo."""
    
    def test_mi_funcion(self):
        """Prueba la función mi_funcion."""
        resultado = mi_funcion()
        self.assertEqual(resultado, valor_esperado)
```

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Mensaje de debug")
logger.info("Información")
logger.warning("Advertencia")
logger.error("Error")
```

### Puntos de Quiebre en IDE

- VSCode: F9 para establecer breakpoint
- PyCharm: Clic en la línea para establecer breakpoint
- Ejecutar con debugger: `python -m pdb main_gui.py`

## Performance

### Considerar para Grandes Volúmenes

1. **Paginación**: Para tablas con miles de filas
2. **Lazy Loading**: Cargar datos bajo demanda
3. **Índices en BD**: Para queries frecuentes
4. **Caché**: Para cálculos repetitivos
5. **Threads**: Para operaciones I/O largas

## Seguridad

### Buenas Prácticas

1. Validar entrada de usuario
2. Usar parameterized queries en SQL
3. No guardar datos sensibles en BD
4. Sanitizar rutas de archivos
5. Verificar permisos antes de operaciones

## Deployment

### Crear Ejecutable Standalone

```bash
pip install pyinstaller

pyinstaller \
    --onefile \
    --windowed \
    --icon=icon.ico \
    --name=simulAR \
    run_app.py
```

## Links Útiles

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [SQLite Python](https://docs.python.org/3/library/sqlite3.html)
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Contribuciones

Al contribuir:
1. Mantener consistencia con el código existente
2. Agregar docstrings completos
3. Incluir pruebas para nuevas funciones
4. Actualizar el README si es necesario
5. Seguir las convenciones de nombres

---

**Última actualización**: Octubre 2024
