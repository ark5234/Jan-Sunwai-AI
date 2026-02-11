from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query, Body, Depends
from app.classifier import CivicClassifier
from app.geotagging import extract_location
from app.generator import generate_complaint
from app.database import get_database
from app.services.storage import storage_service
from app.auth import get_current_user
from app.schemas import (
    ComplaintCreate, 
    ComplaintResponse, 
    ComplaintStatus,
    UserRole
)
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
    
    # After saving, the file pointer might be at the end. 
    # But storage_service.save_file resets it (await file.seek(0)).
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # 2. Classify
    classification = classifier.classify(image)
    
    # 3. Extract Location
    location = extract_location(image)
    
    # 4. Generate Complaint Text
    generated_text = generate_complaint(file_path, classification, {"name": username}, location)
    
    return {
        "classification": classification,
        "location": location,
        "generated_complaint": generated_text,
        "image_url": file_path # Return the path so frontend can pass it to /complaints
    }

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
    complaint_dict.update({
        "user_id": user_id,
        "assigned_to": None,
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
    limit: int = 50
):
    """
    Role-based complaint listing:
    - CITIZEN: Only their own complaints
    - DEPT_HEAD: Complaints from their department
    - ADMIN: All complaints (with optional filtering)
    """
    db = get_database()
    query = {}
    
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
        
    cursor = db["complaints"].find(query).limit(limit).sort("created_at", -1)
    
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
    status: ComplaintStatus = Body(..., embed=True)
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    db = get_database()
    
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
