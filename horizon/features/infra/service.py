"""
InfraService — Logique métier pour le diagnostic cluster et le contrôle VM.

Responsabilités :
  1. get_cluster_nodes()      → état de tous les nœuds (CPU, RAM, VM count)
  2. get_storage_isos()       → liste des ISOs sur le stockage 'local' du nœud cible
  3. start_vm()               → démarrage Proxmox + mise à jour BD + UPID
  4. stop_vm_realtime()       → arrêt Proxmox + mise à jour BD + UPID
  5. get_vm_proxmox_status()  → statut direct Proxmox (pas le cache BD)

Toutes les fonctions lèvent PolicyError (convertie en HTTPException dans le router).
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.shared.audit_service import log_action
from horizon.shared.models import AuditAction, VirtualMachine, VMStatus
from horizon.shared.policies.enforcer import PolicyError, enforce_vm_ownership

logger = logging.getLogger("horizon.infra.service")

# ─────────────────────────── Helpers privés ────────────────────────────────


def _get_proxmox_svc():
    """
    Instancie ProxmoxService. 
    Lève PolicyError 503 si Proxmox est désactivé ou injoignable.
    Lève PolicyError 503 spécifique si l'hôte est une IP 192.168.43.x
    et qu'il est injoignable (contrainte réseau VirtualBox imbriqué).
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError, ProxmoxService

    s = get_settings()
    if not s.PROXMOX_ENABLED:
        raise PolicyError(
            "INFRA",
            "Proxmox est désactivé dans la configuration (PROXMOX_ENABLED=false). "
            "Activez-le et renseignez PROXMOX_HOST, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET.",
            503,
        )

    try:
        svc = ProxmoxService()
        return svc
    except ProxmoxError as exc:
        # Détection réseau VirtualBox imbriqué (192.168.43.x)
        host = s.PROXMOX_HOST or ""
        if host.startswith("192.168.43."):
            raise PolicyError(
                "INFRA",
                f"Le cluster Proxmox ({host}) est injoignable. "
                f"Vérifiez que VirtualBox est démarré, que le réseau hôte-seul est actif "
                f"et que la VM Proxmox est en cours d'exécution. "
                f"Détail technique : {exc.message}",
                503,
            ) from exc
        raise PolicyError("INFRA", exc.message, exc.status_code) from exc


def _size_human(size_bytes: int) -> str:
    """Convertit des octets en chaîne lisible (Ko / Mo / Go)."""
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.1f} Go"
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.0f} Mo"
    if size_bytes >= 1_024:
        return f"{size_bytes / 1_024:.0f} Ko"
    return f"{size_bytes} o"


def _get_vm_or_404(db: Session, vm_id: UUID) -> VirtualMachine:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    return vm


# ─────────────────────────── 1. Nœuds du cluster ───────────────────────────


def get_cluster_nodes(settings=None) -> dict:
    """
    GET /infra/nodes

    Interroge directement l'API Proxmox pour lister tous les nœuds
    avec leur statut (online/offline), CPU usage, et RAM disponible.

    Returns:
        dict compatible ClusterNodesResponse
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    svc = _get_proxmox_svc()
    s = settings or get_settings()

    try:
        # On passe par l'API brute pour avoir aussi les nœuds offline
        raw_nodes = svc._require().nodes.get()
    except ProxmoxError as exc:
        raise PolicyError("INFRA", exc.message, exc.status_code) from exc
    except Exception as exc:
        raise PolicyError("INFRA", f"Erreur lecture nœuds : {exc}", 502) from exc

    nodes_out = []
    online_count = 0
    offline_count = 0
    total_vms = 0

    for n in raw_nodes:
        node_name = n.get("node", "?")
        is_online = n.get("status") == "online"

        if is_online:
            online_count += 1
        else:
            offline_count += 1

        # Comptage des VMs (uniquement si en ligne)
        vm_count = 0
        if is_online:
            try:
                vms = svc._require().nodes(node_name).qemu.get()
                vm_count = len(vms)
                total_vms += vm_count
            except Exception as e:
                logger.warning("get_cluster_nodes — impossible de lister VMs nœud %s : %s", node_name, e)

        # RAM
        mem_total = n.get("maxmem", 0)
        mem_used = n.get("mem", 0)
        mem_free = max(0, mem_total - mem_used)

        # Uptime
        uptime_seconds = n.get("uptime", 0)
        uptime_hours = round(uptime_seconds / 3600, 1) if uptime_seconds else None

        # CPU (0.0 → 1.0 dans Proxmox → on convertit en %)
        cpu_raw = n.get("cpu", 0.0)
        cpu_pct = round(cpu_raw * 100, 1)

        nodes_out.append(
            {
                "name": node_name,
                "status": "online" if is_online else "offline",
                "cpu_usage_pct": cpu_pct,
                "mem_used_gb": round(mem_used / (1024 ** 3), 2),
                "mem_total_gb": round(mem_total / (1024 ** 3), 2),
                "mem_free_gb": round(mem_free / (1024 ** 3), 2),
                "vm_count": vm_count,
                "uptime_hours": uptime_hours,
            }
        )

    return {
        "nodes": nodes_out,
        "total_nodes": len(nodes_out),
        "nodes_online": online_count,
        "nodes_offline": offline_count,
        "total_vms": total_vms,
        "proxmox_host": s.PROXMOX_HOST,
    }


# ─────────────────────────── 2. ISOs stockage local ────────────────────────


def get_storage_isos(node: str | None = None) -> dict:
    """
    GET /infra/storage/local/isos

    Liste les fichiers présents dans le stockage 'local' du nœud Proxmox.
    Filtre pour ne retourner que les fichiers .iso.

    Args:
        node: nœud cible. Si None, utilise PROXMOX_HOST ou le premier nœud online.

    Returns:
        dict compatible StorageISOListResponse
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    svc = _get_proxmox_svc()
    s = get_settings()
    storage = "local"

    # Résolution du nœud cible
    if not node:
        # On essaie d'extraire le nom d'hôte / nom de nœud depuis les settings
        # En pratique pour un cluster VirtualBox, le nœud s'appelle souvent "pve" ou "pve1"
        node = s.PROXMOX_HOST  # peut être une IP — on appellera get_vm_status avec l'IP directement
        # Récupère le vrai nom du premier nœud online
        try:
            raw_nodes = svc._require().nodes.get()
            online_nodes = [n["node"] for n in raw_nodes if n.get("status") == "online"]
            if online_nodes:
                node = online_nodes[0]
        except Exception as e:
            logger.warning("get_storage_isos — impossible de lister nœuds, fallback IP : %s", e)

    logger.info("get_storage_isos — node=%s storage=%s", node, storage)

    try:
        # L'API Proxmox : GET /nodes/{node}/storage/{storage}/content?content=iso
        contents = svc._require().nodes(node).storage(storage).content.get(content="iso")
    except ProxmoxError as exc:
        raise PolicyError("INFRA", exc.message, exc.status_code) from exc
    except Exception as exc:
        raise PolicyError(
            "INFRA",
            f"Impossible de lister le contenu du stockage '{storage}' sur le nœud '{node}' : {exc}",
            502,
        ) from exc

    # Filtrage strict : uniquement les fichiers .iso
    iso_items = []
    for item in contents:
        volid = item.get("volid", "")
        filename = volid.split("/")[-1] if "/" in volid else volid.split(":")[-1]

        # Filtre .iso (contrainte explicite du cahier des charges)
        if not filename.lower().endswith(".iso"):
            continue

        size_bytes = item.get("size", 0)
        iso_items.append(
            {
                "volid": volid,
                "filename": filename,
                "size_bytes": size_bytes,
                "size_human": _size_human(size_bytes),
            }
        )

    logger.info("get_storage_isos — %d ISO(s) trouvée(s) sur %s:%s", len(iso_items), node, storage)

    return {
        "node": node,
        "storage": storage,
        "isos": iso_items,
        "total": len(iso_items),
    }


# ─────────────────────────── 3. Démarrage VM ───────────────────────────────


def start_vm(
    db: Session,
    vm_id: UUID,
    requester_id,
    requester_role: str,
) -> dict:
    """
    POST /vms/{id}/start

    1. Récupère la VM en BD et vérifie l'ownership.
    2. Appelle Proxmox start → récupère l'UPID.
    3. Met à jour le statut BD à ACTIVE.
    4. Logue l'action dans l'audit.

    Returns:
        dict compatible VMActionResponse
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    vm = _get_vm_or_404(db, vm_id)

    # Vérification ownership (les admins peuvent démarrer n'importe quelle VM)
    enforce_vm_ownership(vm.owner_id, requester_id, requester_role)

    # Garde : une VM déjà ACTIVE n'a pas besoin d'être redémarrée
    if vm.status == VMStatus.ACTIVE:
        raise PolicyError(
            "VM",
            f"La VM '{vm.name}' est déjà en cours d'exécution (statut : ACTIVE).",
            409,
        )

    # Résolution du nœud Proxmox
    node = _resolve_node(vm)

    svc = _get_proxmox_svc()
    logger.info(
        "start_vm — vm=%s vmid=%d node=%s demandé_par=%s",
        vm.id, vm.proxmox_vmid, node, requester_id,
    )

    try:
        upid: str = svc.start_vm(node, vm.proxmox_vmid)
    except ProxmoxError as exc:
        raise PolicyError("PROXMOX", exc.message, exc.status_code) from exc

    # Mise à jour BD
    vm.status = VMStatus.ACTIVE
    vm.last_upid = upid

    log_action(
        db, requester_id, AuditAction.VM_STARTED, "vm", vm.id,
        metadata={"proxmox_node": node, "vmid": vm.proxmox_vmid, "upid": upid},
    )
    db.commit()
    db.refresh(vm)

    return {
        "vm_id": vm.id,
        "proxmox_vmid": vm.proxmox_vmid,
        "proxmox_node": node,
        "action": "start",
        "upid": upid,
        "message": f"VM '{vm.name}' démarrée. UPID Proxmox : {upid}",
    }


# ─────────────────────────── 4. Arrêt VM ───────────────────────────────────


def stop_vm_realtime(
    db: Session,
    vm_id: UUID,
    requester_id,
    requester_role: str,
    force: bool = False,
) -> dict:
    """
    POST /vms/{id}/stop  (et POST /admin/vms/{id}/stop pour l'arrêt forcé)

    1. Récupère la VM en BD.
    2. Appelle Proxmox shutdown (ACPI) ou stop (forcé) → UPID.
    3. Met à jour le statut BD à STOPPED.
    4. Logue l'action.

    Args:
        force: si True, utilise stop (power-cut) au lieu de shutdown (ACPI).

    Returns:
        dict compatible VMActionResponse
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requester_id, requester_role)

    if vm.status == VMStatus.STOPPED:
        raise PolicyError(
            "VM",
            f"La VM '{vm.name}' est déjà arrêtée.",
            409,
        )

    node = _resolve_node(vm)
    svc = _get_proxmox_svc()
    logger.info(
        "stop_vm_realtime — vm=%s vmid=%d node=%s force=%s demandé_par=%s",
        vm.id, vm.proxmox_vmid, node, force, requester_id,
    )

    try:
        if force:
            upid: str = svc.stop_vm(node, vm.proxmox_vmid)
        else:
            upid = svc.shutdown_vm(node, vm.proxmox_vmid)
    except ProxmoxError as exc:
        raise PolicyError("PROXMOX", exc.message, exc.status_code) from exc

    # Mise à jour BD
    vm.status = VMStatus.STOPPED
    vm.last_upid = upid

    audit_action = AuditAction.VM_FORCE_STOPPED if force else AuditAction.VM_STOPPED
    log_action(
        db, requester_id, audit_action, "vm", vm.id,
        metadata={
            "proxmox_node": node,
            "vmid": vm.proxmox_vmid,
            "upid": upid,
            "force": force,
        },
    )
    db.commit()
    db.refresh(vm)

    action_label = "stop forcé" if force else "shutdown ACPI"
    return {
        "vm_id": vm.id,
        "proxmox_vmid": vm.proxmox_vmid,
        "proxmox_node": node,
        "action": "stop",
        "upid": upid,
        "message": f"VM '{vm.name}' — {action_label} initié. UPID : {upid}",
    }


# ─────────────────────────── 5. Statut temps-réel VM ───────────────────────


def get_vm_proxmox_status(
    db: Session,
    vm_id: UUID,
    requester_id,
    requester_role: str,
) -> dict:
    """
    GET /vms/{id}/status

    Récupère l'état courant de la VM DIRECTEMENT depuis Proxmox
    (pas depuis le cache en base de données) pour garantir la
    synchronisation avec l'interface Proxmox.

    Synchronise également le statut BD si nécessaire.

    Returns:
        dict compatible VMProxmoxStatusResponse
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requester_id, requester_role)

    node = _resolve_node(vm)
    svc = _get_proxmox_svc()
    logger.info(
        "get_vm_proxmox_status — vm=%s vmid=%d node=%s",
        vm.id, vm.proxmox_vmid, node,
    )

    try:
        raw = svc.get_vm_status(node, vm.proxmox_vmid)
    except ProxmoxError as exc:
        raise PolicyError("PROXMOX", exc.message, exc.status_code) from exc

    proxmox_status = raw.get("status", "unknown")  # "running", "stopped", "paused"

    # ── Synchronisation BD ──
    # Si Proxmox dit "running" mais la BD dit STOPPED/PENDING → on corrige
    _sync_vm_status(db, vm, proxmox_status)

    # Extraction des métriques
    uptime = raw.get("uptime")          # secondes (présent uniquement si running)
    cpu_raw = raw.get("cpu", None)      # 0.0–1.0
    mem_used = raw.get("mem", None)     # bytes
    mem_total = raw.get("maxmem", None) # bytes
    disk_read = raw.get("diskread", None)
    disk_write = raw.get("diskwrite", None)
    net_in = raw.get("netin", None)
    net_out = raw.get("netout", None)

    # IP depuis QEMU Guest Agent (si disponible)
    ip_address = vm.ip_address
    if proxmox_status == "running":
        try:
            agent_info = svc._require().nodes(node).qemu(vm.proxmox_vmid).agent("network-get-interfaces").get()
            for iface in agent_info.get("result", []):
                if iface.get("name", "lo") == "lo":
                    continue
                for ip_entry in iface.get("ip-addresses", []):
                    if ip_entry.get("ip-address-type") == "ipv4":
                        ip_address = ip_entry["ip-address"]
                        break
                if ip_address and ip_address != vm.ip_address:
                    vm.ip_address = ip_address
                    db.commit()
                    break
        except Exception:
            pass  # Guest agent peut être absent — pas bloquant

    return {
        "vm_id": vm.id,
        "proxmox_vmid": vm.proxmox_vmid,
        "proxmox_node": node,
        "proxmox_status": proxmox_status,
        "horizon_status": vm.status.value if hasattr(vm.status, "value") else vm.status,
        "uptime_seconds": uptime,
        "cpu_usage_pct": round(cpu_raw * 100, 1) if cpu_raw is not None else None,
        "mem_used_mb": (mem_used // (1024 * 1024)) if mem_used is not None else None,
        "mem_total_mb": (mem_total // (1024 * 1024)) if mem_total is not None else None,
        "disk_read_bytes": disk_read,
        "disk_write_bytes": disk_write,
        "net_in_bytes": net_in,
        "net_out_bytes": net_out,
        "ip_address": ip_address,
    }


# ─────────────────────────── Helpers ───────────────────────────────────────


def _resolve_node(vm: VirtualMachine) -> str:
    """
    Retourne le nom du nœud Proxmox d'une VM.
    proxmox_node est soit une enum PhysicalNode, soit une string.
    """
    node = vm.proxmox_node
    if node is None:
        raise PolicyError("VM", "Nœud Proxmox non défini pour cette VM.", 500)
    # Si c'est une enum SQLAlchemy, extraire la valeur string
    return node.value if hasattr(node, "value") else str(node)


def _sync_vm_status(db: Session, vm: VirtualMachine, proxmox_status: str) -> None:
    """
    Synchronise le statut BD avec l'état Proxmox.
    Évite les incohérences entre le cache BD et la réalité Proxmox.
    """
    proxmox_to_horizon = {
        "running": VMStatus.ACTIVE,
        "stopped": VMStatus.STOPPED,
        "paused": VMStatus.STOPPED,
        "suspended": VMStatus.SUSPENDED,
    }

    target_status = proxmox_to_horizon.get(proxmox_status)
    if target_status and vm.status != target_status:
        logger.info(
            "_sync_vm_status — vm=%s : BD=%s → Proxmox=%s (sync)",
            vm.id, vm.status, target_status,
        )
        vm.status = target_status
        db.commit()
        db.refresh(vm)
