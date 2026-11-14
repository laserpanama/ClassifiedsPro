from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
import logging

from app.backend.models.ad import Ad, AdCreate
from app.backend.utils import utcnow

logger = logging.getLogger(__name__)

COLLECTION = "ads"
PUBLISH_HISTORY = "publish_history"


async def get_ad(db: AsyncIOMotorDatabase, ad_id: str) -> Ad | None:
    ad = await db[COLLECTION].find_one({"id": ad_id})
    return Ad(**ad) if ad else None


async def get_ads(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 100) -> List[Ad]:
    cursor = db[COLLECTION].find().skip(skip).limit(limit)
    ads = await cursor.to_list(length=limit)
    return [Ad(**ad) for ad in ads]


async def get_ads_by_account(db: AsyncIOMotorDatabase, account_id: str) -> List[Ad]:
    cursor = db[COLLECTION].find({"account_id": account_id})
    ads = await cursor.to_list(length=None)
    return [Ad(**ad) for ad in ads]


async def create_ad(db: AsyncIOMotorDatabase, ad: AdCreate) -> Ad:
    new_ad = Ad(**ad.model_dump())
    await db[COLLECTION].insert_one(new_ad.model_dump())
    return new_ad


async def update_ad(db: AsyncIOMotorDatabase, ad_id: str, ad_data: dict) -> bool:
    result = await db[COLLECTION].update_one({"id": ad_id}, {"$set": ad_data})
    return result.matched_count > 0


async def mark_published(db: AsyncIOMotorDatabase, ad_id: str) -> None:
    await db[COLLECTION].update_one({"id": ad_id}, {"$set": {"last_published_at": utcnow()}})


async def record_publish_result(
    db: AsyncIOMotorDatabase,
    ad_id: str,
    account_id: Optional[str],
    status: str,
    detail: str = "",
) -> None:
    """Writes one row to the publish_history collection (audit trail)."""
    await db[PUBLISH_HISTORY].insert_one(
        {
            "ad_id": ad_id,
            "account_id": account_id,
            "status": status,  # "success" | "failed" | "skipped"
            "detail": detail[:500],
            "published_at": utcnow(),
        }
    )


async def get_publish_history(db: AsyncIOMotorDatabase, ad_id: str, limit: int = 20) -> list[dict]:
    cursor = db[PUBLISH_HISTORY].find({"ad_id": ad_id}).sort("published_at", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    for row in rows:
        row.pop("_id", None)
    return rows


async def delete_ad(db: AsyncIOMotorDatabase, ad_id: str) -> bool:
    result = await db[COLLECTION].delete_one({"id": ad_id})
    return result.deleted_count > 0
