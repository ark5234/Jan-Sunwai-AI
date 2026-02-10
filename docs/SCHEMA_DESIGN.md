# Jan-Sunwai AI - System Architecture

## Entity Relationship Diagram (ERD)

The following diagram illustrates the relationship between the Users (Citizens/Admins) and the Complaints (Grievances) they report and manage.

```mermaid
erDiagram
    USER {
        ObjectId _id PK "Unique Identifier"
        string username "Display Name"
        string email "Unique Email Address"
        string password_hash "Hashed Password"
        string role "Enum: citizen, admin"
        datetime created_at "Timestamp"
    }

    COMPLAINT {
        ObjectId _id PK "Unique Identifier"
        ObjectId user_id FK "Reference to USER"
        string image_url "Path to stored image"
        string department "Predicted Dept (e.g., Civil, VBD)"
        float confidence_score "AI Confidence (0.0 - 1.0)"
        string description "AI Generated/User Edited text"
        string status "Enum: Open, In Progress, Resolved, Rejected"
        object location "GeoJSON Point (type, coordinates)"
        string address "Human readable address"
        datetime created_at "Timestamp"
        datetime updated_at "Last status change time"
    }

    USER ||--o{ COMPLAINT : reports
```

## Schema Definitions

### 1. User Entity
Represents a registered user of the system.
*   **_id**: MongoDB ObjectId.
*   **full_name**: String, min 3 chars.
*   **email**: String, valid email format. Unique index.
*   **password**: String, hashed (bcrypt).
*   **role**: String, default "citizen". Options: ["citizen", "admin"].
*   **created_at**: DateTime, default `now()`.

### 2. Complaint Entity
Represents a civic grievance filed by a user.
*   **user_id**: Reference to User.
*   **image_url**: URL/Path to the uploaded evidence.
*   **ai_metadata**: Embedded Object.
    *   **model_used**: "CLIP-ViT-B/32"
    *   **confidence**: Float.
    *   **tags**: List[String].
*   **geo_location**: Embedded Object.
    *   **latitude**: Float.
    *   **longitude**: Float.
    *   **address**: String.
*   **status_history**: List[Object].
    *   **status**: String.
    *   **changed_by**: UserID.
    *   **timestamp**: DateTime.
