from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
import uuid
from datetime import datetime

from app.backend.utils import utcnow, next_run_after


class ScheduleBase(BaseModel):
    republish_interval_hours: int = Field(gt=0, le=24 * 90)  # max one quarter
    is_active: bool = True


class ScheduleCreate(ScheduleBase):
    ad_id: str


class ScheduleUpdate(BaseModel):
    republish_interval_hours: Optional[int] = Field(default=None, gt=0, le=24 * 90)
    is_active: Optional[bool] = None


class Schedule(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ad_id: str
    next_republish_at: datetime = Field(default_factory=lambda: next_run_after(24))
