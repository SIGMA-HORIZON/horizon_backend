"""Check DB - suppress SQLAlchemy logging."""
import logging
logging.disable(logging.CRITICAL)

import asyncio
from app.db.base import get_db
from sqlalchemy import text

async def check():
    async for db in get_db():
        r = await db.execute(
            text("SELECT typname FROM pg_type WHERE typcategory = 'E' ORDER BY typname")
        )
        print("Enums:", [row[0] for row in r.fetchall()])
        r2 = await db.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        )
        print("Tables:", [row[0] for row in r2.fetchall()])
        break

asyncio.run(check())
