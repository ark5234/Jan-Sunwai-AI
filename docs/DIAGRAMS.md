# Chapter 5: System Architecture and Design Diagrams

This document contains the detailed system architecture, UML, and Database diagrams reflecting the exact specifications of the Jan-Sunwai AI project.

## 5.1 System Architecture Design

### 5.1.1 Architectural Style
Jan-Sunwai AI follows a **Client-Server architecture** with a clear separation of concerns:
- **Client Tier**: A React/Vite Single Page Application (SPA) serving different roles (Citizen, Worker, Dept Head, Admin).
- **Service Tier**: A FastAPI backend adhering to RESTful principles (`/api/v1` routes) handling business logic, authentication (JWT), and AI orchestration.
- **Data Tier**: MongoDB stores users, complaints, assignments, and audit logs (NDMC MongoDB).
- **AI Processing Tier**: Local Ollama runtime used for vision classification, reasoning, and drafting.

### 5.1.2 Key Architectural Decisions
- **Local-First AI Execution**: Chosen to ensure data privacy and reduce dependency on external APIs.
- **Asynchronous AI Queue**: In-memory worker queue in FastAPI ensures that long-running LLM generation tasks do not block incoming HTTP requests.
- **Role-Based Access Control (RBAC)**: Strict segregation between Admin, Department Head, Worker, and Citizen spaces.
- **Containerization**: Use of Docker Compose to bundle the React frontend, FastAPI backend, and MongoDB instances for predictable deployments.

### 5.1.3 AI Classification Pipeline

```mermaid
flowchart TD
    A[Image Upload] --> B[Storage + Geotag Extraction]
    B --> C[Vision Cascade: Qwen2.5-VL / Granite / Moondream]
    C --> D{Non-Civic Guard?}
    D -->|Yes| E[Invalid/Uncategorized]
    D -->|No| F[Rule Engine Scoring]
    F --> G{Ambiguous or Uncategorized?}
    G -->|Yes| H[Vision Retry w/ Alt Model]
    H --> I{Still Ambiguous?}
    I -->|Yes| J[Llama 3.2 Reasoning Model]
    I -->|No| K[Finalize Category]
    J --> K
    G -->|No| K
    K --> L[NDMC AI API Comparison]
    L --> M[Queue Draft Generation]
    M --> N[Citizen Review + Submit]
    N --> O[Complaint Saved + Auto-Routed]
```
![AI Classification Pipeline](./images/system_context_diagram.png)

## 5.2 UML Diagrams

### 5.2.1 E-R Diagram (Entity-Relationship)

```mermaid
erDiagram
    USER ||--o{ COMPLAINT : "creates / handles"
    COMPLAINT ||--o{ NOTIFICATION : triggers
    USER ||--o{ NOTIFICATION : receives
    
    USER {
        ObjectId _id PK
        string username
        string email
        string password_hash
        string full_name
        string phone_number
        string role
        string department
        string worker_status
        object service_area
        boolean is_approved
    }
    
    COMPLAINT {
        ObjectId _id PK
        ObjectId user_id FK
        ObjectId assigned_to FK
        string authority_id
        string department
        string description
        string user_grievance_text
        string image_url
        object location
        object ai_metadata
        float routing_confidence
        string priority
        string status
        boolean escalated
        datetime created_at
        list status_history
        list dept_notes
    }
    
    NOTIFICATION {
        ObjectId _id PK
        ObjectId user_id FK
        ObjectId complaint_id FK
        string type
        string title
        string message
        boolean is_read
        datetime created_at
    }
```
![E-R Diagram](./images/new_er.png)

### 5.2.2 Use Case Diagram

```mermaid
flowchart LR
    Citizen((Citizen))
    Worker((Worker))
    DeptHead((Department Head))
    Admin((Admin))
    
    Citizen --> UC1([Upload Issue Photo])
    Citizen --> UC2([Review Generated Draft])
    Citizen --> UC3([Track Complaint Status])
    Citizen --> UC14([Provide Feedback])
    
    Worker --> UC4([View Assigned Tasks])
    Worker --> UC5([Add Dept Notes & Update Status])
    Worker --> UC6([Mark Complaint Resolved])
    
    DeptHead --> UC7([Monitor Department Queue])
    DeptHead --> UC8([Handle Escalations])
    DeptHead --> UC9([View Analytics & Heatmap])
    DeptHead --> UC15([Reassign Workers])
    
    Admin --> UC10([Manage & Approve Workers])
    Admin --> UC11([Triage Low-Confidence Issues])
    Admin --> UC12([System & AI Configurations])
    Admin --> UC16([View Global Analytics])
    
    UC1 -.->|includes| UC13([AI Classification & Generation])
    UC11 -.->|updates| UC8
```
![Use Case Diagram](./images/flowchart.png)
*(Note: Mermaid flowchart can also depict use case functionality if actual Use Case UML is not fully supported in your renderer, standard UML boundaries apply)*

### 5.2.3 Class Diagram

```mermaid
classDiagram
    class UsersRouter {
        +register()
        +login()
        +updateProfile()
        +getMe()
    }
    class ComplaintsRouter {
        +analyze()
        +create()
        +getList()
        +updateStatus()
        +escalate()
        +addDeptNote()
        +transferDepartment()
    }
    class WorkersRouter {
        +getQueue()
        +approveWorker()
        +updateWorkerStatus()
        +assignTaskManual()
    }
    class AnalyticsRouter {
        +getOverview()
        +getHeatmap()
    }
    class TriageRouter {
        +getReviewQueue()
        +resolveTriage()
    }
    class NotificationsRouter {
        +getMyNotifications()
        +markAsRead()
    }
    class ClassifierEngine {
        +runVisionCascade()
        +runRuleEngine()
    }
    class GeneratorEngine {
        +generateDraft()
    }
    class NDMCApiClient {
        +logAudit()
    }
    class AssignmentService {
        +autoAssignGeo()
    }
    
    ComplaintsRouter --> ClassifierEngine : uses
    ComplaintsRouter --> GeneratorEngine : uses
    ComplaintsRouter --> AssignmentService : triggers
    ComplaintsRouter --> NotificationsRouter : emits
    ComplaintsRouter --> NDMCApiClient : triggers_audit
```
![Class Diagram](./images/class_diagram.png)

### 5.2.4 Sequence Diagram
(Complaint Lifecycle Sequence)

```mermaid
sequenceDiagram
    actor Citizen
    participant FE as Frontend (React)
    participant API as FastAPI Backend
    participant CLSF as Classifier/Generator Engine
    participant DB as MongoDB
    participant NDMC as NDMC Audit DB
    participant ASSIGN as Assignment Service
    participant NOTIFY as Notification System

    Citizen->>FE: Upload Image & Grievance Text
    FE->>API: POST /api/v1/analyze
    API->>CLSF: Run Vision Model & Rule Engine
    CLSF-->>API: Category & Confidence
    API->>CLSF: Generate Draft (Reasoning Model)
    CLSF-->>API: Drafted Text
    API-->>FE: Return Analysis Payload (Category, Draft)

    Citizen->>FE: Review, Edit & Submit
    FE->>API: POST /api/v1/complaints
    API->>DB: Store Complaint (status=Open)
    par Audit Logging
        API->>NDMC: Log Classification Audit
    and Auto-Assignment
        API->>ASSIGN: Attempt autoAssignGeo()
        ASSIGN->>DB: Update Complaint (Assigned/In Progress)
    and Notifications
        API->>NOTIFY: Emit Assignment Notification to Worker
    end
    API-->>FE: Success, Complaint ID
```
![Sequence Diagram](./images/sequence_diagram.png)

### 5.2.5 Activity Diagram
(Image Analysis & Triage Activity)

```mermaid
stateDiagram-v2
    [*] --> UploadImage
    UploadImage --> ValidateFormat
    ValidateFormat --> RunVisionCascade
    RunVisionCascade --> RuleEngineScoring
    
    state RuleEngineScoring {
        [*] --> ConfidenceCheck
        ConfidenceCheck --> HighConfidence: Confidence > AMBIGUITY_THRESHOLD
        ConfidenceCheck --> LowConfidence: Confidence <= AMBIGUITY_THRESHOLD
    }
    
    HighConfidence --> FinalizeCategory
    LowConfidence --> RunReasoningModel
    RunReasoningModel --> FinalizeCategory
    
    FinalizeCategory --> GenerateDraft
    GenerateDraft --> NDMC_Comparison_Audit
    NDMC_Comparison_Audit --> CitizenReview
    CitizenReview --> SubmitComplaint
    SubmitComplaint --> [*]
```
![Activity Diagram](./images/activity_diagram.png)

### 5.2.6 DFD Diagram (Data Flow Diagram - Context & Level 1)

#### Level 0 DFD (Context Diagram)

```mermaid
flowchart TD
    Citizen((Citizen))
    Worker((Worker))
    Admin((Admin))
    DeptHead((Department Head))
    
    System[0\nJan-Sunwai AI System]
    
    Citizen -->|Uploads Image & Submits Form| System
    System -->|Generated Draft & Status Updates| Citizen
    
    Worker -->|Resolves Complaints| System
    System -->|Assigned Tasks| Worker
    
    DeptHead -->|Escalations & Approvals| System
    System -->|Department Analytics| DeptHead
    
    Admin -->|Triage Operations & Configs| System
    System -->|Low-Confidence Queue| Admin
```

#### Level 1 DFD

```mermaid
---
config:
  layout: elk
---
flowchart TB
    Citizen(("Citizen")) -->|1. Image + metadata| P1["Process 1: Issue Analysis"]
    P1 -->|2. Image Hash + Text| Ollama(("Ollama AI Models"))
    Ollama -->|3. Category, Confidence, Draft| P1
    
    P1 -->|4. Review Payload| Citizen
    Citizen -->|5. Confirmed & Edited Details| P2["Process 2: Complaint Submission"]
    
    P2 -->|6. Save Complaint| DB[("Primary MongoDB: Complaints/Users")]
    P2 -->|7. Log Audit Data| NDMC[("NDMC Audit MongoDB")]
    
    DB -->|8. Fetch Open Issues & Geo| P3["Process 3: Worker Auto-Assignment"]
    P3 -->|9. Update Assigned Worker ID| DB
    P3 -->|10. Emit Notification| Notifications[("Notifications Collection")]
    
    Worker(("Worker")) -->|11. Fetch Tasks| P4["Process 4: Task Resolution"]
    DB -->|12. Task List| P4
    P4 -->|13. Add Dept Notes / Status Updates| DB
    
    DeptHead(("Dept Head")) -->|14. Approve Escalations / Reassign| P5["Process 5: Queue Management"]
    P5 -->|15. Update Status/Worker| DB
```
![DFD Level 1](./images/architecture.png)

### 5.2.7 Deployment Diagram

The system's infrastructure scales between local development and production via Docker Compose environment configurations (`APP_ENV=production` vs `local`), utilizing distinct `.env` loading and build profiles.

- **Production Environment (`Dockerfile.prod`)**: The React frontend is built statically and served via an Nginx container. The FastAPI backend runs via Uvicorn workers. MongoDB enforces strict authentication using Docker secrets.
- **Local Environment**: The frontend relies on the Vite development server with Hot Module Replacement (HMR). The backend runs Uvicorn with `--reload` enabled.

```mermaid
flowchart TD
    subgraph "Docker Host (Production / Local Environments)"
        subgraph Frontend_Container
            Nginx[Nginx HTTP Server]
            React[React/Vite Static Files]
            Nginx --> React
        end
        
        subgraph Backend_Container
            Uvicorn[Uvicorn / FastAPI]
            PyLogic[Routing & Queues]
            Uvicorn --> PyLogic
        end
        
        subgraph Database_Containers
            MongoDB[(Primary MongoDB)]
            NDMCDB[(Audit MongoDB)]
        end
        
        subgraph AI_Container
            Ollama[Ollama Server]
        end
    end

    subgraph "External Services"
        NDMC_API[NDMC AI API]
    end
    
    ClientBrowser[Client Browser] -->|HTTPS| Frontend_Container
    ClientBrowser -->|API/REST| Backend_Container
    
    Backend_Container -->|Python Motor| Database_Containers
    Backend_Container -->|HTTP/REST| AI_Container
    Backend_Container -->|HTTP/REST| NDMC_API
```
![Deployment Diagram](./images/deployment_diagram.png)

## 5.3 Database Design

### Database Schema & Indexing Architecture

Because Jan-Sunwai AI uses **MongoDB** (a NoSQL document database), strict relational mapping is replaced by references and embedding. The diagram below illustrates how collections interlock, where data is embedded for read-performance, and which fields are heavily indexed:

```mermaid
classDiagram
    class Users_Collection {
        +ObjectId _id [PK]
        +String username [Unique Index]
        +String email [Unique Index]
        +String role
        +String department
        +String worker_status
        +Object service_area
        +Boolean is_approved
    }
    class Complaints_Collection {
        +ObjectId _id [PK]
        +ObjectId user_id [Reference]
        +ObjectId assigned_to [Reference]
        +String department [Text Index]
        +String description [Text Index]
        +String status [Compound Index]
        +DateTime created_at [Compound Index]
        +Object location [2dsphere Geospatial Index]
        +List status_history [Embedded]
        +List dept_notes [Embedded]
        +List comments [Embedded]
    }
    class Notifications_Collection {
        +ObjectId _id [PK]
        +ObjectId user_id [Reference]
        +String type
        +String title
        +String message
        +Boolean is_read
    }
    
    Users_Collection <-- Complaints_Collection : References
    Users_Collection <-- Notifications_Collection : References
```

### 5.3.1 Collection Design and Relationships
Because Jan-Sunwai AI uses **MongoDB** (a NoSQL document database), "Tables" map to **Collections** and "Rows" map to **Documents**. 
- **Users Collection**: Core identity and role metadata. Citizens, Workers, Dept Heads, and Admins are all stored here.
- **Complaints Collection**: The central entity linking `user_id`, `department`, and `assigned_to` (worker). Contains nested structures for `location` (GeoJSON), `status_history`, `dept_notes`, and `comments`.
- **Notifications Collection**: Tracks alerts for status changes, assignments, and escalations.
- **Audit Logs (NDMC MongoDB)**: A secondary database used for recording AI classification agreement between local models and NDMC's API.

### 5.3.2 Normalization
Instead of strict 3NF (Third Normal Form) typical of Relational DBs, MongoDB relies on a hybrid approach:
- **References (Normalization)**: `user_id` and `worker_id` are kept as `ObjectId` references within `Complaint` documents to ensure updates to user names/roles propagate easily.
- **Embedding (Denormalization)**: Timestamps, small arrays like `status_history`, and coordinates are embedded directly in the `Complaint` document for extremely fast read-query performance during dashboard rendering.

### 5.3.3 Indexing Strategy
To meet the high-performance demands of location-based sorting and massive audit queues:
1. **Geospatial Index**: `2dsphere` index on `location.coordinates` in the Complaints collection for fast auto-assignment querying (e.g., "$near" queries).
2. **Compound Index**: `{ status: 1, created_at: -1 }` on Complaints to optimize the heavy load of dashboard rendering where Dept Heads and Workers view recent active issues.
3. **Unique Index**: `{ email: 1 }` and `{ username: 1 }` on Users collection to enforce constraint uniqueness natively.
4. **Text Index**: Free-text index on the `draft` and `category` fields to support Admin full-text searches.

### 5.3.4 Data Dictionary

#### **Users Collection (`users`)**
| Field Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Unique identifier for the user. |
| `username` | String | Unique, Min 3, Max 50 | The user's login name. |
| `email` | String | Unique, Valid Email | The user's contact email. |
| `password_hash` | String | Required | Bcrypt hashed password. |
| `full_name` | String | Max 100 | The user's full display name. |
| `phone_number` | String | Max 20 | Contact number. |
| `role` | Enum | citizen, dept_head, admin, worker | Defines RBAC permissions. |
| `department` | String | Optional | The department assignment for Dept Heads and Workers. |
| `worker_status` | Enum | available, busy, offline | Status indicating if a worker can take new assignments. |
| `service_area` | Object | Optional | Geospatial data (`lat`, `lon`, `radius_km`) defining a worker's operational range. |
| `is_approved` | Boolean | Default: True | False for pending worker registrations until Admin approval. |

#### **Complaints Collection (`complaints`)**
| Field Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Unique identifier for the complaint. |
| `user_id` | ObjectId | Foreign Key (users) | The citizen who filed the grievance. |
| `assigned_to` | ObjectId | Foreign Key (users) | The worker currently assigned to the issue. |
| `department` | String | Required | The assigned civic department (e.g., Civil, Health). |
| `description` | String | Min 10 chars | The AI-generated or user-edited description of the issue. |
| `user_grievance_text` | String | Max 1200 | Optional original text provided by the citizen. |
| `image_url` | String | Required | Path/URL to the uploaded evidentiary photo. |
| `location` | Object | Required | `GeoLocation` containing `lat`, `lon`, `address`, and `source` (exif/device/manual). |
| `ai_metadata` | Object | Required | AI analysis results including `confidence_score` and `detected_department`. |
| `priority` | Enum | Low, Medium, High, Critical | System-assigned urgency level. |
| `status` | Enum | Open, In Progress, Resolved, Rejected | Current state of the grievance lifecycle. |
| `created_at` | DateTime | Auto-generated | UTC timestamp of submission. |
| `status_history` | Array | Embedded Docs | Audit trail of all status changes with timestamps and user IDs. |

#### **Notifications Collection (`notifications`)**
| Field Name | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Unique notification identifier. |
| `user_id` | ObjectId | Foreign Key (users) | Recipient of the notification. |
| `complaint_id` | ObjectId | Foreign Key (complaints) | Associated complaint. |
| `type` | Enum | status_change, escalation, assignment, system | Category of the alert. |
| `title` | String | Required | Short summary. |
| `message` | String | Required | Full notification body. |
| `is_read` | Boolean | Default: False | Read status for the UI badge. |
| `created_at` | DateTime | Auto-generated | UTC timestamp. |

## 5.4 GUI Design

The Jan-Sunwai AI user interface is a responsive Single Page Application (SPA) built with React. It is divided into distinct role-based experiences.

### 5.4.1 Interface Areas and Purpose

- **Citizen Portal**: Focuses on frictionless complaint filing. Includes the Image Upload wizard, AI Draft Review, and a personal Status Tracker.
- **Worker Dashboard**: Optimized for mobile usage. Shows a map/list of assigned tasks, allows status updates, and uploading proof of resolution.
- **Department Head View**: A queue management interface allowing re-assignment, priority adjustment, and viewing department-specific analytics.
- **Admin Dashboard**: The overarching control center. Features a high-level analytics overview, the Triage Queue for low-confidence AI routing, and User Management.

### 5.4.2 Visual References

*The following are references to the actual implementation screenshots located in the `docs/images/` directory:*

1. **Citizen Experience**:
   - *Home Page / Filing*: `![Citizen Homepage](./images/citizen_homepage.png)`
   - *Reviewing AI Analysis*: `![AI Analysis Result](./images/complaint_review_with_geo_tag.png)`
   - *Tracking Dashboard*: `![Tracking Dashboard](./images/grievance_status_tracker.png)`

2. **Admin & Department Management**:
   - *Admin Dashboard Overview*: `![Admin Dashboard](./images/admin_dashboard.png)`
   - *Triage Queue (Low Confidence)*: `![Admin Triage Queue](./images/admin_human_complaint_review_pannel.png)`
   - *Analytics & Heatmap*: `![Grievance Heatmap](./images/grievance_heatmap.png)`

3. **System Wide**:
   - *Login & Registration*: `![Login Page](./images/login_page.png)`
   - *Map Visualization*: `![Complaints Map](./images/complaints_map.png)`