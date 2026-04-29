from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def update_templates():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        print("Updating all ISO templates to point to VMID 100...")
        conn.execute(text("UPDATE iso_proxmox_templates SET proxmox_template_vmid = 100;"))
    print("Done.")

if __name__ == "__main__":
    update_templates()
