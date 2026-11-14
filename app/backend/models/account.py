from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal
import uuid

CaptchaMethod = Literal["api", "manual", "script"]


class AccountCreate(BaseModel):
    email: EmailStr
    # Stored Fernet-encrypted at rest; never returned by the API.
    wanuncios_password: str = Field(min_length=1)
    is_active: bool = True
    captcha_solving_method: CaptchaMethod = "api"


class AccountUpdate(BaseModel):
    email: EmailStr | None = None
    wanuncios_password: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None
    captcha_solving_method: CaptchaMethod | None = None


class Account(BaseModel):
    """Internal representation — includes the (decrypted) password for automation."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    is_active: bool = True
    wanuncios_password: str
    captcha_solving_method: CaptchaMethod = "api"


class AccountOut(BaseModel):
    """Public representation — safe to serialize to API clients."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    is_active: bool
    captcha_solving_method: CaptchaMethod
