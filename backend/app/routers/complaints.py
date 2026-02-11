from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query, Body
from app.classifier import CivicClassifier
from app.geotagging import extract_location
from app.generator import generate_complaint
from app.database import get_database
from app.services.storage import storage_service
from app.schemas import (
    ComplaintCreate, 
    ComplaintResponse, 
    ComplaintStatus
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
    username: str = Form(...)
):
    # Authorization Check: Ensure user exists
    db = get_database()
    user = await db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not registered. Please sign up first.")

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
    username: str = Query(..., description="Username of the submitter")
):
    db = get_database()
    
    # 1. Validate User
    user = await db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_id = str(user["_id"])
    
    # 2. Prepare Data
    complaint_dict = complaint.model_dump()
    complaint_dict.update({
        "user_id": user_id,
        "status": ComplaintStatus.OPEN,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status_history": [{
            "status": ComplaintStatus.OPEN,
            "timestamp": datetime.utcnow(),
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
    username: Optional[str] = None,
    status: Optional[ComplaintStatus] = None,
    limit: int = 20
):
    db = get_database()
    query = {}
    
    # Filter by user if provided
    if username:
        user = await db["users"].find_one({"username": username})
        if user:
            query["user_id"] = str(user["_id"])
    
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
