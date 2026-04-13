"""
service.py — Logique métier pour la connexion SSH aux VMs.

Ce service est responsable de :
  - Vérifier que la VM existe et appartient à l'utilisateur
  - Vérifier que la VM est dans un état qui permet la connexion SSH
  - Construire et retourner les informations de connexion SSH
"""

import uuid

from sqlalchemy.orm import Session

from horizon.shared.models.virtual_machine import VirtualMachine, VMStatus
from horizon.shared.policies.enforcer import PolicyError, enforce_vm_ownership


# ─── Constantes SSH ───────────────────────────────────────────────────────────

# Port SSH par défaut (modifiable par l'utilisateur selon POL-NETWORK-03)
DEFAULT_SSH_PORT = 22

# Utilisateur système créé automatiquement dans chaque VM Horizon
DEFAULT_SSH_USER = "horizon"


# ─── Fonction principale ──────────────────────────────────────────────────────

def get_ssh_info(
    db: Session,
    vm_id: uuid.UUID,
    current_user_id: uuid.UUID,
    current_user_role: str,
) -> dict:
    """
    Retourne les informations de connexion SSH d'une VM.

    Vérifie dans l'ordre :
      1. La VM existe en base de données
      2. L'utilisateur est bien le propriétaire de la VM
      3. La VM est en statut ACTIVE (SSH impossible sur VM arrêtée)
      4. L'adresse IP est disponible (assignée par Proxmox)
    """

    # ── Étape 1 : récupérer la VM ─────────────────────────────────────────────
    vm: VirtualMachine = (
        db.query(VirtualMachine)
        .filter(VirtualMachine.id == vm_id)
        .first()
    )
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)

    # ── Étape 2 : vérifier que c'est bien la VM de l'utilisateur ─────────────
    # (les admins peuvent voir n'importe quelle VM)
    enforce_vm_ownership(vm.owner_id, current_user_id, current_user_role)

    # ── Étape 3 : vérifier que la VM est active ───────────────────────────────
    if vm.status != VMStatus.ACTIVE:
        raise PolicyError(
            "POL-NETWORK-03",
            f"Connexion SSH impossible : la VM est en statut '{vm.status.value}'. "
            "La VM doit être démarrée et active.",
            409,  # Conflict
        )

    # ── Étape 4 : vérifier que l'adresse IP est disponible ───────────────────
    if not vm.ip_address:
        raise PolicyError(
            "POL-NETWORK-03",
            "L'adresse IP de la VM n'est pas encore disponible. "
            "Patientez quelques instants puis réessayez.",
            503,  # Service Unavailable
        )

    # ── Construire la commande SSH prête à l'emploi ───────────────────────────
    # Exemple de commande générée :
    #   ssh -i /chemin/vers/cle_privee -p 22 horizon@192.168.1.10
    ssh_command = (
        f"ssh -i <chemin_vers_votre_cle_privee> "
        f"-p {DEFAULT_SSH_PORT} "
        f"{DEFAULT_SSH_USER}@{vm.ip_address}"
    )

    return {
        "vm_id":       vm.id,
        "vm_name":     vm.name,
        "ip_address":  vm.ip_address,
        "port":        DEFAULT_SSH_PORT,
        "username":    DEFAULT_SSH_USER,
        "ssh_command": ssh_command,
    }
