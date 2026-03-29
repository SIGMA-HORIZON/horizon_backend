"""One-time script to drop orphaned enums from the database so migrations can run cleanly."""
import asyncio
from sqlalchemy import text
from app.db.base import get_db

async def cleanup():
    async for db in get_db():
        enums = [
            'roletype', 'vmstatus', 'nodestatus', 'ostype',
            'sshalgorithm', 'actiontype', 'notiftype', 'accountrequeststatus'
        ]
        for e in enums:
            await db.execute(text(f'DROP TYPE IF EXISTS {e} CASCADE'))
            print(f'Dropped: {e}')
        await db.commit()
        print('All done')
        break  # only need one session

asyncio.run(cleanup())
