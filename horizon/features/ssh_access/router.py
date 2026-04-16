"""
router.py — Endpoints HTTP pour la connexion SSH aux VMs.

Préfixe  : /api/v1/vms/{vm_id}/ssh
Tag Swagger : Connexion SSH
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from horizon.features.ssh_access import schemas
from horizon.features.ssh_access import service as ssh_service
from horizon.infrastructure.database import get_db
from horizon.shared.dependencies import CurrentUser


# ─── Router ───────────────────────────────────────────────────────────────────

# Ce router sera monté sous /vms dans main.py,
# ce qui donne l'URL finale : /api/v1/vms/{vm_id}/ssh-info
router = APIRouter(
    prefix="/vms",
    tags=["Connexion SSH"],
)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "/{vm_id}/ssh-info",
    response_model=schemas.SSHInfoResponse,
    summary="Obtenir les informations de connexion SSH d'une VM",
    description=(
        "Retourne l'adresse IP, le port, l'utilisateur et la commande SSH "
        "prête à copier-coller pour se connecter à la VM. "
        "La VM doit être en statut **ACTIVE**. "
        "La clé privée SSH doit avoir été téléchargée séparément via `GET /vms/{vm_id}/ssh-key`."
    ),
)
async def get_ssh_info(
    vm_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return ssh_service.get_ssh_info(
        db=db,
        vm_id=vm_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role.value,
    )