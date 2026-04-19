"""Tâches planifiées APScheduler."""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from horizon.core.config import get_settings

logger = logging.getLogger("horizon.scheduler")
settings = get_settings()

scheduler = BackgroundScheduler(timezone="UTC")


def _get_db():
    from horizon.infrastructure.database import SessionLocal

    return SessionLocal()


def task_expire_vms():
    from horizon.infrastructure.email_service import send_vm_expiry_warning
    from horizon.shared.audit_service import log_action
    from horizon.shared.models import AuditAction, VirtualMachine, VMStatus

    db = _get_db()
    try:
        now = datetime.now(timezone.utc)
        warning_threshold = now + timedelta(minutes=settings.VM_EXPIRY_WARNING_MINUTES)

        vms_expiring_soon = (
            db.query(VirtualMachine)
            .filter(
                VirtualMachine.status == VMStatus.ACTIVE,
                VirtualMachine.lease_end <= warning_threshold,
                VirtualMachine.lease_end > now,
            )
            .all()
        )
        for vm in vms_expiring_soon:
            remaining = int((vm.lease_end - now).total_seconds() / 60)
            send_vm_expiry_warning(vm.owner.email, vm.name, remaining)
            logger.info("[POL-RESSOURCES-01] Notif expiration VM %s dans %smin", vm.id, remaining)

        vms_expired = (
            db.query(VirtualMachine)
            .filter(
                VirtualMachine.status == VMStatus.ACTIVE,
                VirtualMachine.lease_end <= now,
            )
            .all()
        )
        for vm in vms_expired:
            vm.status = VMStatus.EXPIRED
            vm.stopped_at = now
            log_action(
                db,
                None,
                AuditAction.VM_EXPIRED,
                "vm",
                vm.id,
                metadata={"auto": True, "lease_end": vm.lease_end.isoformat()},
            )
            logger.info("[POL-RESSOURCES-01] VM %s expirée", vm.id)

        db.commit()
    except Exception as e:
        logger.error("[task_expire_vms] Erreur : %s", e)
        db.rollback()
    finally:
        db.close()


def task_delete_old_vms():
    from horizon.shared.audit_service import log_action
    from horizon.shared.models import AuditAction, VirtualMachine, VMStatus

    db = _get_db()
    try:
        threshold = datetime.now(timezone.utc) - timedelta(
            days=settings.VM_AUTO_DELETE_AFTER_STOPPED_DAYS
        )
        old_vms = (
            db.query(VirtualMachine)
            .filter(
                VirtualMachine.status.in_([VMStatus.STOPPED, VMStatus.EXPIRED]),
                VirtualMachine.stopped_at <= threshold,
            )
            .all()
        )
        for vm in old_vms:
            log_action(
                db,
                None,
                AuditAction.VM_DELETED,
                "vm",
                vm.id,
                metadata={"reason": "auto_delete_after_7_days"},
            )
            db.delete(vm)
            logger.info("[POL-RESSOURCES-01] VM %s supprimée automatiquement", vm.id)
        db.commit()
    except Exception as e:
        logger.error("[task_delete_old_vms] Erreur : %s", e)
        db.rollback()
    finally:
        db.close()


def task_purge_shared_spaces():
    from horizon.infrastructure.email_service import send_shared_space_purge_warning
    from horizon.shared.models import VirtualMachine, VMStatus

    db = _get_db()
    try:
        now = datetime.now(timezone.utc)
        warning_at = now + timedelta(hours=settings.SHARED_SPACE_PURGE_WARNING_HOURS)
        purge_threshold = now - timedelta(hours=settings.SHARED_SPACE_RETENTION_HOURS)

        vms_to_warn = (
            db.query(VirtualMachine)
            .filter(
                VirtualMachine.status.in_([VMStatus.STOPPED, VMStatus.EXPIRED]),
                VirtualMachine.stopped_at <= warning_at,
                VirtualMachine.stopped_at > purge_threshold,
                VirtualMachine.shared_space_gb > 0,
            )
            .all()
        )
        for vm in vms_to_warn:
            send_shared_space_purge_warning(
                vm.owner.email,
                vm.name,
                settings.SHARED_SPACE_PURGE_WARNING_HOURS,
            )

        vms_to_purge = (
            db.query(VirtualMachine)
            .filter(
                VirtualMachine.status.in_([VMStatus.STOPPED, VMStatus.EXPIRED]),
                VirtualMachine.stopped_at <= purge_threshold,
                VirtualMachine.shared_space_gb > 0,
            )
            .all()
        )
        for vm in vms_to_purge:
            vm.shared_space_gb = 0.0
            logger.info("[POL-FICHIERS-01] Espace partagé purgé pour VM %s", vm.id)

        db.commit()
    except Exception as e:
        logger.error("[task_purge_shared_spaces] Erreur : %s", e)
        db.rollback()
    finally:
        db.close()


def task_handle_inactive_accounts():
    from horizon.infrastructure.email_service import send_account_suspended, send_inactivity_warning
    from horizon.shared.audit_service import log_action
    from horizon.shared.models import AuditAction, User

    db = _get_db()
    try:
        now = datetime.now(timezone.utc)
        warning_threshold = now - timedelta(days=settings.INACTIVITY_WARNING_DAYS)
        suspension_threshold = now - timedelta(days=settings.INACTIVITY_SUSPENSION_DAYS)
        deletion_threshold = now - timedelta(
            days=settings.INACTIVITY_SUSPENSION_DAYS + settings.DELETION_AFTER_SUSPENSION_DAYS
        )

        users_to_warn = (
            db.query(User)
            .filter(
                User.is_active == True,  # noqa: E712
                User.last_login_at <= warning_threshold,
                User.last_login_at > suspension_threshold,
            )
            .all()
        )
        for user in users_to_warn:
            days_left = settings.INACTIVITY_SUSPENSION_DAYS - (now - user.last_login_at).days
            send_inactivity_warning(user.email, user.username, days_left)

        users_to_suspend = (
            db.query(User)
            .filter(
                User.is_active == True,  # noqa: E712
                User.last_login_at <= suspension_threshold,
            )
            .all()
        )
        for user in users_to_suspend:
            user.is_active = False
            log_action(
                db,
                None,
                AuditAction.ACCOUNT_SUSPENDED,
                "user",
                user.id,
                metadata={"reason": "inactivity_90_days", "auto": True},
            )
            send_account_suspended(user.email, user.username)
            logger.info("[POL-COMPTE-03] Compte %s suspendu", user.username)

        users_to_delete = (
            db.query(User)
            .filter(
                User.is_active == False,  # noqa: E712
                User.last_login_at <= deletion_threshold,
            )
            .all()
        )
        for user in users_to_delete:
            log_action(
                db,
                None,
                AuditAction.ACCOUNT_DELETED,
                "user",
                user.id,
                metadata={"reason": "auto_deletion_120_days"},
            )
            db.delete(user)
            logger.info("[POL-COMPTE-03] Compte %s supprimé", user.username)

        db.commit()
    except Exception as e:
        logger.error("[task_handle_inactive_accounts] Erreur : %s", e)
        db.rollback()
    finally:
        db.close()


def task_monitor_vms():
    from horizon.shared.models import VirtualMachine, VMStatus, ProxmoxNodeMapping
    from horizon.infrastructure.proxmox_client import ProxmoxClient

    db = _get_db()
    try:
        # On ne synchronise que les VMs actives qui n'ont pas encore d'IP (ou pour mise à jour)
        active_vms = db.query(VirtualMachine).filter(VirtualMachine.status == VMStatus.ACTIVE).all()
        
        if not active_vms:
            return

        client = ProxmoxClient()
        if not client.enabled:
            return

        for vm in active_vms:
            # Résoudre le nom du nœud Proxmox
            mapping = db.query(ProxmoxNodeMapping).filter(
                ProxmoxNodeMapping.physical_node == vm.node
            ).first()
            px_node = mapping.proxmox_node_name if mapping else vm.node
            
            try:
                # Vérifier si la VM existe encore sur Proxmox
                status_data = client.get_vm_current_status(px_node, vm.proxmox_vmid)
                
                # Récupérer les IPs via l'agent
                ips = client.get_vm_ips(px_node, vm.proxmox_vmid)
                if ips:
                    vm.ip_address = ips[0]
                    logger.info("[POL-SURV-01] IP synchronisée pour VM %s : %s", vm.id, vm.ip_address)
                else:
                    logger.debug("[POL-SURV-01] Pas d'IP détectée pour VM %s (%s)", vm.id, vm.name)
            except Exception as e:
                # Si erreur 404 : la VM a disparu de Proxmox
                if "does not exist" in str(e) or "404" in str(e):
                    logger.error("[POL-SURV-01] VM %s introuvable sur Proxmox ! Passage en statut STOPPED.", vm.id)
                    vm.status = VMStatus.STOPPED
                    vm.stopped_at = datetime.now(timezone.utc)
                else:
                    logger.error("[POL-SURV-01] Erreur monitoring VM %s : %s", vm.id, e)
        
        db.commit()
    except Exception as e:
        logger.error("[task_monitor_vms] Erreur : %s", e)
        db.rollback()
    finally:
        db.close()


def task_purge_old_audit_logs():
    from horizon.shared.models import AuditLog

    db = _get_db()
    try:
        threshold = datetime.now(timezone.utc) - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
        deleted = db.query(AuditLog).filter(AuditLog.timestamp <= threshold).delete()
        db.commit()
        logger.info("[POL-SEC-03] %s entrées d'audit purgées", deleted)
    except Exception as e:
        logger.error("[task_purge_old_audit_logs] Erreur : %s", e)
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        task_expire_vms,
        IntervalTrigger(seconds=settings.MONITORING_INTERVAL_SECONDS),
        id="expire_vms",
        replace_existing=True,
    )
    scheduler.add_job(
        task_monitor_vms,
        IntervalTrigger(seconds=settings.MONITORING_INTERVAL_SECONDS),
        id="monitor_vms",
        replace_existing=True,
    )
    scheduler.add_job(
        task_purge_shared_spaces,
        IntervalTrigger(hours=1),
        id="purge_shared_spaces",
        replace_existing=True,
    )
    scheduler.add_job(
        task_delete_old_vms,
        IntervalTrigger(hours=24),
        id="delete_old_vms",
        replace_existing=True,
    )
    scheduler.add_job(
        task_handle_inactive_accounts,
        IntervalTrigger(hours=24),
        id="handle_inactive_accounts",
        replace_existing=True,
    )
    scheduler.add_job(
        task_purge_old_audit_logs,
        IntervalTrigger(weeks=1),
        id="purge_audit_logs",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Horizon Scheduler démarré - toutes les tâches planifiées actives.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Horizon Scheduler arrêté.")
