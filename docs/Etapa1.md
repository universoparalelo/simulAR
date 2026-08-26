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
| <br>GROMACS | Motor de Simulación (Dinámica Molecular) | `.gro` (Coordenadas) , `.top` (Topología) , `.mdp` (Parámetros) | `.xtc` / `.trr` (Trayectorias binarias), `.log` (Log de energías), `.edr` (Energía binaria) |
| <br>MDAnalysis (Python) | Procesamiento de Datos y Análisis de Trayectorias | Topologías (`.prmtop`, `.pdb`, `.gro`, `.top`) + Trayectorias (`.nc`, `.dcd`, `.xtc`) | Arrays numéricos en memoria (RMSF, RMSD, Rg) serializados como JSON en la DB |
| <br>cpptraj (AmberTools) | Procesamiento de Datos y Análisis de Trayectorias (trayectorias > 200 MB) | <br>`.prmtop` (Topología) , `.nc` / `.mdcrd` (Trayectorias) | Archivos de datos estructurados (`.dat`, `.txt`) con valores numéricos filtrados, nuevas trayectorias reducidas |
| VMD / PyMOL | Visualizadores Estructura Molecular | <br>`.pdb` (Estático), `.prmtop` + `.nc` (Dinámico) | Animaciones ("Películas" de la simulación), renders de alta calidad, mapas de densidad de carga. |

> **Nota de implementación:** En la versión actual de simulAR, el motor principal de análisis es **MDAnalysis** (librería de Python integrada directamente en el backend). cpptraj se usa como fallback automático para trayectorias que superan los 200 MB, ya que es más eficiente con archivos grandes. La detección del motor es transparente para el usuario.

## 3\. "Métricas" Clave Extraídas (¿Qué busca el investigador?)
Dado que la simulación no devuelve respuestas directas, los investigadores ejecutan scripts de análisis (principalmente a través de MDAnalysis o `cpptraj`) para extraer las siguientes métricas indirectas:
### A. Métricas de Estabilidad y Dinámica Estructural
*   **RMSF (Root-Mean-Square Fluctuation):** Evalúa qué partes o residuos específicos de la proteína son los que más se mueven o tienen mayor flexibilidad durante la simulación. Es la **métrica principal** del laboratorio QuITEx y se calcula por defecto al analizar una simulación con trayectoria.
*   RMSD (Root-Mean-Square Deviation): Mide cuánto se deforma o se aleja la proteína de su estructura inicial a lo largo del tiempo. Sirve para saber si la simulación es estable o si el sistema "explotó". Se ofrece como análisis extra opcional.
*   Radio de Giro ($R\_g$): Mide el grado de compactación de la estructura molecular. Sirve para determinar si la proteína se mantiene plegada o si se está desplegando en el agua. Se ofrece como análisis extra opcional.
### A-bis. Métricas de Simulaciones sin Trayectoria (Minimización)
*   Energía de minimización: Para simulaciones que no producen trayectoria temporal (solo archivos `.mdin`, `.out`, `.rst`), el sistema parsea la curva de energía del archivo `.out` con regex y grafica la convergencia energética paso a paso.
*   Propiedades estáticas: Número de residuos (moléculas), radio de giro estático y masa total de la estructura cargada.
### B. Métricas de Interacción Química
*   Análisis de Puentes de Hidrógeno: Cuenta la cantidad y persistencia de las interacciones de hidrógeno formadas y destruidas a lo largo del tiempo (clave para estudiar cómo se une un fármaco a una proteína).
*   Energía Libre de Unión (MM/PBSA o MM/GBSA): Cálculos post-procesamiento que toman las trayectorias para estimar numéricamente la fuerza con la que se unen dos moléculas.
### C. Métricas de Química Cuántica (Gaussian/GAMESS)
*   Optimización de Geometría: Distancias y ángulos de enlace exactos del estado de mínima energía de una molécula.
*   Frecuencias Vibracionales: Valores numéricos que confirman si la estructura hallada es un mínimo real o un estado de transición (punto de silla).
*   Energías de Orbitales (HOMO / LUMO): Valores que definen la reactividad química de la molécula analizada.
### D. Configuración de Análisis por Métrica
El usuario puede configurar cada métrica individualmente al momento de ejecutar el análisis:
*   **Selección de átomos:** C-alpha (un valor por residuo), Backbone, Proteína completa, Todos los átomos, o una expresión MDAnalysis personalizada (ej: `name CA and resid 1:100`).
*   **Rango temporal:** Frame de inicio y fin opcionales para analizar un segmento específico de la trayectoria.
*   **Múltiples análisis:** Se pueden agregar múltiples gráficos del mismo tipo con rangos de residuos o temporales distintos. Cada gráfico muestra su configuración (selección de átomos, rango de residuos, rango de frames) como etiqueta visible.

### E. Organización de Resultados en la Vista de Detalle
Los resultados de análisis se organizan en dos secciones:
*   **Métricas analizadas:** RMSF (métrica principal), propiedades estáticas y energía de minimización. Botón para agregar gráficos RMSF adicionales con distintas configuraciones.
*   **Análisis extras:** RMSD y Radio de giro. Botón para agregar análisis extras. Cada gráfico individual puede eliminarse de forma independiente.

## 4\. Consideraciones para la Futura Optimización del Flujo
Teniendo claro que el cuello de botella está en el procesamiento y la traducción de estos archivos, cualquier propuesta de modernización para el laboratorio debería apuntar a:
1. Automatizar la extracción inicial: Crear scripts que, apenas termine una simulación con `sander`/`pmemd`, ejecuten automáticamente un set estándar de análisis para escupir los gráficos de RMSF, RMSD y Radio de Giro.
2. Reducción de espacio mediante filtrado: Las trayectorias crudas (`.nc`) pesan decenas de gigabytes porque guardan cada molécula de agua de la caja. Una herramienta clave de `cpptraj` es quitar el agua sobrante y guardar una trayectoria "limpia y liviana", que es la que el usuario finalmente se descarga a su PC local para armar los videos de las moléculas.

# Arquitectura

(módulos, flujo de datos, separación UI / lógica)

## 1\. Estructura Modular del Sistema
Al utilizar FastAPI, podemos aplicar un patrón arquitectónico limpio separando las responsabilidades en capas muy bien definidas:

```cs
simulAR/
│
├── Dockerfile               # Imagen Docker para despliegue
├── docker-compose.yml        # Orquestación del contenedor con volúmenes
├── requirements.txt          # Dependencias Python (FastAPI, MDAnalysis, etc.)
│
├── app/
│   ├── main.py              # Punto de entrada de FastAPI: todas las rutas HTTP y montaje de static
│   ├── database.py          # Engine SQLAlchemy, SessionLocal, Base declarativa, init_db()
│   │
│   ├── models/              # Modelos de datos (Tablas de SQLAlchemy)
│   │   ├── simulacion.py    # ORM: Simulacion (1) → Archivo (N)
│   │   ├── metrica.py       # ORM: ResultadoMetrica (N) → Simulacion (1)
│   │   └── schemas.py       # Pydantic schemas para request/response
│   │
│   ├── repositories/        # Capa CRUD pura (sin lógica de negocio)
│   │   ├── simulacion_repo.py
│   │   ├── archivo_repo.py
│   │   └── metrica_repo.py
│   │
│   ├── services/            # LÓGICA DE NEGOCIO (Python puro)
│   │   ├── escaner.py       # Módulo 1: Escaneo de directorios, detección de software, registro en DB
│   │   └── analizador.py    # Módulo 2: Pipeline MDAnalysis/cpptraj: RMSF, RMSD, Rg, energía de minimización
│   │
│   ├── templates/           # CAPA DE INTERFAZ (UI)
│   │   ├── dashboard.html   # Vista principal (lista de simulaciones, filtros, paginación, carga/upload)
│   │   └── detalle.html     # Vista de detalle: métricas analizadas, análisis extras, gráficos Chart.js
│   └── static/
│       ├── dashboard.css    # Estilos compartidos (CSS propio con variables CSS, sin Tailwind)
│       └── UTN_logo.jpg     # Logo UTN servido también como favicon
```

> **Nota sobre CSS:** Se usa CSS propio con variables CSS para colores/espaciado/tipografía en lugar de Tailwind CSS. La decisión es consciente: Tailwind agregaría una dependencia de build tooling (Node, PostCSS) a un proyecto que es 100% Python y corre local en la máquina del laboratorio. La superficie de UI es chica (dos vistas) y no justifica la complejidad adicional.

## 2\. Flujo de Datos y Separación UI / Lógica
Para cumplir con las buenas prácticas de ingeniería de software, la interfaz de usuario no debe saber _cómo_ se calcula un RMSF, y el motor de análisis no debe saber _cómo_ se renderiza una página web.

```scss
[ Navegador Web ] (HTML/JS/Chart.js)
       │  ▲
       │  │  Peticiones HTTP (GET/POST) — API REST JSON
       ▼  │
[ Rutas de FastAPI (main.py) ]  <───> [ Base de Datos (SQLite / Supabase) ]
       │  ▲
       │  │  Invoca funciones de negocio y pasa datos limpios
       ▼  │
[ Capa de Servicios (Services) ]
       │
       ├─► escaner.py    ──► (Explora el Sistema de Archivos Local, detecta software)
       └─► analizador.py ──► (MDAnalysis en proceso / cpptraj vía subprocess para archivos > 200 MB)
```

### Paso a paso del flujo de información:
1. **Registro de simulación:** El investigador entra a la web local ([`http://localhost:8000`](http://localhost:8000)) y puede: (a) pegar una ruta local para importar, (b) subir archivos desde el navegador vía drag & drop, o (c) escanear una carpeta raíz para detectar automáticamente subcarpetas que sean simulaciones.
2. **Controlador (FastAPI):** Recibe la ruta o los archivos y delega al escáner.
3. **Capa de Lógica (Módulo 1 - Escáner):** Recorre la ruta usando `os.walk`, clasifica archivos por extensión, detecta el software (AMBER, GAMESS, Gaussian, GROMACS) inspeccionando extensiones y primeras líneas de los `.log`/`.inp`, y extrae metadatos (tamaño total, archivos por tipo, fecha de última modificación).
4. **Persistencia:** Guarda el registro en las tablas `Simulacion` y `Archivo` de la base de datos.
5. **Capa de Lógica (Módulo 2 - Analizador):** Cuando el usuario solicita analizar, FastAPI marca `estado_analisis = "procesando"` y encola el trabajo con `BackgroundTasks` (responde 202 inmediato). En background, `analizador.py` abre su propia sesión de DB, carga un `mda.Universe` con MDAnalysis, calcula las métricas configuradas (RMSF, RMSD, Rg) y persiste los resultados como JSON en `ResultadoMetrica`. Para trayectorias > 200 MB, usa cpptraj automáticamente si está disponible.
6. **Renderizado (UI):** El frontend hace `fetch` a la API REST, obtiene los datos JSON y Chart.js dibuja los gráficos de línea interactivos. Mientras el análisis está en curso, un `setInterval` de 3 segundos hace polling hasta que `estado_analisis` cambia a `completado` o `error`.
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
### MDAnalysis
*   Definición: Librería de Python para el análisis de simulaciones de dinámica molecular. Soporta formatos de AMBER, GROMACS, CHARMM, NAMD y otros.
*   Justificación: Es el motor principal de análisis en simulAR. Permite cargar topologías y trayectorias directamente en Python (sin depender de binarios externos como cpptraj), calcular RMSF, RMSD y radio de giro con una API de alto nivel, y operar sobre selecciones de átomos flexibles. Al estar integrado como librería Python, el pipeline de análisis corre en el mismo proceso que FastAPI (vía `BackgroundTasks`), sin generar archivos temporales intermedios.
### Subprocess (Módulo nativo de Python)
*   Definición: Módulo estándar de Python que permite generar nuevos procesos, conectarse a sus tuberías de entrada/salida/error y obtener sus códigos de retorno.
*   Justificación: Se usa como fallback para cpptraj cuando las trayectorias superan los 200 MB, ya que cpptraj es más eficiente con archivos grandes. El sistema detecta automáticamente el tamaño y elige el motor adecuado.
### Docker
*   Definición: Plataforma de contenedorización que empaqueta la aplicación junto con todas sus dependencias en una imagen reproducible.
*   Justificación: simulAR incluye dependencias científicas complejas (MDAnalysis, HDF5, NetCDF) que son difíciles de instalar consistentemente entre máquinas. El `Dockerfile` instala las librerías de sistema necesarias (`libhdf5-dev`, `libnetcdf-dev`) y las dependencias Python en un entorno aislado. `docker-compose.yml` orquesta el contenedor con volúmenes para persistir la base de datos y montar las carpetas de simulaciones del host como read-only.
## 2\. Capa de Base de Datos y Persistencia
### SQLite
*   Definición: Un motor de base de datos relacional SQL autónomo, empotrado (embebido), de alta confiabilidad y que no requiere un servidor independiente.
*   Justificación: El Plan de Trabajo estipula la necesidad de una base de datos local y centralizada. Al ser un archivo local dentro del proyecto, SQLite elimina la complejidad de tener que instalar y configurar servidores pesados (como MySQL o PostgreSQL) en cada computadora del laboratorio, cumpliendo con la premisa de ser una aplicación liviana.
### SQLAlchemy (ORM)
*   Definición: Un Kit de herramientas SQL y un mapeador objeto-relacional (ORM) para Python.
*   Justificación: Permite interactuar con las tablas de SQLite utilizando clases y objetos de Python puros en lugar de escribir consultas SQL manuales. Esto acelera drásticamente el desarrollo de la capa de acceso a datos (CRUD de simulaciones y métricas).
## 3\. Capa de Interfaz de Usuario (Front-end)
### HTML5 y CSS3 (CSS propio con variables CSS)
*   Definición: HTML5 es el lenguaje de marcado estándar para estructurar páginas web; CSS3 con custom properties (variables CSS) permite definir un sistema de diseño consistente sin dependencias de build.
*   Justificación: Se usa CSS propio (`dashboard.css`) con variables CSS para colores, espaciado y tipografía en lugar de Tailwind CSS. La decisión es consciente: Tailwind agregaría una dependencia de build tooling (Node, PostCSS/CLI) a un proyecto que es 100% Python y corre local en la máquina del laboratorio. La superficie de UI es chica (dos vistas: dashboard y detalle) y no justifica la complejidad adicional.
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
### Matplotlib (Disponible en backend, no usado en la UI)
*   ¿Qué es? Una librería clásica de Python para la generación de gráficos estáticos, animados e interactivos.
*   Estado actual: Sigue instalada como dependencia (la requieren MDAnalysis y SciPy), pero los gráficos del usuario se delegan a Chart.js 4 (CDN) en el frontend. Esto permite que el servidor se concentre en los datos numéricos crudos y el navegador renderice gráficos interactivos (zoom, hover, tooltips) sin generar imágenes estáticas.

# Modelo de datos

## El Modelo de Datos
La estructura elegida es un Modelo Híbrido Estructurado. En lugar de crear millones de filas en una tabla de series temporales, agrupamos los vectores de datos calculados por `cpptraj` dentro de un único registro estructurado en formato de texto o binario nativo.
El esquema de tablas queda de la siguiente manera:
*   Tabla `Simulacion`: Almacena la cabecera de la corrida científica.
    *   _Campos:_ `id` (PK), `nombre`, `ruta_absoluta` (clave para encontrarla localmente y borrar archivos), `software` (AMBER, Gaussian, GROMACS, GAMESS, o None), `fecha_registro`, `metadata_json` (JSON con `total_bytes`, `archivos_por_tipo`, `fecha_modificacion_mas_reciente`), `estado_analisis` (`pendiente` | `procesando` | `completado` | `error`), `analisis_error` (mensaje de error si falló).
*   Tabla `Archivo`: Mapea de forma relacional (1 a N con Simulación) los archivos detectados en el disco.
    *   _Campos:_ `id` (PK), `simulacion_id` (FK), `nombre_archivo` (ruta relativa a `ruta_absoluta`), `extension`, `tamano_bytes`, `tipo` (input / output / trajectory / restart / other).
*   Tabla `Resultado_Metrica`: Almacena el "jugo" extraído de los análisis para graficar.
    *   _Campos:_ `id` (PK), `simulacion_id` (FK), `tipo_metrica` (`rmsf`, `rmsd`, `rg`, `propiedades_estaticas`, `energia_minimizacion`), `valores_tiempo_json` (campo `JSON` en SQLite / `JSONB` nativo en PostgreSQL). Contiene los vectores completos junto con la configuración del análisis (selección de átomos, rango de frames).
    *   _Múltiples registros por tipo:_ Puede haber varios `ResultadoMetrica` del mismo `tipo_metrica` para una misma simulación, cada uno con configuración distinta (ej: dos RMSF con rangos de residuos diferentes). Esto permite al usuario acumular gráficos comparativos.
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
    *   Desarrollar la lógica con `os.walk` para rastrear las carpetas de simulación proporcionadas por el usuario (importación por ruta, upload desde browser, o escaneo recursivo de una carpeta raíz).
    *   Clasificar archivos por extensión en tipos: `input`, `output`, `trajectory`, `restart`, `other`.
    *   Detectar el software utilizado (AMBER, GAMESS, Gaussian, GROMACS) inspeccionando extensiones y primeras líneas de los `.log`/`.inp`.
    *   Extraer metadatos físicos (tamaño total, archivos por tipo, fecha de última modificación) e insertarlos en las tablas `Simulacion` y `Archivo`.
*   Fase 2.2: Módulo 2 - Pipeline de Extracción Analítica
    *   Implementar el llamado a tareas en segundo plano (_Background Tasks_) en FastAPI para no congelar la aplicación (respuesta 202 inmediata + polling desde el frontend).
    *   Usar MDAnalysis como motor principal: carga de `Universe` con topología + trayectoria, cálculo de RMSF (`rms.RMSF`), RMSD (`rms.RMSD`), radio de giro (`radius_of_gyration()`).
    *   Fallback automático a cpptraj (vía `subprocess`) para trayectorias > 200 MB, con detección de disponibilidad nativa y WSL.
    *   Parsear la curva de energía de minimización de archivos `.out` de AMBER con regex para simulaciones sin trayectoria.
    *   Calcular propiedades estáticas (número de residuos, radio de giro, masa total) para toda simulación independientemente de si tiene trayectoria.
*   Fase 2.3: Módulo 3 - Serialización y Persistencia
    *   Serializar los arrays de MDAnalysis/cpptraj como JSON (con la configuración usada: selección de átomos, rango de frames) y guardarlos en `ResultadoMetrica`.
    *   Los campos JSON usan `JSON().with_variant(JSONB(), "postgresql")` para ser `TEXT` en SQLite y `JSONB` indexable en PostgreSQL.
    *   Soporte para múltiples registros del mismo tipo de métrica por simulación (el usuario puede agregar gráficos con distintas configuraciones).
    *   Implementar el Borrado en Cascada en las relaciones de SQLAlchemy y la eliminación individual de métricas vía API REST.
## Etapa 3: Interfaz de Usuario (UI) y Visualización Interactiva (Estimación: 50 horas)
En esta etapa le darás forma visual al sistema, permitiendo que los investigadores interactúen con el backend y vean los gráficos científicos de forma fluida.
*   Fase 3.1: Vistas y Renderizado Dinámico
    *   Configurar Jinja2 en FastAPI para servir plantillas HTML estructuradas.
    *   Diseñar la maquetación visual (Panel de control, buscador de simulaciones, carga por upload) utilizando CSS propio con variables CSS.
    *   Implementar dashboard con filtros por estado y software, paginación, y cards de simulación.
    *   Implementar vista de detalle con información general, timeline de estado, y tablas de archivos.
*   Fase 3.2: Módulo de Graficación (Front-end)
    *   Crear los endpoints en FastAPI que devuelven los vectores numéricos en formato JSON.
    *   Integrar Chart.js 4 (CDN, sin build tooling) en las plantillas HTML.
    *   Renderizar gráficos interactivos: RMSF (por residuo), RMSD y Rg (en el tiempo), energía de minimización (por paso).
    *   Separar gráficos en dos secciones: "Métricas analizadas" (RMSF) y "Análisis extras" (RMSD, Rg), con capacidad de agregar múltiples gráficos con configuraciones distintas.
*   Fase 3.3: Despliegue con Docker
    *   Crear `Dockerfile` con imagen Python 3.11-slim y dependencias de sistema (HDF5, NetCDF).
    *   Crear `docker-compose.yml` con volúmenes para persistencia de datos y montaje de carpetas de simulaciones.
    *   Comando de despliegue: `docker compose up --build -d`.
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

