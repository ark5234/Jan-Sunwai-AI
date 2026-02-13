import asyncio

from fastapi import APIRouter, File, UploadFile, HTTPException, Body, Depends
from app.classifier import CivicClassifier
from app.geotagging import extract_location
from app.database import get_database
from app.services.storage import storage_service
from app.services.llm_queue import llm_queue_service
from app.auth import get_current_user, get_current_admin_or_dept_head
from app.schemas import (
    ComplaintCreate, 
    ComplaintResponse, 
    ComplaintStatus,
    UserRole
)
from app.authorities import route_authority, get_authority_by_id
from app.config import settings
from PIL import Image
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import io

router = APIRouter()
classifier = CivicClassifier()

# Helper to fix ObjectId serialization
def fix_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def await_generation(job_id: str, timeout_seconds: float) -> dict:
    elapsed = 0.0
    sleep_interval = 0.2
    while elapsed < timeout_seconds:
        result = llm_queue_service.get_result(job_id)
        if result and result.get("status") in ["completed", "failed"]:
            return result
        await asyncio.sleep(sleep_interval)
        elapsed += sleep_interval
    return {"status": "queued"}

@router.post("/analyze")
async def analyze_complaint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Authorization handled by Depends(get_current_user)
    username = current_user["username"]

    # 1. Save File Securely (New: Feb 06 Requirement)
    # The file pointer is at the start here.
    file_path = await storage_service.save_file(file)
    absolute_file_path = storage_service.resolve_path(file_path)
    
    # After saving, the file pointer might be at the end. 
    # But storage_service.save_file resets it (await file.seek(0)).
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # 2. Classify
    classification = classifier.classify(image)
    
    # 3. Extract Location
    location = extract_location(image)
    
    # 4. Generate Complaint Text (Async queue)
    if classification.get("is_valid", True):
        job_id = await llm_queue_service.enqueue(absolute_file_path, classification, {"name": username}, location)
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
        "image_url": file_path # Return the path so frontend can pass it to /complaints
    }


@router.get("/complaints/generation/{job_id}")
async def get_generation_result(job_id: str, current_user: dict = Depends(get_current_user)):
    result = llm_queue_service.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return result

# --- CRUD Endpoints ---

@router.post("/complaints", response_model=ComplaintResponse)
async def create_complaint(
    complaint: ComplaintCreate, 
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    user_id = str(current_user["_id"])
    
    # 2. Prepare Data
    complaint_dict = complaint.model_dump()
    
    # Resolve Authority routing metadata
    routing = route_authority(complaint.department)

    complaint_dict.update({
        "user_id": user_id,
        "assigned_to": None,
        "authority_id": routing.get("authority_id"),
        "routing_confidence": routing.get("confidence"),
        "escalation_parent_authority_id": routing.get("escalation_parent_authority_id"),
        "status": ComplaintStatus.OPEN,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status_history": [{
            "status": ComplaintStatus.OPEN,
            "timestamp": datetime.utcnow(),
            "changed_by_user_id": user_id,
            "note": "Complaint created"
        }]
    })
    
    # 3. Insert into DB
    result = await db["complaints"].insert_one(complaint_dict)
    
    # 4. Return Created
    complaint_dict["_id"] = str(result.inserted_id)
    return complaint_dict

@router.get("/complaints", response_model=List[ComplaintResponse])
async def list_complaints(
    current_user: dict = Depends(get_current_user),
    status: Optional[ComplaintStatus] = None,
    department: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = None,
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
    elif user_role == UserRole.ADMIN:
        # Admin can filter by department if provided
        if department:
            query["department"] = department
    
    # Filter by status if provided
    if status:
        query["status"] = status.value
        
    cursor = db["complaints"].find(query).skip(skip).limit(page_size).sort("created_at", -1)
    
    complaints = []
    async for doc in cursor:
        complaints.append(fix_id(doc))
        
    return complaints

@router.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(complaint_id: str):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    db = get_database()
    doc = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    return fix_id(doc)

@router.patch("/complaints/{complaint_id}/status", response_model=ComplaintResponse)
async def update_complaint_status(
    complaint_id: str,
    status: ComplaintStatus = Body(..., embed=True),
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
    
    # Update Query
    update_data = {
        "$set": {
            "status": status, 
            "updated_at": datetime.utcnow()
        },
        "$push": {
            "status_history": {
                "status": status,
                "timestamp": datetime.utcnow(),
                "changed_by_user_id": str(current_user.get("_id")),
                "note": "Status updated via API"
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
            "updated_at": datetime.utcnow(),
        },
        "$push": {
            "status_history": {
                "status": complaint.get("status", ComplaintStatus.OPEN),
                "timestamp": datetime.utcnow(),
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
    return fix_id(updated)
