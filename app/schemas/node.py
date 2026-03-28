from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from app.models.enums import NodeStatus

class PhysicalNodeBase(BaseModel):
    hostname: str = Field(..., max_length=64)
    status: NodeStatus = NodeStatus.ONLINE
    total_cpu_cores: int = Field(..., gt=0)
    total_ram_gb: int = Field(..., gt=0)
    total_disk_gb: int = Field(..., gt=0)

class PhysicalNode(PhysicalNodeBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
