# GUI Wireframes (Mermaid Canonical)

This document is the canonical wireframe source for the current UI. 

![Canonical GUI Wireframe](./images/GUI_Wireframe.png)

Mermaid diagrams below provide the functional logic and flow for the wireframes.

## App Navigation Map

```mermaid
flowchart LR
    Home[/ /] --> Login[/login/]
    Home --> Register[/register/]
    Home --> WorkerRegister[/worker/register/]

    Login --> Dashboard[/dashboard/]

    Dashboard --> CitizenDash[/citizen role/]
    Dashboard --> WorkerDash[/worker role/]
    Dashboard --> DeptDash[/dept_head role/]
    Dashboard --> AdminDash[/admin role/]

    CitizenDash --> Analyze[/api/v1/analyze/]
    Analyze --> Result[/result/]
    CitizenDash --> Profile[/profile/]
    CitizenDash --> Notifications[/api/v1/notifications/]

    WorkerDash --> Notifications
    DeptDash --> Map[/map/]
    DeptDash --> Heatmap[/heatmap/]
    DeptDash --> Notifications

    AdminDash --> Triage[/triage-review/]
    AdminDash --> Analytics[/api/v1/analytics/]
    AdminDash --> Map
    AdminDash --> Heatmap
    AdminDash --> Notifications

    Home --> PublicBoard[/api/v1/public/]
```

## Citizen Submission Wireframe

```mermaid
flowchart TB
    A[Analyze Page]
    A --> A1[Upload Image Card]
    A --> A2[Language Selector]
    A --> A3[Analyze Action]

    A3 --> B[Result Page]
    B --> B1[Classification Summary]
    B --> B2[Generated Draft Textarea]
    B --> B3[Map Panel: Street/Satellite Toggle]
    B --> B4[Manual Address + Lat/Lon Inputs]
    B --> B5[Use Device Location]
    B --> B6[Regenerate Draft with Language Picker]
    B --> B7[Submit Complaint]

    B7 --> C[Citizen Dashboard]
    C --> C1[Cards: Open/In Progress/Resolved]
    C --> C2[SLA Badge + Timeline]
    C --> C3[Feedback + Comments]
```

## Admin and Department Head Wireframe

```mermaid
flowchart LR
    D[Admin Dashboard]
    D --> D1[Complaint Table + Filters]
    D --> D2[Bulk Status and Bulk Transfer]
    D --> D3[Worker Approvals + Assignments]
    D --> D4[CSV Export]
    D --> D5[Links: Triage + Analytics]

    E[Dept Head Dashboard]
    E --> E1[Department Complaint Queue]
    E --> E2[Status Update with Note]
    E --> E3[Department Notes]
    E --> E4[Department Transfer Action]
    E --> E5[Worker List for Department]
```

## Worker Wireframe

```mermaid
flowchart TB
    W[Worker Dashboard]
    W --> W1[Profile + Worker Status Toggle]
    W --> W2[Active Assigned Complaints]
    W --> W3[Mark Task Done]
    W --> W4[Resolved History]
```

## Notification UX Flow

```mermaid
sequenceDiagram
    participant User as Logged-in User
    participant Nav as Navbar Bell
    participant API as /api/v1/notifications API

    User->>Nav: Open app
    Nav->>API: GET /api/v1/notifications/unread-count
    API-->>Nav: count

    User->>Nav: Open bell panel
    Nav->>API: GET /api/v1/notifications?limit=10
    API-->>Nav: latest notifications

    User->>Nav: Mark one as read
    Nav->>API: PATCH /api/v1/notifications/{id}/read
    API-->>Nav: ok

    User->>Nav: Mark all as read
    Nav->>API: PATCH /api/v1/notifications/read-all
    API-->>Nav: ok
```

## Layout Notes

- Frontend routes are role-gated in `frontend/src/App.jsx`.
- Public transparency board is available at `/api/v1/public` without authentication.
- Primary complaint map uses MapLibre via `react-map-gl`; grievance heatmap page currently uses Leaflet.
- Mobile responsiveness is supported across dashboard and submission flows.
