"""
ProxmoxService — Couche d'abstraction complète Proxmox VE.

Fonctionnalités :
- Connexion au cluster via token API
- Sélection automatique du nœud (least-VMs / most-free-RAM)
- Parcours A : clone depuis template + Cloud-Init
- Parcours B : création manuelle ISO
- Gestion des ISO (download-url + suivi UPID)
- Monitoring ressources cluster
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

import urllib3

from horizon.core.config import get_settings

logger = logging.getLogger("horizon.proxmox")


# ─────────────────────────── Exceptions ────────────────────────────────────

class ProxmoxError(Exception):
    """Erreur Proxmox — convertie en HTTPException dans les routers."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProxmoxNodeUnavailableError(ProxmoxError):
    """Aucun nœud disponible pour placer la VM."""

    def __init__(self) -> None:
        super().__init__("Aucun nœud Proxmox disponible.", 503)


# ─────────────────────────── Data classes ──────────────────────────────────

@dataclass
class NodeInfo:
    name: str
    cpu_usage: float       # 0–1
    mem_used: int          # bytes
    mem_total: int         # bytes
    vm_count: int

    @property
    def mem_free(self) -> int:
        return self.mem_total - self.mem_used

    @property
    def mem_free_gb(self) -> float:
        return round(self.mem_free / (1024 ** 3), 2)


@dataclass
class UpidStatus:
    upid: str
    status: str            # "running" | "stopped"
    exit_status: str | None  # "OK" | "ERROR: ..." | None si en cours
    pct: int               # pourcentage (0–100), estimé


# ─────────────────────────── Service ───────────────────────────────────────

class ProxmoxService:
    """
    Singleton léger : instancié à la demande, pas à l'import.
    Usage :
        svc = ProxmoxService()
        if not svc.enabled:
            raise ProxmoxError("Proxmox désactivé.", 503)
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._api: Any | None = None

        if not self._settings.PROXMOX_ENABLED:
            return

        h = self._settings.PROXMOX_HOST
        u = self._settings.PROXMOX_USER
        p = self._settings.PROXMOX_PASSWORD
        # tid = self._settings.PROXMOX_TOKEN_ID
        # ts = self._settings.PROXMOX_TOKEN_SECRET

        # if not all([h, u, tid, ts]):
        #     raise ProxmoxError(
        #         "Configuration Proxmox incomplète (host / user / token_id / token_secret).",
        #         500,
        #     )
        
        if not all([h, u, p]):
            raise ProxmoxError(
                "Configuration Proxmox incomplète (host / user / password).",
                500,
            )

        if not self._settings.PROXMOX_VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        try:
            from proxmoxer import ProxmoxAPI  # type: ignore

            # self._api = ProxmoxAPI(
            #     h,
            #     user=u,
            #     token_name=tid,
            #     token_value=ts,
            #     verify_ssl=self._settings.PROXMOX_VERIFY_SSL,
            # )

            self._api = ProxmoxAPI(
                h,
                user=u,
                password=p, # On utilise password ici
                verify_ssl=self._settings.PROXMOX_VERIFY_SSL,
            )

            # Vérification rapide de connectivité
            self._api.version.get()
            logger.info("======= ProxmoxService ========\n===>\n====>\n=====> Connexion réussie via mot de passe")
        except ProxmoxError:
            raise
        except Exception as exc:
            logger.exception("ProxmoxService connexion échouée")
            raise ProxmoxError(f"Connexion Proxmox impossible : {exc}", 502) from exc

    # ──────────────────────────── Propriétés ───────────────────────────────

    @property
    def enabled(self) -> bool:
        return self._api is not None

    def _require(self) -> Any:
        if not self._api:
            raise ProxmoxError("Proxmox désactivé dans la configuration.", 503)
        return self._api

    # ──────────────────────────── Cluster / Nœuds ──────────────────────────

    def list_nodes(self) -> list[NodeInfo]:
        """Retourne l'état de tous les nœuds actifs du cluster."""
        try:
            raw = self._require().nodes.get()
        except ProxmoxError:
            raise
        except Exception as exc:
            raise ProxmoxError(f"list_nodes : {exc}", 502) from exc

        nodes: list[NodeInfo] = []
        for n in raw:
            if n.get("status") != "online":
                continue
            try:
                vm_count = len(self._api.nodes(n["node"]).qemu.get())
            except Exception:
                vm_count = 0
            nodes.append(
                NodeInfo(
                    name=n["node"],
                    cpu_usage=n.get("cpu", 0.0),
                    mem_used=n.get("mem", 0),
                    mem_total=n.get("maxmem", 1),
                    vm_count=vm_count,
                )
            )
        return nodes

    def pick_node(self, strategy: str = "least_vms") -> str:
        """
        Sélectionne automatiquement le meilleur nœud.

        Stratégies :
        - "least_vms"  : nœud avec le moins de VMs actives
        - "most_ram"   : nœud avec le plus de RAM libre
        """
        nodes = self.list_nodes()
        if not nodes:
            raise ProxmoxNodeUnavailableError()

        if strategy == "most_ram":
            best = max(nodes, key=lambda n: n.mem_free)
        else:  # least_vms (défaut)
            best = min(nodes, key=lambda n: n.vm_count)

        logger.info(
            "pick_node(%s) → %s  (VMs=%d, RAM libre=%.1f GB)",
            strategy, best.name, best.vm_count, best.mem_free_gb,
        )
        return best.name

    def cluster_resources_summary(self) -> dict[str, Any]:
        """Résumé des ressources globales du cluster."""
        nodes = self.list_nodes()
        return {
            "nodes": [
                {
                    "name": n.name,
                    "cpu_usage_pct": round(n.cpu_usage * 100, 1),
                    "mem_used_gb": round(n.mem_used / (1024 ** 3), 2),
                    "mem_total_gb": round(n.mem_total / (1024 ** 3), 2),
                    "mem_free_gb": n.mem_free_gb,
                    "vm_count": n.vm_count,
                }
                for n in nodes
            ],
            "total_nodes": len(nodes),
            "total_vms": sum(n.vm_count for n in nodes),
        }

    # ──────────────────────────── Templates ────────────────────────────────

    def list_templates(
        self,
        node: str | None = None,
        os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Liste les VMs marquées comme templates sur le cluster.

        Args:
            node       : filtrer sur un nœud spécifique (sinon tous)
            os_filter  : sous-chaîne à rechercher dans le nom (ex: "ubuntu")
        """
        api = self._require()
        results: list[dict[str, Any]] = []

        target_nodes = [node] if node else [n.name for n in self.list_nodes()]

        for node_name in target_nodes:
            try:
                vms = api.nodes(node_name).qemu.get()
            except Exception as exc:
                logger.warning("list_templates — nœud %s inaccessible : %s", node_name, exc)
                continue

            for vm in vms:
                if not vm.get("template"):
                    continue
                name = vm.get("name", "")
                if os_filter and os_filter.lower() not in name.lower():
                    continue
                results.append(
                    {
                        "vmid": vm["vmid"],
                        "name": name,
                        "node": node_name,
                        "status": vm.get("status"),
                        "mem_mb": vm.get("maxmem", 0) // (1024 ** 2),
                        "cpus": vm.get("cpus"),
                        "disk_gb": round(vm.get("maxdisk", 0) / (1024 ** 3), 1),
                        "tags": vm.get("tags", ""),
                    }
                )
        return results

    # ──────────────────────────── Parcours A : Clone + Cloud-Init ──────────

    def deploy_from_template(
        self,
        *,
        node: str,
        template_vmid: int,
        new_vmid: int,
        vm_name: str,
        memory_mb: int,
        cores: int,
        disk_storage: str,
        net0: str,
        # Cloud-Init
        ci_user: str | None = None,
        ci_ssh_keys: str | None = None,
        ci_password: str | None = None,
        ci_ip_config: str | None = None,      # ex: "ip=dhcp" ou "ip=192.168.1.10/24,gw=192.168.1.1"
    ) -> str:
        """
        Clone un template puis injecte les paramètres Cloud-Init.

        Returns:
            UPID de la tâche de démarrage.
        """
        api = self._require()
        n = api.nodes(node)

        try:
            # 1. Clone complet
            logger.info("deploy_from_template — clone vmid=%d → %d sur %s", template_vmid, new_vmid, node)
            clone_upid = n.qemu(template_vmid).clone.post(
                newid=new_vmid,
                name=vm_name,
                full=1,
                storage=disk_storage,
            )
            self._wait_upid(node, clone_upid, timeout=300)

            # 2. Reconfiguration ressources
            config_params: dict[str, Any] = {
                "memory": memory_mb,
                "cores": cores,
                "net0": net0,
            }

            # 3. Paramètres Cloud-Init (uniquement si présents)
            if ci_user:
                config_params["ciuser"] = ci_user
            if ci_password:
                config_params["cipassword"] = ci_password
            if ci_ssh_keys:
                # Proxmox attend les clés URL-encodées
                config_params["sshkeys"] = ci_ssh_keys.replace("\n", "%0A")
            if ci_ip_config:
                config_params["ipconfig0"] = ci_ip_config

            n.qemu(new_vmid).config.post(**config_params)

            # 4. Démarrage
            start_upid: str = n.qemu(new_vmid).status.start.post()
            logger.info("deploy_from_template — démarrage upid=%s", start_upid)
            return start_upid

        except ProxmoxError:
            raise
        except Exception as exc:
            logger.exception("deploy_from_template")
            raise ProxmoxError(f"Déploiement template échoué : {exc}", 502) from exc

    # ──────────────────────────── Parcours B : Création manuelle ───────────

    def create_vm_manual(
        self,
        *,
        node: str,
        vmid: int,
        vm_name: str,
        memory_mb: int,
        cores: int,
        sockets: int = 1,
        disk_size_gb: int,
        disk_storage: str,
        iso_path: str,           # ex: "local:iso/ubuntu-22.04.iso"
        net0: str,
        bios: str = "seabios",   # ou "ovmf" pour UEFI
        ostype: str = "l26",     # l26=Linux 2.6+, win10, etc.
        boot_order: str = "order=ide2;scsi0",
    ) -> str:
        """
        Crée une VM vierge, alloue le disque et monte l'ISO.

        Returns:
            UPID de la tâche de création.
        """
        api = self._require()
        n = api.nodes(node)

        try:
            logger.info("===\n==\n==\n==\n==\n==create_vm_manual==\n==\n==> vmid=%d sur %s", vmid, node)

            create_upid: str = n.qemu.post(
                vmid=vmid,
                name=vm_name,
                memory=memory_mb,
                cores=cores,
                sockets=sockets,
                cpu="host",
                bios=bios,
                ostype=ostype,
                net0=net0,
                # Disque principal
                # **{f"scsi0": f"{disk_storage}:{disk_size_gb},format=qcow2"},
                **{f"scsi0": f"{disk_storage}:{disk_size_gb}"},
                scsihw="virtio-scsi-single",
                # Lecteur CD-ROM
                ide2=f"{iso_path},media=cdrom",
                boot=boot_order,
                agent="enabled=0",
            )
            logger.info("create_vm_manual — upid=%s", create_upid)
            return create_upid

        except ProxmoxError:
            raise
        except Exception as exc:
            logger.exception("create_vm_manual")
            raise ProxmoxError(f"Création VM manuelle échouée : {exc}", 502) from exc

    # ──────────────────────────── ISO Management ───────────────────────────

    def list_storage_isos(self, node: str, storage: str) -> list[dict[str, Any]]:
        """Liste les ISOs disponibles sur un stockage donné."""
        try:
            contents = self._require().nodes(node).storage(storage).content.get(content="iso")
            return [
                {
                    "volid": item["volid"],
                    "filename": item["volid"].split("/")[-1],
                    "size_bytes": item.get("size", 0),
                    "format": item.get("format", "iso"),
                }
                for item in contents
            ]
        except ProxmoxError:
            raise
        except Exception as exc:
            raise ProxmoxError(f"list_storage_isos : {exc}", 502) from exc

    def download_iso_url(
        self,
        node: str,
        storage: str,
        url: str,
        filename: str,
        checksum: str | None = None,
        checksum_algorithm: str = "sha256",
    ) -> str:
        """
        Lance le téléchargement d'une ISO via l'API Proxmox download-url.

        Returns:
            UPID de la tâche de téléchargement.
        """
        try:
            params: dict[str, Any] = {
                "url": url,
                "filename": filename,
                "content": "iso",
            }
            if checksum:
                params["checksum"] = checksum
                params["checksum-algorithm"] = checksum_algorithm

            upid: str = (
                self._require()
                .nodes(node)
                .storage(storage)
                .download_url.post(**params)
            )
            logger.info("download_iso_url — node=%s storage=%s url=%s upid=%s", node, storage, url, upid)
            return upid
        except ProxmoxError:
            raise
        except Exception as exc:
            raise ProxmoxError(f"download_iso_url : {exc}", 502) from exc

    # ──────────────────────────── UPID Tracking ────────────────────────────

    def get_task_status(self, node: str, upid: str) -> UpidStatus:
        """Interroge le statut d'une tâche Proxmox via son UPID."""
        try:
            raw = self._require().nodes(node).tasks(upid).status.get()
            status = raw.get("status", "unknown")
            exit_status = raw.get("exitstatus")

            # Estimation de la progression (Proxmox ne fournit pas de %)
            pct = 100 if status == "stopped" else 50

            return UpidStatus(
                upid=upid,
                status=status,
                exit_status=exit_status,
                pct=pct,
            )
        except ProxmoxError:
            raise
        except Exception as exc:
            raise ProxmoxError(f"get_task_status({upid}) : {exc}", 502) from exc

    def _wait_upid(self, node: str, upid: str, timeout: int = 120) -> None:
        """Attend la fin d'une tâche Proxmox (synchrone, usage interne)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            s = self.get_task_status(node, upid)
            if s.status == "stopped":
                if s.exit_status and s.exit_status != "OK":
                    raise ProxmoxError(f"Tâche {upid} échouée : {s.exit_status}", 502)
                return
            time.sleep(2)
        raise ProxmoxError(f"Timeout ({timeout}s) en attendant la tâche {upid}.", 504)

    async def poll_task_async(
        self, node: str, upid: str, interval: float = 2.0, timeout: float = 600.0
    ) -> UpidStatus:
        """Attend la fin d'une tâche de manière asynchrone (usage dans endpoints async)."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            s = self.get_task_status(node, upid)
            if s.status == "stopped":
                return s
            await asyncio.sleep(interval)
        raise ProxmoxError(f"Timeout async ({timeout}s) tâche {upid}.", 504)

    # ──────────────────────────── Opérations VM ────────────────────────────

    def start_vm(self, node: str, vmid: int) -> str:
        try:
            return self._require().nodes(node).qemu(vmid).status.start.post()
        except Exception as exc:
            raise ProxmoxError(f"start_vm({vmid}) : {exc}", 502) from exc

    def stop_vm(self, node: str, vmid: int) -> str:
        try:
            return self._require().nodes(node).qemu(vmid).status.stop.post()
        except Exception as exc:
            raise ProxmoxError(f"stop_vm({vmid}) : {exc}", 502) from exc

    def shutdown_vm(self, node: str, vmid: int) -> str:
        """Arrêt propre (ACPI)."""
        try:
            return self._require().nodes(node).qemu(vmid).status.shutdown.post()
        except Exception as exc:
            raise ProxmoxError(f"shutdown_vm({vmid}) : {exc}", 502) from exc

    def suspend_vm(self, node: str, vmid: int) -> str:
        try:
            return self._require().nodes(node).qemu(vmid).status.suspend.post()
        except Exception as exc:
            raise ProxmoxError(f"suspend_vm({vmid}) : {exc}", 502) from exc

    def delete_vm(self, node: str, vmid: int, purge: bool = True) -> str:
        try:
            return self._require().nodes(node).qemu(vmid).delete(purge=int(purge))
        except Exception as exc:
            raise ProxmoxError(f"delete_vm({vmid}) : {exc}", 502) from exc

    def get_vm_status(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            return self._require().nodes(node).qemu(vmid).status.current.get()
        except Exception as exc:
            raise ProxmoxError(f"get_vm_status({vmid}) : {exc}", 502) from exc

    def list_node_vms(self, node: str) -> list[dict[str, Any]]:
        try:
            return self._require().nodes(node).qemu.get()
        except Exception as exc:
            raise ProxmoxError(f"list_node_vms({node}) : {exc}", 502) from exc

    def next_free_vmid(self) -> int:
        """Demande à Proxmox un VMID libre."""
        try:
            return int(self._require().cluster.nextid.get())
        except Exception as exc:
            raise ProxmoxError(f"next_free_vmid : {exc}", 502) from exc
