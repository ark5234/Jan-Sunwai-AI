# Jan-Sunwai AI — System Diagrams

---

## 4.1 Proposed End-to-End Workflow

```mermaid
flowchart TD
    A([Citizen Uploads Image]) --> B

    subgraph INTAKE ["Intake and Perception"]
        B[Image Received by System]
    end

    B --> C

    subgraph AI_ENRICH ["AI Enrichment - Parallel"]
        C{Trigger AI Pipeline}
        C --> D[Vision Model\nExtract Features and Category]
        C --> E[Rule Engine\nAssign Department]
        C --> F[Reasoning Model\nDraft Complaint Text]
    end

    D & E & F --> G

    subgraph HUMAN ["Human Verification"]
        G[Present AI Suggestions to Citizen]
        G --> H{Citizen Reviews}
        H -->|Approves| I[Confirmed Submission]
        H -->|Edits and Approves| I
    end

    I --> J

    subgraph OPS ["Operational Routing"]
        J[Complaint Enters Departmental Queue]
        J --> K{AI Confidence Level}
        K -->|High Confidence| L[Auto-Assign to Worker]
        K -->|Low Confidence| M[Admin Triage]
        M --> L
    end

    L --> N

    subgraph CLOSURE ["Closure"]
        N[Worker Executes Field Task]
        N --> O[Mark Complaint as Resolved]
        O --> P([Notify Citizen])
    end

    
```

---

## 5.1 Overall System Context Diagram

```mermaid
flowchart TB
    Citizen(["Citizen\nIntake and Tracking"])
    Worker(["Worker\nTask Fulfillment"])
    Admin(["Admin / Dept Head\nSupervisory Control"])

    subgraph JAN_SUNWAI ["Jan-Sunwai AI Platform"]
        direction TB
        Frontend["React Frontend\nNginx"]
        Backend["FastAPI Backend\nCentral Orchestrator"]
    end

    subgraph EXTERNAL ["External and Local Services"]
        Ollama["Ollama Model Runtime\nLocal Inference"]
        MongoDB[("MongoDB\nState Persistence")]
        FS[("Filesystem\nImage Storage")]
    end

    Citizen -->|"Upload Image / Track Complaint"| Frontend
    Worker -->|"View Tasks / Update Status"| Frontend
    Admin -->|"Triage / Approve Workers"| Frontend
    Frontend -->|"REST API Calls"| Backend
    Backend -->|"Inference Requests"| Ollama
    Ollama -->|"Model Responses"| Backend
    Backend -->|"Read / Write Records"| MongoDB
    Backend -->|"Store / Retrieve Images"| FS

   
```

---

## 5.2 AI Pipeline and Classification Flow

```mermaid
flowchart TD
    A([Image Received]) --> B["Vision-Language Model\nVLM Analysis"]
    B --> C{Confidence Gate}

    C -->|">= 0.7 High Confidence"| D["Auto-Route to Department"]
    C -->|"< 0.7 Below Threshold"| E

    subgraph REASONING ["Reasoning Fallback"]
        E["Secondary Reasoning Check\nLlama 3.2"]
        E --> F{Reasoning Confidence}
        F -->|"Sufficient"| D
        F -->|"Still Ambiguous"| G["Administrative\nTriage Queue"]
    end

    G --> H["Admin Manual\nDepartment Assignment"]
    H --> I(["Complaint Created and Auto-Assigned"])
    D --> I

    
```

---

## 5.3 E-R Diagram

```mermaid
erDiagram
    USER {
        string id PK
        string name
        string email
        string role
        string phone
        string department_id FK
        boolean is_active
    }

    COMPLAINT {
        string id PK
        string title
        string description
        string category
        string status
        float geo_latitude
        float geo_longitude
        string geo_address
        float ai_confidence
        string ai_model_id
        string ai_suggested_category
        string ai_suggested_department
        string filed_by FK
        string assigned_to FK
        string department_id FK
        datetime created_at
        datetime updated_at
    }

    DEPARTMENT {
        string id PK
        string name
        string escalation_parent FK
        string service_areas
    }

    STATUS_HISTORY {
        string id PK
        string complaint_id FK
        string status
        string note
        string changed_by FK
        datetime timestamp
    }

    NOTIFICATION {
        string id PK
        string user_id FK
        string complaint_id FK
        string message
        boolean read
        datetime created_at
    }

    USER ||--o{ COMPLAINT : files
    USER ||--o{ COMPLAINT : "assigned to"
    DEPARTMENT ||--o{ COMPLAINT : handles
    COMPLAINT ||--|{ STATUS_HISTORY : has
    USER ||--o{ NOTIFICATION : receives
    COMPLAINT ||--o{ NOTIFICATION : triggers
```

---

## 5.5 Use Case Diagram (System Flow)

```mermaid
flowchart LR
    Citizen(["Citizen"])
    Worker(["Worker"])
    Admin(["Admin / Dept Head"])

    subgraph RBAC ["Jan-Sunwai AI - Role-Based Access Control"]
        subgraph CITIZEN_UC ["Citizen Use Cases"]
            UC1["Submit Complaint\nUpload Image and Details"]
            UC2["Track Complaint Status"]
            UC3["Review and Confirm AI Suggestions"]
        end

        subgraph WORKER_UC ["Worker Use Cases"]
            UC4["View Assigned Tasks"]
            UC5["Accept or Reject Assignment"]
            UC6["Execute Field Task"]
            UC7["Mark Complaint Resolved"]
        end

        subgraph ADMIN_UC ["Admin Use Cases"]
            UC8["Triage Ambiguous Complaints"]
            UC9["Approve and Manage Workers"]
            UC10["View Department Dashboard"]
            UC11["Escalate to Higher Authority"]
        end
    end

    Citizen --> UC1
    Citizen --> UC2
    Citizen --> UC3

    Worker --> UC4
    Worker --> UC5
    Worker --> UC6
    Worker --> UC7

    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11

    
```

---

## 5.6 Class Diagram

```mermaid
classDiagram
    class User {
        +String id
        +String name
        +String email
        +String role
        +String phone
        +String department_id
        +Boolean is_active
        +login() void
        +logout() void
        +updateProfile() void
    }

    class Complaint {
        +String id
        +String title
        +String description
        +String category
        +String status
        +GeoLocation location
        +AIMetadata ai_metadata
        +StatusHistory[] history
        +String filed_by
        +String assigned_to
        +String department_id
        +DateTime created_at
        +submit() void
        +updateStatus(status, note) void
        +assignWorker(worker_id) void
    }

    class GeoLocation {
        +Float latitude
        +Float longitude
        +String address
    }

    class AIMetadata {
        +Float confidence
        +String model_id
        +String suggested_category
        +String suggested_department
        +String drafted_description
    }

    class StatusHistory {
        +String status
        +String note
        +String changed_by
        +DateTime timestamp
    }

    class Department {
        +String id
        +String name
        +String escalation_parent
        +String[] service_areas
        +escalate(complaint_id) void
    }

    class Notification {
        +String id
        +String user_id
        +String complaint_id
        +String message
        +Boolean read
        +DateTime created_at
        +markRead() void
        +send() void
    }

    Complaint "1" *-- "1" GeoLocation : contains
    Complaint "1" *-- "1" AIMetadata : contains
    Complaint "1" *-- "*" StatusHistory : embeds
    User "1" --> "*" Complaint : files
    User "1" --> "*" Complaint : assignedTo
    Department "1" --> "*" Complaint : handles
    Department "1" --> "0..1" Department : escalatesTo
    Notification "*" ..> "1" User : observes
    Notification "*" ..> "1" Complaint : observes
```

---

## 5.7 Sequence Diagram

```mermaid
sequenceDiagram
    actor Citizen
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant AI as Ollama AI Engine
    participant DB as MongoDB

    Citizen->>FE: Upload image and details
    FE->>BE: POST /complaints/analyze
    BE->>DB: Create complaint record - status PROCESSING
    DB-->>BE: complaint_id
    BE-->>FE: 202 Accepted with complaint_id
    BE->>AI: Send image for inference
    Note over BE,AI: Non-blocking - GPU inference begins

    loop Poll every 3 seconds
        FE->>BE: GET /complaints/id/status
        BE->>DB: Fetch complaint status
        DB-->>BE: status PROCESSING
        BE-->>FE: status PROCESSING
    end

    AI-->>BE: category, confidence, description, department
    BE->>DB: Update complaint with AI metadata - status READY
    FE->>BE: GET /complaints/id/status
    BE-->>FE: status READY with ai_suggestions
    FE-->>Citizen: Display AI suggestions for review
    Citizen->>FE: Confirm or edit and submit
    FE->>BE: POST /complaints/id/submit
    BE->>DB: Finalize complaint - status SUBMITTED
    BE->>BE: Trigger Worker Assignment Engine
    DB-->>BE: OK
    BE-->>FE: 200 OK
    FE-->>Citizen: Complaint submitted successfully
```

---

## 5.8 Activity Diagram — Worker Assignment Engine

```mermaid
flowchart TD
    A([Complaint Submitted]) --> B[Start Worker Search]
    B --> C{Any Workers\nAvailable?}
    C -->|None Found| D[Flag as Unassigned]
    C -->|Check Next Worker| E{Worker Online?}
    E -->|No| C
    E -->|Yes| F{Department Match?}
    F -->|No| C
    F -->|Yes| G{In Service Area?}
    G -->|No| C
    G -->|Yes| H[Assign to Worker]
    D --> I[Admin Review Queue]
    I --> J[Admin Manual Assignment]
    H --> K[Notify Worker]
    J --> K
    K --> L{Worker Accepts?}
    L -->|No or Timeout| B
    L -->|Yes| M[Status: IN PROGRESS]
    M --> N[Execute Field Task]
    N --> O[Mark as RESOLVED]
    O --> P([Notify Citizen])

    
```

---

## 5.9 Data Flow Diagram (DFD)

```mermaid
flowchart LR
    Citizen(["Citizen"])
    Admin(["Admin"])
    Worker(["Worker"])

    subgraph PROCESSES ["Core Processes"]
        P1["1. Validate Input\nFormat and Auth Check"]
        P2["2. AI Transformation\nClassify and Enrich"]
        P3["3. Routing Process\nAssign and Triage"]
        P4["4. Notification Process\nGenerate Alerts"]
        P5["5. Auth Process\nToken Hashing"]
    end

    subgraph STORES ["Data Stores"]
        DB[("MongoDB")]
        FS[("Filesystem\nImages")]
    end

    Citizen -->|"Raw Image and Details"| P1
    P1 -->|"Invalid - Rejected"| Citizen
    P1 -->|"Validated Input"| P2
    P2 -->|"Structured Complaint Record"| DB
    P2 -->|"Image File"| FS
    Admin -->|"Manual Triage Decision"| P3
    P3 -->|"Assignment Update"| DB
    DB -->|"Complaint State Change"| P4
    P4 -->|"Citizen Alert"| Citizen
    P4 -->|"Task Alert"| Worker
    Worker -->|"Status Update"| P3
    Citizen -->|"Reset Request"| P5
    P5 -->|"Hashed Reset Token"| DB

    
```

---

## 5.10 Deployment Diagram

```mermaid
flowchart TB
    Browser(["Browser / Mobile Client"])

    subgraph DOCKER ["Docker Compose Network"]
        Nginx["Nginx Web Server"]
        ReactBuild["React App - Static Build"]
        Uvicorn["Uvicorn ASGI Server"]
        FastAPI["FastAPI Application"]
        MongoDB[("MongoDB Database")]
    end

    subgraph HOST ["Host Machine - Outside Docker"]
        Ollama["Ollama Model Runtime"]
        GPU["GPU Resources"]
    end

    Browser -->|"HTTPS"| Nginx
    Nginx --> ReactBuild
    ReactBuild -->|"REST API"| FastAPI
    Uvicorn --> FastAPI
    FastAPI -->|"Mongoose ODM"| MongoDB
    FastAPI -->|"HTTP Bridge\nhost.docker.internal"| Ollama
    Ollama --> GPU

    
```