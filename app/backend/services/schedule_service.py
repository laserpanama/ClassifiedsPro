from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.backend.models.schedule import Schedule, ScheduleCreate
from app.backend.utils import next_run_after

COLLECTION = "schedules"


async def get_schedule(db: AsyncIOMotorDatabase, schedule_id: str) -> Schedule | None:
    schedule = await db[COLLECTION].find_one({"id": schedule_id})
    return Schedule(**schedule) if schedule else None


async def get_schedules(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 100) -> List[Schedule]:
    cursor = db[COLLECTION].find().skip(skip).limit(limit)
    schedules = await cursor.to_list(length=limit)
    return [Schedule(**schedule) for schedule in schedules]


async def get_schedules_by_ad(db: AsyncIOMotorDatabase, ad_id: str) -> List[Schedule]:
    cursor = db[COLLECTION].find({"ad_id": ad_id})
    schedules = await cursor.to_list(length=None)
    return [Schedule(**schedule) for schedule in schedules]


async def get_active_schedules(db: AsyncIOMotorDatabase) -> List[Schedule]:
    cursor = db[COLLECTION].find({"is_active": True})
    schedules = await cursor.to_list(length=None)
    return [Schedule(**schedule) for schedule in schedules]


async def create_schedule(db: AsyncIOMotorDatabase, schedule: ScheduleCreate) -> Schedule:
    data = schedule.model_dump()
    data["next_republish_at"] = next_run_after(schedule.republish_interval_hours)
    new_schedule = Schedule(**data)
    await db[COLLECTION].insert_one(new_schedule.model_dump())
    return new_schedule


async def update_schedule(db: AsyncIOMotorDatabase, schedule_id: str, schedule_data: dict) -> bool:
    result = await db[COLLECTION].update_one({"id": schedule_id}, {"$set": schedule_data})
    return result.matched_count > 0


async def delete_schedule(db: AsyncIOMotorDatabase, schedule_id: str) -> bool:
    result = await db[COLLECTION].delete_one({"id": schedule_id})
    return result.deleted_count > 0
