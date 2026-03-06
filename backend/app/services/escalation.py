"""
Auto-escalation background service.

Runs a periodic check (every hour) for complaints that have exceeded their
authority's SLA (escalation_days). Overdue complaints are automatically
escalated to the parent authority and the citizen is notified.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from app.database import get_database
from app.authorities import get_authority_by_id
from app.schemas import ComplaintStatus, NotificationType

logger = logging.getLogger("JanSunwaiAI.escalation")

CHECK_INTERVAL_SECONDS = 3600  # run every hour


async def run_escalation_check() -> int:
    """
    Single escalation pass. Returns the number of complaints escalated.
    """
    escalated_count = 0
    try:
        db = get_database()
        now = datetime.utcnow()

        cursor = db["complaints"].find({
            "status": {"$in": [ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS]},
            "escalated": {"$ne": True},
        })

        async for complaint in cursor:
            authority_id = complaint.get("authority_id")
            if not authority_id:
                continue

            authority = get_authority_by_id(authority_id)
            if not authority or not authority.parent_authority_id:
                continue

            created_at = complaint.get("created_at")
            if not created_at:
                continue

            deadline = created_at + timedelta(days=authority.escalation_days)
            if now < deadline:
                continue

            # Past SLA — escalate to parent authority
            parent_id = authority.parent_authority_id
            complaint_id = str(complaint["_id"])
            note = (
                f"Auto-escalated: SLA of {authority.escalation_days} days exceeded. "
                f"Moved from '{authority_id}' to '{parent_id}'."
            )

            await db["complaints"].update_one(
                {"_id": complaint["_id"]},
                {
                    "$set": {
                        "authority_id": parent_id,
                        "escalated": True,
                        "escalated_at": now,
                        "updated_at": now,
                    },
                    "$push": {
                        "status_history": {
                            "status": complaint.get("status", ComplaintStatus.OPEN),
                            "timestamp": now,
                            "changed_by_user_id": "system",
                            "note": note,
                        }
                    },
                },
            )

            citizen_id = complaint.get("user_id")
            if citizen_id:
                # Import here to avoid circular imports at module load
                from app.routers.notifications import create_notification
                await create_notification(
                    user_id=citizen_id,
                    notification_type=NotificationType.ESCALATION,
                    title="Grievance Auto-Escalated",
                    message=(
                        f"Your grievance regarding '{complaint.get('department', 'civic issue')}' "
                        f"has been automatically escalated after {authority.escalation_days} days "
                        f"without resolution."
                    ),
                    complaint_id=complaint_id,
                )

            escalated_count += 1
            logger.info(f"[Escalation] Complaint {complaint_id} escalated to {parent_id}")

    except Exception:
        logger.exception("[Escalation] Error during escalation check")

    if escalated_count:
        logger.info(f"[Escalation] Cycle complete — escalated {escalated_count} complaint(s).")

    return escalated_count


async def escalation_loop():
    """Perpetual background task. Starts after a 60-second grace period."""
    await asyncio.sleep(60)
    logger.info("[Escalation] Background service started.")
    while True:
        await run_escalation_check()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
