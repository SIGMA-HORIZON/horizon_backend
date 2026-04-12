"""
service.py — Logique métier pour l'espace partagé des VMs.

Chaque VM dispose d'un espace partagé (défini par vm.shared_space_gb)
accessible depuis le portail Horizon (POL-FICHIERS-01).

Les fichiers sont stockés sur le système de fichiers local :
    SHARED_SPACE_ROOT / {vm_id} / {nom_du_fichier}

En production, ce dossier est monté sur un volume Docker persistant.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from horizon.shared.models.virtual_machine import VirtualMachine, VMStatus
from horizon.shared.policies.enforcer import (
    PolicyError,
    enforce_vm_ownership,
    enforce_shared_space_available,
)


# ─── Configuration ────────────────────────────────────────────────────────────

# Dossier racine de stockage — peut être surchargé via variable d'environnement
SHARED_SPACE_ROOT = Path(os.getenv("SHARED_SPACE_ROOT", "/tmp/horizon_shared"))

# Taille maximale d'un fichier uploadé en une seule fois : 100 Mo
MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024  # 100 Mo


# ─── Fonctions utilitaires (privées) ─────────────────────────────────────────

def _get_vm_directory(vm_id: uuid.UUID) -> Path:
    """
    Retourne le dossier dédié à la VM et le crée si nécessaire.
    Exemple : /tmp/horizon_shared/a1b2c3d4-.../
    """
    vm_dir = SHARED_SPACE_ROOT / str(vm_id)
    vm_dir.mkdir(parents=True, exist_ok=True)
    return vm_dir


def _calculate_used_gb(vm_dir: Path) -> float:
    """
    Calcule l'espace disque total utilisé dans le dossier d'une VM (en Go).
    Retourne 0.0 si le dossier n'existe pas encore.
    """
    if not vm_dir.exists():
        return 0.0
    total_bytes = sum(
        f.stat().st_size
        for f in vm_dir.iterdir()
        if f.is_file()
    )
    return round(total_bytes / (1024 ** 3), 4)  # conversion octets → Go


def _get_vm_and_check_access(
    db: Session,
    vm_id: uuid.UUID,
    current_user_id: uuid.UUID,
    current_user_role: str,
) -> VirtualMachine:
    """
    Récupère la VM en base et vérifie les droits d'accès.
    Utilisé en début de chaque fonction du service pour éviter la répétition.
    """
    vm: VirtualMachine = (
        db.query(VirtualMachine)
        .filter(VirtualMachine.id == vm_id)
        .first()
    )
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)

    # Vérifie que l'utilisateur est le propriétaire (ou admin)
    enforce_vm_ownership(vm.owner_id, current_user_id, current_user_role)

    # Vérifie que l'espace partagé n'a pas été purgé (24h après extinction)
    enforce_shared_space_available(vm.stopped_at)

    return vm


# ─── Lister les fichiers ──────────────────────────────────────────────────────

def list_files(
    db: Session,
    vm_id: uuid.UUID,
    current_user_id: uuid.UUID,
    current_user_role: str,
) -> dict:
    """
    Retourne la liste de tous les fichiers présents dans l'espace partagé
    de la VM, avec l'espace utilisé et le quota maximum.
    """
    vm = _get_vm_and_check_access(db, vm_id, current_user_id, current_user_role)
    vm_dir = _get_vm_directory(vm_id)

    # Parcourir les fichiers du dossier et construire la liste
    files = []
    if vm_dir.exists():
        for file_path in sorted(vm_dir.iterdir()):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename":    file_path.name,
                    "size_bytes":  stat.st_size,
                    # Convertir le timestamp Unix en date lisible ISO 8601
                    "uploaded_at": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                })

    return {
        "vm_id":   vm.id,
        "used_gb": _calculate_used_gb(vm_dir),
        "max_gb":  vm.shared_space_gb,
        "files":   files,
    }


# ─── Uploader un fichier ──────────────────────────────────────────────────────

async def upload_file(
    db: Session,
    vm_id: uuid.UUID,
    current_user_id: uuid.UUID,
    current_user_role: str,
    file: UploadFile,
) -> dict:
    """
    Uploade un fichier dans l'espace partagé de la VM.

    Vérifications dans l'ordre :
      1. VM accessible et droits utilisateur OK
      2. La VM n'est pas expirée ou suspendue
      3. Taille du fichier ≤ 100 Mo
      4. Quota d'espace partagé non dépassé
      5. Nom de fichier valide (sécurité anti path traversal)
    """
    vm = _get_vm_and_check_access(db, vm_id, current_user_id, current_user_role)

    # ── Vérification 2 : la VM doit être utilisable ───────────────────────────
    if vm.status in (VMStatus.EXPIRED, VMStatus.SUSPENDED):
        raise PolicyError(
            "POL-FICHIERS-01",
            f"Upload impossible : la VM est en statut '{vm.status.value}'.",
            409,
        )

    # ── Vérification 3 : lire le contenu et contrôler la taille ──────────────
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        max_mo = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise PolicyError(
            "POL-FICHIERS-01",
            f"Fichier trop volumineux. Taille maximale autorisée : {max_mo} Mo.",
            413,  # Payload Too Large
        )

    # ── Vérification 4 : quota d'espace partagé ───────────────────────────────
    vm_dir = _get_vm_directory(vm_id)
    used_gb = _calculate_used_gb(vm_dir)
    file_size_gb = len(content) / (1024 ** 3)

    if used_gb + file_size_gb > vm.shared_space_gb:
        raise PolicyError(
            "POL-FICHIERS-01",
            f"Quota d'espace partagé dépassé. "
            f"Utilisé : {used_gb:.3f} Go sur {vm.shared_space_gb} Go.",
            409,
        )

    # ── Vérification 5 : sécuriser le nom du fichier ──────────────────────────
    # Path(file.filename).name retire les dossiers (ex: "../../etc/passwd" → "passwd")
    safe_name = Path(file.filename).name if file.filename else ""
    if not safe_name:
        raise PolicyError("POL-FICHIERS-01", "Nom de fichier invalide.", 400)

    # ── Écriture du fichier ───────────────────────────────────────────────────
    destination = vm_dir / safe_name
    destination.write_bytes(content)

    return {"message": f"Fichier '{safe_name}' uploadé avec succès."}


# ─── Télécharger un fichier ───────────────────────────────────────────────────

def get_file_path(
    db: Session,
    vm_id: uuid.UUID,
    filename: str,
    current_user_id: uuid.UUID,
    current_user_role: str,
) -> Path:
    """
    Vérifie les droits et retourne le chemin absolu du fichier demandé.
    Le router utilise ce chemin pour envoyer le fichier avec FileResponse.
    """
    _get_vm_and_check_access(db, vm_id, current_user_id, current_user_role)

    vm_dir = _get_vm_directory(vm_id)

    # Sécurité : interdire les chemins comme "../../../etc/passwd"
    safe_name = Path(filename).name
    file_path = vm_dir / safe_name

    if not file_path.exists() or not file_path.is_file():
        raise PolicyError(
            "POL-FICHIERS-01",
            f"Fichier '{filename}' introuvable dans l'espace partagé.",
            404,
        )

    return file_path


# ─── Supprimer un fichier ─────────────────────────────────────────────────────

def delete_file(
    db: Session,
    vm_id: uuid.UUID,
    filename: str,
    current_user_id: uuid.UUID,
    current_user_role: str,
) -> dict:
    """
    Supprime définitivement un fichier de l'espace partagé de la VM.
    """
    # get_file_path vérifie déjà les droits et l'existence du fichier
    file_path = get_file_path(db, vm_id, filename, current_user_id, current_user_role)
    file_path.unlink()

    return {"message": f"Fichier '{filename}' supprimé avec succès."}
