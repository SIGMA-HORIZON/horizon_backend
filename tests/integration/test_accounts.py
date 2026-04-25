"""Tests d'intégration — /api/v1/accounts."""

import uuid

API = "/api/v1"


class TestAccountRequests:
    def test_submit_account_request(self, client):
        resp = client.post(
            f"{API}/accounts/request",
            json={
                "first_name": "Marie",
                "last_name": "DUPONT",
                "email": "marie.dupont@enspy.cm",
                "organisation": "ENSPY — INFO3",
                "justification": "Projet de fin d'année",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "PENDING"

    def test_duplicate_email_rejected(self, client):
        payload = {
            "first_name": "Jean",
            "last_name": "MARC",
            "email": "jean.marc.dup@enspy.cm",
            "organisation": "ENSPY",
        }
        client.post(f"{API}/accounts/request", json=payload)
        resp = client.post(f"{API}/accounts/request", json=payload)
        assert resp.status_code == 409
        assert "POL-COMPTE-01" in resp.json()["detail"]

    def test_admin_can_list_requests(self, client, admin_token):
        resp = client.get(
            f"{API}/accounts/requests",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_user_cannot_list_requests(self, client, user_token):
        resp = client.get(
            f"{API}/accounts/requests",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestAdminUsers:
    def test_admin_lists_users(self, client, admin_token):
        resp = client.get(
            f"{API}/accounts",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_user_cannot_list_users(self, client, user_token):
        resp = client.get(
            f"{API}/accounts",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_admin_get_user(self, client, admin_token, standard_user):
        resp = client.get(
            f"{API}/accounts/{standard_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == standard_user.email

    def test_get_user_unknown(self, client, admin_token):
        rid = uuid.uuid4()
        resp = client.get(
            f"{API}/accounts/{rid}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404
