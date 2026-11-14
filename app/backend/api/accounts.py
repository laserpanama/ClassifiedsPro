from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.backend.api.deps import get_database
from app.backend.models.account import AccountCreate, AccountOut, AccountUpdate
from app.backend.services import account_service, ad_service, schedule_service, scheduler_service

router = APIRouter()


@router.post("/accounts/", response_model=AccountOut, status_code=201, tags=["accounts"])
async def create_account_endpoint(account: AccountCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    new_account = await account_service.create_account(db=db, account=account)
    return new_account


@router.get("/accounts/", response_model=List[AccountOut], tags=["accounts"])
async def read_accounts_endpoint(skip: int = 0, limit: int = 100, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await account_service.get_accounts(db=db, skip=skip, limit=limit)


@router.get("/accounts/{account_id}", response_model=AccountOut, tags=["accounts"])
async def read_account_endpoint(account_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    db_account = await account_service.get_account(db=db, account_id=account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account


@router.patch("/accounts/{account_id}", response_model=AccountOut, tags=["accounts"])
async def update_account_endpoint(account_id: str, account: AccountUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = account.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    success = await account_service.update_account(db=db, account_id=account_id, account_data=update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")

    updated_account = await account_service.get_account(db=db, account_id=account_id)
    if updated_account is None:
        raise HTTPException(status_code=404, detail="Account not found after update")
    return updated_account


@router.delete("/accounts/{account_id}", status_code=204, tags=["accounts"])
async def delete_account_endpoint(account_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    # Cascade: remove the account's ads, their schedules and the scheduler jobs.
    ads = await ad_service.get_ads_by_account(db=db, account_id=account_id)
    for ad in ads:
        for schedule in await schedule_service.get_schedules_by_ad(db=db, ad_id=ad.id):
            scheduler_service.remove_schedule(schedule_id=schedule.id)
            await schedule_service.delete_schedule(db=db, schedule_id=schedule.id)
        await ad_service.delete_ad(db=db, ad_id=ad.id)

    success = await account_service.delete_account(db=db, account_id=account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return None
