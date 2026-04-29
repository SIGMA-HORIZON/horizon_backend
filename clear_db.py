import asyncio
import os
from sqlalchemy import text
from dotenv import load_dotenv

# Re-ajouter le répertoire courant au path si nécessaire
import sys
sys.path.append(os.getcwd())

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def drop_all():
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # On utilise asyncpg pour le drop cascade du schema
    async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("+psycopg2", "")
    engine = create_async_engine(async_url)
    
    async with engine.begin() as conn:
        print("Dropping public schema...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
    
    print("Database cleared.")

if __name__ == "__main__":
    asyncio.run(drop_all())
