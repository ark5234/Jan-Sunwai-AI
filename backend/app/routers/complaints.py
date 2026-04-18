import asyncio
import csv
import io
import logging
import time
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Body, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from jose import JWTError, jwt
from app.classifier import CivicClassifier
from app.geotagging import extract_location
from app.database import get_database
from app.services.storage import storage_service
from app.services.llm_queue import llm_queue_service
from app.auth import get_current_user, get_current_admin, get_current_admin_or_dept_head
from app.schemas import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatus,
    TransferRequest,
    UserRole,
    FeedbackRequest,
    DeptNoteRequest,
    CommentRequest,
    BulkStatusUpdate,
    BulkTransfer,
    StatusUpdateRequest,
    PriorityLevel,
)
from app.authorities import route_authority, get_authority_by_id
from app.routers.notifications import create_notification
from app.schemas import NotificationType
from app.config import settings
from app.services.priority import compute_priority
from app.services.assignment import auto_assign, free_worker_slot
from app.services.sanitization import sanitize_text
from app.services.email_service import send_status_update_email
from app.category_utils import canonicalize_label
from app.rate_limiter import limiter
from PIL import Image
from datetime import datetime, timedelta, timezone
from bson import ObjectId

router = APIRouter()
classifier = CivicClassifier()
logger = logging.getLogger("JanSunwaiAI.complaints")

ANALYSIS_TOKEN_TTL_MINUTES = 30

# Helper to fix ObjectId serialization
def fix_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def _build_analysis_token(*, user_id: str, image_url: str) -> str:
    payload = {
        "type": "analysis_bind",
        "sub": user_id,
        "img": image_url,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ANALYSIS_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _verify_analysis_token(token: str, *, user_id: str, image_url: str) -> bool:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return False
    return (
        payload.get("type") == "analysis_bind"
        and payload.get("sub") == user_id
        and payload.get("img") == image_url
    )


def _public_generation_payload(result: dict | None) -> dict | None:
    if not result:
        return None
    return {k: v for k, v in result.items() if k != "owner_id"}


def _assert_complaint_access(current_user: dict, complaint: dict) -> None:
    role = current_user.get("role")
    user_id = str(current_user.get("_id"))

    if role == UserRole.ADMIN:
        return
    if role == UserRole.CITIZEN and complaint.get("user_id") == user_id:
        return
    if role == UserRole.WORKER and complaint.get("assigned_to") == user_id:
        return
    if role == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if user_dept and complaint.get("department") == user_dept:
            return

    raise HTTPException(status_code=403, detail="You are not allowed to access this complaint")


def _normalize_optional_user_grievance(text: str) -> str:
    if not isinstance(text, str):
        return ""
    cleaned = sanitize_text(text or "", max_len=1200).strip()
    # Ignore ultra-short hints; they are often noise and degrade routing quality.
    if len(cleaned) < 8:
        return ""
    return cleaned


def _apply_user_text_routing_override(classification: dict, user_text_result: dict) -> dict:
    resolved = dict(classification or {})
    resolved["routing_source"] = "image"
    resolved["image_department"] = resolved.get("department")
    resolved["image_confidence"] = resolved.get("confidence")
    resolved["user_text_department"] = user_text_result.get("department")
    resolved["user_text_confidence"] = user_text_result.get("confidence")
    resolved["user_text_method"] = user_text_result.get("method")
    resolved["user_text_rationale"] = user_text_result.get("rationale")
    resolved["user_text_used_for_routing"] = False

    image_marked_non_civic = bool(resolved.get("is_non_civic", False))
    user_text_is_valid = bool(user_text_result.get("is_valid", False))

    if user_text_is_valid and not image_marked_non_civic:
        resolved["department"] = user_text_result.get("department")
        resolved["confidence"] = float(user_text_result.get("confidence", 0.0))
        resolved["is_valid"] = True
        resolved["is_non_civic"] = False
        resolved["raw_category"] = user_text_result.get("department")
        resolved["method"] = f"{resolved.get('method', 'vision')}+user_text_override"
        resolved["rationale"] = (
            f"{resolved.get('rationale', '')}; overridden using user grievance text"
        ).strip(" ;")
        resolved["routing_source"] = "user_text"
        resolved["user_text_used_for_routing"] = True
    elif image_marked_non_civic:
        resolved["user_text_override_blocked_reason"] = "image_marked_non_civic"

    return resolved


async def await_generation(job_id: str, timeout_seconds: float) -> dict:
    elapsed = 0.0
    sleep_interval = 0.2
    while elapsed < timeout_seconds:
        result = await llm_queue_service.get_result_async(job_id)
        if result and result.get("status") in ["completed", "failed"]:
            return result
        await asyncio.sleep(sleep_interval)
        elapsed += sleep_interval
    return {"status": "queued"}

@router.post("/analyze")
@limiter.limit("20/minute")
async def analyze_complaint(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("en"),
    user_grievance_text: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    analyze_start = time.perf_counter()
    username = current_user["username"]
    user_id = str(current_user["_id"])
    normalized_user_grievance = _normalize_optional_user_grievance(user_grievance_text)

    # 1. Save file and resolve absolute path
    file_path = await storage_service.save_file(file)
    analysis_token = _build_analysis_token(user_id=user_id, image_url=file_path)
    absolute_file_path = storage_service.resolve_path(file_path)

    # 2. Classify — offload sync model inference so the event loop stays responsive
    classification = await asyncio.to_thread(classifier.classify, absolute_file_path)

    # Graceful degradation: if classifier hard-fails (Ollama unavailable / all tiers failed),
    # return a user-friendly retryable 503 payload.
    if classification.get("method") == "error":
        return JSONResponse(
            status_code=503,
            content={
                "message": "AI analysis unavailable — please try again in a few minutes.",
                "details": "Model pipeline unavailable",
                "error_code": "MODEL_PIPELINE_UNAVAILABLE",
                "retryable": True,
            },
        )

    # Optional user-text routing assist: if user provides a clear grievance hint,
    # use deterministic text classification to improve department selection.
    if normalized_user_grievance:
        user_text_result = await asyncio.to_thread(
            classifier.classify_user_description,
            normalized_user_grievance,
        )
        classification = _apply_user_text_routing_override(classification, user_text_result)

    # 3. Extract Location — open from the saved file on disk (avoids re-reading HTTP body)
    image = Image.open(absolute_file_path)
    location = extract_location(image)
    image.close()
    
    # 4. Generate Complaint Text (Async queue)
    # Only skip generation for images that are genuinely non-civic (selfie, food,
    # animal, train station, etc.) OR when the classifier itself errored out.
    # An image that the classifier couldn't categorise (Uncategorized) may still
    # be a real civic issue — generate a draft for it rather than hard-rejecting.
    is_truly_non_civic = (
        not classification.get("is_valid", True)
        and classification.get("is_non_civic", False)
    ) or classification.get("method") in ("non_civic_guard", "error")

    if not is_truly_non_civic:
        job_id = await llm_queue_service.enqueue(
            absolute_file_path,
            classification,
            {
                "name": username,
                "user_id": user_id,
                "reported_issue_text": normalized_user_grievance,
            },
            location,
            language,
        )
        result = await await_generation(job_id, settings.llm_inline_timeout_seconds)
        if result.get("status") == "completed":
            generated_text = result.get("generated_complaint", "")
            generation_status = "completed"
        elif result.get("status") == "failed":
            generated_text = "AI draft failed. Please write complaint manually."
            generation_status = "failed"
        else:
            generated_text = "Complaint draft is being generated. Please refresh in a few seconds."
            generation_status = "queued"
    else:
        job_id = None
        generation_status = "skipped"
        if classification.get("method") == "error":
            generated_text = (
                "Image analysis failed — the AI model could not process this photo. "
                "Please try again or describe the issue manually below."
            )
        else:
            generated_text = (
                f"AI Analysis Result: {classification['label']}.\n\n"
                "This image does not appear to show a valid civic grievance relevant to municipal authorities. "
                "Please upload a photo of a civic issue (e.g., pothole, garbage, broken light) to generate a formal complaint."
            )
    
    return {
        "classification": classification,
        "location": location,
        "generated_complaint": generated_text,
        "generation_status": generation_status,
        "generation_job_id": job_id,
        "analysis_token": analysis_token,
        "user_grievance_text": normalized_user_grievance,
        "image_url": file_path, # Return the path so frontend can pass it to /complaints
        "timings": {
            "vision_ms": classification.get("timings", {}).get("vision_ms", 0.0),
            "rule_engine_ms": classification.get("timings", {}).get("rule_engine_ms", 0.0),
            "reasoning_ms": classification.get("timings", {}).get("reasoning_ms", 0.0),
            "total_analyze_ms": round((time.perf_counter() - analyze_start) * 1000.0, 2),
        },
    }


@router.get("/complaints/generation/{job_id}")
async def get_generation_result(job_id: str, current_user: dict = Depends(get_current_user)):
    result = await llm_queue_service.get_result_async(job_id, include_private=True)
    if not result:
        raise HTTPException(status_code=404, detail="Generation job not found")

    current_user_id = str(current_user.get("_id"))
    role = current_user.get("role")
    owner_id = str(result.get("owner_id") or "")
    if role != UserRole.ADMIN and (not owner_id or owner_id != current_user_id):
        raise HTTPException(status_code=403, detail="You are not allowed to view this generation job")

    return _public_generation_payload(result)


@router.post("/analyze/regenerate")
async def regenerate_complaint(
    payload: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Re-run the complaint draft generator for an already-analysed image.
    Expects: { classification, location, image_url }
    Returns:  { job_id, status } — poll /complaints/generation/{job_id}
    """
    username = current_user["username"]
    user_id = str(current_user["_id"])
    classification = payload.get("classification", {})
    location       = payload.get("location", {})
    image_url      = payload.get("image_url", "")
    language       = payload.get("language", "en")
    user_hint      = _normalize_optional_user_grievance(payload.get("user_grievance_text", ""))

    if user_hint:
        user_text_result = await asyncio.to_thread(
            classifier.classify_user_description,
            user_hint,
        )
        classification = _apply_user_text_routing_override(classification, user_text_result)

    absolute_file_path = storage_service.resolve_path(image_url)

    job_id = await llm_queue_service.enqueue(
        absolute_file_path,
        classification,
        {
            "name": username,
            "user_id": user_id,
            "reported_issue_text": user_hint,
        },
        location,
        language,
    )
    return {
        "job_id": job_id,
        "status": "queued",
        "classification": classification,
        "analysis_token": _build_analysis_token(user_id=user_id, image_url=image_url),
    }



@router.post("/complaints", response_model=ComplaintResponse)
async def create_complaint(
    complaint: ComplaintCreate, 
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    user_id = str(current_user["_id"])
    
    # 2. Prepare Data
    complaint_dict = complaint.model_dump()
    analysis_token = str(complaint_dict.pop("analysis_token", "") or "").strip()

    # Validate image path from untrusted payload before persisting anything.
    raw_image_url = str(complaint_dict.get("image_url", "") or "").strip()
    if not raw_image_url:
        raise HTTPException(status_code=400, detail="Missing image_url in complaint payload")

    if settings.is_production and not analysis_token:
        raise HTTPException(status_code=400, detail="analysis_token is required")
    if analysis_token and not _verify_analysis_token(analysis_token, user_id=user_id, image_url=raw_image_url):
        raise HTTPException(status_code=400, detail="Invalid or expired analysis token")

    resolved_image_path = storage_service.resolve_path(raw_image_url)
    if not Path(resolved_image_path).exists():
        raise HTTPException(status_code=400, detail="Referenced uploaded image was not found")
    complaint_dict["image_url"] = f"uploads/{Path(resolved_image_path).name}"

    complaint_dict["description"] = sanitize_text(complaint_dict.get("description", ""), max_len=3000)
    if complaint_dict.get("user_grievance_text"):
        complaint_dict["user_grievance_text"] = sanitize_text(
            complaint_dict.get("user_grievance_text", ""),
            max_len=1200,
        )
        if len(complaint_dict["user_grievance_text"]) < 8:
            complaint_dict["user_grievance_text"] = None
    if len(complaint_dict["description"]) < 10:
        raise HTTPException(status_code=400, detail="Complaint description is too short after sanitization")
    if isinstance(complaint_dict.get("location"), dict) and complaint_dict["location"].get("address"):
        complaint_dict["location"]["address"] = sanitize_text(
            complaint_dict["location"]["address"],
            max_len=300,
        )
    
    resolved_department = canonicalize_label(
        str(complaint_dict.get("department") or complaint.department or "")
    )
    user_text_result = None

    if complaint_dict.get("user_grievance_text"):
        user_text_result = await asyncio.to_thread(
            classifier.classify_user_description,
            complaint_dict.get("user_grievance_text", ""),
        )
        if bool(user_text_result.get("is_valid", False)):
            resolved_department = canonicalize_label(
                str(user_text_result.get("department") or resolved_department)
            )

    complaint_dict["department"] = resolved_department

    incoming_ai = complaint_dict.get("ai_metadata") if isinstance(complaint_dict.get("ai_metadata"), dict) else {}
    safe_labels: list[str] = []
    for label in incoming_ai.get("labels", []):
        clean_label = sanitize_text(str(label), max_len=80).strip()
        if clean_label:
            safe_labels.append(clean_label)
        if len(safe_labels) >= 8:
            break

    try:
        existing_conf = float(incoming_ai.get("confidence_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        existing_conf = 0.0

    if user_text_result and bool(user_text_result.get("is_valid", False)):
        try:
            user_conf = float(user_text_result.get("confidence", 0.0) or 0.0)
            existing_conf = max(existing_conf, user_conf)
        except (TypeError, ValueError):
            pass

    complaint_dict["ai_metadata"] = {
        "model_used": sanitize_text(str(incoming_ai.get("model_used") or "ollama"), max_len=120),
        "confidence_score": max(0.0, min(existing_conf, 1.0)),
        "detected_department": resolved_department,
        "labels": safe_labels or [resolved_department],
    }

    # Resolve Authority routing metadata
    routing = route_authority(resolved_department)

    # Compute priority using final complaint text plus optional user context.
    priority_input_text = complaint_dict.get("description", "")
    if complaint_dict.get("user_grievance_text"):
        priority_input_text = (
            f"{priority_input_text}\n{complaint_dict.get('user_grievance_text', '')}"
        ).strip()

    priority = compute_priority(
        priority_input_text,
        complaint_dict.get("department", ""),
    )

    # Duplicate detection: same user + same department + similar location within 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    dup_query: dict = {
        "user_id": user_id,
        "department": resolved_department,
        "created_at": {"$gte": thirty_days_ago},
        "status": {"$nin": [ComplaintStatus.REJECTED]},
    }
    location_val = complaint_dict.get("location")
    if location_val:
        try:
            lat = float(location_val.get("lat"))
            lon = float(location_val.get("lon"))
            tolerance = 0.0008  # approx ~90m latitude; good practical duplicate radius
            dup_query["location.lat"] = {"$gte": lat - tolerance, "$lte": lat + tolerance}
            dup_query["location.lon"] = {"$gte": lon - tolerance, "$lte": lon + tolerance}
        except (TypeError, ValueError):
            if location_val.get("address"):
                dup_query["location.address"] = location_val.get("address")
    duplicate = await db["complaints"].find_one(dup_query)
    is_duplicate = bool(duplicate)

    complaint_dict.update({
        "user_id": user_id,
        "assigned_to": None,
        "authority_id": routing.get("authority_id"),
        "routing_confidence": routing.get("confidence"),
        "escalation_parent_authority_id": routing.get("escalation_parent_authority_id"),
        "status": ComplaintStatus.OPEN,
        "priority": priority,
        "is_duplicate": is_duplicate,
        "duplicate_of": str(duplicate["_id"]) if is_duplicate else None,
        "escalated": False,
        "dept_notes": [],
        "comments": [],
        "feedback": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "status_history": [{
            "status": ComplaintStatus.OPEN,
            "timestamp": datetime.now(timezone.utc),
            "changed_by_user_id": user_id,
            "note": "Complaint created"
        }]
    })

    # 3. Insert into DB
    result = await db["complaints"].insert_one(complaint_dict)
    
    # 4. Notify citizen that complaint was filed
    complaint_dict["_id"] = str(result.inserted_id)
    await create_notification(
        user_id=user_id,
        notification_type=NotificationType.STATUS_CHANGE,
        title="Grievance Registered",
        message=f"Your grievance has been registered and routed to {resolved_department}. Current status: Open.",
        complaint_id=complaint_dict["_id"],
        status_from=None,
        status_to=ComplaintStatus.OPEN.value,
    )

    # 5. Auto-assign to an available field worker
    location_data = complaint_dict.get("location")
    await auto_assign(
        complaint_id=complaint_dict["_id"],
        department=resolved_department,
        complaint_location=location_data,
        db=db,
    )
    
    return complaint_dict

@router.get("/complaints", response_model=list[ComplaintResponse])
async def list_complaints(
    current_user: dict = Depends(get_current_user),
    status: ComplaintStatus | None = None,
    department: str | None = None,
    skip: int = 0,
    limit: int | None = None,
):
    """
    Role-based complaint listing:
    - CITIZEN: Only their own complaints
    - DEPT_HEAD: Complaints from their department
    - ADMIN: All complaints (with optional filtering)
    """
    db = get_database()
    query = {}
    page_size = limit if limit is not None else settings.default_page_size
    page_size = max(1, min(page_size, settings.max_page_size))
    
    user_role = current_user.get("role")
    user_id = str(current_user["_id"])

    # Apply role-based filters
    if user_role == UserRole.CITIZEN:
        # Citizens only see their own complaints
        query["user_id"] = user_id
    elif user_role == UserRole.DEPT_HEAD:
        # Department heads see complaints from their department
        user_dept = current_user.get("department")
        if user_dept:
            query["department"] = user_dept
        else:
            # If dept head has no department assigned, show nothing
            query["_id"] = {"$exists": False}
    elif user_role == UserRole.WORKER:
        # H-09: Workers may only see complaints assigned to them — not all dept complaints
        query["assigned_to"] = user_id
    elif user_role == UserRole.ADMIN:
        # Admin can filter by department if provided
        if department:
            query["department"] = department
    else:
        # Unknown role — show nothing for safety
        query["_id"] = {"$exists": False}
    
    # Filter by status if provided
    if status:
        query["status"] = status.value
        
    cursor = db["complaints"].find(query).skip(skip).limit(page_size).sort("created_at", -1)
    
    complaints = []
    async for doc in cursor:
        complaints.append(fix_id(doc))
        
    return complaints


# ---------------------------------------------------------------------------
# CSV export (admin only)
# ---------------------------------------------------------------------------

@router.get("/complaints/export/csv")
async def export_complaints_csv(
    current_user: dict = Depends(get_current_admin),
    status: ComplaintStatus | None = None,
    department: str | None = None,
):
    """
    H-05: True async streaming CSV export.
    The old version loaded the entire collection into io.StringIO in memory.
    This generator yields rows as they come from the cursor — O(1) memory.
    """
    db = get_database()
    query: dict = {}
    if status:
        query["status"] = status.value
    if department:
        query["department"] = department

    fieldnames = [
        "id", "department", "status", "priority", "description",
        "location", "created_at", "updated_at", "escalated", "user_id",
    ]

    async def _csv_stream():
        import csv as _csv
        import io as _io

        buf = _io.StringIO()
        writer = _csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        yield buf.getvalue()
        buf.truncate(0)
        buf.seek(0)

        async for doc in db["complaints"].find(query).sort("created_at", -1):
            writer.writerow({
                "id": str(doc["_id"]),
                "department": doc.get("department", ""),
                "status": doc.get("status", ""),
                "priority": doc.get("priority", ""),
                "description": doc.get("description", ""),
                "location": doc.get("location", ""),
                "created_at": doc.get("created_at", ""),
                "updated_at": doc.get("updated_at", ""),
                "escalated": doc.get("escalated", False),
                "user_id": doc.get("user_id", ""),
            })
            yield buf.getvalue()
            buf.truncate(0)
            buf.seek(0)

    return StreamingResponse(
        _csv_stream(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=complaints_export.csv"},
    )

@router.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: str,
    current_user: dict = Depends(get_current_user),  # C-04: was unauthenticated
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    doc = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})

    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")

    _assert_complaint_access(current_user, doc)

    return fix_id(doc)

@router.patch("/complaints/{complaint_id}/status", response_model=ComplaintResponse)
async def update_complaint_status(
    complaint_id: str,
    payload: StatusUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    db = get_database()

    existing = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept or existing.get("department") != user_dept:
            raise HTTPException(status_code=403, detail="Cannot update complaints outside your department")
    
    status = payload.status
    safe_note = sanitize_text(payload.note, max_len=500) if payload.note else "Status updated via API"

    # Update Query
    update_data = {
        "$set": {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        },
        "$push": {
            "status_history": {
                "status": status,
                "timestamp": datetime.now(timezone.utc),
                "changed_by_user_id": str(current_user.get("_id")),
                "note": safe_note,
            }
        }
    }
    
    result = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        update_data,
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # When resolved, free the assigned worker's slot
    if status == ComplaintStatus.RESOLVED:
        assigned_worker_id = existing.get("assigned_to")
        if assigned_worker_id:
            await free_worker_slot(assigned_worker_id, complaint_id, db)

    # Notify the citizen who filed the complaint
    old_status = existing.get("status", ComplaintStatus.OPEN)
    citizen_id = existing.get("user_id")
    if citizen_id:
        status_messages = {
            ComplaintStatus.IN_PROGRESS: "Your grievance is now being reviewed by the department.",
            ComplaintStatus.RESOLVED: "Your grievance has been resolved. If the issue persists, please file a new complaint.",
            ComplaintStatus.REJECTED: "Your grievance has been reviewed and was not accepted. Please check the details.",
            ComplaintStatus.OPEN: "Your grievance has been re-opened for further review.",
        }
        dept = existing.get("department", "the department")
        msg = status_messages.get(status, f"Status updated to {status}.")
        if payload.note:
            msg = f"{msg} Note: {safe_note}"
        status_val = status.value if hasattr(status, 'value') else str(status)
        old_status_val = old_status.value if hasattr(old_status, 'value') else str(old_status)
        await create_notification(
            user_id=citizen_id,
            notification_type=NotificationType.STATUS_CHANGE,
            title=f"Status Updated: {status_val}",
            message=f"{msg} Department: {dept}.",
            complaint_id=complaint_id,
            status_from=old_status_val,
            status_to=status_val,
        )

        if ObjectId.is_valid(citizen_id):
            citizen_user = await db["users"].find_one({"_id": ObjectId(citizen_id)}, {"email": 1})
            citizen_email = citizen_user.get("email") if citizen_user else None
            if citizen_email:
                await asyncio.to_thread(
                    send_status_update_email,
                    citizen_email,
                    complaint_id,
                    dept,
                    status_val,
                    msg,
                )

    return fix_id(result)


@router.post("/complaints/{complaint_id}/escalate", response_model=ComplaintResponse)
async def escalate_complaint(complaint_id: str, current_user: dict = Depends(get_current_admin_or_dept_head)):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept or complaint.get("department") != user_dept:
            raise HTTPException(status_code=403, detail="Cannot escalate complaints outside your department")

    current_authority = complaint.get("authority_id")
    authority = get_authority_by_id(current_authority) if current_authority else None
    parent_id = authority.parent_authority_id if authority else complaint.get("escalation_parent_authority_id")
    if not parent_id:
        raise HTTPException(status_code=400, detail="No escalation target available")

    update_data = {
        "$set": {
            "authority_id": parent_id,
            "updated_at": datetime.now(timezone.utc),
        },
        "$push": {
            "status_history": {
                "status": complaint.get("status", ComplaintStatus.OPEN),
                "timestamp": datetime.now(timezone.utc),
                "changed_by_user_id": str(current_user.get("_id")),
                "note": f"Escalated from {current_authority} to {parent_id}",
            }
        }
    }

    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        update_data,
        return_document=True,
    )

    # Notify citizen about escalation
    citizen_id = complaint.get("user_id")
    if citizen_id:
        await create_notification(
            user_id=citizen_id,
            notification_type=NotificationType.ESCALATION,
            title="Grievance Escalated",
            message=f"Your grievance for {complaint.get('department', 'the department')} has been escalated to a higher authority for faster resolution.",
            complaint_id=complaint_id,
        )

    return fix_id(updated)


# ---------------------------------------------------------------------------
# Citizen feedback (star rating + comment) — only once, only after Resolved
# ---------------------------------------------------------------------------

@router.post("/complaints/{complaint_id}/feedback", response_model=ComplaintResponse)
async def submit_feedback(
    complaint_id: str,
    payload: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.get("user_id") != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not your complaint")

    if complaint.get("status") != ComplaintStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Feedback can only be submitted for resolved complaints")

    if complaint.get("feedback"):
        raise HTTPException(status_code=409, detail="Feedback already submitted")

    feedback_doc = {
        "rating": payload.rating,
        "comment": sanitize_text(payload.comment, max_len=500) if payload.comment else None,
        "submitted_at": datetime.now(timezone.utc),
    }
    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        {"$set": {"feedback": feedback_doc, "updated_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    return fix_id(updated)


# ---------------------------------------------------------------------------
# Internal dept notes (dept_head / admin only, hidden from citizen)
# ---------------------------------------------------------------------------

@router.post("/complaints/{complaint_id}/notes", response_model=ComplaintResponse)
async def add_dept_note(
    complaint_id: str,
    payload: DeptNoteRequest,
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    _assert_complaint_access(current_user, complaint)

    note_doc = {
        "note": sanitize_text(payload.note, max_len=1000),
        "created_by": current_user.get("username"),
        "created_at": datetime.now(timezone.utc),
    }
    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        {"$push": {"dept_notes": note_doc}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    return fix_id(updated)


@router.get("/complaints/{complaint_id}/notes")
async def get_dept_notes(
    complaint_id: str,
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one(
        {"_id": ObjectId(complaint_id)},
        {"dept_notes": 1, "department": 1, "user_id": 1, "assigned_to": 1},
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    _assert_complaint_access(current_user, complaint)

    return complaint.get("dept_notes", [])


# ---------------------------------------------------------------------------
# Public comments thread (visible to all parties on this complaint)
# ---------------------------------------------------------------------------

@router.post("/complaints/{complaint_id}/comments")
async def add_comment(
    complaint_id: str,
    payload: CommentRequest,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    _assert_complaint_access(current_user, complaint)

    comment_doc = {
        "text": sanitize_text(payload.text, max_len=1000),
        "author_id": str(current_user["_id"]),
        "author_name": current_user.get("username"),
        "author_role": current_user.get("role"),
        "created_at": datetime.now(timezone.utc),
    }
    await db["complaints"].update_one(
        {"_id": ObjectId(complaint_id)},
        {"$push": {"comments": comment_doc}, "$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": "Comment added", "comment": comment_doc}


@router.get("/complaints/{complaint_id}/comments")
async def get_comments(
    complaint_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one(
        {"_id": ObjectId(complaint_id)},
        {"comments": 1, "user_id": 1},
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    _assert_complaint_access(current_user, complaint)

    return complaint.get("comments", [])


# ---------------------------------------------------------------------------
# Bulk operations (admin only)
# ---------------------------------------------------------------------------

@router.post("/complaints/bulk/status")
async def bulk_update_status(
    payload: BulkStatusUpdate,
    current_user: dict = Depends(get_current_admin),
):
    db = get_database()
    valid_ids = [ObjectId(cid) for cid in payload.complaint_ids if ObjectId.is_valid(cid)]
    if not valid_ids:
        raise HTTPException(status_code=400, detail="No valid complaint IDs provided")

    history_entry = {
        "status": payload.status,
        "timestamp": datetime.now(timezone.utc),
        "changed_by_user_id": str(current_user["_id"]),
        "note": payload.note or "Bulk status update",
    }
    result = await db["complaints"].update_many(
        {"_id": {"$in": valid_ids}},
        {
            "$set": {"status": payload.status, "updated_at": datetime.now(timezone.utc)},
            "$push": {"status_history": history_entry},
        },
    )

    # P2-C: If setting status to Resolved, free each worker's slot.
    if payload.status == ComplaintStatus.RESOLVED:
        resolved_docs = db["complaints"].find(
            {"_id": {"$in": valid_ids}, "assigned_to": {"$ne": None}},
            {"assigned_to": 1}
        )
        async for resolved_doc in resolved_docs:
            worker_id = resolved_doc.get("assigned_to")
            if worker_id:
                await free_worker_slot(worker_id, str(resolved_doc["_id"]), db)

    return {"updated": result.modified_count}


@router.post("/complaints/bulk/transfer")
async def bulk_transfer(
    payload: BulkTransfer,
    current_user: dict = Depends(get_current_admin),
):
    from app.category_utils import CANONICAL_CATEGORIES

    if payload.new_department not in CANONICAL_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid department: {payload.new_department}")

    db = get_database()
    valid_ids = [ObjectId(cid) for cid in payload.complaint_ids if ObjectId.is_valid(cid)]
    if not valid_ids:
        raise HTTPException(status_code=400, detail="No valid complaint IDs provided")

    routing = route_authority(payload.new_department)
    note = f"Bulk transferred to '{payload.new_department}'"
    safe_reason = sanitize_text(payload.reason, max_len=500) if payload.reason else None
    if safe_reason:
        note += f". Reason: {safe_reason}"

    result = await db["complaints"].update_many(
        {"_id": {"$in": valid_ids}},
        {
            "$set": {
                "department": payload.new_department,
                "authority_id": routing.get("authority_id"),
                "routing_confidence": routing.get("confidence"),
                "escalation_parent_authority_id": routing.get("escalation_parent_authority_id"),
                "updated_at": datetime.now(timezone.utc),
            },
            "$push": {
                "status_history": {
                    "status": ComplaintStatus.OPEN,
                    "timestamp": datetime.now(timezone.utc),
                    "changed_by_user_id": str(current_user["_id"]),
                    "note": note,
                }
            },
        },
    )
    return {"updated": result.modified_count}

@router.patch("/complaints/{complaint_id}/transfer", response_model=ComplaintResponse)
async def transfer_complaint(
    complaint_id: str,
    payload: TransferRequest,
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    """
    Transfer a grievance to a different department.
    - ADMIN: can transfer any complaint.
    - DEPT_HEAD: can only transfer complaints currently in their own department.
    The AI confidence score is irrelevant — this override is always allowed for authorised roles.
    """
    from app.category_utils import CANONICAL_CATEGORIES

    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if payload.new_department not in CANONICAL_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department '{payload.new_department}'. Must be one of: {', '.join(CANONICAL_CATEGORIES)}",
        )

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Dept heads can only transfer from their own department
    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept or complaint.get("department") != user_dept:
            raise HTTPException(status_code=403, detail="Cannot transfer complaints outside your department")

    old_dept = complaint.get("department", "Unknown")
    new_dept = payload.new_department

    if old_dept == new_dept:
        raise HTTPException(status_code=400, detail="Complaint is already assigned to this department")

    # Re-derive authority routing for the new department
    routing = route_authority(new_dept)

    safe_reason = sanitize_text(payload.reason, max_len=500) if payload.reason else None
    transfer_note = f"Transferred from '{old_dept}' to '{new_dept}'"
    if safe_reason:
        transfer_note += f". Reason: {safe_reason}"

    update_data = {
        "$set": {
            "department": new_dept,
            "authority_id": routing.get("authority_id"),
            "routing_confidence": routing.get("confidence"),
            "escalation_parent_authority_id": routing.get("escalation_parent_authority_id"),
            "updated_at": datetime.now(timezone.utc),
        },
        "$push": {
            "status_history": {
                "status": complaint.get("status", ComplaintStatus.OPEN),
                "timestamp": datetime.now(timezone.utc),
                "changed_by_user_id": str(current_user.get("_id")),
                "note": transfer_note,
            }
        },
    }

    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        update_data,
        return_document=True,
    )

    # Notify the citizen
    citizen_id = complaint.get("user_id")
    if citizen_id:
        citizen_msg = (
            f"Your grievance has been transferred from {old_dept} to {new_dept}."
        )
        if safe_reason:
            citizen_msg += f" Reason: {safe_reason}"
        await create_notification(
            user_id=citizen_id,
            notification_type=NotificationType.ASSIGNMENT,
            title="Grievance Transferred to New Department",
            message=citizen_msg,
            complaint_id=complaint_id,
        )

    return fix_id(updated)
