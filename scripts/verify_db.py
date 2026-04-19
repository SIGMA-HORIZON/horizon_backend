from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

tables = ['users', 'roles', 'virtual_machines', 'iso_images']
with engine.connect() as conn:
    print("Database State Verification:")
    for t in tables:
        count = conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()
        print(f"  {t}: {count}")
