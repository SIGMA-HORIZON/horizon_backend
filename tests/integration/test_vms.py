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
