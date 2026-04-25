"""Tests d'intégration — /api/v1/admin."""

API = "/api/v1"


class TestAdmin:
    def test_admin_list_vms(self, client, admin_token):
        resp = client.get(
            f"{API}/admin/vms",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_non_admin_forbidden(self, client, user_token):
        resp = client.get(
            f"{API}/admin/vms",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_audit_logs(self, client, admin_token):
        resp = client.get(
            f"{API}/admin/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "limit" in data

    def test_incidents(self, client, admin_token):
        resp = client.get(
            f"{API}/admin/incidents",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_violations(self, client, admin_token):
        resp = client.get(
            f"{API}/admin/violations",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_quota_override_for_user(self, client, admin_token, standard_user):
        resp = client.post(
            f"{API}/admin/quota-override",
            json={
                "user_id": str(standard_user.id),
                "max_vcpu_per_vm": 6,
                "reason": "test intégration",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "appliqué" in resp.json()["message"].lower()
