"""
APScheduler-based republishing.

Design notes:
- The MongoDB `schedules` collection is the single source of truth. Jobs are
  re-created from it at startup (`rehydrate_jobs`), so republishing survives
  restarts without any job store at all.
- Jobs carry only the ad_id / schedule_id — never credentials or model
  objects. Account and ad are fetched fresh from the database each run, so
  credential changes, deactivations and deletions take effect immediately.
- A previous version passed a Motor (async) client to APScheduler's
  MongoDBJobStore, which expects a synchronous pymongo client; the scheduler
  silently failed to read due jobs. The job store is intentionally gone now.
"""
from datetime import timezone
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.backend.services import automation_service, ad_service, account_service, schedule_service
from app.backend.utils import next_run_after

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")
_db = None  # set at startup; jobs fetch everything fresh from the database


def _job_id(schedule_id: str) -> str:
    return f"post_ad_{schedule_id}"


async def initialize_scheduler(db) -> None:
    """Starts the scheduler and re-creates republish jobs from the database."""
    global _db
    _db = db
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started.")

    if _db is None:
        logger.warning(
            "Scheduler is running without a database connection — "
            "republishing is unavailable until the app is restarted with MongoDB up."
        )
        return

    await rehydrate_jobs()


async def rehydrate_jobs() -> int:
    """Re-creates interval jobs for every active schedule in MongoDB."""
    if _db is None:
        return 0
    try:
        schedules = await schedule_service.get_active_schedules(_db)
    except Exception as e:  # never let rehydration crash app startup
        logger.error(f"Could not load schedules from MongoDB during startup: {e}")
        return 0

    count = 0
    for s in schedules:
        if add_job_for_schedule(s.id, s.republish_interval_hours, s.ad_id):
            count += 1
    logger.info(f"Rehydrated {count} of {len(schedules)} active republish job(s) from MongoDB.")
    return count


async def shutdown_scheduler() -> None:
    global _db
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")
    _db = None


def add_job_for_schedule(schedule_id: str, interval_hours: int, ad_id: str) -> bool:
    if not scheduler.running:
        logger.error(f"Cannot schedule job for schedule {schedule_id}: scheduler is not running.")
        return False
    job_id = _job_id(schedule_id)
    logger.info(f"Scheduling job {job_id} (ad {ad_id}) every {interval_hours}h.")
    scheduler.add_job(
        run_ad_publish,
        "interval",
        hours=interval_hours,
        args=[ad_id, schedule_id],
        id=job_id,
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600,
    )
    return True


def schedule_ad_posting_job(schedule_id: str, interval_hours: int, ad_id: str) -> bool:
    """Public helper used by the API when a schedule is created or re-enabled."""
    return add_job_for_schedule(schedule_id, interval_hours, ad_id)


def remove_schedule(schedule_id: str) -> bool:
    job_id = _job_id(schedule_id)
    try:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}.")
            return True
    except Exception as e:
        logger.error(f"Could not remove job {job_id}: {e}")
        return False
    logger.info(f"No job {job_id} to remove.")
    return False


def sync_next_run(schedule_id: str):
    """Returns the job's next run time (naive UTC) if the job exists, else None."""
    try:
        job = scheduler.get_job(_job_id(schedule_id))
    except Exception:
        return None
    if job and job.next_run_time:
        return job.next_run_time.astimezone(timezone.utc).replace(tzinfo=None)
    return None


async def run_ad_publish(ad_id: str, schedule_id: str | None = None) -> bool:
    """Job entry point: fetches fresh state and publishes the ad."""
    if _db is None:
        logger.error("run_ad_publish called without a database connection.")
        return False

    ad = await ad_service.get_ad(_db, ad_id)
    if ad is None:
        logger.error(f"Ad {ad_id} no longer exists — skipping publish for schedule {schedule_id}.")
        await ad_service.record_publish_result(_db, ad_id, None, "failed", "ad no longer exists")
        return False

    account = await account_service.get_account(_db, ad.account_id)
    if account is None:
        logger.error(f"Account {ad.account_id} for ad {ad_id} no longer exists — skipping.")
        await ad_service.record_publish_result(_db, ad_id, ad.account_id, "failed", "account no longer exists")
        return False

    if not account.is_active:
        logger.info(f"Account {account.email} is deactivated — skipping publish of ad {ad_id}.")
        await ad_service.record_publish_result(_db, ad_id, account.id, "skipped", "account is deactivated")
        return False

    success = await automation_service.post_ad_to_wanuncios(account, ad, db=_db)

    if success and schedule_id:
        next_run = sync_next_run(schedule_id)
        if next_run:
            await schedule_service.update_schedule(_db, schedule_id, {"next_republish_at": next_run})
    return success
