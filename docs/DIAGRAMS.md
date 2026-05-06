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
    USER ||--o{ COMPLAINT : "creates / handles (if worker)"
    COMPLAINT ||--o{ NOTIFICATION : triggers
    
    USER {
        ObjectId _id PK
        string username
        string email
        string password_hash
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
        string department
        float confidence
        string description
        string status
        object location
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
    
    Worker --> UC4([View Assigned Tasks])
    Worker --> UC5([Resolve Complaints])
    Worker --> UC6([Update Status])
    
    DeptHead --> UC7([Monitor Department Queue])
    DeptHead --> UC8([Handle Escalations])
    DeptHead --> UC9([View Analytics])
    
    Admin --> UC10([Manage Users & Roles])
    Admin --> UC11([Triage Low-Confidence Issues])
    Admin --> UC12([System Configurations])
    
    UC1 -.->|includes| UC13([AI Classification])
```
![Use Case Diagram](./images/flowchart.png)
*(Note: Mermaid flowchart can also depict use case functionality if actual Use Case UML is not fully supported in your renderer, standard UML boundaries apply)*

### 5.2.3 Class Diagram

```mermaid
classDiagram
    class UserRouter {
        +register()
        +login()
        +updateProfile()
    }
    class ComplaintRouter {
        +analyze()
        +create()
        +updateStatus()
        +escalate()
    }
    class WorkerRouter {
        +updateStatus()
        +markDone()
        +assignTask()
    }
    class AIPipelineService {
        +runVisionCascade()
        +runRuleEngine()
        +runReasoning()
        +generateDraft()
    }
    class AssignmentService {
        +autoAssign()
        +freeSlot()
    }
    
    ComplaintRouter --> AIPipelineService : uses
    ComplaintRouter --> AssignmentService : triggers
    WorkerRouter --> AssignmentService : uses
```
![Class Diagram](./images/class_diagram.png)

### 5.2.4 Sequence Diagram
(Complaint Lifecycle Sequence)

```mermaid
sequenceDiagram
    actor Citizen
    participant FE as Frontend (React)
    participant API as FastAPI Backend
    participant AI as AI Engine (Ollama)
    participant DB as MongoDB
    participant ASSIGN as Assignment Service

    Citizen->>FE: Upload image + Details
    FE->>API: POST /api/v1/analyze
    API->>AI: classify + draft
    AI-->>API: category + confidence + draft text
    API-->>FE: Return analysis payload

    Citizen->>FE: Review & confirm submission
    FE->>API: POST /api/v1/complaints
    API->>DB: Store complaint (status=Open)
    API->>ASSIGN: Trigger auto_assign()
    ASSIGN->>DB: Update complaint to (Assigned/In Progress)
    API-->>FE: Success, Complaint ID
```
![Sequence Diagram](./images/sequence_diagram.png)

### 5.2.5 Activity Diagram
(Image Analysis & Triage Activity)

```mermaid
stateDiagram-v2
    [*] --> UploadImage
    UploadImage --> ValidateFormat
    ValidateFormat --> RunVisionModel
    RunVisionModel --> ExtractFeatures
    ExtractFeatures --> RuleScoring
    
    state RuleScoring {
        [*] --> ConfidenceCheck
        ConfidenceCheck --> HighConfidence: > 0.8
        ConfidenceCheck --> LowConfidence: <= 0.8
    }
    
    HighConfidence --> GenerateDraft
    LowConfidence --> RunReasoningModel
    RunReasoningModel --> GenerateDraft
    
    GenerateDraft --> CitizenReview
    CitizenReview --> [*]
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
flowchart TD
    Citizen((Citizen)) -->|Image + metadata| P1[Process 1: Issue Analysis]
    P1 -->|Image Hash + Text| Ollama((Ollama Models))
    Ollama -->|Category + Confidence| P1
    
    P1 -->|Draft + Category| Citizen
    Citizen -->|Confirmed Details| P2[Process 2: Complaint Submission]
    
    P2 -->|Save Complaint| DB[(MongoDB: Complaints)]
    P2 -->|User ID| DB2[(MongoDB: Users)]
    
    DB -->|Fetch Open Issues| P3[Process 3: Worker Auto-Assignment]
    P3 -->|Update Worker ID| DB
    
    Worker((Worker)) -->|Fetch Tasks| P4[Process 4: Task Resolution]
    DB -->|Task List| P4
    P4 -->|Status Updates| DB
```
![DFD Level 1](./images/architecture.png)

### 5.2.7 Deployment Diagram

```mermaid
flowchart TD
    subgraph "Docker Host (Production / Local)"
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