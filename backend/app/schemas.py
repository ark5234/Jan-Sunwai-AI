from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    CITIZEN = "citizen"
    DEPT_HEAD = "dept_head"
    ADMIN = "admin"

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    department: Optional[str] = Field(None, description="Department for DEPT_HEAD users")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    role: UserRole = UserRole.CITIZEN

class UserInDB(UserBase):
    id: Optional[str] = Field(None, alias="_id")
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class UserResponse(UserBase):
    id: Optional[str] = Field(None, alias="_id")
    role: UserRole
    created_at: datetime
    department: Optional[str] = None

    class Config:
        populate_by_name = True

# --- Complaint Schemas ---

class ComplaintStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"

class LocationSource(str, Enum):
    EXIF = "exif"           # Extracted from image metadata
    DEVICE = "device"       # Browser/Phone GPS at upload time
    MANUAL = "manual"       # Pinned by user on map

class GeoLocation(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    address: Optional[str] = "Unknown Location"
    source: LocationSource

class AIMetadata(BaseModel):
    model_used: str = "CLIP-ViT-B/32"
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    detected_department: str
    labels: list[str] = []

class StatusHistoryItem(BaseModel):
    """Tracks the lifecycle of a complaint"""
    status: ComplaintStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changed_by_user_id: Optional[str] = Field(None, description="ID of the Admin/User who changed the status")
    note: Optional[str] = None

class ComplaintBase(BaseModel):
    description: str = Field(..., min_length=10, description="The complaint text (AI generated or edited)")
    department: str

class ComplaintCreate(ComplaintBase):
    # This is what comes from the Frontend (after AI analysis + User edit)
    image_url: str
    location: GeoLocation
    ai_metadata: AIMetadata

class ComplaintInDB(ComplaintCreate):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    assigned_to: Optional[str] = Field(None, description="ID of the Admin handling this complaint")
    status: ComplaintStatus = ComplaintStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status_history: list[StatusHistoryItem] = [] # To track changes

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class ComplaintResponse(ComplaintCreate):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    assigned_to: Optional[str]
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime
    status_history: list[StatusHistoryItem]

    class Config:
        populate_by_name = True

