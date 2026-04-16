
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Disabling force password change for negou.donald...")
    result = conn.execute(
        text("UPDATE users SET must_change_pwd = false WHERE username = 'negou.donald'")
    )
    conn.commit()
    print(f"Updated {result.rowcount} user(s).")
