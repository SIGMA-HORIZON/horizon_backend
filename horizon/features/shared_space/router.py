"""
router.py — Endpoints HTTP pour l'espace partagé des VMs.

Préfixe  : /api/v1/vms/{vm_id}/files
Tag Swagger : Espace Partagé
"""

import uuid

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from horizon.features.shared_space import schemas
from horizon.features.shared_space import service as shared_service
from horizon.infrastructure.database import get_db
from horizon.shared.audit_service import log_action
from horizon.shared.dependencies import CurrentUser
from horizon.shared.models.audit_log import AuditAction


# ─── Router ───────────────────────────────────────────────────────────────────

# Ce router sera monté sous /vms dans main.py,
# ce qui donne l'URL finale : /api/v1/vms/{vm_id}/files
router = APIRouter(
    prefix="/vms",
    tags=["Espace Partagé"],
)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "/{vm_id}/files",
    response_model=schemas.SharedSpaceListResponse,
    summary="Lister les fichiers de l'espace partagé",
    description=(
        "Retourne la liste de tous les fichiers présents dans l'espace partagé "
        "de la VM, ainsi que l'espace utilisé et le quota maximum autorisé."
    ),
)
def list_files(
    vm_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return shared_service.list_files(
        db=db,
        vm_id=vm_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role.value,
    )


@router.post(
    "/{vm_id}/files",
    response_model=schemas.SharedSpaceMessageResponse,
    status_code=201,
    summary="Uploader un fichier dans l'espace partagé",
    description=(
        "Uploade un fichier dans l'espace partagé de la VM. "
        "Taille maximale par fichier : **100 Mo**. "
        "Le quota total de l'espace partagé est défini par la politique de la VM."
    ),
)
async def upload_file(
    vm_id: uuid.UUID,
    file: UploadFile,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return await shared_service.upload_file(
        db=db,
        vm_id=vm_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role.value,
        file=file,
    )


@router.get(
    "/{vm_id}/files/{filename}",
    summary="Télécharger un fichier de l'espace partagé",
    description=(
        "Télécharge un fichier depuis l'espace partagé de la VM. "
        "L'action est enregistrée dans le journal d'audit (POL-SEC-03)."
    ),
)
def download_file(
    vm_id: uuid.UUID,
    filename: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    # Récupère et vérifie le chemin du fichier
    file_path = shared_service.get_file_path(
        db=db,
        vm_id=vm_id,
        filename=filename,
        current_user_id=current_user.id,
        current_user_role=current_user.role.value,
    )

    # Enregistrer le téléchargement dans le journal d'audit (POL-SEC-03)
    log_action(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.FILE_DOWNLOADED,
        target_type="vm_shared_file",
        target_id=vm_id,
        metadata={"filename": filename},
    )
    db.commit()

    # Envoyer le fichier au client
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",  # forcer le téléchargement
    )


@router.delete(
    "/{vm_id}/files/{filename}",
    response_model=schemas.SharedSpaceMessageResponse,
    summary="Supprimer un fichier de l'espace partagé",
    description="Supprime définitivement un fichier de l'espace partagé de la VM.",
)
def delete_file(
    vm_id: uuid.UUID,
    filename: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return shared_service.delete_file(
        db=db,
        vm_id=vm_id,
        filename=filename,
        current_user_id=current_user.id,
        current_user_role=current_user.role.value,
    )