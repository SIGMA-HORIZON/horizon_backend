"""Tests d'intégration — /api/v1/auth (POL-COMPTE-02, POL-COMPTE-03)."""

import uuid

import pytest

API = "/api/v1"


class TestLogin:
    def test_login_success(self, client, standard_user):
        resp = client.post(
            f"{API}/auth/login",
            json={"username": "alice.test", "password": "Student@Test2025!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["must_change_pwd"] is False
        assert data["role"] == "USER"

    def test_login_wrong_password_generic_message(self, client, standard_user):
        resp = client.post(
            f"{API}/auth/login",
            json={"username": "alice.test", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert "Identifiants incorrects" in detail
        assert "mot de passe" not in detail.lower()
        assert "username" not in detail.lower()

    def test_login_unknown_user_generic_message(self, client):
        resp = client.post(
            f"{API}/auth/login",
            json={"username": "unknown.user", "password": "AnyPassword!"},
        )
        assert resp.status_code == 401
        assert "Identifiants incorrects" in resp.json()["detail"]

    def test_login_inactive_account_rejected(self, client, db):
        from horizon.features.auth.service import hash_password
        from horizon.shared.models import User, UserRoleEnum

        inactive = User(
            id=uuid.uuid4(),
            username="inactive.bob",
            email="bob.inactive@test.cm",
            hashed_password=hash_password("Student@Test2025!"),
            first_name="Bob",
            last_name="INACTIVE",
            role=UserRoleEnum.USER,
            must_change_pwd=False,
            is_active=False,
        )
        db.add(inactive)
        db.commit()

        resp = client.post(
            f"{API}/auth/login",
            json={"username": "inactive.bob", "password": "Student@Test2025!"},
        )
        assert resp.status_code == 403
        assert "POL-COMPTE-03" in resp.json()["detail"]

    def test_login_must_change_password_flag(self, client, db):
        from horizon.features.auth.service import hash_password
        from horizon.shared.models import User, UserRoleEnum

        new_user = User(
            id=uuid.uuid4(),
            username="newuser.mustchange",
            email="newuser@test.cm",
            hashed_password=hash_password("TempPass@123!"),
            first_name="New",
            last_name="USER",
            role=UserRoleEnum.USER,
            must_change_pwd=True,
            is_active=True,
        )
        db.add(new_user)
        db.commit()

        resp = client.post(
            f"{API}/auth/login",
            json={"username": "newuser.mustchange", "password": "TempPass@123!"},
        )
        assert resp.status_code == 200
        assert resp.json()["must_change_pwd"] is True

    def test_lockout_after_max_attempts(self, client, standard_user):
        for _ in range(5):
            client.post(
                f"{API}/auth/login",
                json={"username": "alice.test", "password": "bad"},
            )
        resp = client.post(
            f"{API}/auth/login",
            json={"username": "alice.test", "password": "Student@Test2025!"},
        )
        assert resp.status_code == 429
        assert "verrouillé" in resp.json()["detail"].lower()


class TestChangePassword:
    def test_change_password_success(self, client, user_token):
        resp = client.patch(
            f"{API}/auth/change-password",
            json={
                "current_password": "Student@Test2025!",
                "new_password": "NewSecure@Pass2025!",
                "confirm_password": "NewSecure@Pass2025!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert "succès" in resp.json()["message"].lower()

    def test_change_password_too_short(self, client, user_token):
        resp = client.patch(
            f"{API}/auth/change-password",
            json={
                "current_password": "Student@Test2025!",
                "new_password": "Short1!",
                "confirm_password": "Short1!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_change_password_no_special_char(self, client, user_token):
        resp = client.patch(
            f"{API}/auth/change-password",
            json={
                "current_password": "Student@Test2025!",
                "new_password": "NoSpecialChar123",
                "confirm_password": "NoSpecialChar123",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_change_password_mismatch(self, client, user_token):
        resp = client.patch(
            f"{API}/auth/change-password",
            json={
                "current_password": "Student@Test2025!",
                "new_password": "NewPass@2025!",
                "confirm_password": "DifferentPass@2025!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_change_password_wrong_current(self, client, user_token):
        resp = client.patch(
            f"{API}/auth/change-password",
            json={
                "current_password": "WrongCurrentPass@!",
                "new_password": "NewSecure@Pass2025!",
                "confirm_password": "NewSecure@Pass2025!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 401

    def test_change_password_unauthenticated(self, client):
        resp = client.patch(
            f"{API}/auth/change-password",
            json={
                "current_password": "x",
                "new_password": "NewSecure@Pass2025!",
                "confirm_password": "NewSecure@Pass2025!",
            },
        )
        assert resp.status_code == 403

    def test_must_change_pwd_blocks_other_endpoints(self, client, db):
        from horizon.features.auth.service import create_access_token, hash_password
        from horizon.shared.models import User, UserRoleEnum

        forced = User(
            id=uuid.uuid4(),
            username="forced.change",
            email="forced@test.cm",
            hashed_password=hash_password("Temp@Pass123!"),
            first_name="Forced",
            last_name="CHANGE",
            role=UserRoleEnum.USER,
            must_change_pwd=True,
            is_active=True,
        )
        db.add(forced)
        db.commit()

        token = create_access_token(str(forced.id), "USER", must_change_pwd=True)

        resp = client.get(f"{API}/vms", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert "POL-COMPTE-02" in resp.json()["detail"]

    def test_unauthenticated_access_rejected(self, client):
        resp = client.get(f"{API}/vms")
        assert resp.status_code == 403


class TestMe:
    def test_me_with_valid_token(self, client, user_token, standard_user):
        resp = client.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == standard_user.username
        assert body["email"] == standard_user.email

    def test_me_without_token(self, client):
        resp = client.get(f"{API}/auth/me")
        assert resp.status_code == 403
