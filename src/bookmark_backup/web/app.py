from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from bookmark_backup import __version__
from bookmark_backup.db import SessionLocal, seed_permissions
from bookmark_backup.web.api import router as api_router
from bookmark_backup.web.frontend_paths import resolve_frontend_dist

FRONTEND_NOT_BUILT_MESSAGE = "Frontend not built. Run: cd frontend && npm install && npm run build"

LOCAL_FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"
FRONTEND_DIST = resolve_frontend_dist() or LOCAL_FRONTEND_DIST

@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as session:
        seed_permissions(session)
    yield

app = FastAPI(
    title="Bookmark Backup",
    description="Unified bookmark storage with deduplication",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if FRONTEND_DIST and (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/")
def root():
    if FRONTEND_DIST is None:
        return JSONResponse(
            status_code=503,
            content= { "detail": FRONTEND_NOT_BUILT_MESSAGE },
        )

    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
    return JSONResponse(
        status_code=503,
        content= { "detail": FRONTEND_NOT_BUILT_MESSAGE },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
