import time
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models.schemas import SimulacionCreate, SimulacionOut
from app.services.escaner import list_simulations, register_simulation


def create_app():
    app = FastAPI(title="simulAR", version="0.1.0")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    templates = Jinja2Templates(directory="app/templates")

    @app.on_event("startup")
    def on_startup():
        # Importar modelos para registrarlos en Base.metadata y luego crear tablas
        try:
            import app.models.metrica  # noqa: F401
            import app.models.simulacion  # noqa: F401
        except Exception:
            # Si la importación falla, init_db() aún intentará crear las tablas
            pass
        init_db()

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse(
            request,
            "dashboard.html",
        )

    @app.get("/simulaciones/{simulation_id}", response_class=HTMLResponse)
    async def detalle(request: Request, simulation_id: str):
        return templates.TemplateResponse(
            request,
            "detalle.html",
            {"simulation_id": simulation_id},
        )

    # API: Registro de una simulación (carga desde ruta de disco)
    @app.post("/api/simulaciones/import", response_model=SimulacionOut)
    def import_simulation(payload: SimulacionCreate, db: Session = Depends(get_db)):
        try:
            sim = register_simulation(
                db,
                payload.ruta_absoluta,
                nombre=payload.nombre,
                software=payload.software,
                metadata=payload.metadata,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        return sim

    @app.post("/api/simulaciones/upload", response_model=SimulacionOut)
    async def upload_simulation(
        files: List[UploadFile] = File(...),
        nombre: Optional[str] = Form(None),
        db: Session = Depends(get_db),
    ):
        """Recibe una carpeta seleccionada en el cliente (subida como múltiples archivos)
        y la guarda preservando la estructura. Luego registra la simulación en la DB.
        """
        if not files:
            raise HTTPException(status_code=400, detail="No se subieron archivos")

        # Directorio raíz de proyecto (dos niveles por encima de este archivo)
        project_root = Path(__file__).resolve().parents[1]
        uploads_root = project_root / "data" / "uploads"
        uploads_root.mkdir(parents=True, exist_ok=True)

        # Determinar nombre base a partir del primer archivo si no se recibe nombre
        first_rel = files[0].filename
        first_parts = Path(first_rel).parts
        top_folder = first_parts[0] if len(first_parts) > 1 else Path(first_rel).stem
        sim_name = nombre or top_folder

        dest_dir = uploads_root / f"{sim_name}_{int(time.time())}"
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Guardar cada archivo en su ruta relativa dentro de dest_dir
        for upload in files:
            rel_path = Path(upload.filename)
            target = dest_dir.joinpath(*rel_path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            content = await upload.read()
            with open(target, "wb") as f:
                f.write(content)
            await upload.close()

        # Registrar la simulación apuntando al directorio creado
        try:
            sim = register_simulation(db, str(dest_dir), nombre=sim_name)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        return sim

    @app.get("/api/simulaciones", response_model=List[SimulacionOut])
    def get_simulations(db: Session = Depends(get_db)):
        sims = list_simulations(db)
        return sims

    return app


app = create_app()
