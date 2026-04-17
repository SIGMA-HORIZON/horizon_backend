"""Client API Proxmox (proxmoxer) - utilisé seulement si PROXMOX_ENABLED."""

from __future__ import annotations

import logging
from typing import Any

import urllib3

from horizon.core.config import get_settings

logger = logging.getLogger("horizon.proxmox")


class ProxmoxIntegrationError(Exception):
    """Erreur d'appel Proxmox - convertie en PolicyError côté métier."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProxmoxClient:
    """Encapsule proxmoxer ; `enabled` faux si PROXMOX_ENABLED est désactivé."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._api: Any | None = None
        if not self._settings.PROXMOX_ENABLED:
            return
        h = self._settings.PROXMOX_HOST
        u = self._settings.PROXMOX_USER
        tid = self._settings.PROXMOX_TOKEN_ID
        ts = self._settings.PROXMOX_TOKEN_SECRET
        if not all([h, u, tid, ts]):
            raise ProxmoxIntegrationError(
                "Configuration Proxmox incomplète (host, user, token).", 500
            )
        if not self._settings.PROXMOX_VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            from proxmoxer import ProxmoxAPI

            self._api = ProxmoxAPI(
                h,
                user=u,
                token_name=tid,
                token_value=ts,
                verify_ssl=self._settings.PROXMOX_VERIFY_SSL,
            )
        except Exception as e:
            logger.exception("Init ProxmoxAPI")
            raise ProxmoxIntegrationError(
                f"Connexion Proxmox impossible : {e}", 502) from e

    @property
    def enabled(self) -> bool:
        return self._api is not None

    def _nodes(self, node: str):
        if not self._api:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)
        return self._api.nodes(node)

    def create_vm_from_template(
        self,
        node: str,
        template_vmid: int,
        new_vmid: int,
        name: str,
        memory_mb: int,
        cores: int,
        net0: str,
        ssh_key: str | None = None,
    ) -> dict[str, Any]:
        try:
            n = self._nodes(node)
            n.qemu(template_vmid).clone.post(newid=new_vmid, name=name, full=1)
            
            config_params = {"memory": memory_mb, "cores": cores, "net0": net0}
            if ssh_key:
                # Injection via Cloud-Init (nécessite que le template ait Cloud-Init)
                config_params["sshkeys"] = ssh_key
                
            n.qemu(new_vmid).config.post(**config_params)
            n.qemu(new_vmid).status.start.post()
            return {"status": "success", "message": f"VM {name} ({new_vmid}) clonée et démarrée."}
        except Exception as e:
            logger.exception("create_vm_from_template")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def start_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            self._nodes(node).qemu(vmid).status.start.post()
            return {"status": "success", "message": f"VM {vmid} démarrée."}
        except Exception as e:
            logger.exception("start_vm")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def stop_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            self._nodes(node).qemu(vmid).status.stop.post()
            return {"status": "success", "message": f"VM {vmid} arrêtée."}
        except Exception as e:
            logger.exception("stop_vm")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def pause_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            self._nodes(node).qemu(vmid).status.suspend.post()
            return {"status": "success", "message": f"VM {vmid} en pause."}
        except Exception as e:
            logger.exception("pause_vm")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def delete_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            self._nodes(node).qemu(vmid).delete(purge=1)
            return {"status": "success", "message": f"VM {vmid} supprimée sur Proxmox."}
        except Exception as e:
            logger.exception("delete_vm")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def list_node_qemu(self, node: str) -> list[Any]:
        try:
            return self._nodes(node).qemu.get()
        except Exception as e:
            logger.exception("list_node_qemu")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def get_vm_current_status(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            return self._nodes(node).qemu(vmid).status.current.get()
        except Exception as e:
            logger.exception("get_vm_current_status")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def get_cluster_status(self) -> dict[str, Any]:
        """Récupère un résumé global du datacenter Proxmox."""
        if not self._api:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)
        try:
            nodes = self._api.nodes.get()
            summary = {
                "nodes": [],
                "total_vms": 0,
                "active_vms": 0,
                "total_cpus": 0,
                "used_cpus": 0,
                "total_memory": 0,
                "used_memory": 0
            }

            for node in nodes:
                n_vms = []
                if node["status"] == "online":
                    n_vms = self._api.nodes(node["node"]).qemu.get()
                    summary["total_vms"] += len(n_vms)
                    summary["active_vms"] += sum(1 for v in n_vms if v["status"] == "running")

                n_info = {
                    "name": node["node"],
                    "status": node["status"],
                    "cpu": node.get("cpu", 0),
                    "memory": {
                        "total": node.get("maxmem", 0),
                        "used": node.get("mem", 0)
                    },
                    "vms_count": len(n_vms) if node["status"] == "online" else 0
                }
                summary["nodes"].append(n_info)

            return summary
        except Exception as e:
            logger.exception("get_cluster_status")
            raise ProxmoxIntegrationError(str(e), 502) from e
