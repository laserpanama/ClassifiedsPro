from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
import logging

from app.backend.models.account import Account, AccountCreate
from app.backend.services import crypto_service

logger = logging.getLogger(__name__)

COLLECTION = "accounts"


def _stored_from_account(account: Account) -> dict:
    """Serializes an account for storage (password encrypted, never plaintext)."""
    return {
        "id": account.id,
        "email": account.email,
        "is_active": account.is_active,
        "captcha_solving_method": account.captcha_solving_method,
        "wanuncios_password": crypto_service.encrypt_text(account.wanuncios_password),
    }


def _account_from_stored(doc: dict) -> Account:
    return Account(
        id=doc["id"],
        email=doc["email"],
        is_active=doc.get("is_active", True),
        captcha_solving_method=doc.get("captcha_solving_method", "api"),
        wanuncios_password=crypto_service.decrypt_text(doc.get("wanuncios_password", "")),
    )


async def get_account(db: AsyncIOMotorDatabase, account_id: str) -> Account | None:
    doc = await db[COLLECTION].find_one({"id": account_id})
    return _account_from_stored(doc) if doc else None


async def get_accounts(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 100) -> List[Account]:
    cursor = db[COLLECTION].find().skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_account_from_stored(doc) for doc in docs]


async def create_account(db: AsyncIOMotorDatabase, account: AccountCreate) -> Account:
    new_account = Account(**account.model_dump())
    await db[COLLECTION].insert_one(_stored_from_account(new_account))
    return new_account


async def update_account(db: AsyncIOMotorDatabase, account_id: str, account_data: dict) -> bool:
    data = dict(account_data)
    if "wanuncios_password" in data and data["wanuncios_password"]:
        data["wanuncios_password"] = crypto_service.encrypt_text(data["wanuncios_password"])
    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"])
    result = await db[COLLECTION].update_one({"id": account_id}, {"$set": data})
    return result.matched_count > 0


async def delete_account(db: AsyncIOMotorDatabase, account_id: str) -> bool:
    result = await db[COLLECTION].delete_one({"id": account_id})
    return result.deleted_count > 0


async def get_account_by_email(db: AsyncIOMotorDatabase, email: str) -> Account | None:
    doc = await db[COLLECTION].find_one({"email": email})
    return _account_from_stored(doc) if doc else None
