"""Tests unitaires — horizon.shared.policies.enforcer."""

import uuid

import pytest


class TestPasswordStrength:
    def test_strong_password_passes(self):
        from horizon.shared.policies.enforcer import enforce_password_strength

        enforce_password_strength("StrongPass@2025!")

    def test_too_short_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_password_strength

        with pytest.raises(PolicyError) as exc:
            enforce_password_strength("Short1!")
        assert "POL-COMPTE-02" in str(exc.value.detail)

    def test_no_uppercase_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_password_strength

        with pytest.raises(PolicyError):
            enforce_password_strength("nouppercase@2025!")

    def test_no_digit_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_password_strength

        with pytest.raises(PolicyError):
            enforce_password_strength("NoDigitPass@!")

    def test_no_special_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_password_strength

        with pytest.raises(PolicyError):
            enforce_password_strength("NoSpecial2025Abc")


class TestQuotaEnforcer:
    def test_vm_within_limits_passes(self):
        from horizon.shared.policies.enforcer import enforce_vm_resource_limits

        enforce_vm_resource_limits(2, 4.0, 20.0, 4, 8.0, 50.0)

    def test_vcpu_exceeded_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_vm_resource_limits

        with pytest.raises(PolicyError) as exc:
            enforce_vm_resource_limits(5, 2.0, 20.0, 2, 8.0, 50.0)
        assert "CPU" in exc.value.detail

    def test_ram_exceeded_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_vm_resource_limits

        with pytest.raises(PolicyError) as exc:
            enforce_vm_resource_limits(2, 10.0, 20.0, 2, 8.0, 50.0)
        assert "RAM" in exc.value.detail

    def test_storage_exceeded_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_vm_resource_limits

        with pytest.raises(PolicyError) as exc:
            enforce_vm_resource_limits(2, 2.0, 60.0, 2, 8.0, 50.0)
        assert "Stockage" in exc.value.detail

    def test_hard_limit_vcpu_absolute(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_hard_limits

        with pytest.raises(PolicyError) as exc:
            enforce_hard_limits(vcpu=9, ram_gb=4.0, storage_gb=20.0, session_hours=8)
        assert "POL-RESSOURCES" in exc.value.detail

    def test_hard_limit_ram_absolute(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_hard_limits

        with pytest.raises(PolicyError):
            enforce_hard_limits(vcpu=2, ram_gb=20.0, storage_gb=20.0, session_hours=8)

    def test_hard_limit_session_absolute(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_hard_limits

        with pytest.raises(PolicyError):
            enforce_hard_limits(vcpu=2, ram_gb=4.0, storage_gb=20.0, session_hours=100)

    def test_vm_count_limit_reached(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_vm_count_limit

        with pytest.raises(PolicyError) as exc:
            enforce_vm_count_limit(current_vm_count=3, max_simultaneous_vms=3)
        assert "POL-RESSOURCES" in exc.value.detail

    def test_vm_count_under_limit_passes(self):
        from horizon.shared.policies.enforcer import enforce_vm_count_limit

        enforce_vm_count_limit(2, 3)

    def test_session_duration_within_limit(self):
        from horizon.shared.policies.enforcer import enforce_session_duration

        enforce_session_duration(8, 48)

    def test_session_duration_exceeded(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_session_duration

        with pytest.raises(PolicyError) as exc:
            enforce_session_duration(73, 72)
        assert "POL-RESSOURCES-01" in exc.value.detail

    def test_session_duration_zero_invalid(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_session_duration

        with pytest.raises(PolicyError):
            enforce_session_duration(0, 8)

    def test_iso_inactive_raises(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_iso_authorized

        with pytest.raises(PolicyError) as exc:
            enforce_iso_authorized(iso_is_active=False)
        assert "POL-RESSOURCES-02" in exc.value.detail

    def test_iso_active_passes(self):
        from horizon.shared.policies.enforcer import enforce_iso_authorized

        enforce_iso_authorized(iso_is_active=True)


class TestVMOwnership:
    def test_owner_can_act(self):
        from horizon.shared.policies.enforcer import enforce_vm_ownership

        uid = uuid.uuid4()
        enforce_vm_ownership(uid, uid, "USER")

    def test_non_owner_user_rejected(self):
        from horizon.shared.policies.enforcer import PolicyError, enforce_vm_ownership

        with pytest.raises(PolicyError) as exc:
            enforce_vm_ownership(uuid.uuid4(), uuid.uuid4(), "USER")
        assert "BD-02" in exc.value.detail

    def test_admin_can_act_on_any_vm(self):
        from horizon.shared.policies.enforcer import enforce_vm_ownership

        enforce_vm_ownership(uuid.uuid4(), uuid.uuid4(), "ADMIN")

    def test_super_admin_can_act_on_any_vm(self):
        from horizon.shared.policies.enforcer import enforce_vm_ownership

        enforce_vm_ownership(uuid.uuid4(), uuid.uuid4(), "SUPER_ADMIN")
