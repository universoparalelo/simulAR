# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexto del proyecto

**simulAR** es una aplicación web local para el laboratorio QuITEx (UTN) que gestiona, analiza y optimiza el almacenamiento de simulaciones moleculares generadas por AMBER, GAMESS y Gaussian. La app corre en la misma máquina donde están los archivos de simulación, lo que permite acceso directo al sistema de archivos.

El alcance actual cubre los módulos 1 y 2 del plan: gestión de simulaciones y análisis de resultados. El módulo 3 (optimización de almacenamiento) es trabajo futuro.

## Comandos esenciales

```powershell
# Activar entorno virtual (Windows)
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Levantar servidor de desarrollo
uvicorn app.main:app --reload

# Verificar que la app importa correctamente
.venv\Scripts\python.exe -c "from app.main import app; print('OK')"
```

El servidor queda disponible en `http://127.0.0.1:8000`. La documentación Swagger se genera automáticamente en `/docs`.

La base de datos SQLite se crea automáticamente en `simular_local.db` al primer arranque. Para cambiarla a PostgreSQL (producción), setear la variable de entorno `DATABASE_URL`.

## Arquitectura

```
app/
├── main.py              # Entrada FastAPI: todas las rutas HTTP y montaje de static
├── database.py          # Engine SQLAlchemy, SessionLocal, Base declarativa, init_db()
├── models/
│   ├── simulacion.py    # ORM: Simulacion (1) → Archivo (N)
│   ├── metrica.py       # ORM: ResultadoMetrica (N) → Simulacion (1)
│   └── schemas.py       # Pydantic schemas para request/response
├── repositories/        # Capa CRUD pura (sin lógica de negocio)
│   ├── simulacion_repo.py
│   ├── archivo_repo.py
│   └── metrica_repo.py
├── services/
│   ├── escaner.py       # Escaneo de directorios, detección de software, registro en DB
│   └── analizador.py    # Pipeline MDAnalysis: RMSD, radio de giro, energía minimización
├── templates/
│   ├── dashboard.html   # Vista principal (lista de simulaciones, filtros, paginación)
│   └── detalle.html     # Vista de detalle: carga datos reales vía fetch() a la API
└── static/
    ├── dashboard.css    # Estilos compartidos por ambas vistas
    └── UTN_logo.jpg     # Logo servido también como favicon en /favicon.ico
```

## Flujo de datos

1. El usuario indica una carpeta → `POST /api/simulaciones/import` o `/api/escanear`
2. `escaner.py` recorre el directorio con `os.walk`, clasifica archivos por extensión, detecta el software (AMBER/GAMESS/Gaussian/GROMACS) inspeccionando extensiones y primeras líneas de los `.log`/`.inp`, y guarda en las tablas `Simulacion` y `Archivo`
3. El usuario dispara análisis → `POST /api/simulaciones/{id}/analizar`. El endpoint marca `estado_analisis="procesando"` y encola el trabajo con `BackgroundTasks`, respondiendo `202` de inmediato sin esperar a que termine
4. En background, `analizar_simulacion_background` (en `analizador.py`) abre su propia sesión de DB (`SessionLocal`, no la del request), localiza topología e coordenadas, carga un `mda.Universe`, calcula RMSD y radio de giro (con trayectoria .nc) o propiedades estáticas + energía de minimización (sin trayectoria), persiste en `ResultadoMetrica` como JSON, y al final actualiza `Simulacion.estado_analisis` a `completado` o `error` (con el detalle en `analisis_error`)
5. El detalle (`/simulaciones/{id}`) hace fetch a `/api/simulaciones/{id}` y `/api/simulaciones/{id}/archivos` para renderizar con datos reales; `estado_analisis`/`analisis_error` viajan en ese mismo GET para hacer polling del progreso (el polling en el frontend todavía no está implementado, es trabajo de la Etapa 3)

## Modelo de datos

- `Simulacion`: una carpeta de simulación registrada. Tiene `metadata_json` con `total_bytes`, `archivos_por_tipo`, `fecha_modificacion_mas_reciente`, etc.
- `Archivo`: cada archivo dentro de la carpeta. `nombre_archivo` es ruta **relativa** a `ruta_absoluta`. El path completo es `os.path.join(sim.ruta_absoluta, archivo.nombre_archivo)`.
- `ResultadoMetrica`: resultados de análisis serializados como JSON en `valores_tiempo_json`. Tipos posibles: `rmsd`, `rg`, `propiedades_estaticas`, `energia_minimizacion`.
- `Simulacion.estado_analisis`: `pendiente` (default) | `procesando` | `completado` | `error`. `Simulacion.analisis_error` guarda el mensaje si falló.

## Decisiones técnicas

**CSS propio en vez de Tailwind CSS**: `app/static/dashboard.css` está escrito a mano (con variables CSS para colores/espaciado/tipografía) en lugar de usar Tailwind, aunque el documento de planificación original (`docs/Etapa1.md`) proponía Tailwind. Es una decisión consciente, no una desviación accidental: Tailwind agregaría una dependencia de build tooling (Node, PostCSS/CLI) a un proyecto que hoy es 100% Python y corre local en la máquina del laboratorio; la superficie de UI es chica (dos vistas, `dashboard.html` y `detalle.html`); y no hay ningún impacto para el usuario final — el navegador recibe CSS compilado en ambos casos, con renderizado y performance equivalentes. El costo de migrar ~1100 líneas de CSS ya funcional no se justifica frente a trabajo pendiente de mayor valor (graficación, migración a Supabase). Si en el futuro el equipo crece o la UI se vuelve mucho más compleja, reevaluar.

## Seguimiento del plan de trabajo

Al terminar una tarea de desarrollo, revisar `docs/plan_trabajo.html` y, si la tarea recién completada corresponde a un ítem de ese checklist, marcarlo agregando su `id` al array `defaultChecked` dentro del `<script>` del archivo.

## Convenciones importantes

**Importar modelos antes de consultar**: SQLAlchemy necesita que ambos modelos estén importados antes de hacer queries. En scripts standalone siempre hacer:
```python
import app.models.simulacion
import app.models.metrica
```

**Pydantic v2**: los schemas usan `model_config = {"from_attributes": True}` en lugar del antiguo `class Config: orm_mode = True`.

**Cache busting**: el CSS en `dashboard.html` lleva `?v=upload-preview-modal-3` y en `detalle.html` lleva `?v=2`. Incrementar el número al modificar `dashboard.css` para forzar recarga en el navegador.

**Archivos de coordenadas AMBER**: MDAnalysis no reconoce `.rst` automáticamente. Hay que pasar `format="RESTRT"` explícitamente. `.inpcrd` se carga como `format="INPCRD"`.

## Librerías científicas instaladas

| Librería | Uso |
|----------|-----|
| MDAnalysis 2.x | Lectura de topologías y trayectorias (AMBER, GROMACS, CHARMM) |
| NumPy | Arrays de coordenadas y métricas |
| SciPy | Análisis estadístico |
| Matplotlib | Generación de gráficos (no usado en UI aún, disponible para backend) |

## API REST — endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/simulaciones/import` | Registra carpeta existente en disco |
| POST | `/api/simulaciones/upload` | Sube archivos desde el browser y registra |
| POST | `/api/escanear` | Escanea subcarpetas de una raíz y registra las que sean simulaciones |
| GET | `/api/simulaciones` | Lista todas |
| GET | `/api/simulaciones/{id}` | Detalle con archivos y métricas |
| PUT | `/api/simulaciones/{id}` | Actualiza nombre/software/metadata |
| DELETE | `/api/simulaciones/{id}` | Elimina (cascade a archivos y métricas) |
| POST | `/api/simulaciones/{id}/rescan` | Re-escanea carpeta y actualiza software/metadata/archivos |
| POST | `/api/simulaciones/{id}/analizar` | Encola pipeline MDAnalysis en background (202 inmediato); progreso vía `estado_analisis` en GET |
| GET | `/api/simulaciones/{id}/metricas` | Lista métricas calculadas |
| DELETE | `/api/simulaciones/{id}/metricas` | Borra todas las métricas |

## Contexto del dominio

- **Minimización de energía** (archivos `.mdin`, `.out`, `.rst`): no genera trayectoria `.nc`. El analizador detecta esto y parsea la curva de energía del `.out` con regex.
- **Dinámica molecular** (produce `.nc` o `.mdcrd`): permite calcular RMSD y radio de giro en el tiempo.
- Los archivos de trayectoria `.nc` pueden pesar decenas de GB. No moverlos ni copiarlos; siempre referenciar por ruta absoluta.
- El campo `software` en `Simulacion` puede ser: `AMBER`, `GAMESS`, `Gaussian`, `GROMACS`, `Travis` o `None` (no detectado).

## Próximos pasos planificados

- Visualización de métricas con Chart.js o Plotly en `detalle.html`, incluyendo polling de `estado_analisis` mientras el análisis está `procesando`
- Módulo de optimización de almacenamiento (identificar archivos redundantes/eliminables)
- Migración a PostgreSQL/Supabase para producción (solo cambiar `DATABASE_URL`)
