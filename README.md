# simulAR

Aplicacion web para gestionar, analizar y visualizar simulaciones moleculares generadas por AMBER, GAMESS, Gaussian y GROMACS. Desarrollada para el laboratorio QuITEx (UTN).

La app usa FastAPI como backend, Jinja2 para templates HTML, Chart.js para graficos interactivos y MDAnalysis para el pipeline de analisis cientifico (RMSD, radio de giro, energia de minimizacion).

## Requisitos

- **Docker** (recomendado para despliegue) o **Python 3.11+** (instalacion manual)

## Deploy en el servidor del laboratorio (Docker Hub)

Cada push a `main` publica la imagen automaticamente en Docker Hub via GitHub Actions. En el servidor solo hace falta:

```bash
docker pull <usuario>/simular:latest
docker compose up -d
```

Para actualizar a una nueva version:

```bash
docker compose pull
docker compose up -d
```

## Desarrollo local con Docker

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd simulAR
```

### 2. Construir y levantar

```bash
docker compose up -d --build
```

La app queda disponible en `http://localhost:8000`.

### Montar carpetas de simulaciones

El contenedor necesita acceso a las carpetas del disco donde estan los archivos de simulacion. Por defecto monta `./simulaciones` del proyecto. Para apuntar a la carpeta real del laboratorio, definir `SIMULACIONES_PATH` en `.env`:

```env
SIMULACIONES_PATH=/ruta/a/las/simulaciones
```

O pasar la variable al levantar:

```bash
SIMULACIONES_PATH=/ruta/simulaciones docker compose up -d
```

Dentro del contenedor, las simulaciones quedan disponibles en `/simulaciones`. Al importar o escanear desde la app, usar esa ruta (por ejemplo `/simulaciones/mi_carpeta`).

Para montar carpetas adicionales, agregar volumenes en `docker-compose.yml`:

```yaml
volumes:
  - /otra/ruta/host:/simulaciones_extra:ro
```

### Comandos utiles

```bash
# Ver logs en tiempo real
docker compose logs -f

# Parar el contenedor
docker compose down

# Eliminar contenedor y volumen de datos (base de datos y uploads)
docker compose down -v

# Reconstruir despues de cambios en el codigo
docker compose up -d --build
```

## Instalacion manual

### 1. Crear entorno virtual

- Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Conda / Miniconda:

```bash
conda create -n simulAR python=3.11 -y
conda activate simulAR
pip install -r requirements.txt
```

### 2. Ejecutar

```bash
uvicorn app.main:app --reload
```

Abrir `http://127.0.0.1:8000` en el navegador.

## Endpoints principales

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Dashboard principal |
| GET | `/simulaciones/{id}` | Detalle con graficos |
| GET | `/docs` | Documentacion Swagger |
| POST | `/api/simulaciones/import` | Registrar carpeta de disco |
| POST | `/api/simulaciones/upload` | Subir archivos desde el browser |
| POST | `/api/escanear` | Escanear subcarpetas de una raiz |
| POST | `/api/simulaciones/{id}/analizar` | Lanzar analisis en background |
| GET | `/api/simulaciones` | Listar simulaciones |
| DELETE | `/api/simulaciones/{id}` | Eliminar simulacion |

## Arquitectura

```
simulAR/
├── app/
│   ├── main.py              # Entrada FastAPI: rutas HTTP y montaje de static
│   ├── database.py          # Engine SQLAlchemy, SessionLocal, Base, init_db()
│   ├── models/
│   │   ├── simulacion.py    # ORM: Simulacion (1) -> Archivo (N)
│   │   ├── metrica.py       # ORM: ResultadoMetrica (N) -> Simulacion (1)
│   │   └── schemas.py       # Pydantic schemas para request/response
│   ├── repositories/        # Capa CRUD
│   ├── services/
│   │   ├── escaner.py       # Escaneo de directorios, deteccion de software
│   │   └── analizador.py    # Pipeline MDAnalysis: RMSD, Rg, energia
│   ├── templates/           # dashboard.html, detalle.html
│   └── static/              # CSS, logo UTN
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
