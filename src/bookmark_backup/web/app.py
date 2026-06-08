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

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi import Request

FRONTEND_NOT_BUILT_MESSAGE = "Frontend not built. Run: cd frontend && npm install && npm run build"
LOCAL_FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"
FRONTEND_DIST = resolve_frontend_dist() or LOCAL_FRONTEND_DIST


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to protect all API routes except /login and /register."""
    UNPROTECTED_PATHS = {"/api/login", "/api/register"}

    async def dispatch(self, request: Request, call_next):
        # Skip protection for unprotected paths
        if request.url.path in self.UNPROTECTED_PATHS:
            return await call_next(request)
        
        # Skip protection for non-API routes (like static files, root, etc.)
        if not request.url.path.startswith("/api"):
            return await call_next(request)
        
        # Check for authentication
        email = request.cookies.get("user_email")
        if not email:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                email = auth.split(" ", 1)[1]
        
        if not email:
            return Response(
                content='{"detail":"Not authenticated"}',
                status_code=401,
                media_type="application/json"
            )
        
        return await call_next(request)

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

app.add_middleware(AuthenticationMiddleware)

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
