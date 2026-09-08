<div align="center">

<img src="app/static/UTN_logo.jpg" alt="UTN" width="90" />

# simulAR

**Gestión, análisis y preparación de simulaciones moleculares**
Desarrollado para el laboratorio **QuITEx** (UTN)

[![Build & Push Docker Image](https://github.com/universoparalelo/simulAR/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/universoparalelo/simulAR/actions/workflows/docker-publish.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/universoparalelo/simular?logo=docker&logoColor=white)](https://hub.docker.com/r/universoparalelo/simular)
[![Docker Image Size](https://img.shields.io/docker/image-size/universoparalelo/simular/latest?logo=docker&logoColor=white)](https://hub.docker.com/r/universoparalelo/simular)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Uso](https://img.shields.io/badge/uso-interno%20UTN%20QuITEx-lightgrey)](#)

</div>

---

## Índice

- [Sobre el proyecto](#sobre-el-proyecto)
- [Funcionalidades](#funcionalidades)
- [Demo](#demo)
- [Stack tecnológico](#stack-tecnológico)
- [Instalación](#instalación)
  - [Opción 1: Docker Hub (recomendado)](#opción-1-docker-hub-recomendado)
  - [Opción 2: Docker, build local](#opción-2-docker-build-local)
  - [Opción 3: Instalación manual](#opción-3-instalación-manual)
- [Configuración](#configuración)
- [Backup y migración de datos](#backup-y-migración-de-datos)
- [Uso](#uso)
  - [Endpoints principales](#endpoints-principales)
- [Arquitectura](#arquitectura)

---

## Sobre el proyecto

**simulAR** es una aplicación web local que corre en la misma máquina donde están alojados los archivos de simulación del laboratorio, lo que le permite acceder directamente al sistema de archivos sin depender de servicios en la nube.

Cubre tres frentes del trabajo diario del lab:

- **Gestión**: registra carpetas de simulaciones existentes (AMBER, GAMESS, Gaussian, GROMACS), las cataloga y detecta automáticamente el software y los archivos que contienen.
- **Análisis**: corre un pipeline con MDAnalysis para calcular RMSD, RMSF, radio de giro y curvas de energía de minimización, con resultados graficados directamente en el navegador.
- **Preparación**: herramientas para armar estructuras de entrada antes de correr una simulación (por ahora, el generador de nanocables supramoleculares).

## Funcionalidades

- 📂 **Importar / escanear** carpetas de simulaciones ya existentes en disco, o subirlas directamente desde el navegador.
- 🔍 **Detección automática de software** (AMBER, GAMESS, Gaussian, GROMACS, Travis) inspeccionando extensiones y contenido de archivos.
- 📊 **Análisis molecular** en segundo plano: RMSD, RMSF, radio de giro y energía de minimización, con gráficos interactivos (Chart.js).
- 🧬 **Parseo de outputs** de GAMESS (con descomposición LMOEDA) y Gaussian.
- 🧪 **Generador de nanocables supramoleculares**: extiende una roseta de amino-triazinas/pirimidinas y rota cada copia para armar un nanocable, con previsualización 3D en el navegador (3Dmol.js) y descarga del `.pdb` resultante.
- 🗑️ **Gestión de archivos**: eliminación con limpieza automática de uploads, copiar ruta absoluta, re-escaneo de carpetas.

## Demo

> 🎥 *Video demo pendiente de agregar* — instalación del contenedor desde Docker Hub, instalación manual paso a paso, y recorrido por el dashboard, el análisis y el generador de nanocables.

<!--
  Reemplazar este bloque por el video/GIF cuando esté listo, por ejemplo:

  https://github.com/universoparalelo/simulAR/assets/<id>/<video>.mp4

  o embeber un GIF corto:

  ![Demo simulAR](docs/demo.gif)
-->

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) (SQLite) |
| Templates | [Jinja2](https://jinja.palletsprojects.com/) (server-side, sin build tooling) |
| Frontend | CSS propio, [Chart.js](https://www.chartjs.org/) (gráficos), [3Dmol.js](https://3dmol.org/) (visualización molecular) |
| Análisis científico | [MDAnalysis](https://www.mdanalysis.org/), NumPy, SciPy, Matplotlib, `cpptraj` (opcional, trayectorias grandes) |
| Deploy | Docker + Docker Compose, GitHub Actions → Docker Hub |

## Instalación

Requisitos: **Docker** (recomendado) o **Python 3.11+** para instalación manual.

### Opción 1: Docker Hub (recomendado)

La imagen se publica automáticamente en Docker Hub en cada push a `main`, así que para levantar la app en el servidor del laboratorio **no hace falta clonar el repositorio completo**: alcanza con bajar el archivo `docker-compose.prod.yml`, que apunta directamente a la imagen publicada.

```bash
# 1. Crear una carpeta de trabajo y entrar
mkdir simulAR && cd simulAR

# 2. Descargar solo el docker-compose.prod.yml del repo
curl -O https://raw.githubusercontent.com/universoparalelo/simulAR/main/docker-compose.prod.yml

# 3. Levantar el contenedor (descarga la imagen desde Docker Hub la primera vez)
docker compose -f docker-compose.prod.yml up -d
```

La app queda disponible en `http://localhost:8000`.

Para actualizar a la última versión publicada (parados en esa misma carpeta):

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Opción 2: Docker, build local

Para desarrollar o correr una versión modificada del código:

```bash
git clone https://github.com/universoparalelo/simulAR.git
cd simulAR
docker compose up -d --build
```

La app queda disponible en `http://localhost:8000`.

### Opción 3: Instalación manual

- **Linux / macOS**

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

- **Windows (PowerShell)**

  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- **Conda / Miniconda**

  ```bash
  conda create -n simulAR python=3.11 -y
  conda activate simulAR
  pip install -r requirements.txt
  ```

Ejecutar:

```bash
uvicorn app.main:app --reload
```

Abrir `http://127.0.0.1:8000` en el navegador.

## Configuración

El contenedor necesita acceso a las carpetas del disco donde están los archivos de simulación. Por defecto monta `./simulaciones` del proyecto; para apuntar a la carpeta real del laboratorio, definir `SIMULACIONES_PATH` en un archivo `.env` (ver [`.env.example`](.env.example)):

```env
SIMULACIONES_PATH=/ruta/a/las/simulaciones
```

o pasarla directamente al levantar el contenedor:

```bash
SIMULACIONES_PATH=/ruta/simulaciones docker compose up -d
```

Dentro del contenedor, las simulaciones quedan disponibles en `/simulaciones`; al importar o escanear desde la app hay que usar esa ruta (por ejemplo `/simulaciones/mi_carpeta`).

Para montar carpetas adicionales, agregar volúmenes en `docker-compose.yml`:

```yaml
volumes:
  - /otra/ruta/host:/simulaciones_extra:ro
```

### Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f

# Parar el contenedor
docker compose down

# Eliminar contenedor y volumen de datos (base de datos y uploads)
docker compose down -v

# Reconstruir después de cambios en el código
docker compose up -d --build
```

## Backup y migración de datos

La base de datos (`simular_local.db`) y los archivos subidos desde el navegador viven en el volumen Docker `simular_data`, **no** en la carpeta del proyecto. Actualizar la app (`pull` + `up -d`) no toca ese volumen, así que los datos persisten entre versiones — solo se pierden si se corre explícitamente `docker compose down -v`.

Igual, conviene tener un backup aparte antes de actualizar o de mover la app a otro servidor:

```bash
# Backup: vuelca el contenido del volumen a un .tar.gz en la carpeta actual
docker run --rm -v simular_data:/data -v "$(pwd)":/backup alpine \
  tar czf /backup/simular_data_backup.tar.gz -C /data .
```

```bash
# Restore: en el servidor nuevo, con el volumen ya creado (docker compose up una vez para crearlo)
docker run --rm -v simular_data:/data -v "$(pwd)":/backup alpine \
  sh -c "cd /data && tar xzf /backup/simular_data_backup.tar.gz"
```

Si solo se necesita la base de datos (sin los uploads), alcanza con copiarla directo del contenedor corriendo:

```bash
docker cp simular:/simulAR/data/simular_local.db ./simular_local_backup.db
```

Las carpetas de simulaciones originales (las que apunta `SIMULACIONES_PATH`) quedan fuera de Docker — se montan como solo lectura — así que su backup depende del respaldo normal del servidor del laboratorio, no de este proyecto.

## Uso

La documentación interactiva de la API (Swagger) queda disponible en `/docs` una vez levantada la app.

### Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Dashboard principal |
| GET | `/simulaciones/{id}` | Detalle con gráficos |
| GET | `/herramientas/nanocable` | Generador de nanocables supramoleculares |
| GET | `/docs` | Documentación Swagger |
| POST | `/api/simulaciones/import` | Registrar carpeta de disco |
| POST | `/api/simulaciones/upload` | Subir archivos desde el navegador |
| POST | `/api/escanear` | Escanear subcarpetas de una raíz |
| POST | `/api/simulaciones/{id}/analizar` | Lanzar análisis en background |
| POST | `/api/herramientas/nanocable` | Generar nanocable a partir de una roseta `.pdb` |
| GET | `/api/simulaciones` | Listar simulaciones |
| DELETE | `/api/simulaciones/{id}` | Eliminar simulación |

## Arquitectura

```
simulAR/
├── app/
│   ├── main.py                    # Entrada FastAPI: rutas HTTP y montaje de static
│   ├── database.py                # Engine SQLAlchemy, SessionLocal, Base, init_db()
│   ├── models/
│   │   ├── simulacion.py          # ORM: Simulacion (1) -> Archivo (N)
│   │   ├── metrica.py             # ORM: ResultadoMetrica (N) -> Simulacion (1)
│   │   └── schemas.py             # Pydantic schemas para request/response
│   ├── repositories/              # Capa CRUD
│   ├── services/
│   │   ├── escaner.py             # Escaneo de directorios, detección de software
│   │   ├── analizador.py          # Pipeline MDAnalysis: RMSD, RMSF, Rg, energía
│   │   └── nanocable.py           # Generador de nanocables (extensión + rotación)
│   ├── templates/                 # dashboard.html, detalle.html, herramientas_nanocable.html
│   └── static/                    # CSS, logo UTN
├── Dockerfile
├── docker-compose.yml             # Build local
├── docker-compose.prod.yml        # Imagen publicada en Docker Hub
├── requirements.txt
└── .env.example
```
