from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional
import uuid

from app.backend.utils import utcnow
from datetime import datetime


def _empty_to_none(v):
    """Coerce blank strings (sent by HTML forms) into None for optional fields."""
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


class AdBase(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str
    subcategory: str
    province: str
    zone: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    images: List[str] = []

    _empty_zone = field_validator("zone", mode="before")(_empty_to_none)
    _empty_price = field_validator("price", mode="before")(_empty_to_none)


class AdCreate(AdBase):
    account_id: str


class AdUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    province: Optional[str] = None
    zone: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    images: Optional[List[str]] = None
    account_id: Optional[str] = None

    _empty_zone = field_validator("zone", mode="before")(_empty_to_none)
    _empty_price = field_validator("price", mode="before")(_empty_to_none)


class Ad(AdBase):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str
    created_at: datetime = Field(default_factory=utcnow)
    last_published_at: Optional[datetime] = None
