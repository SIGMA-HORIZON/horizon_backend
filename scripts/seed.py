"""
Horizon - Seed Dataset
Données de test : 3 admins, 10 users, 15 VMs, 8 ISO, logs, incidents, violations
Exécution : python seed.py
"""

from horizon.shared.models import (
    AccountRequest,
    AccountRequestStatus,
    AuditAction,
    AuditLog,
    ISOImage,
    IsoProxmoxTemplate,
    LoginAttempt,
    OSFamily,
    PhysicalNode,
    QuotaOverride,
    QuotaPolicy,
    QuotaViolation,
    Reservation,
    Role,
    RolePermission,
    SanctionLevel,
    SecurityIncident,
    User,
    UserRoleEnum,
    VirtualMachine,
    ViolationType,
    VMStatus,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
import uuid
import sys
import os
from datetime import datetime, timezone, timedelta

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://horizon_user:horizon_pass@localhost:5432/horizon_db"
)

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

pwd_ctx = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
now = datetime.now(timezone.utc)


def hash_pwd(plain: str) -> str:
    return pwd_ctx.hash(plain)


def seed():
    session = Session()
    try:
        if session.query(Role).first() is not None:
            print("Seed ignoré : la base contient déjà des données (rôles présents).")
            return

        print("Seeding Horizon database...")

        # ------------------------------------------------------------------ ROLES
        print("  -> Roles & permissions...")
        role_user = Role(id=uuid.uuid4(), name="user",
                         description="Standard student user")
        role_admin = Role(id=uuid.uuid4(), name="admin",
                          description="Platform administrator")
        role_super = Role(id=uuid.uuid4(), name="super_admin",
                          description="SIGMA infrastructure team")
        session.add_all([role_user, role_admin, role_super])
        session.flush()

        user_perms = ["vm:create", "vm:read", "vm:stop", "vm:delete", "vm:modify",
                      "reservation:extend", "file:download", "profile:update"]
        admin_perms = user_perms + ["account:approve", "account:reject", "account:suspend",
                                    "vm:force_stop", "vm:admin_delete", "quota:override",
                                    "iso:manage", "audit:read", "dashboard:global"]
        super_perms = admin_perms + ["proxmox:direct", "infra:configure", "role:manage",
                                     "policy:modify", "system:full"]

        for perm in user_perms:
            session.add(RolePermission(id=uuid.uuid4(),
                        role_id=role_user.id, permission=perm))
        for perm in admin_perms:
            session.add(RolePermission(id=uuid.uuid4(),
                        role_id=role_admin.id, permission=perm))
        for perm in super_perms:
            session.add(RolePermission(id=uuid.uuid4(),
                        role_id=role_super.id, permission=perm))

        # -------------------------------------------------------------- QUOTA POLICIES
        print("  -> Quota policies...")
        qp_student = QuotaPolicy(
            id=uuid.uuid4(), name="student_default",
            description="Politique par défaut pour les étudiants",
            max_vcpu_per_vm=2, max_ram_gb_per_vm=2.0, max_storage_gb_per_vm=20.0,
            max_shared_space_gb=5.0, max_simultaneous_vms=2, max_session_duration_hours=8,
            hard_limit_vcpu=8, hard_limit_ram_gb=16.0, hard_limit_storage_gb=100.0,
            hard_limit_simultaneous_vms=5, hard_limit_session_hours=72, hard_limit_shared_space_gb=20.0,
        )
        qp_researcher = QuotaPolicy(
            id=uuid.uuid4(), name="researcher",
            description="Politique pour projets de recherche intensifs",
            max_vcpu_per_vm=4, max_ram_gb_per_vm=8.0, max_storage_gb_per_vm=50.0,
            max_shared_space_gb=10.0, max_simultaneous_vms=4, max_session_duration_hours=48,
            hard_limit_vcpu=8, hard_limit_ram_gb=16.0, hard_limit_storage_gb=100.0,
            hard_limit_simultaneous_vms=5, hard_limit_session_hours=72, hard_limit_shared_space_gb=20.0,
        )
        qp_admin_lab = QuotaPolicy(
            id=uuid.uuid4(), name="admin_lab",
            description="Politique pour les administrateurs (usage labo)",
            max_vcpu_per_vm=8, max_ram_gb_per_vm=16.0, max_storage_gb_per_vm=100.0,
            max_shared_space_gb=20.0, max_simultaneous_vms=5, max_session_duration_hours=72,
            hard_limit_vcpu=8, hard_limit_ram_gb=16.0, hard_limit_storage_gb=100.0,
            hard_limit_simultaneous_vms=5, hard_limit_session_hours=72, hard_limit_shared_space_gb=20.0,
        )
        session.add_all([qp_student, qp_researcher, qp_admin_lab])
        session.flush()

        # ----------------------------------------------------------------------- ADMINS
        print("  -> Admin accounts (3)...")
        admin1 = User(
            id=uuid.uuid4(), username="admin.tamegue",
            email="tameguedonald@gmail.com",
            hashed_password=hash_pwd("Admin@Horizon2025!"),
            first_name="Donald", last_name="TAMEGUE NEGOU",
            organisation="ENSPY / SIGMA",
            role=UserRoleEnum.SUPER_ADMIN, role_id=role_super.id,
            must_change_pwd=False, is_active=True,
            quota_policy_id=qp_admin_lab.id,
            last_login_at=now - timedelta(hours=2),
        )
        admin2 = User(
            id=uuid.uuid4(), username="admin.zuchuon",
            email="zuchuon@enspy.cm",
            hashed_password=hash_pwd("Admin@Horizon2025!"),
            first_name="Nathanael", last_name="ZUCHUON",
            organisation="ENSPY / SIGMA",
            role=UserRoleEnum.ADMIN, role_id=role_admin.id,
            must_change_pwd=False, is_active=True,
            quota_policy_id=qp_admin_lab.id,
            last_login_at=now - timedelta(hours=5),
        )
        admin3 = User(
            id=uuid.uuid4(), username="admin.demanou",
            email="billnelson113@gmail.com",
            hashed_password=hash_pwd("Admin@Horizon2025!"),
            first_name="Bill Nelson", last_name="DEMANOU",
            organisation="ENSPY / SIGMA",
            role=UserRoleEnum.ADMIN, role_id=role_admin.id,
            must_change_pwd=False, is_active=True,
            quota_policy_id=qp_admin_lab.id,
            last_login_at=now - timedelta(days=1),
        )
        session.add_all([admin1, admin2, admin3])
        session.flush()

        # ----------------------------------------------------------------------- USERS (10)
        print("  -> Student accounts (10)...")
        users_data = [
            ("alice.mvondo",   "alice.mvondo@enspy.cm",
             "Alice",    "MVONDO",    "INFO3"),
            ("boris.ateba",    "boris.ateba@enspy.cm",
             "Boris",    "ATEBA",     "INFO3"),
            ("carole.nkolo",   "carole.nkolo@enspy.cm",
             "Carole",   "NKOLO",     "INFO2"),
            ("david.fotso",    "david.fotso@enspy.cm",
             "David",    "FOTSO",     "INFO4"),
            ("eve.ndjomo",     "eve.ndjomo@enspy.cm",
             "Eve",      "NDJOMO",    "INFO2"),
            ("felix.mbarga",   "felix.mbarga@enspy.cm",
             "Felix",    "MBARGA",    "INFO3"),
            ("grace.ondoa",    "grace.ondoa@enspy.cm",
             "Grace",    "ONDOA",     "INFO4"),
            ("herve.nlend",    "herve.nlend@enspy.cm",
             "Herve",    "NLEND",     "INFO3"),
            ("iris.bikoko",    "iris.bikoko@enspy.cm",
             "Iris",     "BIKOKO",    "INFO2"),
            ("jules.ongolo",   "jules.ongolo@enspy.cm",
             "Jules",    "ONGOLO",    "INFO4"),
        ]

        all_users = []
        for uname, email, fn, ln, org in users_data:
            policy = qp_researcher if org == "INFO4" else qp_student
            u = User(
                id=uuid.uuid4(), username=uname, email=email,
                hashed_password=hash_pwd("Student@2025!"),
                first_name=fn, last_name=ln, organisation=f"ENSPY - {org}",
                role=UserRoleEnum.USER, role_id=role_user.id,
                must_change_pwd=False, is_active=True,
                quota_policy_id=policy.id,
                last_login_at=now - timedelta(hours=len(all_users) + 1),
            )
            all_users.append(u)

        # User inactif depuis 95 jours - doit être suspendu (POL-ACCOUNT-03)
        inactive_user = User(
            id=uuid.uuid4(), username="kevin.inactive",
            email="kevin.inactive@enspy.cm",
            hashed_password=hash_pwd("Student@2025!"),
            first_name="Kevin", last_name="INACTIF",
            organisation="ENSPY - INFO2",
            role=UserRoleEnum.USER, role_id=role_user.id,
            must_change_pwd=False, is_active=False,
            quota_policy_id=qp_student.id,
            last_login_at=now - timedelta(days=95),
        )
        all_users.append(inactive_user)
        session.add_all(all_users)
        session.flush()

        # Override individuel pour alice - plus de RAM autorisée
        override_alice = QuotaOverride(
            id=uuid.uuid4(), user_id=all_users[0].id,
            max_ram_gb_per_vm=8.0, max_session_duration_hours=24,
            granted_by_id=admin2.id,
            reason="Projet ML intensif - validation superviseur",
        )
        session.add(override_alice)
        session.flush()

        # ----------------------------------------------------------------- ISO IMAGES (8)
        print("  -> ISO images (8)...")
        iso_data = [
            ("Ubuntu 22.04 LTS",    "ubuntu-22.04-live-server-amd64.iso",
             OSFamily.LINUX,   "22.04 LTS",     "Serveur Ubuntu LTS - recommandé"),
            ("Ubuntu 20.04 LTS",    "ubuntu-20.04.6-live-server-amd64.iso",
             OSFamily.LINUX,  "20.04 LTS",     "Serveur Ubuntu LTS - support étendu"),
            ("Debian 12 Bookworm",  "debian-12.4.0-amd64-netinst.iso",
             OSFamily.LINUX,   "12 Bookworm",   "Debian stable minimaliste"),
            ("CentOS Stream 9",     "CentOS-Stream-9-latest-x86_64.iso",
             OSFamily.LINUX,   "Stream 9",      "CentOS pour environnements serveur"),
            ("Fedora 39 Server",    "Fedora-Server-dvd-x86_64-39.iso",
             OSFamily.LINUX,   "39",            "Fedora Server - technologies récentes"),
            ("Kali Linux 2024.1",   "kali-linux-2024.1-installer-amd64.iso", OSFamily.LINUX,
             "2024.1",        "Kali - sécurité et pentest (usage pédagogique)"),
            ("Windows Server 2022", "WinServer2022_x64.iso",
             OSFamily.WINDOWS, "Server 2022",   "Windows Server pour TP systèmes"),
            ("Windows 11 Pro",      "Win11_23H2_x64.iso",
             OSFamily.WINDOWS, "11 23H2",       "Windows 11 - TP applications bureau"),
        ]

        isos = []
        for name, filename, family, version, desc in iso_data:
            iso = ISOImage(
                id=uuid.uuid4(), name=name, filename=filename,
                os_family=family, os_version=version, description=desc,
                is_active=True, added_by_id=admin1.id,
            )
            isos.append(iso)

        session.add_all(isos)
        session.flush()

        # Correspondances ISO → template Proxmox (VMID d'exemple : à remplacer par vos vrais templates)
        iso_templates = [
            IsoProxmoxTemplate(
                id=uuid.uuid4(),
                iso_image_id=iso.id,
                proxmox_template_vmid=9000 + idx,
            )
            for idx, iso in enumerate(isos)
        ]
        session.add_all(iso_templates)

        # ---------------------------------------------------------- VIRTUAL MACHINES (15)
        print("  -> Virtual machines (15)...")
        nodes_cycle = [PhysicalNode.REM, PhysicalNode.RAM, PhysicalNode.EMILIA]
        vm_configs = [
            # (owner_idx, name, vcpu, ram, storage, iso_idx, status, lease_delta_hours, proxmox_vmid)
            (0, "alice-ml-training",      4, 8.0,
             50.0, 0, VMStatus.ACTIVE,    8,   101),
            (0, "alice-dev-env",          2, 2.0,
             20.0, 0, VMStatus.STOPPED,   0,   102),
            (1, "boris-webserver",        2, 2.0,
             20.0, 2, VMStatus.ACTIVE,    6,   103),
            (2, "carole-data-analysis",   2, 4.0,
             30.0, 1, VMStatus.ACTIVE,    4,   104),
            (3, "david-cuda-lab",         8, 16.0,
             80.0, 0, VMStatus.ACTIVE,    48,  105),
            (3, "david-test-vm",          2, 2.0,
             20.0, 2, VMStatus.STOPPED,   0,   106),
            (4, "eve-django-dev",         2, 2.0,
             20.0, 0, VMStatus.ACTIVE,    3,   107),
            (5, "felix-docker-host",      4, 4.0,
             40.0, 2, VMStatus.ACTIVE,    12,  108),
            (6, "grace-simulation",       4, 8.0,
             60.0, 4, VMStatus.ACTIVE,    24,  109),
            (6, "grace-backup-vm",        2, 2.0,
             20.0, 1, VMStatus.EXPIRED,   0,   110),
            (7, "herve-security-lab",     2, 4.0,
             25.0, 5, VMStatus.ACTIVE,    5,   111),
            (8, "iris-win-dev",           4, 8.0,
             60.0, 6, VMStatus.ACTIVE,    8,   112),
            (9, "jules-research-cluster", 8, 16.0,
             100.0, 0, VMStatus.ACTIVE,    72,  113),
            (9, "jules-staging-env",      4, 4.0,
             40.0, 1, VMStatus.SUSPENDED, 0,   114),
            (2, "carole-win-test",        2, 4.0,
             40.0, 7, VMStatus.STOPPED,   0,   115),
        ]

        vms = []
        for i, (owner_idx, name, vcpu, ram, storage, iso_idx, status, lease_h, pvmid) in enumerate(vm_configs):
            node = nodes_cycle[i % 3]
            lease_start = now - timedelta(hours=2)
            lease_end = now + \
                timedelta(hours=lease_h) if lease_h > 0 else now - \
                timedelta(hours=1)
            vm = VirtualMachine(
                id=uuid.uuid4(), proxmox_vmid=pvmid, name=name,
                owner_id=all_users[owner_idx].id,
                node=node, vcpu=vcpu, ram_gb=ram, storage_gb=storage,
                iso_image_id=isos[iso_idx].id,
                status=status, lease_start=lease_start, lease_end=lease_end,
                vlan_id=100 + owner_idx,
                ip_address=f"10.0.{owner_idx}.{i+10}",
                ssh_public_key="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... horizon-generated",
                shared_space_gb=round(storage * 0.05, 1),
                stopped_at=now -
                timedelta(hours=3) if status != VMStatus.ACTIVE else None,
            )
            vms.append(vm)

        session.add_all(vms)
        session.flush()

        # ------------------------------------------------------------ RESERVATIONS
        print("  -> Reservations...")
        reservations = []
        for vm in vms[:8]:
            r = Reservation(
                id=uuid.uuid4(), vm_id=vm.id, user_id=vm.owner_id,
                start_time=vm.lease_start, end_time=vm.lease_end,
                extended=False,
            )
            reservations.append(r)
        session.add_all(reservations)
        session.flush()

        # --------------------------------------------------------------- AUDIT LOGS
        print("  -> Audit logs...")
        audit_entries = [
            (admin1.id, AuditAction.ACCOUNT_APPROVED,
             "user", all_users[0].id, "192.168.1.1"),
            (admin1.id, AuditAction.ACCOUNT_APPROVED,
             "user", all_users[1].id, "192.168.1.1"),
            (admin2.id, AuditAction.ACCOUNT_APPROVED,
             "user", all_users[2].id, "192.168.1.2"),
            (admin2.id, AuditAction.QUOTA_OVERRIDE_GRANTED,
             "user", all_users[0].id, "192.168.1.2"),
            (all_users[0].id, AuditAction.VM_CREATED,
             "vm", vms[0].id, "10.0.0.10"),
            (all_users[0].id, AuditAction.LOGIN_SUCCESS,
             "user", all_users[0].id, "10.0.0.10"),
            (all_users[3].id, AuditAction.VM_CREATED,
             "vm", vms[4].id, "10.0.3.10"),
            (admin1.id, AuditAction.VM_FORCE_STOPPED,
             "vm", vms[13].id, "192.168.1.1"),
            (admin2.id, AuditAction.ACCOUNT_SUSPENDED,
             "user", inactive_user.id, "192.168.1.2"),
            (all_users[5].id, AuditAction.LOGIN_FAILURE,
             "user", all_users[5].id, "10.0.5.1"),
            (all_users[5].id, AuditAction.LOGIN_SUCCESS,
             "user", all_users[5].id, "10.0.5.1"),
            (admin1.id, AuditAction.ISO_IMAGE_ADDED,
             "iso_image", isos[5].id, "192.168.1.1"),
            (all_users[8].id, AuditAction.VM_CREATED,
             "vm", vms[11].id, "10.0.8.10"),
            (all_users[9].id, AuditAction.VM_LEASE_EXTENDED,
             "vm", vms[12].id, "10.0.9.10"),
            (admin3.id, AuditAction.PASSWORD_RESET,
             "user", all_users[4].id, "192.168.1.3"),
        ]
        for i, (actor, action, ttype, tid, ip) in enumerate(audit_entries):
            session.add(AuditLog(
                id=uuid.uuid4(), actor_id=actor, action=action,
                target_type=ttype, target_id=tid, ip_address=ip,
                timestamp=now - timedelta(minutes=i * 30),
                log_metadata={"source": "horizon_web",
                              "session_id": str(uuid.uuid4())},
            ))

        # ------------------------------------------------------------ LOGIN ATTEMPTS
        print("  -> Login attempts...")
        for i in range(5):
            session.add(LoginAttempt(
                id=uuid.uuid4(), user_id=all_users[5].id,
                username_tried="felix.mbarga", success=(i == 4),
                ip_address="10.0.5.1", timestamp=now - timedelta(minutes=60 - i * 10),
            ))

        # ------------------------------------------------------- SECURITY INCIDENTS (3)
        print("  -> Security incidents...")
        inc1 = SecurityIncident(
            id=uuid.uuid4(), vm_id=vms[13].id, user_id=all_users[9].id,
            incident_type=IncidentType.NETWORK_SCAN_DETECTED,
            severity=IncidentSeverity.HIGH, status=IncidentStatus.RESOLVED,
            description="Scan de port détecté depuis la VM jules-staging-env vers d'autres VMs du cluster.",
            created_at=now - timedelta(hours=48),
            resolved_at=now - timedelta(hours=24),
            resolved_by_id=admin1.id,
        )
        inc2 = SecurityIncident(
            id=uuid.uuid4(), vm_id=vms[10].id, user_id=all_users[7].id,
            incident_type=IncidentType.EXPLOIT_TOOL_DETECTED,
            severity=IncidentSeverity.MEDIUM, status=IncidentStatus.INVESTIGATING,
            description="Outil de fuzzing détecté en exécution sur herve-security-lab - usage pédagogique non déclaré.",
            created_at=now - timedelta(hours=6),
        )
        inc3 = SecurityIncident(
            id=uuid.uuid4(), vm_id=None, user_id=inactive_user.id,
            incident_type=IncidentType.UNAUTHORIZED_API_ACCESS,
            severity=IncidentSeverity.LOW, status=IncidentStatus.RESOLVED,
            description="Tentative d'appel API avec token expiré depuis compte suspendu.",
            created_at=now - timedelta(days=10),
            resolved_at=now - timedelta(days=9),
            resolved_by_id=admin2.id,
        )
        session.add_all([inc1, inc2, inc3])

        # ------------------------------------------------------- QUOTA VIOLATIONS (4)
        print("  -> Quota violations...")
        viol1 = QuotaViolation(
            id=uuid.uuid4(), vm_id=vms[4].id, user_id=all_users[3].id,
            violation_type=ViolationType.SESSION_TIME,
            sanction_level=SanctionLevel.LEVEL_1,
            observed_value=50.0, limit_value=48.0, resolved=True,
            created_at=now - timedelta(hours=72),
        )
        viol2 = QuotaViolation(
            id=uuid.uuid4(), vm_id=vms[0].id, user_id=all_users[0].id,
            violation_type=ViolationType.RAM,
            sanction_level=SanctionLevel.LEVEL_1,
            observed_value=9.2, limit_value=8.0, resolved=True,
            created_at=now - timedelta(hours=24),
        )
        viol3 = QuotaViolation(
            id=uuid.uuid4(), vm_id=vms[8].id, user_id=all_users[6].id,
            violation_type=ViolationType.CPU,
            sanction_level=SanctionLevel.LEVEL_2,
            observed_value=6.0, limit_value=4.0, resolved=False,
            created_at=now - timedelta(hours=3),
        )
        viol4 = QuotaViolation(
            id=uuid.uuid4(), vm_id=None, user_id=all_users[9].id,
            violation_type=ViolationType.VM_COUNT,
            sanction_level=SanctionLevel.LEVEL_2,
            observed_value=3.0, limit_value=2.0, resolved=False,
            created_at=now - timedelta(hours=48),
        )
        session.add_all([viol1, viol2, viol3, viol4])

        # ------------------------------------------------------ ACCOUNT REQUESTS (3)
        print("  -> Account requests...")
        req1 = AccountRequest(
            id=uuid.uuid4(), first_name="Mireille", last_name="TSIMI",
            email="mireille.tsimi@enspy.cm", organisation="ENSPY - INFO1",
            justification="Projet de fin d'année - simulation réseau",
            status=AccountRequestStatus.PENDING,
        )
        req2 = AccountRequest(
            id=uuid.uuid4(), first_name="Patrick", last_name="NOAH",
            email="patrick.noah@enspy.cm", organisation="ENSPY - INFO3",
            justification="TP systèmes d'exploitation - virtualisation",
            status=AccountRequestStatus.APPROVED,
            reviewed_by_id=admin2.id,
            reviewed_at=(now - timedelta(days=5)).isoformat(),
            user_id=all_users[2].id,
        )
        req3 = AccountRequest(
            id=uuid.uuid4(), first_name="Sandra", last_name="KANA",
            email="sandra.kana@external.cm", organisation="Externe",
            justification="Recherche personnelle",
            status=AccountRequestStatus.REJECTED,
            reviewed_by_id=admin1.id,
            reviewed_at=(now - timedelta(days=3)).isoformat(),
            rejection_reason="Accès réservé aux membres ENSPY uniquement.",
        )
        session.add_all([req1, req2, req3])

        session.commit()
        print("\nSeed terminé avec succès.")
        print(f"  Roles         : 3")
        print(f"  Quota policies: 3")
        print(f"  Admins        : 3")
        print(f"  Users         : {len(all_users)}")
        print(f"  ISO images    : {len(isos)}")
        print(f"  VMs           : {len(vms)}")
        print(f"  Reservations  : {len(reservations)}")
        print(f"  Audit logs    : {len(audit_entries)}")
        print(f"  Incidents     : 3")
        print(f"  Violations    : 4")
        print(f"  Requests      : 3")
        print("\nMot de passe admins  : Admin@Horizon2025!")
        print("Mot de passe users   : Student@2025!")

    except Exception as e:
        session.rollback()
        print(f"ERREUR : {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
