import asyncio
import sys
import os
from sqlalchemy import select

# Ajouter le répertoire parent au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import AsyncSessionLocal
from app.models.base_models import PhysicalNode, ISOImage, UsagePolicy, Quota
from app.models.enums import OSType, NodeStatus

async def seed_data():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Seed Usage Policy & Quota
            res = await session.execute(select(UsagePolicy).where(UsagePolicy.name == "Standard"))
            policy = res.scalars().first()
            if not policy:
                print("Creating Standard Usage Policy...")
                policy = UsagePolicy(name="Standard", is_default=True)
                session.add(policy)
                await session.flush()
                
                quota = Quota(
                    policy_id=policy.id,
                    max_cpu_cores=4,
                    max_ram_gb=8,
                    max_disk_gb=100,
                    max_concurrent_vms=2,
                    max_session_hours=24
                )
                session.add(quota)

            # 2. Seed Physical Node
            res = await session.execute(select(PhysicalNode).where(PhysicalNode.hostname == "pve"))
            node = res.scalars().first()
            if not node:
                print("Creating Physical Node 'pve'...")
                node = PhysicalNode(
                    hostname="pve",
                    status=NodeStatus.ONLINE,
                    total_cpu_cores=32,
                    total_ram_gb=128,
                    total_disk_gb=2000
                )
                session.add(node)

            # 3. Seed ISO Images
            isos_data = [
                {"name": "Ubuntu 22.04", "os_type": OSType.LINUX, "version": "22.04", "proxmox_ref": "local:iso/ubuntu-22.04.iso"},
                {"name": "Debian 12", "os_type": OSType.LINUX, "version": "12", "proxmox_ref": "local:iso/debian-12.iso"},
                {"name": "Windows 10", "os_type": OSType.WINDOWS, "version": "10", "proxmox_ref": "local:iso/win10.iso"},
            ]
            
            for iso_in in isos_data:
                res = await session.execute(select(ISOImage).where(ISOImage.proxmox_ref == iso_in["proxmox_ref"]))
                if not res.scalars().first():
                    print(f"Creating ISO: {iso_in['name']}...")
                    iso = ISOImage(**iso_in)
                    session.add(iso)

    print("Infrastructure data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
