"""Client API Proxmox (proxmoxer) - utilisé seulement si PROXMOX_ENABLED."""

from __future__ import annotations

import logging
import asyncio
import time
from typing import Any
import urllib.parse
import requests
import urllib3
import os

from horizon.core.config import get_settings

logger = logging.getLogger("horizon.proxmox")


class FileWithLen:
    """Wrapper pour permettre à requests de connaître la taille d'un flux et éviter le chunked encoding."""
    def __init__(self, file_obj, size):
        self.file_obj = file_obj
        self.size = size

    def __len__(self):
        return self.size

    def read(self, n=-1):
        return self.file_obj.read(n)

    def seek(self, offset, whence=0):
        if hasattr(self.file_obj, 'seek'):
            return self.file_obj.seek(offset, whence)

    def tell(self):
        if hasattr(self.file_obj, 'tell'):
            return self.file_obj.tell()
        return 0


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
        p = self._settings.PROXMOX_PORT
        u = self._settings.PROXMOX_USER
        tn = self._settings.PROXMOX_TOKEN_NAME
        tv = self._settings.PROXMOX_TOKEN_VALUE
        if not all([h, u, tn, tv]):
            raise ProxmoxIntegrationError(
                "Configuration Proxmox incomplète (host, user, token).", 500
            )
        
        # Consolider host:port
        host_str = f"{h}:{p}" if p else h

        if not self._settings.PROXMOX_VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            from proxmoxer import ProxmoxAPI

            self._api = ProxmoxAPI(
                host_str,
                user=u,
                token_name=tn,
                token_value=tv,
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

    async def wait_for_task(self, node: str, upid: str, timeout: int = 300, interval: int = 2) -> dict[str, Any]:
        """Attend la fin d'une tâche Proxmox (UPID)."""
        if not self._api:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Appel synchrone via proxmoxer, on peut le wrapper si on veut être puriste
                # mais dans un threadpool FastAPI ça passe. Ici on utilise asyncio.sleep pour ne pas bloquer.
                status = self._api.nodes(node).tasks(upid).status.get()
                
                if status.get("status") == "stopped":
                    exitstatus = status.get("exitstatus")
                    if exitstatus == "OK":
                        return {"status": "success", "upid": upid}
                    else:
                        raise ProxmoxIntegrationError(f"Tâche Proxmox échouée: {exitstatus}", 502)
                
                await asyncio.sleep(interval)
            except Exception as e:
                if isinstance(e, ProxmoxIntegrationError):
                    raise
                logger.error(f"Erreur lors du polling de la tâche {upid}: {e}")
                await asyncio.sleep(interval)
                
        raise ProxmoxIntegrationError(f"Timeout en attendant la tâche Proxmox {upid}", 504)

    async def create_vm_from_template(
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
            upid = n.qemu(template_vmid).clone.post(newid=new_vmid, name=name, full=1)
            await self.wait_for_task(node, upid, timeout=900)  # Clone peut prendre plusieurs minutes

            config_params = {"memory": memory_mb, "cores": cores, "net0": net0, "agent": "1"}
            if ssh_key:
                parts = ssh_key.split()
                if len(parts) >= 2:
                    clean_key = f"{parts[0].strip()} {parts[1].strip()}"
                else:
                    clean_key = ssh_key.strip()
                # Proxmox requires sshkeys to be URL-encoded within the form body (double-encoded)
                config_params["sshkeys"] = urllib.parse.quote(clean_key, safe="")

            url = f"https://{self._settings.PROXMOX_HOST}:{self._settings.PROXMOX_PORT}/api2/json/nodes/{node}/qemu/{new_vmid}/config"
            headers = {
                "Authorization": f"PVEAPIToken={self._settings.PROXMOX_USER}!{self._settings.PROXMOX_TOKEN_NAME}={self._settings.PROXMOX_TOKEN_VALUE}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            body = urllib.parse.urlencode(config_params)

            resp = requests.post(url, headers=headers, data=body, verify=self._settings.PROXMOX_VERIFY_SSL)
            if resp.status_code >= 400:
                raise ProxmoxIntegrationError(f"Proxmox config error: {resp.status_code} {resp.text}", resp.status_code)

            upid_start = n.qemu(new_vmid).status.start.post()
            await self.wait_for_task(node, upid_start)

            # Polling for IP address before returning
            logger.info(f"VM started. Polling for IP for VMID {new_vmid}...")
            ips = await self.wait_for_vm_ip(node, new_vmid)
            ip = ips[0] if ips else None

            return {
                "status": "success",
                "message": f"VM {name} ({new_vmid}) clonée et démarrée.",
                "ip_address": ip
            }
        except Exception as e:
            logger.exception("create_vm_from_template")
            if isinstance(e, ProxmoxIntegrationError):
                raise
            raise ProxmoxIntegrationError(str(e), 502) from e

    async def start_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            upid = self._nodes(node).qemu(vmid).status.start.post()
            await self.wait_for_task(node, upid)
            return {"status": "success", "message": f"VM {vmid} démarrée."}
        except Exception as e:
            logger.exception("start_vm")
            if isinstance(e, ProxmoxIntegrationError):
                raise
            raise ProxmoxIntegrationError(str(e), 502) from e

    async def stop_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            upid = self._nodes(node).qemu(vmid).status.stop.post()
            await self.wait_for_task(node, upid)
            return {"status": "success", "message": f"VM {vmid} arrêtée."}
        except Exception as e:
            logger.exception(f"Failed to stop VM {vmid} on node {node}")
            if isinstance(e, ProxmoxIntegrationError):
                raise
            raise ProxmoxIntegrationError(f"Proxmox error: {str(e)}", 502) from e

    async def pause_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            upid = self._nodes(node).qemu(vmid).status.suspend.post()
            await self.wait_for_task(node, upid)
            return {"status": "success", "message": f"VM {vmid} en pause."}
        except Exception as e:
            logger.exception("pause_vm")
            if isinstance(e, ProxmoxIntegrationError):
                raise
            raise ProxmoxIntegrationError(str(e), 502) from e

    async def delete_vm(self, node: str, vmid: int) -> dict[str, Any]:
        try:
            upid = self._nodes(node).qemu(vmid).delete(purge=1)
            await self.wait_for_task(node, upid)
            return {"status": "success", "message": f"VM {vmid} supprimée sur Proxmox."}
        except Exception as e:
            logger.exception("delete_vm")
            if isinstance(e, ProxmoxIntegrationError):
                raise
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

    def get_vm_ips(self, node: str, vmid: int) -> list[str]:
        """Récupère les adresses IPv4 du guest via l'agent QEMU."""
        if not self._api:
            return []
        try:
            res = self._nodes(node).qemu(vmid).agent("network-get-interfaces").get()
            ips = []
            interfaces = res.get("result", [])
            for iface in interfaces:
                for addr in iface.get("ip-addresses", []):
                    if addr.get("ip-address-type") == "ipv4":
                        ip = addr.get("ip-address")
                        if ip and not ip.startswith("127.") and not ip.startswith("169.254."):
                            ips.append(ip)
            return ips
        except Exception as e:
            logger.debug(f"Impossible de récupérer l'IP pour VM {vmid} (Agent non actif): {e}")
            return []

    async def wait_for_vm_ip(self, node: str, vmid: int, retries: int = 20, interval: int = 5) -> list[str]:
        """Attend qu'une IP IPv4 soit rapportée par le guest agent."""
        for i in range(retries):
            ips = self.get_vm_ips(node, vmid)
            if ips:
                logger.info(f"IP trouvée pour VM {vmid} au bout de {i*interval}s: {ips}")
                return ips
            await asyncio.sleep(interval)
        logger.warning(f"Timeout en attendant l'IP de la VM {vmid} ({retries*interval}s)")
        return []

    async def upload_iso(self, node: str, storage: str, file_obj, filename: str) -> dict[str, Any]:
        """Upload un fichier ISO sur un stockage spécifique via requests direct."""
        if not self._settings.PROXMOX_ENABLED:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)

        h = self._settings.PROXMOX_HOST
        p = self._settings.PROXMOX_PORT
        u = self._settings.PROXMOX_USER
        tn = self._settings.PROXMOX_TOKEN_NAME
        tv = self._settings.PROXMOX_TOKEN_VALUE

        # Consolider host:port
        host_str = f"{h}:{p}" if p else h
        url = f"https://{host_str}/api2/json/nodes/{node}/storage/{storage}/upload"

        # Tenter de déterminer la taille du fichier pour éviter le chunked encoding
        size = None
        try:
            if hasattr(file_obj, 'fileno'):
                size = os.fstat(file_obj.fileno()).st_size
            elif hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
                file_obj.seek(0, 2)
                size = file_obj.tell()
                file_obj.seek(0)
        except Exception:
            logger.warning("Impossible de déterminer la taille du fichier ISO.")

        headers = {
            "Authorization": f"PVEAPIToken={u}!{tn}={tv}",
            "Connection": "keep-alive"
        }

        data = {
            "content": "iso"
        }

        try:
            # S'assurer que le pointeur est au début
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            wrapped_file = FileWithLen(file_obj, size) if size is not None else file_obj
            
            files = {
                "filename": (filename, wrapped_file)
            }

            # On utilise requests.post directement
            # En passant un objet qui a une méthode __len__, requests peut calculer le Content-Length
            response = await asyncio.to_thread(
                requests.post,
                url,
                headers=headers,
                data=data,
                files=files,
                verify=self._settings.PROXMOX_VERIFY_SSL,
                timeout=600  # 10 minutes
            )

            if response.status_code not in (200, 201):
                logger.error(
                    f"Erreur Proxmox lors de l'upload: {response.status_code} {response.text}")
                raise ProxmoxIntegrationError(
                    f"Proxmox upload error: {response.status_code}", response.status_code
                )

            out = response.json()
            upid = out["data"]
            await self.wait_for_task(node, upid)
            return {"status": "success", "message": f"ISO {filename} uploadé avec succès sur {node}/{storage}."}

        except requests.exceptions.RequestException as e:
            logger.exception(
                f"Erreur reseau lors de l'upload de l'ISO {filename}")
            raise ProxmoxIntegrationError(
                f"Erreur reseau Proxmox : {str(e)}", 502)
        except Exception as e:
            logger.exception(f"Erreur lors de l'upload de l'ISO {filename}")
            if isinstance(e, ProxmoxIntegrationError):
                raise
            raise ProxmoxIntegrationError(str(e), 502) from e

    async def prepare_vm_for_template(
        self,
        node: str,
        vmid: int,
        storage: str,
        iso_filename: str,
        name: str,
        vcpu: int,
        ram_mb: int,
        storage_gb: int,
        iso_storage: str | None = None
    ) -> dict[str, Any]:
        """Crée une VM configurée pour devenir un template (ISO monté, Cloud-Init prêt)."""
        if not self._api:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)
        try:
            n = self._nodes(node)
            
            # Utiliser le stockage spécifié pour l'ISO ou le stockage principal par défaut
            iso_path_storage = iso_storage or storage
            
            # Paramètres de création
            params = {
                "vmid": vmid,
                "name": name,
                "cores": vcpu,
                "memory": ram_mb,
                "scsihw": "virtio-scsi-pci",
                "net0": "virtio,bridge=vmbr0",
                "ide2": f"{iso_path_storage}:iso/{iso_filename},media=cdrom",
                "scsi0": f"{storage}:{storage_gb}",
                "ostype": "l26", # Linux 2.6+
                "agent": 1,      # Activer l'agent QEMU
            }
            
            upid = n.qemu.post(**params)
            await self.wait_for_task(node, upid)
            
            # Ajouter un disque Cloud-Init
            n.qemu(vmid).config.post(ide0=f"{storage}:cloudinit")
            
            return {
                "status": "success",
                "message": f"VM {vmid} préparée sur {node}. Installez l'OS via la console puis convertissez en template.",
                "vmid": vmid
            }
        except Exception as e:
            logger.exception(f"Erreur lors de la préparation de la VM template {vmid}")
            if isinstance(e, ProxmoxIntegrationError):
                raise
            raise ProxmoxIntegrationError(str(e), 502) from e

    def list_isos_on_storage(self, node: str, storage: str = "local") -> list[dict[str, Any]]:
        """Liste les fichiers ISO présents sur un stockage spécifique d'un nœud."""
        try:
            content = self._nodes(node).storage(storage).content.get()
            return [item for item in content if item['content'] == 'iso']
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des ISOs sur {node}/{storage}: {e}")
            return []


    def get_cluster_status(self) -> dict[str, Any]:
        """Récupère un résumé global du datacenter Proxmox via l'API cluster/resources."""
        if not self._api:
            raise ProxmoxIntegrationError("Proxmox désactivé.", 503)
        try:
            # Récupérer les nœuds et les ressources en deux appels seulement
            all_nodes = self._api.nodes.get()
            all_resources = self._api.cluster.resources.get(type="vm")
            
            summary = {
                "nodes": [],
                "total_vms": len(all_resources),
                "active_vms": sum(1 for r in all_resources if r.get("status") == "running"),
                "total_cpus": 0,
                "used_cpus": 0,
                "total_memory": 0,
                "used_memory": 0
            }

            # Grouper les ressources par nœud pour faciliter le mapping
            vms_by_node = {}
            for res in all_resources:
                nodename = res.get("node")
                if nodename not in vms_by_node:
                    vms_by_node[nodename] = 0
                vms_by_node[nodename] += 1

            for node in all_nodes:
                n_vms_count = vms_by_node.get(node["node"], 0)
                n_info = {
                    "name": node["node"],
                    "status": node["status"],
                    "cpu": node.get("cpu", 0),
                    "memory": {
                        "total": node.get("maxmem", 0),
                        "used": node.get("mem", 0)
                    },
                    "vms_count": n_vms_count
                }
                summary["nodes"].append(n_info)

            return summary
        except Exception as e:
            logger.exception("get_cluster_status")
            raise ProxmoxIntegrationError(str(e), 502) from e
