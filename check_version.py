"""Check alembic version stamp."""
import logging
logging.disable(logging.CRITICAL)

import asyncio
from app.db.base import get_db
from sqlalchemy import text

async def check():
    async for db in get_db():
        r = await db.execute(text("SELECT version_num FROM alembic_version"))
        rows = r.fetchall()
        print("Alembic version stamp:", rows)
        break

asyncio.run(check())
