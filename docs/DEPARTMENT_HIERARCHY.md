# Department and Role Hierarchy

This document defines the active department taxonomy and role hierarchy used by Jan-Sunwai AI.

## Canonical Department Taxonomy

The backend classifier and routing logic use these department labels:

1. Health Department
2. Civil Department
3. Horticulture
4. Electrical Department
5. IT Department
6. Commercial
7. Enforcement
8. VBD Department
9. EBR Department
10. Fire Department
11. Uncategorized

## Organizational Hierarchy (Operational)

```mermaid
flowchart TB
    ROOT[Jan-Sunwai Department Tree]

    ROOT --> HD[Health Department]
    ROOT --> CD[Civil Department]
    ROOT --> HT[Horticulture]
    ROOT --> ED[Electrical Department]
    ROOT --> ITD[IT Department]
    ROOT --> COM[Commercial]
    ROOT --> ENF[Enforcement]
    ROOT --> VBD[VBD Department]
    ROOT --> EBR[EBR Department]
    ROOT --> FIRE[Fire Department]

    HD --> HD1[Medical officer of health MOH]
    HD1 --> HD2[Chief medical officer CMO]
    HD2 --> HD3[Chief sanitary inspector CSI]
    HD3 --> HD4[Sanitary inspector SI]
    HD4 --> HD5[Assistant sanitary inspector ASI]

    CD --> CD1[Chief engineer]
    CD1 --> CD2[Superintendent engineer]
    CD2 --> CD3[Executive engineer]
    CD3 --> CD4[Assistant engineer]
    CD4 --> CD5[Junior engineer]

    HT --> HT1[Director]
    HT1 --> HT2[Dy Director]
    HT2 --> HT3[Assistant Director]
    HT3 --> HT4[Section officer]
    HT4 --> HT5[Assistant section officer]

    ED --> ED1[Chief engineer]
    ED1 --> ED2[Superintendent engineer]
    ED2 --> ED3[Executive engineer]
    ED3 --> ED4[Assistant engineer]
    ED4 --> ED5[Junior engineer]

    ITD --> IT1[Director]
    IT1 --> IT2[Joint Director]
    IT2 --> IT3[Nodal programmer]
    IT3 --> IT4[Programmer]
    IT4 --> IT5[Assistant programmer]

    COM --> COM1[Director]
    COM1 --> COM2[Joint director]
    COM2 --> COM3[Executive]

    ENF --> ENF1[Director]
    ENF1 --> ENF2[Joint director]
    ENF2 --> ENF3[Action officer]
    ENF3 --> ENF4[Assistant action officer]
    ENF4 --> ENF5[Executive]

    VBD --> VBD1[Medical officer of health MOH]
    VBD1 --> VBD2[Chief medical officer CMO]
    VBD2 --> VBD3[Assistant sanitary inspector ASI]
    VBD3 --> VBD4[Worker]

    EBR --> EBR1[Chief Architect]
    EBR1 --> EBR2[Senior architect]
    EBR2 --> EBR3[Architect]

    FIRE --> F1[Fire officer]
    F1 --> F2[Senior action worker]
    F2 --> F3[Action worker]
```

## System Role Mapping

In seeded accounts (`backend/create_test_users.py`):

- First title in each department hierarchy is created as `dept_head`.
- Remaining titles in that department are created as `worker`.
- Separate global accounts exist for `citizen` and `admin`.

## Routing to Authority IDs

Classifier categories are routed to authority IDs in `backend/app/authorities.py`.

| Department Label | Authority ID | Escalation Parent |
| --- | --- | --- |
| Health Department | `MUNI_SANITATION` | `STATE_CMO` |
| Civil Department | `MUNI_PWD` | `STATE_CMO` |
| Horticulture | `MUNI_HORTICULTURE` | `STATE_CMO` |
| Electrical Department | `UTIL_DISCOM` | `STATE_CMO` |
| IT Department | `STATE_CMO` | `CENTRAL_DARPG` |
| Commercial | `STATE_CMO` | `CENTRAL_DARPG` |
| Enforcement | `POLICE_TRAFFIC` | `STATE_CMO` |
| VBD Department | `MUNI_SANITATION` | `STATE_CMO` |
| EBR Department | `MUNI_PWD` | `STATE_CMO` |
| Fire Department | `POLICE_LOCAL` | `STATE_CMO` |
| Uncategorized | keyword fallback/unmapped | nullable |

## Escalation Ladder

```mermaid
flowchart LR
    Local[Local Authority]
    State[State CMO Grievance Cell]
    Central[CENTRAL_DARPG]

    Local --> State --> Central
```

## Worker Assignment Hierarchy in Runtime

```mermaid
flowchart TD
    NewComplaint[New Complaint]
    NewComplaint --> DeptFilter[Filter workers by same department]
    DeptFilter --> ApprovalFilter[is_approved == true]
    ApprovalFilter --> StatusFilter[worker_status != offline]
    StatusFilter --> GeoFilter[Within service_area radius if location available]
    GeoFilter --> LoadBalance[Pick least active tasks]
    LoadBalance --> Assign[Assign worker and set complaint status In Progress]
```

This hierarchy is enforced by `backend/app/services/assignment.py`.
