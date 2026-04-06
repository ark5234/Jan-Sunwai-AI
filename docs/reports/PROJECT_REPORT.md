# Jan-Sunwai AI Project Report

Automated visual classification and routing of civic grievances using local vision-language models.

Last updated: 2026-04-06

## Table of Contents

1. Introduction
2. Problem and Motivation
3. System Scope
4. Architecture and Design
5. Data and Schema Design
6. API and Module Design
7. Security, Reliability, and Testing
8. Deployment and Operations
9. Outcomes and Limitations
10. Future Work

## 1. Introduction

Jan-Sunwai AI is a full-stack grievance platform that transforms image uploads into structured civic complaint workflows. The system combines frontend usability, backend orchestration, local AI inference, role-based operations, and lifecycle tracking.

## 2. Problem and Motivation

Existing complaint systems often require users to manually select departments and compose formal complaints. This leads to misrouting and inconsistent complaint quality.

Jan-Sunwai AI addresses this by automating:

- category classification,
- draft generation,
- routing metadata,
- and operational handoff.

## 3. System Scope

### User Roles

- Citizen
- Worker
- Department Head
- Admin

### Functional Scope

- Analyze uploaded image and generate draft.
- Create complaint record with AI metadata and location.
- Auto-assign to workers using department and geography.
- Track status and timeline.
- Admin triage for low-confidence AI cases.
- Notifications and analytics.

## 4. Architecture and Design

## 4.1 Context Diagram

```mermaid
flowchart LR
    Citizen[Citizen] --> App[Jan-Sunwai UI]
    Worker[Worker] --> App
    Dept[Department Head] --> App
    Admin[Admin] --> App

    App --> API[FastAPI]
    API --> DB[(MongoDB)]
    API --> AI[Ollama Models]
    API --> Store[(uploads/)]
```

## 4.2 Component Diagram

```mermaid
flowchart TB
    subgraph Frontend
        F1[Role-based routes]
        F2[Analyze and Result pages]
        F3[Dashboards and notifications]
    end

    subgraph Backend
        B1[Users/Auth]
        B2[Analyze/Complaints]
        B3[Workers]
        B4[Triage]
        B5[Analytics/Public]
        B6[Health]
        B7[LLM Queue]
        B8[Assignment]
        B9[Escalation]
    end

    F1 --> B1
    F2 --> B2
    F3 --> B3
    F3 --> B4
    F3 --> B5

    B1 --> DB[(MongoDB)]
    B2 --> DB
    B3 --> DB
    B4 --> DB
    B5 --> DB
    B6 --> DB

    B2 --> U[(uploads)]
    B7 --> O[Ollama]
    B2 --> B7
```

## 4.3 AI Pipeline Sequence

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as /analyze
    participant Classifier as CivicClassifier
    participant Rule as Rule Engine
    participant Queue as LLM Queue
    participant Generator as Draft Generator

    FE->>API: POST /analyze (image, language)
    API->>Classifier: vision analysis
    Classifier->>Rule: classify_by_rules(payload)

    alt ambiguous
        Rule-->>Classifier: ambiguous
        Classifier->>Classifier: reasoning model
    else confident
        Rule-->>Classifier: confident category
    end

    API->>Queue: enqueue draft job
    Queue->>Generator: generate_complaint
    Generator-->>Queue: text
    Queue-->>API: completed/queued/failed
    API-->>FE: classification + draft status + timings
```

## 4.4 Use Case Diagram

```mermaid
flowchart LR
    Citizen --> UC1[Analyze image]
    Citizen --> UC2[Submit complaint]
    Citizen --> UC3[Track status]
    Citizen --> UC4[Feedback and comments]

    Worker --> UC5[View assigned tasks]
    Worker --> UC6[Mark task done]

    DeptHead --> UC7[Update status]
    DeptHead --> UC8[Add internal notes]
    DeptHead --> UC9[Transfer complaint]

    Admin --> UC10[Approve workers]
    Admin --> UC11[Triage low-confidence queue]
    Admin --> UC12[Bulk actions and exports]
    Admin --> UC13[View analytics and heatmap]
```

## 5. Data and Schema Design

## 5.1 Core Entities

```mermaid
erDiagram
    USER ||--o{ COMPLAINT : files
    USER ||--o{ COMPLAINT : assigned
    USER ||--o{ NOTIFICATION : receives
    COMPLAINT ||--o{ NOTIFICATION : emits

    USER {
        string _id
        string username
        string role
        string department
        bool is_approved
        string worker_status
        array active_complaint_ids
    }

    COMPLAINT {
        string _id
        string user_id
        string assigned_to
        string department
        string status
        object ai_metadata
        object location
        array status_history
        array comments
        array dept_notes
        object feedback
    }

    NOTIFICATION {
        string _id
        string user_id
        string complaint_id
        string type
        bool is_read
    }
```

## 5.2 Complaint State Machine

```mermaid
stateDiagram-v2
    [*] --> Open
    Open --> In_Progress
    Open --> Rejected
    In_Progress --> Resolved
    In_Progress --> Rejected
```

## 6. API and Module Design

## 6.1 Router Groups

- Users: registration, login, profile, password reset.
- Analyze/Complaints: AI analyze, complaint CRUD, status/transfer/escalation, notes/comments/feedback.
- Workers: worker self-service and admin worker operations.
- Notifications: unread, list, mark read.
- Triage: low-confidence review queue and decisions.
- Analytics/Public/Health: reporting and service observability.

## 6.2 Versioning Strategy

All major routers are mounted with `/api/v1` aliases in `backend/main.py`.

## 7. Security, Reliability, and Testing

## 7.1 Security Controls

```mermaid
flowchart TD
    Req[Incoming Request] --> Auth[JWT/Auth check]
    Auth --> Role[Role authorization]
    Role --> Validate[Payload validation]
    Validate --> Sanitize[Sanitize user text]
    Sanitize --> Process[Business logic]
    Process --> Headers[Security headers]
    Headers --> Resp[Response]
```

Implemented controls include:

- Upload validation by extension, size, and magic numbers.
- Role-gated endpoint access.
- Sanitization for user-provided text fields.
- Optional rate limiting.
- Health/readiness diagnostics.

## 7.2 Reliability Behaviors

- Graceful `503` response when AI pipeline is unavailable.
- Notification and email event on status updates.
- Escalation loop for SLA breach handling.
- Worker slot release and reassignment loop on task completion.

## 7.3 Testing Assets

- Integration smoke test (`test_api_integration.py`).
- Security/resilience tests (`test_resilience_security.py`).
- Notification chain tests (`test_notification_chain.py`).
- Load scenario (`locustfile.py`).

## 8. Deployment and Operations

## 8.1 Current Production Deployment

```mermaid
flowchart LR
    Browser --> Frontend[Nginx frontend container]
    Frontend --> Backend[FastAPI backend container]
    Backend --> Mongo[(MongoDB container)]
    Backend --> Ollama[Host Ollama runtime]
```

## 8.2 Operational Runbooks

- `docs/NDMC_DEPLOYMENT.md`
- `docs/LOAD_TESTING.md`
- `docs/SECURITY_TESTING.md`
- `docs/PRODUCTION_DEPLOYMENT_PLAN.md`

## 9. Outcomes and Limitations

### Outcomes

- End-to-end multi-role grievance lifecycle implemented.
- AI-assisted classification and drafting integrated into complaint workflow.
- Worker assignment and triage governance operational.
- Production-style compose deployment and runbooks established.

### Current Limitations

- LLM queue is in-memory (not durable across service restarts).
- Upload storage is local filesystem in baseline deployment.
- Inference path depends on local/host Ollama availability.

## 10. Future Work

```mermaid
flowchart LR
    A[Durable Queue] --> B[Dedicated GPU Workers]
    B --> C[Object Storage Migration]
    C --> D[Managed MongoDB Replication]
    D --> E[Horizontal API Scaling]
    E --> F[City-scale SLA and observability]
```

Planned enhancements:

1. Replace in-memory queue with Redis/RabbitMQ.
2. Decouple API and inference worker nodes.
3. Move uploads to object storage.
4. Expand production observability and UAT automation.
