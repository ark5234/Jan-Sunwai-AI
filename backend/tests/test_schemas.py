import pytest
from pydantic import ValidationError
from app.schemas import ComplaintCreate, GeoLocation, LocationSource, AIMetadata

def test_geolocation_validation():
    # Valid location
    geo = GeoLocation(lat=28.6139, lon=77.2090, source=LocationSource.EXIF)
    assert geo.lat == 28.6139
    
    # Invalid Latitude
    with pytest.raises(ValidationError):
        GeoLocation(lat=91.0, lon=77.2, source=LocationSource.DEVICE)
        
    # Invalid Longitude
    with pytest.raises(ValidationError):
        GeoLocation(lat=28.0, lon=181.0, source=LocationSource.MANUAL)

def test_complaint_create_schema():
    valid_data = {
        "description": "Garbage pile in Sector 45",
        "department": "Sanitation",
        "image_url": "uploads/test.jpg",
        "location": {
            "lat": 28.5,
            "lon": 77.2,
            "address": "Sector 45, Gurgaon",
            "source": "manual"
        },
        "ai_metadata": {
            "confidence_score": 0.95,
            "detected_department": "Sanitation",
            "labels": ["garbage", "trash"]
        }
    }
    
    complaint = ComplaintCreate(**valid_data)
    assert complaint.department == "Sanitation"
    assert complaint.location.source == LocationSource.MANUAL

def test_ai_confidence_score_validation():
    # Valid
    ai = AIMetadata(confidence_score=0.5, detected_department="Civil")
    assert ai.confidence_score == 0.5
    
    # Invalid > 1.0
    with pytest.raises(ValidationError):
        AIMetadata(confidence_score=1.5, detected_department="Civil")
    
    # Invalid < 0.0
    with pytest.raises(ValidationError):
        AIMetadata(confidence_score=-0.1, detected_department="Civil")
