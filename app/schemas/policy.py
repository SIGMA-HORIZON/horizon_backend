from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

# --- Quota ---
class QuotaBase(BaseModel):
    max_cpu_cores: int = Field(2, ge=1, le=64)
    max_ram_gb: int = Field(2, ge=1, le=256)
    max_disk_gb: int = Field(20, ge=10, le=2000)
    max_concurrent_vms: int = Field(2, ge=1, le=20)
    max_session_hours: int = Field(8, ge=1, le=720)
    max_shared_space_gb: int = Field(5, ge=1, le=100)

class Quota(QuotaBase):
    id: UUID
    policy_id: UUID
    model_config = ConfigDict(from_attributes=True)

# --- Usage Policy ---
class UsagePolicyBase(BaseModel):
    name: str = Field(..., max_length=128)
    is_default: bool = False
    notice_minutes_before: int = Field(30, gt=0)
    max_inactive_days: int = Field(2, gt=0)

class UsagePolicyCreate(UsagePolicyBase):
    quota: QuotaBase

class UsagePolicy(UsagePolicyBase):
    id: UUID
    created_at: datetime
    quota: Optional[Quota] = None
    
    model_config = ConfigDict(from_attributes=True)
