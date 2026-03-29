"""
Reset the database: drop all tables and types, reset alembic version.
Uses autocommit to ensure DDL changes are permanent.
"""
import logging
logging.disable(logging.CRITICAL)

import asyncio
import asyncpg
from app.core.config import settings


async def reset_db():
    # Connect directly with asyncpg in autocommit mode
    url = settings.ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "")
    # Parse user:pass@host/db
    user_pass, rest = url.split("@")
    user, password = user_pass.split(":")
    host_db = rest
    host, dbname = host_db.split("/")

    conn = await asyncpg.connect(user=user, password=password, host=host, database=dbname)

    # Drop all tables
    tables = [
        'account_requests', 'notifications', 'audit_logs', 'virtual_machines',
        'ssh_keys', 'iso_images', 'physical_nodes', 'quotas', 'usage_policies',
        'users', 'roles', 'alembic_version'
    ]
    for t in tables:
        await conn.execute(f'DROP TABLE IF EXISTS {t} CASCADE')
        print(f"Dropped table: {t}")

    # Drop all enum types
    enums = [
        'accountrequeststatus', 'notiftype', 'actiontype', 'sshalgorithm',
        'ostype', 'nodestatus', 'vmstatus', 'roletype'
    ]
    for e in enums:
        await conn.execute(f'DROP TYPE IF EXISTS {e} CASCADE')
        print(f"Dropped enum: {e}")

    await conn.close()
    print("\nDatabase fully reset. Ready for fresh migration.")


asyncio.run(reset_db())
