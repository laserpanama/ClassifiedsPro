from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.backend.api.deps import get_database
from app.backend.models.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from app.backend.services import (
    schedule_service,
    ad_service,
    account_service,
    scheduler_service,
)
from app.backend.utils import next_run_after

router = APIRouter()


@router.post("/schedules/", response_model=Schedule, status_code=201, tags=["schedules"])
async def create_schedule_endpoint(schedule: ScheduleCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    # Validate BEFORE inserting anything (previous version persisted the
    # schedule and only then discovered the ad/account was missing).
    ad = await ad_service.get_ad(db=db, ad_id=schedule.ad_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad to schedule not found")
    account = await account_service.get_account(db=db, account_id=ad.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account for ad not found")

    new_schedule = await schedule_service.create_schedule(db=db, schedule=schedule)

    if new_schedule.is_active:
        scheduler_service.schedule_ad_posting_job(
            schedule_id=new_schedule.id,
            interval_hours=new_schedule.republish_interval_hours,
            ad_id=new_schedule.ad_id,
        )
        next_run = scheduler_service.sync_next_run(new_schedule.id)
        if next_run:
            await schedule_service.update_schedule(db=db, schedule_id=new_schedule.id, schedule_data={"next_republish_at": next_run})
            refreshed = await schedule_service.get_schedule(db=db, schedule_id=new_schedule.id)
            if refreshed is not None:
                new_schedule = refreshed
    return new_schedule


@router.get("/schedules/", response_model=List[Schedule], tags=["schedules"])
async def read_schedules_endpoint(skip: int = 0, limit: int = 100, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await schedule_service.get_schedules(db=db, skip=skip, limit=limit)


@router.get("/schedules/{schedule_id}", response_model=Schedule, tags=["schedules"])
async def read_schedule_endpoint(schedule_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    db_schedule = await schedule_service.get_schedule(db=db, schedule_id=schedule_id)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule


@router.patch("/schedules/{schedule_id}", response_model=Schedule, tags=["schedules"])
async def update_schedule_endpoint(schedule_id: str, schedule: ScheduleUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = schedule.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    existing = await schedule_service.get_schedule(db=db, schedule_id=schedule_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Recompute the next run when the interval changes or the schedule is re-enabled.
    interval = update_data.get("republish_interval_hours", existing.republish_interval_hours)
    will_be_active = update_data.get("is_active", existing.is_active)
    if will_be_active and ("republish_interval_hours" in update_data or not existing.is_active):
        update_data["next_republish_at"] = next_run_after(interval)

    success = await schedule_service.update_schedule(db=db, schedule_id=schedule_id, schedule_data=update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")

    updated_schedule = await schedule_service.get_schedule(db=db, schedule_id=schedule_id)
    if updated_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found after update")

    ad = await ad_service.get_ad(db=db, ad_id=updated_schedule.ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad for schedule not found")
    account = await account_service.get_account(db=db, account_id=ad.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account for ad not found")

    if updated_schedule.is_active:
        scheduler_service.schedule_ad_posting_job(
            schedule_id=updated_schedule.id,
            interval_hours=updated_schedule.republish_interval_hours,
            ad_id=updated_schedule.ad_id,
        )
        next_run = scheduler_service.sync_next_run(updated_schedule.id)
        if next_run:
            await schedule_service.update_schedule(db=db, schedule_id=updated_schedule.id, schedule_data={"next_republish_at": next_run})
            refreshed = await schedule_service.get_schedule(db=db, schedule_id=updated_schedule.id)
            if refreshed is not None:
                updated_schedule = refreshed
    else:
        scheduler_service.remove_schedule(schedule_id=updated_schedule.id)

    return updated_schedule


@router.delete("/schedules/{schedule_id}", status_code=204, tags=["schedules"])
async def delete_schedule_endpoint(schedule_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    scheduler_service.remove_schedule(schedule_id=schedule_id)

    success = await schedule_service.delete_schedule(db=db, schedule_id=schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return None
