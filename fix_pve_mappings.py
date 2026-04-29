from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def fix_mappings():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        print("Updating proxmox_node_mappings to use 'pve'...")
        conn.execute(text("UPDATE proxmox_node_mappings SET proxmox_node_name = 'pve';"))
    print("Done.")

if __name__ == "__main__":
    fix_mappings()
