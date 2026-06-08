from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def create_app():
    app = FastAPI(title="simulAR", version="0.1.0")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    templates = Jinja2Templates(directory="app/templates")

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

    return app


app = create_app()
