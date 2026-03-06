from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
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

class PriorityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

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
    model_used: str = "ollama"
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
    authority_id: Optional[str] = Field(None, description="ID of the Authority Organization")
    routing_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    escalation_parent_authority_id: Optional[str] = None
    priority: Optional[PriorityLevel] = PriorityLevel.MEDIUM
    status: ComplaintStatus = ComplaintStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status_history: list[StatusHistoryItem] = []
    feedback: Optional[dict] = None
    dept_notes: List[dict] = []
    comments: List[dict] = []
    escalated: bool = False
    escalated_at: Optional[datetime] = None
    language: Optional[str] = "English"

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class ComplaintResponse(ComplaintBase):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    image_url: Optional[str] = None
    location: Optional[GeoLocation] = None
    ai_metadata: Optional[AIMetadata] = None

    assigned_to: Optional[str] = None
    authority_id: Optional[str] = None
    routing_confidence: Optional[float] = None
    escalation_parent_authority_id: Optional[str] = None
    priority: Optional[PriorityLevel] = None
    status: ComplaintStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    status_history: list[StatusHistoryItem] = []
    feedback: Optional[dict] = None
    dept_notes: List[dict] = []
    comments: List[dict] = []
    escalated: bool = False
    escalated_at: Optional[datetime] = None
    language: Optional[str] = "English"

    class Config:
        populate_by_name = True


# --- Notification Schemas ---

class TransferRequest(BaseModel):
    new_department: str = Field(..., description="The department to transfer this complaint to")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for the transfer (optional)")


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=500)


class DeptNoteRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=1000)


class CommentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class BulkStatusUpdate(BaseModel):
    complaint_ids: List[str] = Field(..., min_length=1)
    status: ComplaintStatus
    note: Optional[str] = None


class BulkTransfer(BaseModel):
    complaint_ids: List[str] = Field(..., min_length=1)
    new_department: str
    reason: Optional[str] = None


class NotificationType(str, Enum):
    STATUS_CHANGE = "status_change"
    ESCALATION = "escalation"
    ASSIGNMENT = "assignment"
    SYSTEM = "system"

class NotificationResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    complaint_id: Optional[str] = None
    type: NotificationType
    title: str
    message: str
    status_from: Optional[str] = None
    status_to: Optional[str] = None
    is_read: bool = False
    created_at: datetime

    class Config:
        populate_by_name = True

