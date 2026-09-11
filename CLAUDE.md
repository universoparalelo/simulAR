# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexto del proyecto

**simulAR** es una aplicación web local para el laboratorio QuITEx (UTN) que gestiona, analiza y optimiza el almacenamiento de simulaciones moleculares generadas por AMBER, GAMESS y Gaussian. La app corre en la misma máquina donde están los archivos de simulación, lo que permite acceso directo al sistema de archivos.

El alcance actual cubre los módulos 1 y 2 del plan (gestión de simulaciones y análisis de resultados) más una primera parte del módulo 3: clasificación y borrado de archivos redundantes en disco.

## Flujo de trabajo con Git

Se trabaja siempre en ramas (`feature/...`, `fix/...`, etc.), nunca commiteando ni pusheando directo a `main`. El merge a `main` se hace vía Pull Request en GitHub, y lo abre/mergea el usuario manualmente (Claude no hace `git push` ni abre PRs salvo pedido explícito).

## Comandos esenciales

```powershell
# Construir y levantar con Docker
docker compose up --build -d

# Ver logs del contenedor
docker compose logs -f simular

# Parar el contenedor
docker compose down

# Verificar que la app importa correctamente (sin Docker)
.venv\Scripts\python.exe -c "from app.main import app; print('OK')"
```

El servidor queda disponible en `http://127.0.0.1:8000`. La documentación Swagger se genera automáticamente en `/docs`.

La base de datos SQLite se crea automáticamente en `simular_local.db` al primer arranque (dentro del volumen Docker `simular_data`). `.env` no se versiona (`.gitignore`).

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
5. El detalle (`/simulaciones/{id}`) hace fetch a `/api/simulaciones/{id}` y `/api/simulaciones/{id}/archivos` para renderizar con datos reales. El botón "Analizar" dispara el paso 3; mientras `estado_analisis === "procesando"`, un `setInterval` de 3s vuelve a pedir `GET /api/simulaciones/{id}` hasta que cambia a `completado`/`error`, y entonces `renderMetricas()` dibuja los gráficos de línea (Chart.js) con los datos ya en `sim.metricas`

## Modelo de datos

- `Simulacion`: una carpeta de simulación registrada. Tiene `metadata_json` con `total_bytes`, `archivos_por_tipo`, `fecha_modificacion_mas_reciente`, etc.
- `Archivo`: cada archivo dentro de la carpeta. `nombre_archivo` es ruta **relativa** a `ruta_absoluta`. El path completo es `os.path.join(sim.ruta_absoluta, archivo.nombre_archivo)`.
- `ResultadoMetrica`: resultados de análisis serializados como JSON en `valores_tiempo_json`. Tipos posibles: `rmsd`, `rg`, `propiedades_estaticas`, `energia_minimizacion`.
- `Simulacion.estado_analisis`: `pendiente` (default) | `procesando` | `completado` | `error`. `Simulacion.analisis_error` guarda el mensaje si falló.

## Decisiones técnicas

**CSS propio en vez de Tailwind CSS**: `app/static/dashboard.css` está escrito a mano (con variables CSS para colores/espaciado/tipografía) en lugar de usar Tailwind. Tailwind agregaría build tooling (Node, PostCSS) a un proyecto 100% Python; la superficie de UI es chica (dos vistas) y el CSS funcional no justifica migración.

**SQLite local, sin Supabase**: la app corre en el mismo servidor que los archivos de simulación; no hay beneficio en una DB en la nube. Se probó la integración con Supabase (Fase 4.1 del plan) pero se decidió quedar con SQLite. Los backups se manejan en el servidor con un cron que copie el archivo `.db`.

**Borrado de archivos: revalidación server-side, no confiar en el cliente**: `classify_deletability()` (en `escaner.py`) es la única fuente de verdad sobre qué archivo es "deletable". El endpoint `POST /api/simulaciones/{id}/archivos/eliminar` vuelve a calcular la categoría de cada archivo en el momento del borrado y rechaza cualquiera que no sea "deletable", sin importar qué mande el frontend. Después de borrar, resincroniza `Archivo`/`metadata_json` re-escaneando el disco (`sync_files_from_disk`, compartida con `/rescan`) en vez de llevar la cuenta manualmente.

**⚠️ El mount `simulaciones/` es read-only en Docker**: tanto `docker-compose.yml` como `docker-compose.prod.yml` montan `${SIMULACIONES_PATH:-./simulaciones}:/simulaciones:ro`. Esto significa que el borrado físico de archivos **falla silenciosamente con `OSError: Read-only file system`** para cualquier simulación importada desde esa carpeta cuando la app corre en Docker (sí funciona para simulaciones subidas vía `/api/simulaciones/upload`, que se guardan en el volumen `simular_data`, que es read-write). Si se quiere que el borrado funcione contra la carpeta real de simulaciones, hay que cambiar ese mount a lectura-escritura a propósito (impacto de seguridad: la app deja de tener garantizado que nunca puede tocar los archivos originales) — no cambiarlo sin decisión explícita del usuario.

## Deploy (CI/CD)

Cada push a `main` dispara GitHub Actions (`.github/workflows/docker-publish.yml`) que buildea la imagen Docker y la pushea a Docker Hub. En el servidor del laboratorio se usa `docker-compose.prod.yml` que pullée la imagen publicada en vez de buildear local.

Secrets necesarios en GitHub: `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN`.

## Seguimiento del plan de trabajo

Al terminar una tarea de desarrollo, revisar `docs/plan_trabajo.html` y, si la tarea recién completada corresponde a un ítem de ese checklist, marcarlo agregando su `id` al array `defaultChecked` dentro del `<script>` del archivo.

## Convenciones importantes

**Importar modelos antes de consultar**: SQLAlchemy necesita que ambos modelos estén importados antes de hacer queries. En scripts standalone siempre hacer:
```python
import app.models.simulacion
import app.models.metrica
```

**Pydantic v2**: los schemas usan `model_config = {"from_attributes": True}` en lugar del antiguo `class Config: orm_mode = True`.

**Cache busting**: `dashboard.html`, `detalle.html` y `herramientas_nanocable.html` referencian `dashboard.css?v=<label>` con la misma etiqueta en los tres. Cambiar la etiqueta (a algo descriptivo del cambio, no necesariamente un número) en los tres archivos a la vez al modificar `dashboard.css`, para forzar recarga en el navegador.

**`metadata_json` ya es un dict, no un string**: desde la migración a columna JSON nativa, `sim.metadata_json` viaja como objeto en las respuestas de la API. No usar `JSON.parse()` sobre él en el frontend (había un bug así en `detalle.html` que dejaba `meta = {}` siempre, ya corregido).

**Gráficos en Chart.js con eje X numérico**: pasar los puntos como `{x, y}` en el dataset (no `labels` + `data` separados) y usar `scales.x.type = 'linear'`; si no, Chart.js trata el eje X como categorías de texto y muestra los `tiempos_ps` completos (con todos los decimales) como labels.

**Archivos de coordenadas AMBER**: MDAnalysis no reconoce `.rst` automáticamente. Hay que pasar `format="RESTRT"` explícitamente. `.inpcrd` se carga como `format="INPCRD"`.

## Librerías científicas instaladas

| Librería | Uso |
|----------|-----|
| MDAnalysis 2.x | Lectura de topologías y trayectorias (AMBER, GROMACS, CHARMM) |
| NumPy | Arrays de coordenadas y métricas |
| SciPy | Análisis estadístico |
| Matplotlib | Generación de gráficos (no usado en UI, disponible para backend) |
| Chart.js 4 (CDN) | Gráficos de línea de RMSD/Rg/energía en `detalle.html`, sin build tooling |

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
| GET | `/api/simulaciones/{id}/storage` | Clasifica archivos en `essential`/`useful`/`deletable` (`analyze_storage`) |
| POST | `/api/simulaciones/{id}/archivos/eliminar` | Borra del disco los `archivo_ids` indicados, revalidando `classify_deletability` en el backend; ver nota sobre el mount `:ro` en Decisiones técnicas |

## Contexto del dominio

- **Minimización de energía** (archivos `.mdin`, `.out`, `.rst`): no genera trayectoria `.nc`. El analizador detecta esto y parsea la curva de energía del `.out` con regex.
- **Dinámica molecular** (produce `.nc` o `.mdcrd`): permite calcular RMSD y radio de giro en el tiempo.
- Los archivos de trayectoria `.nc` pueden pesar decenas de GB. No moverlos ni copiarlos; siempre referenciar por ruta absoluta.
- El campo `software` en `Simulacion` puede ser: `AMBER`, `GAMESS`, `Gaussian`, `GROMACS`, `Travis` o `None` (no detectado).

## Próximos pasos planificados

- Decidir si el mount `simulaciones/` pasa a lectura-escritura para que el borrado funcione contra la carpeta real (ver nota en Decisiones técnicas), o si el borrado queda limitado a simulaciones subidas vía upload.
