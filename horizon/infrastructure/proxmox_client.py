"""Client API Proxmox (proxmoxer) — utilisé seulement si PROXMOX_ENABLED."""

from __future__ import annotations

import logging
from typing import Any

import urllib3

from horizon.core.config import get_settings

logger = logging.getLogger("horizon.proxmox")


class ProxmoxIntegrationError(Exception):
    """Erreur d'appel Proxmox — convertie en PolicyError côté métier."""

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
    ) -> dict[str, Any]:
        try:
            n = self._nodes(node)
            n.qemu(template_vmid).clone.post(newid=new_vmid, name=name, full=1)
            n.qemu(new_vmid).config.post(
                memory=memory_mb, cores=cores, net0=net0)
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

    def get_vnc_proxy(self, node: str, vmid: int) -> dict[str, Any]:
        """Obtient un ticket pour une session NoVNC (Interface graphique)."""
        if not self._api:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)
        try:
            return self._nodes(node).qemu(vmid).vncproxy.post(generate_ticket=1)
        except Exception as e:
            logger.exception("get_vnc_proxy")
            raise ProxmoxIntegrationError(str(e), 502) from e

    def get_xterm_proxy(self, node: str, vmid: int) -> dict[str, Any]:
        """Obtient un ticket pour une session xtermjs (Terminal texte)."""
        if not self._api:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)
        try:
            # L'endpoint spécifique xtermjs renvoie un ticket pour WebSocket
            return self._nodes(node).qemu(vmid).xtermjs.post()
        except Exception as e:
            logger.exception("get_xterm_proxy")
            raise ProxmoxIntegrationError(str(e), 502) from e
