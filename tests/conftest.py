"""
Pytest — PostgreSQL via Testcontainers, Alembic, transaction par test.
Docker doit être disponible sur la machine.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:15-alpine") as pg:
        url = pg.get_connection_url().replace("postgresql://", "postgresql+psycopg2://")
        yield url


@pytest.fixture(scope="session", autouse=True)
def _test_env(postgres_url: str) -> Generator[None, None, None]:
    os.environ["DATABASE_URL"] = postgres_url
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-horizon-jwt-32bytes-x"
    os.environ["APP_SECRET_KEY"] = "test-app-secret-key-32bytes-xx"
    os.environ["EMAIL_MODE"] = "mock"
    os.environ["ENFORCE_HTTPS"] = "false"
    os.environ["APP_DEBUG"] = "false"
    os.environ["BCRYPT_ROUNDS"] = "4"
    os.environ["PROXMOX_ENABLED"] = "false"

    alembic_cfg = Config(str(ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)
    command.upgrade(alembic_cfg, "head")

    import horizon.infrastructure.scheduler as sched

    sched.start_scheduler = lambda: None
    sched.stop_scheduler = lambda: None

    yield


@pytest.fixture(scope="session")
def app(_test_env):
    from horizon.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def test_session(app) -> Generator[Session, None, None]:
    from horizon.core.config import get_settings
    from horizon.infrastructure.database import get_db

    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    connection = engine.connect()
    transaction = connection.begin()
    SessionTesting = sessionmaker(
        autocommit=False, autoflush=False, bind=connection)
    session = SessionTesting()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture
def client(app, test_session: Session) -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc


@pytest.fixture
def db(test_session: Session) -> Session:
    return test_session


@pytest.fixture
def quota_policy(db: Session):
    from horizon.shared.models import QuotaPolicy

    policy = QuotaPolicy(
        id=uuid.uuid4(),
        name="test_policy",
        max_vcpu_per_vm=2,
        max_ram_gb_per_vm=4.0,
        max_storage_gb_per_vm=20.0,
        max_shared_space_gb=5.0,
        max_simultaneous_vms=3,
        max_session_duration_hours=8,
        hard_limit_vcpu=8,
        hard_limit_ram_gb=16.0,
        hard_limit_storage_gb=100.0,
        hard_limit_simultaneous_vms=5,
        hard_limit_session_hours=72,
        hard_limit_shared_space_gb=20.0,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@pytest.fixture
def admin_user(db: Session, quota_policy):
    from horizon.features.auth.service import hash_password
    from horizon.shared.models import User, UserRoleEnum

    user = User(
        id=uuid.uuid4(),
        username="admin.test",
        email="admin@test.enspy.cm",
        hashed_password=hash_password("Admin@Test2025!"),
        first_name="Admin",
        last_name="TEST",
        role=UserRoleEnum.ADMIN,
        must_change_pwd=False,
        is_active=True,
        quota_policy_id=quota_policy.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def standard_user(db: Session, quota_policy):
    from horizon.features.auth.service import hash_password
    from horizon.shared.models import User, UserRoleEnum

    user = User(
        id=uuid.uuid4(),
        username="alice.test",
        email="alice@test.enspy.cm",
        hashed_password=hash_password("Student@Test2025!"),
        first_name="Alice",
        last_name="TEST",
        role=UserRoleEnum.USER,
        must_change_pwd=False,
        is_active=True,
        quota_policy_id=quota_policy.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    from horizon.features.auth.service import create_access_token

    return create_access_token(str(admin_user.id), admin_user.role.value, False)


@pytest.fixture
def user_token(standard_user):
    from horizon.features.auth.service import create_access_token

    return create_access_token(str(standard_user.id), standard_user.role.value, False)


@pytest.fixture
def iso_image(db: Session, admin_user):
    from horizon.shared.models import ISOImage, OSFamily

    iso = ISOImage(
        id=uuid.uuid4(),
        name="Ubuntu 22.04 LTS Test",
        filename="ubuntu-22.04-test.iso",
        os_family=OSFamily.LINUX,
        os_version="22.04 LTS",
        is_active=True,
        added_by_id=admin_user.id,
    )
    db.add(iso)
    db.commit()
    db.refresh(iso)
    return iso
