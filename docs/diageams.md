# Diagrams

This file consolidates the main project diagrams from the report and system architecture documentation into one Markdown reference.

## 4.1 Proposed End-to-End Workflow

```mermaid
flowchart LR
    A[Citizen Registration and Login] --> B[Upload Image and Complaint Details]
    B --> C[AI Analysis and Draft Generation]
    C --> D{Confidence >= Threshold?}
    D -->|Yes| E[Auto Department Routing]
    D -->|No| F[Admin Triage and Label Correction]
    F --> E
    E --> G[Create Complaint Record in MongoDB]
    G --> H[Auto Assignment to Worker]
    H --> I[Worker Updates Progress and Notes]
    I --> J{Resolved?}
    J -->|No| K[Department Head Review and Escalation]
    K --> I
    J -->|Yes| L[Citizen Notification and Timeline Update]
    L --> M[Feedback Collection]
    M --> N[Analytics and Governance Reporting]
```

## 5.1 Overall System Context Diagram

```mermaid
flowchart LR
    Citizen[Citizen]
    Worker[Field Worker]
    DeptHead[Department Head]
    Admin[Administrator]
    Public[Public Transparency Viewer]

    Citizen --> Portal[Jan-Sunwai Frontend]
    Worker --> Portal
    DeptHead --> Portal
    Admin --> Portal
    Public --> Portal

    Portal --> API[FastAPI Backend]
    API --> DB[(MongoDB)]
    API --> Files[(File Storage uploads/)]
    API --> AI[Ollama Inference Runtime]
    API --> Notify[SMTP Email Notifications]
    API --> Logs[Audit and Activity Logs]
```

## 5.2 Component Architecture Diagram

```mermaid
flowchart TB
    subgraph Frontend Layer
        FE1[React SPA]
        FE2[Role Dashboards - Citizen, Worker, DeptHead, Admin]
        FE3[Analyze and Result Pages]
        FE4[Map, Heatmap and Public Views]
    end

    subgraph API Layer
        BE1[Auth Router]
        BE2[Users Router]
        BE3[Complaints and Analyze Router]
        BE4[Workers Router]
        BE5[Triage Router]
        BE6[Notifications Router]
        BE7[Analytics Router]
        BE8[Public Router]
        BE9[Health Router]
    end

    subgraph Service Layer
        S1[Assignment Service]
        S2[Escalation Service]
        S3[LLM Queue Service]
        S4[Email Service]
        S5[Priority Service]
        S6[Storage Service]
        S7[Sanitization Service]
    end

    subgraph Data Layer
        DB[(MongoDB)]
        UP[(File Storage uploads/)]
        IDX[(Indexes and Aggregations)]
    end

    subgraph Inference Layer
        O1[Vision Model - qwen2.5vl / granite3.2-vision]
        O2[Reasoning Model - llama3.2]
    end

    FE1 --> BE1
    FE1 --> BE2
    FE2 --> BE3
    FE2 --> BE4
    FE2 --> BE5
    FE2 --> BE6
    FE3 --> BE3
    FE4 --> BE7
    FE4 --> BE8

    BE3 --> S3
    BE4 --> S1
    BE5 --> S2
    BE3 --> S6
    BE3 --> S5
    BE3 --> S4
    BE6 --> DB

    S3 --> O1
    S3 --> O2

    BE1 --> DB
    BE2 --> DB
    BE3 --> DB
    BE4 --> DB
    BE5 --> DB
    BE7 --> IDX
    BE8 --> IDX
    BE3 --> UP
```

## 5.3 E-R Diagram

```mermaid
erDiagram
    USER {
        string user_id PK
        string username
        string full_name
        string email UK
        string role
        string department
        string job_title
        string phone_number
        object service_area
        string worker_status
        array active_complaint_ids
        bool is_approved
        datetime created_at
    }

    COMPLAINT {
        string complaint_id PK
        string user_id FK
        string assigned_to FK
        string authority_id
        string department
        string status
        string priority
        string description
        string user_grievance_text
        string image_url
        string language
        object location
        object ai_metadata
        float routing_confidence
        array status_history
        array dept_notes
        array comments
        object feedback
        bool escalated
        datetime escalated_at
        datetime created_at
        datetime updated_at
    }

    NOTIFICATION {
        string notification_id PK
        string complaint_id FK
        string user_id FK
        string type
        string title
        string message
        string status_from
        string status_to
        boolean is_read
        datetime created_at
    }

    LLM_JOB {
        string job_id PK
        string owner_id FK
        int worker_id
        string status
        string generated_complaint
        datetime created_at
    }

    USER ||--o{ COMPLAINT : files
    USER ||--o{ COMPLAINT : assigned_to
    USER ||--o{ NOTIFICATION : receives
    COMPLAINT ||--o{ NOTIFICATION : triggers
    USER ||--o{ LLM_JOB : owns
```

## 5.4 Use Case Diagram

```mermaid
flowchart TD
    subgraph Actors
        Citizen([Citizen])
        Worker([Worker])
        DeptHead([Department Head])
        Admin([Administrator])
        AI([AI Service])
        Notify([Notification Service])
    end

    subgraph Platform["Jan-Sunwai AI Platform"]
        UC1[Authenticate User]
        UC2[Submit Complaint with Evidence]
        UC3[Analyze Image and Generate Draft]
        UC4[Edit and Confirm Complaint]
        UC5[Track Complaint and SLA]
        UC6[View Assigned Queue]
        UC7[Update Status with Note]
        UC8[Resolve Complaint]
        UC9[Reassign / Transfer Complaint]
        UC10[Escalate Complaint]
        UC11[Approve Worker Onboarding]
        UC12[Review Low-Confidence Triage]
        UC13[View Analytics and Public Dashboard]
        UC14[Send Email Notifications]
        UC15[Reset Password]
    end

    Citizen --> UC1
    Citizen --> UC2
    Citizen --> UC4
    Citizen --> UC5
    Citizen --> UC15

    Worker --> UC1
    Worker --> UC6
    Worker --> UC7
    Worker --> UC8

    DeptHead --> UC1
    DeptHead --> UC6
    DeptHead --> UC7
    DeptHead --> UC9
    DeptHead --> UC10

    Admin --> UC1
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC9

    UC2 -->|includes| UC3
    UC4 -->|includes| UC3
    UC7 -->|includes| UC14
    UC8 -->|includes| UC14
    UC9 -->|includes| UC14
    UC10 -->|includes| UC14

    AI --> UC3
    Notify --> UC14
```

## 5.5 Class Diagram

```mermaid
classDiagram
    class User {
        +user_id: string
        +username: string
        +full_name: string
        +email: string
        +role: UserRole
        +department: string
        +job_title: string
        +phone_number: string
        +service_area: ServiceArea
        +worker_status: WorkerStatus
        +active_complaint_ids: list
        +is_approved: bool
        +login()
        +updateProfile()
    }

    class Complaint {
        +complaint_id: string
        +description: string
        +user_grievance_text: string
        +department: string
        +status: ComplaintStatus
        +priority: PriorityLevel
        +image_url: string
        +language: string
        +routing_confidence: float
        +escalated: bool
        +escalated_at: datetime
        +dept_notes: list
        +comments: list
        +feedback: dict
        +created_at: datetime
        +updated_at: datetime
        +assignWorker()
        +updateStatus()
        +escalate()
    }

    class Notification {
        +notification_id: string
        +type: NotificationType
        +title: string
        +message: string
        +is_read: boolean
        +created_at: datetime
        +markRead()
        +send()
    }

    class AIMetadata {
        +model_used: string
        +confidence_score: float
        +detected_department: string
        +labels: list
    }

    class GeoLocation {
        +lat: float
        +lon: float
        +address: string
        +source: LocationSource
    }

    class ServiceArea {
        +lat: float
        +lon: float
        +radius_km: float
        +locality: string
    }

    class StatusHistoryItem {
        +status: ComplaintStatus
        +timestamp: datetime
        +changed_by_user_id: string
        +note: string
    }

    class AssignmentService {
        +auto_assign(complaint)
        +free_worker_slot(worker, complaint)
    }

    class LLMQueueService {
        +enqueue(image_path, classification, user_details, location_details, language)
        +get_result(job_id)
        +get_result_async(job_id)
    }

    class PriorityService {
        +compute_priority(description, department)
    }

    class EscalationService {
        +escalation_loop()
    }

    class EmailService {
        +send_status_update_email(to_email, complaint_id, department, status_to, message)
        +send_password_reset_email(to_email, reset_token)
    }

    class ComplaintStatus {
        <<enumeration>>
        OPEN
        IN_PROGRESS
        RESOLVED
        REJECTED
    }

    class UserRole {
        <<enumeration>>
        CITIZEN
        WORKER
        DEPT_HEAD
        ADMIN
    }

    class WorkerStatus {
        <<enumeration>>
        AVAILABLE
        BUSY
        OFFLINE
    }

    class NotificationType {
        <<enumeration>>
        STATUS_CHANGE
        ESCALATION
        ASSIGNMENT
        SYSTEM
    }

    class PriorityLevel {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
        CRITICAL
    }

    class LocationSource {
        <<enumeration>>
        EXIF
        DEVICE
        MANUAL
    }

    User "1" --> "0..*" Complaint : files
    User "0..1" --> "0..*" Complaint : assigned_to
    User "1" --> "0..*" Notification : receives
    Complaint "1" --> "0..*" Notification : triggers
    Complaint "1" *-- "1" AIMetadata : ai_metadata
    Complaint "1" *-- "1" GeoLocation : location
    Complaint "1" *-- "0..*" StatusHistoryItem : status_history
    User "1" *-- "0..1" ServiceArea : service_area
    AssignmentService ..> Complaint : manages
    LLMQueueService ..> Complaint : generates_draft_for
    PriorityService ..> Complaint : scores
    EscalationService ..> Complaint : escalates
    EmailService ..> Notification : delivers
    Complaint --> ComplaintStatus
    User --> UserRole
```

## 5.6 Sequence Diagram

```mermaid
sequenceDiagram
    actor Citizen
    actor Admin
    actor Worker
    participant FE as Frontend
    participant API as Backend
    participant Queue as LLM Queue
    participant AI as Ollama
    participant DB as MongoDB
    participant Email as Email Service

    Citizen->>FE: Upload image and enter details
    FE->>API: POST /api/v1/analyze
    API->>Queue: enqueue(image_path, classification, user_details, location)
    Queue->>AI: run vision and reasoning inference
    AI-->>Queue: category, confidence, draft
    Queue-->>API: job result (completed)
    API-->>FE: return draft for citizen review

    Citizen->>FE: Confirm and submit complaint
    FE->>API: POST /api/v1/complaints
    API->>DB: create complaint record

    alt high confidence
        API->>DB: auto-assign worker and set In Progress
    else low confidence
        API->>DB: add to triage queue
        Admin->>API: POST /api/v1/triage/review-queue/decision
        API->>DB: update department and assignment
    end

    API->>Email: send_status_update_email (complaint created)
    Email-->>Citizen: status notification via SMTP

    Worker->>API: PATCH /api/v1/complaints/{id}/status
    API->>DB: update status and timeline
    API->>Email: send_status_update_email (resolved)
    Email-->>Citizen: complaint resolved message
```

## 5.7 Activity Diagram

```mermaid
flowchart TD
    A([Start]) --> B[Login and Open Dashboard]
    B --> C[Submit Complaint with Image]
    C --> D[AI Analysis and Draft]
    D --> E{Citizen accepts draft?}
    E -->|No| F[Citizen edits description]
    F --> G[Submit Complaint]
    E -->|Yes| G
    G --> H{Confidence high?}
    H -->|Yes| I[Auto-route and assign worker]
    H -->|No| J[Send to admin triage]
    J --> K[Admin reviews and confirms route]
    K --> I
    I --> L[Worker starts and updates progress]
    L --> M{Issue resolved?}
    M -->|No| N[Escalate to department head]
    N --> L
    M -->|Yes| O[Close complaint and notify citizen]
    O --> P([End])
```

## 5.8 Data Flow Diagram

### 5.8.1 DFD Level 0 (Context)

```mermaid
flowchart LR
    Citizen[Citizen]
    Worker[Worker]
    DeptHead[Department Head]
    Admin[Admin]
    AI[Ollama Inference]

    System((Jan-Sunwai AI System))

    Citizen -->|Image + complaint details| System
    System -->|Complaint ID, status, email notifications| Citizen

    Worker -->|Progress updates| System
    System -->|Assigned complaints| Worker

    DeptHead -->|Escalation and routing decisions| System
    Admin -->|Triage and governance actions| System

    System -->|Classification request| AI
    AI -->|Category + confidence + draft| System
```

### 5.8.2 DFD Level 1

```mermaid
flowchart LR
    C[Citizen]
    W[Worker]
    A[Admin]

    C --> P1[1.0 Complaint Submission]
    P1 --> D1[(D1 Complaints)]

    P1 --> P2[2.0 AI Classification and Draft]
    P2 --> D2[(D2 LLM Jobs - MongoDB TTL)]

    P2 --> P3[3.0 Triage and Routing]
    A --> P3
    P3 --> D1
    P3 --> D3[(D3 Triage Decisions)]

    W --> P4[4.0 Status Update and Resolution]
    P4 --> D1
    P4 --> D4[(D4 Status History)]

    D1 --> P5[5.0 Email Notification Delivery]
    D4 --> P5
    P5 --> C
    P5 --> W
```

### 5.8.3 DFD Level 2 (Process 1.0 Complaint Submission)

```mermaid
flowchart LR
    C[Citizen]

    P11[1.1 Upload Image and Inputs]
    P12[1.2 Validate Token and Payload]
    P13[1.3 Persist Uploaded File via Storage Service]
    P14[1.4 Compute Priority and Create Complaint Record]
    P15[1.5 Trigger Assignment and Email Notifications]

    D1[(D1 Complaints)]
    D5[(D5 Upload Storage)]
    D6[(D6 User and Worker Data)]

    C --> P11
    P11 --> P12
    P12 --> P13
    P13 --> D5
    P13 --> P14
    P14 --> D1
    P14 --> P15
    D6 --> P15
    P15 --> D1
    P15 --> C
```

## 5.9 Deployment Diagram

```mermaid
flowchart LR
    User[Web Browser]

    subgraph FrontendContainer[Frontend Container - prod profile]
        Nginx[NGINX Serving React Build - port 5173 to 80]
    end

    subgraph BackendContainer[Backend Container]
        API[FastAPI and Uvicorn - port 8000]
    end

    subgraph DatabaseContainer[MongoDB Container]
        DB[(MongoDB 7.0 - port 27018)]
    end

    subgraph Volumes[Persistent Volumes]
        DBVol[(mongodb_data)]
        Files[(backend_uploads)]
    end

    subgraph External[External Services]
        Ollama[Host Ollama Runtime - host.docker.internal:11434]
        Mail[SMTP Provider - via email_service.py]
    end

    User --> Nginx
    Nginx --> API
    API --> DB
    API --> Files
    DB --> DBVol
    API --> Ollama
    API --> Mail
```