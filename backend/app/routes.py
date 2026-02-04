from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from app.classifier import CivicClassifier
from app.geotagging import extract_location
from app.generator import generate_complaint
from app.database import get_database
from PIL import Image
import io

router = APIRouter()
classifier = CivicClassifier()

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

    # Read Image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # 1. Classify
    classification = classifier.classify(image)
    
    # 2. Extract Location
    location = extract_location(image)
    
    # 3. Generate Complaint Text
    # Pass raw bytes for LLaVA
    generated_text = generate_complaint(contents, {"name": username}, location)
    
    return {
        "classification": classification,
        "location": location,
        "generated_complaint": generated_text
    }
