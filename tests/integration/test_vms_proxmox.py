"""Proxmox : PROXMOX_ENABLED=true avec API proxmoxer mockée."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

API = "/api/v1"


def _vm_payload(iso_image):
    return {
        "name": "vm-proxmox-test",
        "iso_image_id": str(iso_image.id),
        "vcpu": 1,
        "ram_gb": 2.0,
        "storage_gb": 10.0,
        "session_hours": 2,
    }


@pytest.fixture
def proxmox_on(monkeypatch):
    monkeypatch.setenv("PROXMOX_ENABLED", "true")
    monkeypatch.setenv("PROXMOX_HOST", "https://pve.test:8006")
    monkeypatch.setenv("PROXMOX_USER", "root@pam")
    monkeypatch.setenv("PROXMOX_TOKEN_ID", "tid")
    monkeypatch.setenv("PROXMOX_TOKEN_SECRET", "tsec")
    from horizon.core.config import get_settings

    get_settings.cache_clear()
    yield
    monkeypatch.delenv("PROXMOX_ENABLED", raising=False)
    get_settings.cache_clear()


def _mock_proxmox_api():
    mock_api = MagicMock()

    def qemu_vm(_vmid):
        sub = MagicMock()
        sub.clone.post = MagicMock(return_value={})
        sub.config.post = MagicMock(return_value={})
        sub.status.start.post = MagicMock(return_value={})
        sub.status.stop.post = MagicMock(return_value={})
        sub.status.suspend.post = MagicMock(return_value={})
        sub.delete = MagicMock(return_value={})
        sub.status.current.get = MagicMock(return_value={"status": "running"})
        return sub

    mock_node = MagicMock()
    mock_node.qemu.side_effect = lambda vmid: qemu_vm(vmid)
    mock_api.nodes.return_value = mock_node
    return mock_api


@pytest.mark.usefixtures("proxmox_on")
class TestVMsProxmoxEnabled:
    def test_create_vm_409_without_iso_template(self, client, user_token, iso_image):
        resp = client.post(
            f"{API}/vms",
            json=_vm_payload(iso_image),
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert "ISO" in detail or "Proxmox" in detail

    def test_create_vm_201_with_template_mocked_api(self, client, user_token, iso_image, db):
        from horizon.shared.models import IsoProxmoxTemplate

        tpl = IsoProxmoxTemplate(
            id=uuid.uuid4(),
            iso_image_id=iso_image.id,
            proxmox_template_vmid=9001,
        )
        db.add(tpl)
        db.commit()

        with patch("proxmoxer.ProxmoxAPI") as MockAPI:
            MockAPI.return_value = _mock_proxmox_api()
            resp = client.post(
                f"{API}/vms",
                json=_vm_payload(iso_image),
                headers={"Authorization": f"Bearer {user_token}"},
            )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "ACTIVE"

    def test_create_vm_rollback_on_clone_failure(self, client, user_token, iso_image, db):
        from horizon.shared.models import IsoProxmoxTemplate, VirtualMachine

        tpl = IsoProxmoxTemplate(
            id=uuid.uuid4(),
            iso_image_id=iso_image.id,
            proxmox_template_vmid=9001,
        )
        db.add(tpl)
        db.commit()

        mock_api = _mock_proxmox_api()
        mock_node = mock_api.nodes.return_value

        def qemu_fail_clone(vmid):
            sub = MagicMock()
            if vmid == 9001:
                sub.clone.post.side_effect = RuntimeError("clone failed")
            else:
                sub.clone.post = MagicMock(return_value={})
            sub.config.post = MagicMock(return_value={})
            sub.status.start.post = MagicMock(return_value={})
            return sub

        mock_node.qemu.side_effect = qemu_fail_clone

        with patch("proxmoxer.ProxmoxAPI", return_value=mock_api):
            resp = client.post(
                f"{API}/vms",
                json=_vm_payload(iso_image),
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert resp.status_code == 502
        n = (
            db.query(VirtualMachine)
            .filter(VirtualMachine.name == "vm-proxmox-test")
            .count()
        )
        assert n == 0
