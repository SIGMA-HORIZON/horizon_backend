import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Path adjustment
sys.path.append(os.getcwd())

load_dotenv()

from horizon.features.vms.service import _resolve_proxmox_node_name
from horizon.shared.models import PhysicalNode

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    for node in [PhysicalNode.REM, PhysicalNode.RAM, PhysicalNode.EMILIA]:
        res = _resolve_proxmox_node_name(db, node)
        print(f"{node} -> {res}")
finally:
    db.close()
