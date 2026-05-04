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
    A[Image Upload] --> B[Storage Validation + Save]
    B --> C[Vision Model Cascade]
    C --> D[Rule Engine Scoring]
    D --> E{Ambiguous?}
    E -->|No| F[Category Finalized]
    E -->|Yes| G[Reasoning Model]
    G --> F
    F --> H[Queue Draft Generation]
    H --> I[Formal Complaint Draft]
    I --> J[Citizen Review + Submit]
    J --> K[Complaint Saved + Routed]
```

## 5.2 UML Diagrams

### 5.2.1 E-R Diagram (Entity-Relationship)

```mermaid
erDiagram
    USER ||--o{ COMPLAINT : creates
    WORKER ||--o{ COMPLAINT : assigned_to
    DEPARTMENT ||--o{ WORKER : employs
    DEPARTMENT ||--o{ COMPLAINT : handles
    COMPLAINT ||--o{ NOTIFICATION : triggers
    
    USER {
        ObjectId _id PK
        string username
        string email
        string password_hash
        string role
    }
    
    WORKER {
        ObjectId _id PK
        ObjectId user_id FK
        ObjectId department_id FK
        object service_area
        boolean is_active
    }
    
    COMPLAINT {
        ObjectId _id PK
        ObjectId user_id FK
        ObjectId assigned_worker_id FK
        string category
        float confidence
        string draft
        string status
        object location
        datetime created_at
    }
    
    DEPARTMENT {
        ObjectId _id PK
        string name
        ObjectId head_user_id FK
    }
```

### 5.2.2 Use Case Diagram

```mermaid
usecaseDiagram
    actor Citizen
    actor Worker
    actor DeptHead as "Department Head"
    actor Admin
    
    Citizen --> (Upload Issue Photo)
    Citizen --> (Review Generated Draft)
    Citizen --> (Track Complaint Status)
    
    Worker --> (View Assigned Tasks)
    Worker --> (Resolve Complaints)
    Worker --> (Update Status)
    
    DeptHead --> (Monitor Department Queue)
    DeptHead --> (Handle Escalations)
    DeptHead --> (View Analytics)
    
    Admin --> (Manage Users & Roles)
    Admin --> (Triage Low-Confidence Issues)
    Admin --> (System Configurations)
    
    (Upload Issue Photo) ..> (AI Classification) : <<includes>>
```
*(Note: Mermaid flowchart can also depict use case functionality if actual Use Case UML is not fully supported in your renderer, standard UML boundaries apply)*

### 5.2.3 Class Diagram

```mermaid
classDiagram
    class User {
        +ObjectId id
        +String username
        +String email
        +String role
        +login()
        +register()
    }
    class Complaint {
        +ObjectId id
        +ObjectId userId
        +String category
        +String status
        +Location loc
        +String draftText
        +submit()
        +updateStatus()
        +assignWorker()
    }
    class WorkerInfo {
        +ObjectId departmentId
        +GeoJSON serviceArea
        +Boolean isActive
        +getAssignedComplaints()
    }
    class AIPipeline {
        +runVision(image)
        +analyzeRules(visionOutput)
        +generateDraft(category)
    }
    
    User "1" -- "many" Complaint : files
    WorkerInfo "1" -- "many" Complaint : handles
    User <|-- WorkerInfo : extends via relation
    Complaint --> AIPipeline : uses for triage
```

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

### 5.2.6 DFD Diagram (Data Flow Diagram - Level 1)

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
    
    Client Browser -->|HTTPS| Frontend_Container
    Client Browser -->|API/REST| Backend_Container
    
    Backend_Container -->|Python Motor| Database_Containers
    Backend_Container -->|HTTP/REST| AI_Container
```

## 5.3 Database Design

### 5.3.1 Table Design and Relationships
Because Jan-Sunwai AI uses **MongoDB** (a NoSQL document database), "Tables" map to **Collections** and "Rows" map to **Documents**. 
- **Users Collection**: Core user identity.
- **Workers Collection**: Operational metadata for worker roles linking back to ``user_id``.
- **Complaints Collection**: The central entity linking `user_id`, `category`, and `worker_id`. Contains nested structures for `location` (GeoJSON) and arrays for `status_history`.
- **Departments Collection**: Organizational divisions linking to `head_user_id`.

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