# simulAR

Aplicacion web minima para visualizar y simular la gestion de simulaciones moleculares.

La arquitectura actual usa FastAPI como backend, Jinja2 para templates HTML y archivos estaticos servidos desde la propia aplicacion.

## Requisitos

- Python 3.10 o superior
- pip

## Instalacion

Puedes crear un entorno virtual usando `venv` o usar `conda`/`mamba`. Abajo hay ejemplos para ambos casos.

- Usando `venv` (Linux / macOS):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Usando `venv` (Windows PowerShell):

```powershell
python -m venv .venv
# PowerShell
. .venv/Scripts/Activate.ps1
# Si estás usando cmd.exe:
# .venv\Scripts\activate.bat
pip install -r requirements.txt
```

- Usando `conda` (Anaconda / Miniconda). Este flujo crea un entorno con la versión requerida de Python y utiliza `pip` para instalar las dependencias definidas en `requirements.txt`:

```bash
# Crear el entorno (ej. Python 3.10)
conda create -n simulAR python=3.10 -y
conda activate simulAR
# Instalar dependencias desde pip (recomendado para este proyecto)
pip install -r requirements.txt
```

Opcional: instalar algunas dependencias vía conda (ej.: SQLAlchemy o paquetes científicos) desde conda-forge:

```bash
conda install -n simulAR -c conda-forge sqlalchemy
# o usando mamba (si lo tenés instalado):
# mamba install -n simulAR -c conda-forge sqlalchemy
```

Notas:
- Si trabajás con archivos y librerías científicas pesadas (BLAS, LAPACK, etc.), `conda`/`conda-forge` suele resolver binarios de forma más cómoda.
- En entornos compartidos (servidor del laboratorio) podés preferir `conda` para gestionar dependencias del sistema.


## Ejecutar

```powershell
uvicorn app.main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000/
```

Vista de detalle simulada:

```text
http://127.0.0.1:8000/simulaciones/protein_folding_md_001
```

Documentacion automatica de la API:

```text
http://127.0.0.1:8000/docs
```

## Arquitectura

```text
simulAR/
|-- app/
|   |-- main.py                 # Entrada FastAPI, rutas y montaje de static
|   |-- database.py             # Futuro acceso a datos
|   |-- models/
|   |   |-- metrica.py          # Futuro modelo de metricas
|   |   `-- simulacion.py       # Futuro modelo de simulaciones
|   |-- services/
|   |   |-- analizador.py       # Futuro analisis de resultados
|   |   `-- escaner.py          # Futuro escaneo de directorios
|   |-- static/
|   |   `-- dashboard.css       # Estilos compartidos
|   `-- templates/
|       |-- dashboard.html      # Vista principal
|       `-- detalle.html        # Vista de detalle simulada
|-- docs/
|-- requirements.txt
`-- README.md
```

## Rutas actuales

- `GET /`: dashboard principal.
- `GET /simulaciones/{simulation_id}`: detalle simulado de una simulacion.
- `GET /static/{path}`: archivos estaticos.
- `GET /docs`: documentacion Swagger generada por FastAPI.

## Estado actual

La interfaz usa datos simulados. Los modulos de base de datos, modelos y servicios estan preparados como puntos de extension para conectar escaneo real, persistencia y analisis de simulaciones.
