# Relevamiento

(estructura de carpetas, tipos de archivos, tamaños, flujos actuales)

## Relevamiento del estado actual: Gestión de datos y flujos de trabajo en el laboratorio
Con el objetivo de planificar los próximos pasos en la optimización y automatización de procesos, se presenta un diagnóstico del estado actual del manejo de la información, el cual se caracteriza por una metodología mayoritariamente manual y artesanal.

### 1\. Estructura de carpetas y organización
Actualmente, la organización del almacenamiento depende en gran medida del criterio individual de cada operador o investigador, lo que genera inconsistencias. La estructura típica (cuando se mantiene) sigue un esquema basado en usuarios o proyectos:
*   Raíz del Servidor / Disco Local:
    *   `/[Nombre_Investigador, Usuario, Materia+Año]/`
        *   `/[Año_o_Proyecto]/`
            *   `/Inputs_o_Procesamiento/` (Archivos crudos, scripts de inicio)
            *   `/Outputs_o_Resultados/` (Archivos de salida, bitácoras)
            *   `/Backups_Temporales/` (Copias manuales muchas veces duplicadas)
> Nota crítica: No existe una nomenclatura estandarizada para el nombrado de archivos (ej. uso indiscriminado de "final", "test\_2", "copia\_buena"), lo que dificulta la trazabilidad y la búsqueda indexada.

### 2\. Tipos de Archivos Utilizados
El laboratorio opera de manera híbrida con herramientas de simulación molecular, química cuántica y análisis genéricos. Los principales formatos identificados se dividen según el software:
**Entorno AMBER (Dinámica Molecular):**
*       *   Estructuras y Coordenadas: Archivos `.pdb` (Protein Data Bank) y archivos `.inpcrd` o `.rst` (restart) para las coordenadas iniciales o reinicios de fases.
    *   Topologías y Parámetros: Archivos de topología molecular `.prmtop` , parámetros modificados `.frcmod` y librerías de residuos no estándar `.lib` o `.prepi`.
    *   Control y Configuración: Archivos `.mdin` que controlan las condiciones de la simulación (minimización, equilibración y producción).
    *   Trayectorias: Archivos binarios o ASCII de coordenadas a lo largo del tiempo, típicamente `.mdcrd` o archivos NetCDF `.nc`.
    *   Preparación: Archivos estructurales `.mol2` intermediarios para la asignación de cargas y visualización.
**Entorno GAMESS & Gaussian (Química Cuántica / Estructura Electrónica):**
*       *   Inputs: Archivos de entrada de texto plano `.inp` (para GAMESS) o formatos estructurados con comandos Link 0 y secciones de ruta (como `.com` o `.txt` para Gaussian).
    *   Outputs / Logs: Archivos de texto `.log` donde se vuelcan las energías, optimizaciones de geometría y frecuencias.
    *   Datos Auxiliares y Checkpoints: Archivos `.dat` (en GAMESS, para vectores, Hessianos e información de restart de IRC) y archivos de checkpoint `.chk` (en Gaussian, para almacenar la función de onda y reiniciar cálculos).

### 3\. Tamaños de los Datos y Almacenamiento
*   Archivos de entrada y configuración: Tamaño despreciable (pocos KB a MB) , compuestos principalmente por texto ASCII estructurado.
*   Archivos de salida estándar y checkpoints: Moderados (entre 10 MB y un par de GB según el tipo de cálculo).
*   Trayectorias y simulaciones dinámicas: Son los archivos críticos. Pueden oscilar entre 5 GB y más de 100 GB por tanda de simulación, dependiendo del número de átomos y de la frecuencia de guardado (pasos).
*   Infraestructura: El almacenamiento se realiza en discos locales de las estaciones de trabajo o en un almacenamiento en red (NAS) compartido sin políticas estrictas de depuración, lo que suele provocar saturación de espacio.

### 4\. Flujo de Trabajo Actual
El flujo operativo es secuencial y requiere supervisión humana constante en cada etapa intermediaria:

```css
[Preparación Manual] ──> [Lanzamiento de Trabajo] ──> [Monitoreo Visual] ──> [Extracción Manual]
```

1. Preparación: El usuario edita manualmente los archivos de entrada (añadiendo coordenadas, modificando bloques de texto o parámetros de fuerza).
2. Ejecución: Se lanzan los trabajos mediante scripts locales o comandos directos en la terminal. No hay un sistema centralizado o automatizado de colas que gestione eficientemente las prioridades del laboratorio.
3. Monitoreo: El seguimiento del estado de las tareas se hace "a ojo", abriendo intermitentemente los archivos `.log` o `.dat` para verificar que no haya errores (como fallas de convergencia o violaciones de restricciones).
4. Post-procesamiento: Una vez finalizado el cálculo, el investigador extrae manualmente las propiedades de interés empleando scripts propios independientes (scripts de Python, comandos de Bash sueltos o herramientas de análisis nativas).
5. Resguardo: Si el usuario lo recuerda, mueve los resultados finales al almacenamiento compartido; de lo contrario, permanecen en la máquina local de manera indefinida.

### 5\. Inventario de Software y Licenciamiento
Identificar qué herramientas se usan, en qué versiones y bajo qué condiciones legales, ya que esto limita o habilita la automatización en servidores compartidos.
*   Software libre vs. comercial: Detallar qué herramientas requieren licencias pagas (como Gaussian o ciertas versiones de AMBER comercial) y cuáles son académicas/libres (como GAMESS o herramientas de análisis).
*   Versiones en uso: Exponer si conviven versiones obsoletas (ej. scripts viejos que solo corren en versiones previas) por miedo a romper la compatibilidad, lo que frena actualizaciones de sistemas operativos.
### 6\. Infraestructura de Hardware y Cómputo (Capacidad de Ejecución)
El "dónde" se calcula es vital para entender las limitaciones actuales del flujo.
*   Estaciones de trabajo locales: Especificar si los cómputos se realizan en las PCs de escritorio de cada investigador (con procesadores o GPUs comerciales) o si se cuenta con un nodo/clúster centralizado.
*   Uso de GPU vs. CPU: Indicar si aprovechan aceleración por GPU (muy común y crítico para AMBER moderno) o si los cálculos cuánticos pesados (Gaussian/GAMESS) saturan los hilos de CPU de las máquinas de uso diario, ralentizando el resto de las tareas del personal.
### 7\. Políticas de Respaldo (Backup) y Seguridad de Datos
Poner en evidencia el nivel de riesgo de pérdida de información.
*   Inexistencia de automatización: Dejar constancia de que no existen tareas programadas (_cron jobs_) que respalden los discos locales de forma periódica.
*   Riesgo de pérdida: Si una estación de trabajo sufre una falla de hardware, se pierden semanas de cálculos de dinámicas moleculares que costaron tiempo de procesamiento y luz.
*   Control de versiones: Explicar cómo se gestionan los scripts de análisis caseros (¿están en un repositorio como GitHub/GitLab o se pasan por pendrive, Telegram o carpetas compartidas?).
### 8\. Perfil de los Usuarios y Brecha Digital
Muchas veces la precariedad no es por falta de equipamiento, sino por resistencia cultural o falta de capacitación técnica.
*   Nivel técnico informático: Describir si los operadores tienen buen dominio de la terminal Linux, Bash y Python, o si dependen exclusivamente de guías paso a paso (_copypaste_) sin entender el trasfondo informático, lo que dificulta que adopten sistemas de colas complejos.
*   Documentación interna: Evaluar si el conocimiento de "cómo se corre cada sistema" está documentado en un Readme/Wiki interno o si es puramente transmisión oral de un investigador senior a uno junior.
### 9\. Principales Puntos de Dolor (Pain Points) Identificados
Un resumen directo de las ineficiencias para justificar la inversión de tiempo en mejoras:
*   Tiempos muertos de hardware: Máquinas potentes inactivas los fines de semana porque nadie lanzó un trabajo manualmente, o colas virtuales formadas por investigadores "reservándose" PCs de palabra.
*   Inconsistencia de datos: Imposibilidad de que un investigador retome el trabajo de otro de años anteriores porque no entiende la lógica con la que se guardaron las trayectorias o los inputs cuánticos.

# Etapa 1



# Métricas claves

(RMSD, Rg, etc.) y herramientas a utilizar

# Mapeo de Herramientas, Archivos y Métricas de Análisis en el Laboratorio
Este documento establece la relación entre los datos crudos generados por los motores de simulación (AMBER, Gaussian, GAMESS) y las herramientas utilizadas para extraer información biológica, estructural o química de interés.
## 1\. El Pipeline de Datos: De la Simulación al Análisis
El flujo de información en el laboratorio no genera resultados directamente legibles de forma humana, sino que sigue una cadena de transformación:

```css
[Inputs de Configuración] ──> [Motor de Cálculo] ──> [Archivos Crudos Binarios/Texto] ──> [Software de Análisis] ──> [Métricas y Películas]
```

## 2\. Matriz de Herramientas y Formatos de Entrada/Salida
Para entender qué programas se deben automatizar u optimizar, es fundamental identificar qué archivos consumen y qué subproductos generan:

| Software / Entorno | Tipo de Herramienta | Archivos que Consume (Inputs) | Archivos que Genera (Outputs Crudos) |
| ---| ---| ---| --- |
| <br>AMBER / sander | Motor de Simulación (Dinámica Molecular) | `.prmtop` (Topología) , `.inpcrd` / `.rst` (Coordenadas) , `.mdin` (Control) | `.nc` / `.mdcrd` (Trayectorias binarias), `.mdout` (Log de energías en texto) |
| <br>Gaussian / GAMESS | Motores de Cálculo (Química Cuántica) | <br>`.com`, `.inp`, `.txt` (Configuración y coordenadas iniciales) | <br>`.log` / `.out` (Texto plano con energías y frecuencias) , `.chk` / `.dat` (Checkpoints y matrices binarias) |
| <br>cpptraj (AmberTools) | Procesamiento de Datos y Análisis de Trayectorias | <br>`.prmtop` (Topología) , `.nc` / `.mdcrd` (Trayectorias) | Archivos de datos estructurados (`.dat`, `.txt`) con valores numéricos filtrados, nuevas trayectorias reducidas |
| VMD / PyMOL | Visualizadores Estructura Molecular | <br>`.pdb` (Estático), `.prmtop` + `.nc` (Dinámico) | Animaciones ("Películas" de la simulación), renders de alta calidad, mapas de densidad de carga. |

## 3\. "Métricas" Clave Extraídas (¿Qué busca el investigador?)
Dado que la simulación no devuelve respuestas directas, los investigadores ejecutan scripts de análisis (principalmente a través de `cpptraj` o scripts propios en Python) para extraer las siguientes métricas indirectas:
### A. Métricas de Estabilidad y Dinámica Estructural
*   RMSD (Root-Mean-Square Deviation): Mide cuánto se deforma o se aleja la proteína de su estructura inicial a lo largo del tiempo. Es la métrica analítica número uno para saber si la simulación es estable o si el sistema "explotó".
*   RMSF (Root-Mean-Square Fluctuation): Evalúa qué partes o aminoácidos específicos de la proteína son los que más se mueven o tienen mayor flexibilidad durante la simulación.
*   Radio de Giro ($R\_g$): Mide el grado de compactación de la estructura molecular. Sirve para determinar si la proteína se mantiene plegada o si se está desplegando en el agua.
### B. Métricas de Interacción Química
*   Análisis de Puentes de Hidrógeno: Cuenta la cantidad y persistencia de las interacciones de hidrógeno formadas y destruidas a lo largo del tiempo (clave para estudiar cómo se une un fármaco a una proteína).
*   Energía Libre de Unión (MM/PBSA o MM/GBSA): Cálculos post-procesamiento que toman las trayectorias para estimar numéricamente la fuerza con la que se unen dos moléculas.
### C. Métricas de Química Cuántica (Gaussian/GAMESS)
*   Optimización de Geometría: Distancias y ángulos de enlace exactos del estado de mínima energía de una molécula.
*   Frecuencias Vibracionales: Valores numéricos que confirman si la estructura hallada es un mínimo real o un estado de transición (punto de silla).
*   Energías de Orbitales (HOMO / LUMO): Valores que definen la reactividad química de la molécula analizada.
## 4\. Consideraciones para la Futura Optimización del Flujo
Teniendo claro que el cuello de botella está en el procesamiento y la traducción de estos archivos, cualquier propuesta de modernización para el laboratorio debería apuntar a:
1. Automatizar la extracción inicial: Crear scripts que, apenas termine una simulación con `sander`/`pmemd`, ejecuten automáticamente un set estándar de `cpptraj` para escupir los gráficos de RMSD y Radio de Giro.
2. Reducción de espacio mediante filtrado: Las trayectorias crudas (`.nc`) pesan decenas de gigabytes porque guardan cada molécula de agua de la caja. Una herramienta clave de `cpptraj` es quitar el agua sobrante y guardar una trayectoria "limpia y liviana", que es la que el usuario finalmente se descarga a su PC local para armar los videos de las moléculas.

# Arquitectura

(módulos, flujo de datos, separación UI / lógica)

## 1\. Estructura Modular del Sistema
Al utilizar FastAPI, podemos aplicar un patrón arquitectónico limpio separando las responsabilidades en capas muy bien definidas:

```cs
mi_proyecto/
│
├── app/
│   ├── database.py          # Configuración y conexión a SQLite
│   ├── main.py              # Punto de entrada de FastAPI y rutas principales
│   │
│   ├── models/              # Modelos de datos (Tablas de SQLAlchemy)
│   │   ├── simulación.py
│   │   └── métrica.py
│   │
│   ├── services/            # LÓGICA DE NEGOCIO (Python puro)
│   │   ├── escáner.py       # Módulo 1: Escaneo de directorios y metadata
│   │   └── analizador.py    # Módulo 2: Pipeline de cpptraj y extracción de datos
│   │
│   ├── templates/           # CAPA DE INTERFAZ (UI)
│   │   ├── base.html        # Estructura común (Navbar, Sidebar)
│   │   ├── dashboard.html   # Listado y estado del almacenamiento
│   │   └── detalle.html     # Visualización interactiva de RMSD / Radio de Giro
│   └── static/              # Estilos CSS y scripts JS (Gráficos)
```

## 2\. Flujo de Datos y Separación UI / Lógica
Para cumplir con las buenas prácticas de ingeniería de software, la interfaz de usuario no debe saber _cómo_ se calcula un RMSD, y el motor de análisis no debe saber _cómo_ se renderiza una página web.

```scss
[ Navegador Web ] (HTML/JS)
       │  ▲
       │  │  Peticiones HTTP (GET/POST)
       ▼  │
[ Rutas de FastAPI (main.py) ]  <───> [ Base de Datos (SQLite) ]
       │  ▲
       │  │  Invoca funciones de negocio y pasa datos limpios
       ▼  │
[ Capa de Servicios (Services) ]
       │
       ├─► escáner.py    ──► (Explora el Sistema de Archivos Local)
       └─► analizador.py ──► (Ejecuta subprocesos de cpptraj en segundo plano)
```

### Paso a paso del flujo de información:
1. Petición del Usuario: El investigador entra a la web local ([`http://localhost:8000`](http://localhost:8000)) y hace clic en _"Escanear Carpeta de Simulaciones"_.
2. Controlador (FastAPI): Recibe la ruta del directorio local enviada por el formulario.
3. Capa de Lógica (Módulo 1 - Escáner): Un script de Python recorre la ruta usando `os.walk`, detecta estructuras válidas (archivos `.prmtop`, `.nc`, `.log`) y extrae los metadatos (tamaño, fecha).
4. Persistencia: La lógica guarda este registro en la base de datos local SQLite.
5. Capa de Lógica (Módulo 2 - Analizador): Si el usuario solicita analizar, el servicio invoca a `cpptraj` en segundo plano mediante el módulo `subprocess` de Python, procesa el output numérico generado (`.dat`) y guarda los vectores de RMSD o Radio de Giro en la base de datos.
6. Renderizado (UI): FastAPI toma los datos de la base de datos, los inyecta en la plantilla Jinja2 (`detalle.html`) y Chart.js dibuja de manera interactiva las curvas científicas en la pantalla del usuario.
## 3\. Adaptación de los Módulos a la nueva Arquitectura
### Módulo 1: Gestión de Simulaciones (Local + Web)
*   En la Lógica (Backend): Python aprovecha que corre en la misma máquina que los archivos. Al recibir comandos del navegador, lee directamente el disco local.
*   En la UI (Frontend): En lugar de ventanas emergentes nativas de escritorio, diseñas un formulario web simple con un campo de texto para pegar la ruta absoluta del directorio a analizar (ej: `/home/usuario/simulaciones/proteina1`).
### Módulo 2: Análisis y Estandarización de Resultados
*   En la Lógica (Backend): El pipeline automatizado se ejecuta mediante hilos secundarios (_Background Tasks_ de FastAPI). Esto evita que la página web se "congele" o tire un error de "Timeout" mientras `cpptraj` procesa archivos pesados de varios gigabytes.
*   En la UI (Frontend): Implementas una barra de progreso web o un indicador visual de _"Procesando..."_ que consulte periódicamente al backend si el pipeline numérico ya terminó para refrescar los gráficos.
## 4\. Impacto en el Plan de Trabajo
Esta propuesta no altera los objetivos core de tu PPS ni las horas estimadas (200 hs totales). Solo reenfoca tecnológicamente las tareas de la Etapa 4 (Desarrollo de Interfaz Gráfica):
*   En lugar de _"Implementar ventana principal en PySide6"_, se hará _"Implementar vistas de Dashboard y listados en HTML/Jinja2"_.
*   Las asignaturas involucradas siguen aplicando a la perfección: _Ingeniería de Software_ para la separación de capas, _Sistemas Operativos_ para manejar rutas del servidor, y _Bases de Datos_ para el repositorio SQLite.
# ¿Por qué se ocupa determinada tecnología?
## 1\. Capa de API y Lógica de Negocio (Back-end)
### Python
*   Definición: Lenguaje de programación de alto nivel, interpretado y multiparadigma, ampliamente utilizado en computación científica y desarrollo web.
*   Justificación: Es el estándar _de facto_ en el ámbito del laboratorio QuITEx. El plan original ya lo contemplaba debido a su excelente ecosistema para interactuar con sistemas operativos (manejo de rutas y archivos) y su integración nativa con librerías de análisis de datos científicos.
### FastAPI
*   Definición: Un framework web moderno, de alto rendimiento y ágil para construir APIs con Python, basado en los estándares abiertos OpenAPI y JSON Schema.
*   Justificación: Permite levantar un servidor local liviano en la máquina del investigador de manera inmediata. Es extremadamente veloz y maneja de forma nativa la asincronía, lo que facilita la creación de tareas en segundo plano (_Background Tasks_) para que la interfaz no se congele mientras se procesan archivos pesados.
### Uvicorn
*   Definición: Una implementación de servidor web ASGI (Asynchronous Server Gateway Interface) para Python, ultrarrápida y de producción.
*   Justificación: Es el motor que "corre" la aplicación FastAPI localmente. Al ejecutarse en el entorno de la máquina host del laboratorio, actúa como el puente que le permite al navegador web interactuar de forma segura con los scripts locales de Python.
### Pydantic
*   Definición: Librería de validación de datos y gestión de configuraciones basada en anotaciones de tipos de Python.
*   Justificación: Garantiza que los datos que viajan desde la interfaz web (como la ruta de una carpeta copiada por el usuario) cumplan con el formato estructurado correcto antes de que pasen a los módulos de análisis, evitando excepciones o errores en tiempo de ejecución.
### Subprocess (Módulo nativo de Python)
*   Definición: Módulo estándar de Python que permite generar nuevos procesos, conectarse a sus tuberías de entrada/salida/error y obtener sus códigos de retorno.
*   Justificación: Crucial para el Módulo 2 (Analizador). Es la herramienta informática que permite a Python "tipear en la consola oculta" y ejecutar los comandos de las herramientas científicas del laboratorio (como `cpptraj` de AmberTools) , capturando sus outputs numéricos directos.
## 2\. Capa de Base de Datos y Persistencia
### SQLite
*   Definición: Un motor de base de datos relacional SQL autónomo, empotrado (embebido), de alta confiabilidad y que no requiere un servidor independiente.
*   Justificación: El Plan de Trabajo estipula la necesidad de una base de datos local y centralizada. Al ser un archivo local dentro del proyecto, SQLite elimina la complejidad de tener que instalar y configurar servidores pesados (como MySQL o PostgreSQL) en cada computadora del laboratorio, cumpliendo con la premisa de ser una aplicación liviana.
### SQLAlchemy (ORM)
*   Definición: Un Kit de herramientas SQL y un mapeador objeto-relacional (ORM) para Python.
*   Justificación: Permite interactuar con las tablas de SQLite utilizando clases y objetos de Python puros en lugar de escribir consultas SQL manuales. Esto acelera drásticamente el desarrollo de la capa de acceso a datos (CRUD de simulaciones y métricas).
## 3\. Capa de Interfaz de Usuario (Front-end)
### HTML5 y CSS3 (Tailwind CSS)
*   Definición: HTML5 es el lenguaje de marcado estándar para estructurar páginas web; Tailwind CSS es un framework de CSS orientado a utilidades para diseñar interfaces rápidamente.
*   Justificación: Reemplazan los componentes rígidos de escritorio por un diseño web moderno, responsivo y estético. Tailwind permite estructurar visualmente un _Dashboard_ limpio para el laboratorio sin sobrecargar el código de la interfaz.
### Jinja2
*   Definición: Un motor de plantillas de diseño rápido, expresivo y extensible para Python.
*   Justificación: Integrado por defecto con FastAPI. Permite "inyectar" los datos provenientes de SQLite (como la lista de simulaciones detectadas o el tamaño de los archivos) directamente dentro del código HTML antes de enviarlo al navegador.
### JavaScript + Chart.js / Plotly
*   Definición: JavaScript es el lenguaje de programación del lado del cliente en la web; Chart.js y Plotly son librerías robustas especializadas en el renderizado de gráficos estadísticos y científicos interactivos.
*   Justificación: Permite al investigador interactuar con las métricas clave calculadas (RMSD, Radio de Giro). En lugar de generar una imagen estática, el usuario puede hacer zoom, ocultar curvas y recorrer los puntos de la trayectoria molecular en tiempo real directamente sobre el navegador.
## 4\. Tecnologías Reemplazadas (Análisis de Cambios respecto al Plan de Trabajo)
El cambio arquitectónico implica descartar ciertas herramientas mencionadas originalmente en tu plan. A continuación se justifica técnicamente cada reemplazo:
### PySide6 / Qt (Reemplazado por FastAPI + HTML/Jinja2)
*   ¿Qué es? El binding oficial de Python para la biblioteca gráfica multiplataforma Qt, usado para aplicaciones de escritorio nativas.
*   Por qué NO se utiliza: PySide6 requiere instalar librerías gráficas pesadas en el sistema operativo y su curva de diseño para interfaces fluidas es elevada. Al cambiar a un entorno web con FastAPI, la interfaz se independiza del sistema operativo (corre idéntico en Windows 11 o Linux/WSL) y se vuelve escalable: si el laboratorio decide centralizar la herramienta en un servidor web del anexo, no habrá que reinstalar código en las terminales de los alumnos.
### Matplotlib (Reemplazado por Chart.js / Plotly en Front-end)
*   ¿Qué es? Una librería clásica de Python para la generación de gráficos estáticos, animados e interactivos.
*   Por qué NO se utiliza: Aunque Matplotlib es excelente para scripts científicos, al integrarse con aplicaciones visuales tiende a exportar los gráficos como imágenes estáticas (`.png`) o requiere incrustar ventanas de dibujo complejas. Delegar los gráficos a Chart.js o Plotly en el Front-end permite que el procesamiento del servidor web se concentre puramente en los datos numéricos crudos, logrando una experiencia de usuario mucho más fluida, moderna e interactiva.

# Modelo de datos

## El Modelo de Datos
La estructura elegida es un Modelo Híbrido Estructurado. En lugar de crear millones de filas en una tabla de series temporales, agrupamos los vectores de datos calculados por `cpptraj` dentro de un único registro estructurado en formato de texto o binario nativo.
El esquema de tablas queda de la siguiente manera:
*   Tabla `Simulacion`: Almacena la cabecera de la corrida científica.
    *   _Campos:_ `id` (PK), `nombre`, `ruta_absoluta` (clave para encontrarla localmente y borrar archivos), `software` (AMBER, Gaussian, etc.), `fecha_registro`, `metadata_json`.
*   Tabla `Archivo`: Mapea de forma relacional (1 a N con Simulación) los archivos detectados en el disco.
    *   _Campos:_ `id` (PK), `simulacion_id` (FK), `nombre_archivo`, `extension`, `tamaño_bytes`, `tipo` (Input / Output / Trajectory).
*   Tabla `Resultado_Metrica`: Almacena el "jugo" extraído de los análisis para graficar.
    *   _Campos:_ `id` (PK), `simulacion_id` (FK), `tipo_metrica` (RMSD, Radio de Giro, etc.), `valores_tiempo_json` (campo `TEXT` en desarrollo / `JSONB` en producción). Contiene el vector completo (ej: `[0.15, 0.22, 0.31, ...]`).
## Tecnologías a Utilizar
### En Desarrollo (Entorno Local y de Pruebas):
*   Backend: FastAPI (Python) corriendo en `localhost`.
*   Base de Datos: SQLite (un archivo local `.db` autogenerado en la raíz del proyecto).
*   Librería de Conexión: SQLAlchemy (ORM) configurado con un driver SQLite.
### En Producción (Entorno de Laboratorio / Nube Centralizado):
*   Backend: FastAPI (Python) corriendo en la computadora o servidor central del laboratorio QuITEx.
*   Base de Datos: Supabase (PostgreSQL) alojado en la nube en su plan gratuito.
*   Librería de Conexión: SQLAlchemy (ORM) configurado con el driver de PostgreSQL (`psycopg2` o `asyncpg`).
## Estrategia Híbrida: ¿Cómo trabajar con ambas a la vez?
Para que la transición de SQLite a Supabase no te rompa el programa, vas a implementar una arquitectura desacoplada usando las bondades de SQLAlchemy.
En tu archivo de configuración ([`config.py`](http://config.py) o las variables de entorno `.env`), manejarás una sola variable encargada de la conexión, alternando su valor según dónde estés trabajando:
Python

```haskell
import os

# Si estás en tu PC probando: lee la local. Si estás en producción, lee Supabase
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./simular_local.db")
```

Como tu lógica de negocio (el escaneo de carpetas con `os.walk`, la ejecución de procesos de consola mediante `subprocess` y las inserciones de datos) interactúa únicamente con los modelos declarativos de SQLAlchemy, el cambio de motor es 100% transparente para Python.
Cuando uses SQLite, el vector se guardará como texto plano en el archivo local; cuando cambies la URL a la de Supabase, SQLAlchemy se encargará de traducir automáticamente ese mismo objeto a una columna binaria avanzada `JSONB` en la nube de PostgreSQL.
## Qué debes investigar para arrancar
Para encarar con éxito la primera etapa de desarrollo, priorizá investigar estos conceptos específicos:
1. Declarative Mapping Moderno en SQLAlchemy (v2.0): Estudiá cómo definir tus tablas usando el tipado moderno de Python con `Mapped[...]` y `mapped_column()`. Esto te ahorrará muchos errores de código.
2. Manejo del tipo JSON en SQLAlchemy: Investigá cómo declarar una columna que sea interpretada automáticamente como JSON por el ORM (usando `sqlalchemy.types.JSON`), asegurándote de que sea compatible tanto con el `TEXT` de SQLite como con el `JSONB` de PostgreSQL.
3. Variables de Entorno en Python (`python-dotenv`): Aprendé a estructurar un archivo `.env` local para gestionar de manera limpia las credenciales de base de datos sin exponerlas públicamente en tu repositorio.
4. Operaciones en Cascada (Cascade Deletes) en el ORM: Fundamental para tu módulo de optimización de almacenamiento. Investigá cómo configurar las relaciones de SQLAlchemy para que, al eliminar una simulación por su ruta local, la base de datos borre automáticamente en cadena todos los registros de sus archivos y métricas asociadas.

# Plan ajustado

# Plan General de Desarrollo: Proyecto simulAR

```css
[Etapa 1: Fundaciones] ──> [Etapa 2: Pipeline Local] ──> [Etapa 3: UI e Integración] ──> [Etapa 4: Supabase & Cierre]
```

## Etapa 1: Fundaciones, Entorno e Infraestructura Base (Estimación: 35 horas)
El objetivo de esta etapa es dejar listo tu espacio de trabajo y el "molde" donde se van a guardar los datos del laboratorio, asegurándote un desarrollo rápido sin dependencias externas.
*   Fase 1.1: Entorno Virtual y Core Backend
    *   Configurar el entorno de Python 3.11+ con `FastAPI` y `Uvicorn`.
    *   Verificar el acceso a las herramientas de consola como `cpptraj` mediante la terminal (WSL/Linux).
*   Fase 1.2: Modelado de Datos y Persistencia Local (SQLite)
    *   Crear el archivo [`models.py`](http://models.py) usando el mapeo declarativo moderno de SQLAlchemy 2.0.
    *   Implementar las tres entidades clave bajo la Propuesta B: `Simulacion`, `Archivo` y `Resultado_Metrica`.
    *   Configurar el tipo `JSON` genérico en SQLAlchemy para que lea y escriba los vectores numéricos de manera transparente.
    *   Establecer la cadena de conexión dinámica (`sqlite:///./simular_local.db`).
## Etapa 2: Módulos de Lógica y Pipeline Científico Local (Estimación: 65 horas)
Aquí programarás el "motor" de tu aplicación. Todo corre de forma local en la máquina del laboratorio para tener acceso directo y veloz a los discos duros y archivos pesados.
*   Fase 2.1: Módulo 1 - Escaneo y Catalogación de Archivos
    *   Desarrollar la lógica con `os.walk` para rastrear las carpetas de simulación proporcionadas por el usuario.
    *   Filtrar e identificar archivos críticos de Dinámica Molecular (topologías `.prmtop`, trayectorias `.nc`, archivos `.log`).
    *   Extraer metadatos físicos (tamaño en bytes, nombre, extensiones) e insertarlos en las tablas `Simulacion` y `Archivo`.
*   Fase 2.2: Módulo 2 - Pipeline de Extracción Analítica
    *   Implementar el llamado a tareas en segundo plano (_Background Tasks_) en FastAPI para no congelar la aplicación.
    *   Utilizar el módulo `subprocess` de Python para automatizar la ejecución de `cpptraj` sobre las trayectorias pesadas del disco.
    *   Escribir los scripts de análisis dinámicos (comandos para calcular RMSD y Radio de Giro).
*   Fase 2.3: Módulo 3 - Parseo, Serialización y Optimización
    *   Programar el lector que procesa los archivos `.dat` temporales generados por `cpptraj`.
    *   Transformar las columnas de texto en vectores/arrays puros de Python (ej. `[0.12, 0.23, ...]`).
    *   Guardar dichos vectores en la tabla `Resultado_Metrica` y ejecutar la limpieza de archivos temporales.
    *   Implementar la función de Borrado en Cascada y eliminación física de archivos redundantes en el disco local para cumplir con el objetivo de optimización de almacenamiento.
## Etapa 3: Interfaz de Usuario (UI) y Visualización Interactiva (Estimación: 50 horas)
En esta etapa le darás forma visual al sistema, permitiendo que los investigadores interactúen con el backend y vean los gráficos científicos de forma fluida.
*   Fase 3.1: Vistas y Renderizado Dinámico
    *   Configurar Jinja2 en FastAPI para servir plantillas HTML estructuradas.
    *   Diseñar la maquetación visual (Panel de control, buscador de simulaciones, indicador de carga de tareas) utilizando Tailwind CSS.
*   Fase 3.2: Módulo de Graficación (Front-end)
    *   Crear los endpoints en FastAPI que devuelven los vectores numéricos en formato JSON de manera ultra veloz.
    *   Integrar Chart.js (o Plotly) en las plantillas HTML.
    *   Conectar los datos del endpoint para renderizar gráficos dinámicos e interactivos de las series temporales (curvas de RMSD frente al tiempo).
## Etapa 4: Conexión a Supabase, Validación y Cierre (Estimación: 50 horas)
Una vez que el sistema funciona perfectamente al 100% en tu computadora, es momento de conectarlo con el entorno centralizado de producción en la nube y finalizar la documentación.
*   Fase 4.1: Migración a Supabase (PostgreSQL Cloud)
    *   Crear la cuenta y el proyecto en el plan gratuito de Supabase.
    *   Crear las tablas en Supabase ejecutando el script SQL generado por tus modelos o configurándolas desde su panel.
    *   Configurar las variables de entorno (`.env`) en la aplicación para apuntar la `DATABASE_URL` hacia la URL de conexión de Supabase.
    *   Validar que al escanear una simulación local, el backend extraiga los vectores numéricos y los envíe exitosamente a la columna binaria `JSONB` de Supabase a través de internet.
*   Fase 4.2: Pruebas Integrales con Usuarios Reales
    *   Desplegar el backend de FastAPI de forma local en una computadora del laboratorio QuITEx.
    *   Realizar pruebas con archivos reales de los investigadores para verificar tiempos de respuesta, estabilidad del pipeline y correcto dibujado de gráficos.
*   Fase 4.3: Documentación Final de la PPS
    *   Redactar el informe final detallando la arquitectura web híbrida implementada.
    *   Incluir el diagrama Entidad-Relación final (Modelo B) y justificar el uso mixto de SQLite (Desarrollo) y Supabase/PostgreSQL (Producción).
    *   Preparar la presentación para la defensa de la práctica en la UTN.

# Etapa 2

