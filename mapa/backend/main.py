from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .database import init_db
from .routers import earthquakes, annotations, catalog_proxy, volcanoes, slabs, faults, geodata, stations, gravity

app = FastAPI(
    title="Mapa Tectónico Sulawesi — API",
    version="1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


@app.on_event("startup")
def startup():
    init_db()


# ── API routes ─────────────────────────────────────────────────────────────
app.include_router(earthquakes.router,    prefix="/api", tags=["Sismicidad"])
app.include_router(annotations.router,    prefix="/api", tags=["Anotaciones"])
app.include_router(catalog_proxy.router,  prefix="/api", tags=["Catálogo live"])
app.include_router(volcanoes.router,      prefix="/api", tags=["Volcanismo"])
app.include_router(slabs.router,          prefix="/api", tags=["Sismología estructural"])
app.include_router(faults.router,         prefix="/api", tags=["Fallas"])
app.include_router(geodata.router,        prefix="/api", tags=["Geodatos multi-fuente"])
app.include_router(stations.router,       prefix="/api", tags=["Estaciones sismológicas"])
app.include_router(gravity.router,        prefix="/api", tags=["Gravimetría"])


# ── Frontend estático — debe ir AL FINAL (catch-all) ──────────────────────
FRONTEND = Path(__file__).parent.parent   # mapa/
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="static")
