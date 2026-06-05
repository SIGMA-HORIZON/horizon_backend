"""Tests d'intégration — /api/v1/vms."""

API = "/api/v1"


def _vm_payload(iso_image):
    return {
        "name": "vm-test-1",
        "iso_image_id": str(iso_image.id),
        "vcpu": 1,
        "ram_gb": 2.0,
        "storage_gb": 10.0,
        "session_hours": 2,
        "description": "test",
    }


class TestVMs:
    def test_create_vm_201(self, client, user_token, iso_image):
        resp = client.post(
            f"{API}/vms",
            json=_vm_payload(iso_image),
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "vm-test-1"

    def test_list_vms(self, client, user_token, iso_image):
        client.post(
            f"{API}/vms",
            json=_vm_payload(iso_image),
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            f"{API}/vms",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1

    def test_get_vm_detail(self, client, user_token, iso_image):
        created = client.post(
            f"{API}/vms",
            json=_vm_payload(iso_image),
            headers={"Authorization": f"Bearer {user_token}"},
        ).json()
        vm_id = created["id"]
        resp = client.get(
            f"{API}/vms/{vm_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == vm_id

    def test_iso_not_found(self, client, user_token):
        import uuid

        resp = client.post(
            f"{API}/vms",
            json={
                "name": "bad-iso",
                "iso_image_id": str(uuid.uuid4()),
                "vcpu": 1,
                "ram_gb": 2.0,
                "storage_gb": 10.0,
                "session_hours": 2,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    def test_quota_exceeded_vcpu(self, client, user_token, iso_image):
        resp = client.post(
            f"{API}/vms",
            json={
                "name": "too-big",
                "iso_image_id": str(iso_image.id),
                "vcpu": 10,
                "ram_gb": 2.0,
                "storage_gb": 10.0,
                "session_hours": 2,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403
        assert "POL-RESSOURCES" in resp.json()["detail"]

    def test_create_vm_isolated_network_gets_new_vlan(self, client, user_token, iso_image):
        first = client.post(
            f"{API}/vms",
            json={**_vm_payload(iso_image), "name": "vm-shared-1", "shared_network": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert first.status_code == 201
        vlan1 = first.json()["vlan_id"]

        isolated = client.post(
            f"{API}/vms",
            json={**_vm_payload(iso_image), "name": "vm-isolated", "shared_network": False},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert isolated.status_code == 201
        assert isolated.json()["vlan_id"] != vlan1

        shared2 = client.post(
            f"{API}/vms",
            json={**_vm_payload(iso_image), "name": "vm-shared-2", "shared_network": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert shared2.status_code == 201
        assert shared2.json()["vlan_id"] == vlan1

    def test_quota_includes_network_groups(self, client, user_token, iso_image):
        client.post(
            f"{API}/vms",
            json=_vm_payload(iso_image),
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            f"{API}/vms/quota",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        groups = resp.json()["network_groups"]
        assert len(groups) >= 1
        assert groups[0]["vm_count"] >= 1
