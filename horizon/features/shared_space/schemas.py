"""
schemas.py — Schémas Pydantic pour le package shared_space.

Définit la structure des données échangées avec les endpoints
de gestion de l'espace partagé des VMs.
"""

from uuid import UUID
from pydantic import BaseModel


class SharedFileInfo(BaseModel):
    """
    Métadonnées d'un fichier présent dans l'espace partagé.
    Retourné dans la liste des fichiers.
    """
    filename:    str    # nom du fichier
    size_bytes:  int    # taille en octets
    uploaded_at: str    # date d'upload au format ISO 8601


class SharedSpaceListResponse(BaseModel):
    """
    Réponse à GET /vms/{vm_id}/files
    Affiche l'espace utilisé, le quota max et la liste des fichiers.
    """
    vm_id:   UUID                  # identifiant de la VM
    used_gb: float                 # espace déjà utilisé (en Go)
    max_gb:  float                 # quota maximum autorisé (en Go)
    files:   list[SharedFileInfo]  # liste des fichiers présents


class SharedSpaceMessageResponse(BaseModel):
    """
    Réponse simple pour les opérations d'upload et de suppression.
    """
    message: str