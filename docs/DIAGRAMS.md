# Jan-Sunwai AI — System Diagrams

---

## 4.1 Proposed End-to-End Workflow

```mermaid
flowchart TD
    A([🧑 Citizen Uploads Image]) --> B

    subgraph INTAKE ["① Intake & Perception"]
        B[Image Received by System]
    end

    B --> C

    subgraph AI_ENRICH ["② AI Enrichment (Parallel)"]
        C{Trigger AI Pipeline}
        C --> D[🔍 Vision Model\nExtract Features & Category]
        C --> E[📋 Rule Engine\nAssign Department]
        C --> F[✍️ Reasoning Model\nDraft Complaint Text]
    end

    D & E & F --> G

    subgraph HUMAN ["③ Human Verification"]
        G[Present AI Suggestions to Citizen]
        G --> H{Citizen Reviews}
        H -->|Approves| I[Confirmed Submission]
        H -->|Edits & Approves| I
    end

    I --> J

    subgraph OPS ["④ Operational Routing"]
        J[Complaint Enters Departmental Queue]
        J --> K{AI Confidence Level}
        K -->|High Confidence| L[Auto-Assign to Worker]
        K -->|Low Confidence| M[🛑 Admin Triage]
        M --> L
    end

    L --> N

    subgraph CLOSURE ["⑤ Closure"]
        N[Worker Executes Field Task]
        N --> O[Mark Complaint as Resolved]
        O --> P([📲 Notify Citizen])
    end

    style INTAKE fill:#dbeafe,stroke:#3b82f6
    style AI_ENRICH fill:#ede9fe,stroke:#8b5cf6
    style HUMAN fill:#fef9c3,stroke:#ca8a04
    style OPS fill:#fee2e2,stroke:#ef4444
    style CLOSURE fill:#dcfce7,stroke:#16a34a
```

---

## 5.1 Overall System Context Diagram

```mermaid
flowchart TB
    Citizen(["🧑 Citizen\n(Intake & Tracking)"])
    Worker(["🔧 Worker\n(Task Fulfillment)"])
    Admin(["🛡️ Dept Head / Admin\n(Supervisory Control)"])

    subgraph JAN_SUNWAI ["Jan-Sunwai AI Platform"]
        direction TB
        Frontend["⚛️ React Frontend\n(Nginx)"]
        Backend["⚙️ FastAPI Backend\n(Central Orchestrator)"]
    end

    subgraph EXTERNAL ["External / Local Services"]
        Ollama["🤖 Ollama Model Runtime\n(Local Inference)"]
        MongoDB[("🗄️ MongoDB\n(State Persistence)")]
        FS[("📁 Filesystem\n(Image Storage)")]
    end

    Citizen -->|"Upload Image / Track Complaint"| Frontend
    Worker -->|"View Tasks / Update Status"| Frontend
    Admin -->|"Triage / Approve Workers"| Frontend

    Frontend -->|"REST API Calls"| Backend

    Backend -->|"Inference Requests"| Ollama
    Ollama -->|"Model Responses"| Backend

    Backend -->|"Read / Write Records"| MongoDB
    Backend -->|"Store / Retrieve Images"| FS

    style JAN_SUNWAI fill:#eff6ff,stroke:#2563eb,stroke-width:2px
    style EXTERNAL fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
```

---

## 5.2 AI Pipeline and Classification Flow

```mermaid
flowchart TD
    A([📷 Image Received]) --> B["🔎 Vision-Language Model\nVLM Analysis"]
    B --> C{Confidence Gate}

    C -->|">= 0.7\nHigh Confidence"| D["✅ Auto-Route\nto Department"]
    C -->|"< 0.7\nBelow AMBIGUITY_THRESHOLD"| E

    subgraph REASONING ["Reasoning Fallback"]
        E["🧠 Secondary Reasoning Check\n(e.g. Llama 3.2)"]
        E --> F{Reasoning Confidence}
        F -->|"Sufficient"| D
        F -->|"Still Ambiguous"| G["🛑 Administrative\nTriage Queue"]
    end

    G --> H["👤 Admin Manual\nDepartment Assignment"]
    H --> I

    D --> I(["📝 Complaint Created\n& Auto-Assigned"])

    style REASONING fill:#fdf4ff,stroke:#a855f7,stroke-width:1.5px
    style C fill:#fef3c7,stroke:#d97706
    style F fill:#fef3c7,stroke:#d97706
    style G fill:#fee2e2,stroke:#ef4444
    style D fill:#dcfce7,stroke:#16a34a
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
        string[] service_areas
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

    USER ||--o{ COMPLAINT : "files"
    USER ||--o{ COMPLAINT : "assigned to"
    DEPARTMENT ||--o{ COMPLAINT : "handles"
    DEPARTMENT ||--o| DEPARTMENT : "escalates to"
    COMPLAINT ||--|{ STATUS_HISTORY : "has (embedded)"
    USER ||--o{ NOTIFICATION : "receives"
    COMPLAINT ||--o{ NOTIFICATION : "triggers"
```

---

## 5.5 Use Case Diagram (System Flow)

```mermaid
flowchart LR
    Citizen(["🧑 Citizen"])
    Worker(["🔧 Worker"])
    Admin(["🛡️ Admin / Dept Head"])

    subgraph RBAC ["Jan-Sunwai AI — Role-Based Access Control"]
        subgraph CITIZEN_UC ["Citizen Use Cases"]
            UC1["📤 Submit Complaint\n(Upload Image + Details)"]
            UC2["🔍 Track Complaint Status"]
            UC3["✅ Review & Confirm AI Suggestions"]
        end

        subgraph WORKER_UC ["Worker Use Cases"]
            UC4["📋 View Assigned Tasks"]
            UC5["✔️ Accept / Reject Assignment"]
            UC6["🔧 Execute Field Task"]
            UC7["📌 Mark Complaint Resolved"]
        end

        subgraph ADMIN_UC ["Admin Use Cases"]
            UC8["🛑 Triage Ambiguous Complaints"]
            UC9["👤 Approve / Manage Workers"]
            UC10["📊 View Department Dashboard"]
            UC11["↗️ Escalate to Higher Authority"]
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

    style CITIZEN_UC fill:#dbeafe,stroke:#3b82f6
    style WORKER_UC fill:#dcfce7,stroke:#16a34a
    style ADMIN_UC fill:#fee2e2,stroke:#ef4444
    style RBAC fill:#f8fafc,stroke:#64748b,stroke-width:2px
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
        +List~StatusHistory~ history
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
        +List~String~ service_areas
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
    User "1" --> "*" Complaint : assigned to
    Department "1" --> "*" Complaint : handles
    Department "1" --> "0..1" Department : escalates to
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

    Citizen->>FE: Upload image + details

    FE->>BE: POST /complaints/analyze (multipart image)
    BE->>DB: Create complaint record (status: PROCESSING)
    DB-->>BE: complaint_id
    BE-->>FE: 202 Accepted { complaint_id }

    BE-)AI: Async inference request (image)
    Note over BE,AI: Non-blocking — GPU inference begins

    loop Async Polling (every 3s)
        FE->>BE: GET /complaints/{id}/status
        BE->>DB: Fetch complaint status
        DB-->>BE: { status: "PROCESSING" }
        BE-->>FE: { status: "PROCESSING" }
    end

    AI--)BE: { category, confidence, description, department }
    BE->>DB: Update complaint with AI metadata (status: READY)

    FE->>BE: GET /complaints/{id}/status
    BE-->>FE: { status: "READY", ai_suggestions: { ... } }
    FE-->>Citizen: Display AI suggestions for review

    Citizen->>FE: Review → Confirm / Edit & Submit
    FE->>BE: POST /complaints/{id}/submit { confirmed_data }
    BE->>DB: Finalize complaint (status: SUBMITTED)
    BE->>BE: Trigger Worker Assignment Engine
    DB-->>BE: OK
    BE-->>FE: 200 OK
    FE-->>Citizen: ✅ Complaint submitted successfully
```

---

## 5.8 Activity Diagram — Worker Assignment Engine

```mermaid
flowchart TD
    START([▶ New Complaint Submitted]) --> POOL[Fetch Available Worker Pool]

    POOL --> ONLINE{Is Worker Online?}
    ONLINE -->|No| POOL
    ONLINE -->|Yes| DEPT{Department Match?}

    DEPT -->|No| POOL
    DEPT -->|Yes| GEO{Location within\nService Area?}

    GEO -->|No| POOL
    GEO -->|Yes| ASSIGN[Assign Complaint to Worker]

    POOL -->|"No Suitable Worker Found\n(Pool Exhausted)"| UNASSIGNED

    ASSIGN --> NOTIFY[Notify Worker via Push Alert]
    NOTIFY --> ACCEPT{Worker Accepts?}

    ACCEPT -->|"No / Timeout"| POOL
    ACCEPT -->|Yes| INPROG[Status → IN PROGRESS]

    INPROG --> FIELD[Worker Executes Field Task]
    FIELD --> RESOLVE[Mark Complaint as RESOLVED]
    RESOLVE --> END([🔔 Notify Citizen — End])

    UNASSIGNED[🚩 Flag as Unassigned] --> ADMIN[Send to Admin Review Queue]
    ADMIN --> MANUAL[Admin Manually Assigns Worker]
    MANUAL --> NOTIFY

    style UNASSIGNED fill:#fee2e2,stroke:#ef4444
    style ADMIN fill:#fef3c7,stroke:#d97706
    style RESOLVE fill:#dcfce7,stroke:#16a34a
    style INPROG fill:#dbeafe,stroke:#3b82f6
```

---

## 5.9 Data Flow Diagram (DFD)

```mermaid
flowchart LR
    Citizen(["🧑 Citizen"])
    Admin(["🛡️ Admin"])
    Worker(["🔧 Worker"])

    subgraph PROCESSES ["Core Processes"]
        P1["① Validate Input\n(Format / Auth check)"]
        P2["② AI Transformation\n(Classify & Enrich)"]
        P3["③ Routing Process\n(Assign & Triage)"]
        P4["④ Notification Process\n(Generate Alerts)"]
        P5["⑤ Auth Process\n(Token Hashing)"]
    end

    subgraph STORES ["Data Stores"]
        DB[("🗄️ MongoDB")]
        FS[("📁 Filesystem\n(Images)")]
    end

    Citizen -->|"Raw Image + Details"| P1
    P1 -->|"Invalid — Rejected"| Citizen
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

    style PROCESSES fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px
    style STORES fill:#f0fdf4,stroke:#16a34a,stroke-width:1.5px
```

---

## 5.10 Deployment Diagram

```mermaid
flowchart TB
    Browser(["🌐 Browser / Mobile Client"])

    subgraph HOST ["🖥️ Host Machine"]
        subgraph DOCKER ["🐳 Docker Compose Network"]
            subgraph FE_CONTAINER ["Frontend Container"]
                Nginx["Nginx Web Server"]
                ReactBuild["React App (Static Build)"]
                Nginx --> ReactBuild
            end

            subgraph BE_CONTAINER ["Backend Container"]
                Uvicorn["Uvicorn ASGI Server"]
                FastAPI["FastAPI Application"]
                Uvicorn --> FastAPI
            end

            subgraph DB_CONTAINER ["MongoDB Container"]
                MongoDB[("MongoDB\nDatabase")]
            end
        end

        subgraph HOST_RUNTIME ["Host Runtime (Outside Docker)"]
            Ollama["🤖 Ollama Model Runtime"]
            GPU["⚡ GPU Resources"]
            Ollama --> GPU
        end
    end

    Browser -->|"HTTPS Request"| Nginx
    ReactBuild -->|"REST API (HTTP)"| FastAPI
    FastAPI -->|"Mongoose ODM\n(Internal Network)"| MongoDB
    FastAPI -->|"HTTP Bridge\n(host.docker.internal)"| Ollama

    style DOCKER fill:#eff6ff,stroke:#2563eb,stroke-width:2px
    style HOST_RUNTIME fill:#fef9c3,stroke:#ca8a04,stroke-width:2px
    style FE_CONTAINER fill:#dbeafe,stroke:#3b82f6
    style BE_CONTAINER fill:#ede9fe,stroke:#8b5cf6
    style DB_CONTAINER fill:#dcfce7,stroke:#16a34a
```