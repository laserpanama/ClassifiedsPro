from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from pydantic import BaseModel

from app.backend.api.deps import get_database
from app.backend.rate_limit import limiter
from app.backend.services import ai_service, ad_service, account_service, automation_service, schedule_service, scheduler_service
from app.backend.models.ad import Ad, AdCreate, AdUpdate

router = APIRouter()


class AdTextGenerationRequest(BaseModel):
    prompt: str


@router.post("/ads/generate-text", tags=["ads"])
@limiter.limit("10/minute")
async def generate_ad_text_endpoint(request: Request, body: AdTextGenerationRequest):
    return {"generated_text": ai_service.generate_ad_text(body.prompt)}


@router.post("/ads/", response_model=Ad, status_code=201, tags=["ads"])
async def create_ad_endpoint(ad: AdCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    db_account = await account_service.get_account(db=db, account_id=ad.account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail=f"Account with id {ad.account_id} not found")
    return await ad_service.create_ad(db=db, ad=ad)


@router.get("/ads/", response_model=List[Ad], tags=["ads"])
async def read_ads_endpoint(skip: int = 0, limit: int = 100, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await ad_service.get_ads(db=db, skip=skip, limit=limit)


@router.get("/ads/{ad_id}", response_model=Ad, tags=["ads"])
async def read_ad_endpoint(ad_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    db_ad = await ad_service.get_ad(db=db, ad_id=ad_id)
    if db_ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    return db_ad


@router.get("/ads/{ad_id}/publish-history", tags=["ads"])
async def publish_history_endpoint(ad_id: str, limit: int = 20, db: AsyncIOMotorDatabase = Depends(get_database)):
    db_ad = await ad_service.get_ad(db=db, ad_id=ad_id)
    if db_ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    history = await ad_service.get_publish_history(db=db, ad_id=ad_id, limit=limit)
    return history


@router.patch("/ads/{ad_id}", response_model=Ad, tags=["ads"])
async def update_ad_endpoint(ad_id: str, ad: AdUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = ad.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    if "account_id" in update_data:
        db_account = await account_service.get_account(db=db, account_id=update_data["account_id"])
        if db_account is None:
            raise HTTPException(status_code=404, detail=f"Account with id {update_data['account_id']} not found")

    success = await ad_service.update_ad(db=db, ad_id=ad_id, ad_data=update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Ad not found")

    updated_ad = await ad_service.get_ad(db=db, ad_id=ad_id)
    if updated_ad is None:
        raise HTTPException(status_code=404, detail="Ad not found after update")
    return updated_ad


@router.delete("/ads/{ad_id}", status_code=204, tags=["ads"])
async def delete_ad_endpoint(ad_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    # Cascade: delete the ad's schedules and remove their scheduler jobs.
    for schedule in await schedule_service.get_schedules_by_ad(db=db, ad_id=ad_id):
        scheduler_service.remove_schedule(schedule_id=schedule.id)
        await schedule_service.delete_schedule(db=db, schedule_id=schedule.id)

    success = await ad_service.delete_ad(db=db, ad_id=ad_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ad not found")
    return None


@router.post("/ads/{ad_id}/publish", tags=["ads"])
@limiter.limit("20/hour")
async def publish_ad_endpoint(request: Request, ad_id: str, background_tasks: BackgroundTasks, db: AsyncIOMotorDatabase = Depends(get_database)):
    db_ad = await ad_service.get_ad(db=db, ad_id=ad_id)
    if db_ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")

    db_account = await account_service.get_account(db=db, account_id=db_ad.account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account for this ad not found")
    if not db_account.is_active:
        raise HTTPException(status_code=409, detail="Account for this ad is deactivated")

    background_tasks.add_task(automation_service.post_ad_to_wanuncios, db_account, db_ad, db)
    return {"message": "Ad publishing has been started in the background."}
