
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import redis

load_dotenv()

db_url = os.getenv("DATABASE_URL")
redis_url = os.getenv("REDIS_URL")

print(f"Testing DB connection to: {db_url}")
try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("DB Connection successful!")
except Exception as e:
    print(f"DB Connection failed: {e}")

print(f"Testing Redis connection to: {redis_url}")
try:
    r = redis.from_url(redis_url)
    if r.ping():
        print("Redis Connection successful!")
    else:
        print("Redis Connection failed (no pong)!")
except Exception as e:
    print(f"Redis Connection failed: {e}")
