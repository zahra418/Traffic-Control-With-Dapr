import mimetypes
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Windows can map .js to text/plain, which browsers refuse for ES modules.
mimetypes.add_type("text/javascript", ".js")

app = FastAPI(title="VisualSimulation")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "wwwroot", html=True), name="static")