import time
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models.schemas import (
    MetricaCreate,
    MetricaOut,
    SimulacionCreate,
    SimulacionOut,
    SimulacionUpdate,
)
from app.repositories import archivo_repo, metrica_repo, simulacion_repo
from app.services.escaner import list_simulations, register_simulation


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size or 0)
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    if unit_index == 0 or value >= 10:
        return f"{value:.0f} {units[unit_index]}"
    return f"{value:.1f} {units[unit_index]}"


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
    async def dashboard(request: Request, db: Session = Depends(get_db)):
        simulations = list_simulations(db)
        simulation_rows = []
        total_bytes = 0
        total_files = 0
        analyzed_count = 0
        available_software = []
        seen_software = set()

        for sim in simulations:
            file_count = len(sim.archivos)
            sim_bytes = sum(
                archivo.tamano_bytes or 0 for archivo in sim.archivos
            )
            total_bytes += sim_bytes
            total_files += file_count
            if sim.metricas:
                analyzed_count += 1

            software = sim.software or "Sin software"
            software_key = software.strip().lower()
            if software_key not in seen_software:
                seen_software.add(software_key)
                available_software.append(software)

            simulation_rows.append(
                {
                    "id": sim.id,
                    "nombre": sim.nombre,
                    "ruta_absoluta": sim.ruta_absoluta,
                    "software": sim.software or "Sin software",
                    "fecha_registro": sim.fecha_registro,
                    "file_count": file_count,
                    "size_label": format_bytes(sim_bytes),
                    "status_label": "Analizado" if sim.metricas else "Pendiente",
                    "status_class": "success" if sim.metricas else "pending",
                    "status_icon": "ti-check" if sim.metricas else "ti-hourglass",
                }
            )

        response = templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "simulations": simulation_rows,
                "total_simulations": len(simulation_rows),
                "analyzed_simulations": analyzed_count,
                "total_files": total_files,
                "total_storage": format_bytes(total_bytes),
                "available_software": available_software,
            },
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        return response

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
        return list_simulations(db)

    @app.get("/api/simulaciones/{simulacion_id}", response_model=SimulacionOut)
    def get_simulation(simulacion_id: int, db: Session = Depends(get_db)):
        sim = simulacion_repo.get_by_id(db, simulacion_id)
        if sim is None:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        return sim

    @app.put("/api/simulaciones/{simulacion_id}", response_model=SimulacionOut)
    def update_simulation(
        simulacion_id: int,
        payload: SimulacionUpdate,
        db: Session = Depends(get_db),
    ):
        sim = simulacion_repo.update(
            db,
            simulacion_id,
            nombre=payload.nombre,
            software=payload.software,
            metadata=payload.metadata,
        )
        if sim is None:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        return sim

    @app.delete("/api/simulaciones/{simulacion_id}", status_code=204)
    def delete_simulation(simulacion_id: int, db: Session = Depends(get_db)):
        deleted = simulacion_repo.delete(db, simulacion_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")

    # --- Archivos ---

    @app.get("/api/simulaciones/{simulacion_id}/archivos")
    def get_archivos(simulacion_id: int, db: Session = Depends(get_db)):
        sim = simulacion_repo.get_by_id(db, simulacion_id)
        if sim is None:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        return archivo_repo.get_by_simulacion(db, simulacion_id)

    @app.delete("/api/archivos/{archivo_id}", status_code=204)
    def delete_archivo(archivo_id: int, db: Session = Depends(get_db)):
        deleted = archivo_repo.delete(db, archivo_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # --- Métricas ---

    @app.get("/api/simulaciones/{simulacion_id}/metricas", response_model=List[MetricaOut])
    def get_metricas(simulacion_id: int, db: Session = Depends(get_db)):
        sim = simulacion_repo.get_by_id(db, simulacion_id)
        if sim is None:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        return metrica_repo.get_by_simulacion(db, simulacion_id)

    @app.post(
        "/api/simulaciones/{simulacion_id}/metricas",
        response_model=MetricaOut,
        status_code=201,
    )
    def create_metrica(
        simulacion_id: int,
        payload: MetricaCreate,
        db: Session = Depends(get_db),
    ):
        sim = simulacion_repo.get_by_id(db, simulacion_id)
        if sim is None:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        return metrica_repo.create(db, simulacion_id, payload.tipo_metrica, payload.valores)

    @app.delete("/api/simulaciones/{simulacion_id}/metricas", status_code=204)
    def delete_metricas(simulacion_id: int, db: Session = Depends(get_db)):
        sim = simulacion_repo.get_by_id(db, simulacion_id)
        if sim is None:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        metrica_repo.delete_by_simulacion(db, simulacion_id)

    @app.delete("/api/metricas/{metrica_id}", status_code=204)
    def delete_metrica(metrica_id: int, db: Session = Depends(get_db)):
        deleted = metrica_repo.delete_by_id(db, metrica_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Métrica no encontrada")

    return app


app = create_app()
