"""
Horizon API — Point d'entrée FastAPI (v2).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from horizon.core.config import get_settings
from horizon.core.constants import API_V1_PREFIX
from horizon.features.accounts.router import router as accounts_router
from horizon.features.admin.router import router as admin_router
from horizon.features.auth.router import router as auth_router
from horizon.features.vms.router import router as vms_router
from horizon.infrastructure.scheduler import start_scheduler, stop_scheduler
from horizon.shared.middleware.security import HTTPSEnforcementMiddleware

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("horizon.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Horizon API v2 — Démarrage (Proxmox=%s)", settings.PROXMOX_ENABLED)
    start_scheduler()
    yield
    logger.info("Horizon API v2 — Arrêt.")
    stop_scheduler()


app = FastAPI(
    title="Horizon API",
    description=(
        "API de gestion de machines virtuelles — Projet SIGMA / ENSPY\n\n"
        "**v2** : Parcours A (templates + Cloud-Init), Parcours B (ISO + disque), "
        "téléchargement ISO avec cache et WebSocket de suivi, "
        "load balancing automatique des nœuds Proxmox.\n\n"
        f"Préfixe des routes : **`{API_V1_PREFIX}`**"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(HTTPSEnforcementMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3010", "http://localhost:3000", "http://127.0.0.1:3010", "https://horizon.enspy.cm"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1 = APIRouter(prefix=API_V1_PREFIX)
api_v1.include_router(auth_router)
api_v1.include_router(accounts_router)
api_v1.include_router(vms_router)
api_v1.include_router(admin_router)
app.include_router(api_v1)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Erreur non gérée : %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur. Contactez l'équipe SIGMA."},
    )


@app.get("/health", tags=["Système"], summary="État de l'API")
def health_check():
    return {
        "status": "ok",
        "app": "Horizon API",
        "version": "2.0.0",
        "env": settings.APP_ENV,
        "proxmox_enabled": settings.PROXMOX_ENABLED,
        "proxmox_host": settings.PROXMOX_HOST or "non configuré",
    }


@app.get("/", tags=["Système"], include_in_schema=False)
def root():
    return {"message": "Horizon API v2 — SIGMA / ENSPY. Docs : /docs"}
