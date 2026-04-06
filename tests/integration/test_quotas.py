"""Tests d'intégration — résolution des quotas (get_effective_quota)."""

import uuid


class TestEffectiveQuota:
    def test_quota_from_policy(self, db, standard_user, quota_policy):
        from horizon.features.vms.quota_service import get_effective_quota

        quota = get_effective_quota(db, standard_user.id)
        assert quota.max_vcpu_per_vm == 2
        assert quota.max_ram_gb_per_vm == 4.0
        assert quota.max_simultaneous_vms == 3

    def test_quota_override_takes_precedence(self, db, standard_user, quota_policy):
        from horizon.features.vms.quota_service import get_effective_quota
        from horizon.shared.models import QuotaOverride

        override = QuotaOverride(
            id=uuid.uuid4(),
            user_id=standard_user.id,
            max_vcpu_per_vm=6,
            max_ram_gb_per_vm=12.0,
        )
        db.add(override)
        db.commit()

        quota = get_effective_quota(db, standard_user.id)
        assert quota.max_vcpu_per_vm == 6
        assert quota.max_ram_gb_per_vm == 12.0
        assert quota.max_storage_gb_per_vm == 20.0

        db.delete(override)
        db.commit()

    def test_null_override_fields_use_policy(self, db, standard_user, quota_policy):
        from horizon.features.vms.quota_service import get_effective_quota
        from horizon.shared.models import QuotaOverride

        override = QuotaOverride(
            id=uuid.uuid4(),
            user_id=standard_user.id,
            max_vcpu_per_vm=4,
        )
        db.add(override)
        db.commit()

        quota = get_effective_quota(db, standard_user.id)
        assert quota.max_vcpu_per_vm == 4
        assert quota.max_ram_gb_per_vm == 4.0

        db.delete(override)
        db.commit()
