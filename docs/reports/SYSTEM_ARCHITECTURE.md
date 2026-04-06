# Jan-Sunwai AI System Architecture

Last updated: 2026-04-06

## 1. System Context

Jan-Sunwai AI is a role-based civic grievance platform where image-first complaint submission is transformed into structured, routed grievance records with lifecycle tracking.

```mermaid
flowchart LR
    Citizen[Citizen] --> Portal[Jan-Sunwai Frontend]
    Worker[Field Worker] --> Portal
    DeptHead[Department Head] --> Portal
    Admin[Administrator] --> Portal

    Portal --> API[FastAPI Backend]
    API --> Mongo[(MongoDB)]
    API --> Files[(uploads/)]
    API --> Ollama[Ollama Models]

    API --> Notify[Notification Service]
    API --> Escalate[Escalation Loop]
    API --> Analytics[Analytics Aggregations]
```

## 2. Runtime Components

```mermaid
flowchart TB
    subgraph Frontend
        FE1[React App]
        FE2[Role Dashboards]
        FE3[Map Views]
    end

    subgraph Backend
        BE1[Auth and Users Router]
        BE2[Analyze and Complaints Router]
        BE3[Workers Router]
        BE4[Triage Router]
        BE5[Notifications Router]
        BE6[Analytics and Public Routers]
        BE7[Health Router]
        BE8[LLM Queue Service]
        BE9[Assignment Service]
        BE10[Escalation Service]
    end

    subgraph Persistence
        DB[(MongoDB)]
        UP[(uploads/)]
    end

    subgraph Inference
        OLLAMA[Vision + Reasoning Models]
    end

    FE1 --> BE1
    FE1 --> BE2
    FE2 --> BE3
    FE2 --> BE4
    FE2 --> BE5
    FE3 --> BE6

    BE1 --> DB
    BE2 --> DB
    BE3 --> DB
    BE4 --> DB
    BE5 --> DB
    BE6 --> DB
    BE7 --> DB

    BE2 --> UP
    BE2 --> BE8
    BE8 --> OLLAMA
    BE9 --> DB
    BE10 --> DB
```

## 3. AI Pipeline Architecture

```mermaid
flowchart TD
    Input[Uploaded Image] --> Validate[Storage Validation]
    Validate --> Vision[Vision Model Cascade]
    Vision --> RuleEngine[Deterministic Rule Engine]
    RuleEngine --> Ambiguous{Ambiguous score?}
    Ambiguous -->|No| Category[Department category]
    Ambiguous -->|Yes| Reasoning[Reasoning model]
    Reasoning --> Category
    Category --> QueueDraft[Queue draft generation]
    QueueDraft --> Draft[Generated grievance draft]
```

### Key Design Points

- Vision model cascade supports primary/mid/fallback model configuration.
- Rule engine classifies most clear cases without reasoning model invocation.
- Reasoning model runs only for ambiguous cases.
- Draft generation is queued and pollable.

## 4. Complaint Lifecycle and Routing

```mermaid
sequenceDiagram
    actor Citizen
    participant FE as Frontend
    participant API as Backend
    participant DB as MongoDB
    participant Assign as Assignment Service

    Citizen->>FE: Analyze image and review draft
    FE->>API: POST /complaints
    API->>DB: Insert complaint (Open)
    API->>Assign: auto_assign by department and location

    alt eligible worker found
        Assign->>DB: assigned_to set and status In Progress
    else no worker available
        Assign->>DB: keep status Open
    end

    API-->>FE: complaint response
```

## 5. Worker and Department Operational Flow

```mermaid
flowchart LR
    NewComplaint[New Complaint] --> WorkerFilter[Eligible worker filter]
    WorkerFilter --> GeoMatch[Service-area distance check]
    GeoMatch --> LoadPick[Least active worker]
    LoadPick --> Assigned[Assigned and In Progress]
    Assigned --> WorkerDone[Worker marks done]
    WorkerDone --> Resolved[Status Resolved]
    Resolved --> SlotFree[Worker slot freed]
    SlotFree --> Reassign[Reassign queued opens if possible]
```

## 6. Triage and Escalation

```mermaid
flowchart TD
    AnalyzeResult[Analyze result] --> Confidence{confidence < 0.65?}
    Confidence -->|Yes| TriageQueue[Admin triage queue]
    Confidence -->|No| DirectRoute[Direct department route]

    TriageQueue --> Decision[Approve/Reject/Correct label]
    Decision --> Routed[Complaint continues in lifecycle]

    Routed --> SLAClock[SLA elapsed check]
    SLAClock --> Escalate{deadline exceeded?}
    Escalate -->|Yes| AuthorityEscalation[Move to parent authority]
    Escalate -->|No| NormalFlow[Normal status handling]
```

## 7. Deployment View

```mermaid
flowchart LR
    Browser[Browser] --> Nginx[Frontend Nginx]
    Nginx --> Backend[Backend Gunicorn/Uvicorn]
    Backend --> Mongo[(MongoDB)]
    Backend --> Ollama[Host Ollama]
```

This is the currently supported production-style deployment in `docker-compose.prod.yml`.
