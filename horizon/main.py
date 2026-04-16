"""
Horizon API — point d'entrée FastAPI
POL-SIGMA-HORIZON-v1.0
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
    logger.info("Horizon API — Démarrage...")
    start_scheduler()
    yield
    logger.info("Horizon API — Arrêt...")
    stop_scheduler()


app = FastAPI(
    title="Horizon API",
    description=(
        "API de gestion de machines virtuelles — Projet SIGMA / ENSPY\n\n"
        "Politique de référence : **POL-SIGMA-HORIZON-v1.0**\n\n"
        "Préfixe des routes métier : **`/api/v1`**"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(HTTPSEnforcementMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3010", "https://horizon.enspy.cm"],
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


from horizon.shared.policies.enforcer import PolicyError

@app.exception_handler(PolicyError)
async def policy_exception_handler(request: Request, exc: PolicyError):
    with open('/tmp/horizon_debug.log', 'a') as f:
        f.write(f"PolicyError: {exc.detail}\n")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    with open('/tmp/horizon_debug.log', 'a') as f:
        f.write(f"ValidationError: {exc.errors()}\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Erreur non gérée : %s", exc, exc_info=True)
    import traceback
    with open('/tmp/horizon_debug.log', 'a') as f:
        f.write(f"Exception: {traceback.format_exc()}\n")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur. Contactez l'équipe SIGMA."},
    )


@app.get("/health", tags=["Système"], summary="État de l'API")
def health_check():
    return {
        "status": "ok",
        "app": "Horizon API",
        "version": "1.0.0",
        "env": settings.APP_ENV,
        "email_mode": settings.EMAIL_MODE,
    }


@app.get("/", tags=["Système"], include_in_schema=False)
def root():
    return {
        "message": "Horizon API — SIGMA / ENSPY. Documentation : /docs — API métier : /api/v1"
    }
