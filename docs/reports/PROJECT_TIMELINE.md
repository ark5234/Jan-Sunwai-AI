# Project Timeline

Project window: January 2026 to May 2026

This timeline reflects delivered architecture, security, worker assignment, analytics, and production-readiness features.

## Phase Overview

| Phase | Focus | Outcome |
| --- | --- | --- |
| Phase 1 | Foundation and core backend/frontend | End-to-end complaint flow established |
| Phase 2 | Security and operational capability | Role hardening, notifications, worker ops, triage, analytics |
| Phase 3 | Production readiness and handover prep | Compose production profile, docs, testing runbooks |

## Mermaid Gantt

```mermaid
gantt
    title Jan-Sunwai AI Development Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %m-%d

    section Phase 1: Foundation
    Repo and architecture setup              :done, p1a, 2026-01-28, 2026-02-06
    Auth, schemas, complaint CRUD            :done, p1b, 2026-02-07, 2026-02-16
    Vision + rule + generation pipeline      :done, p1c, 2026-02-17, 2026-02-29
    Frontend core pages and role routing     :done, p1d, 2026-03-01, 2026-03-10

    section Phase 2: Reliability and Features
    Security hardening                       :done, p2a, 2026-03-11, 2026-03-20
    Worker assignment and department ops     :done, p2b, 2026-03-21, 2026-03-31
    Notifications and profile/password flows :done, p2c, 2026-04-01, 2026-04-10
    Analytics, public board, triage updates  :done, p2d, 2026-04-11, 2026-04-20

    section Phase 3: Production and QA
    Production compose and deployment docs   :done, p3a, 2026-04-21, 2026-04-30
    Security and load testing runbooks       :done, p3b, 2026-05-01, 2026-05-12
    Report consolidation and handover pack   :done, p3c, 2026-05-13, 2026-05-27
```

## Milestone Map

```mermaid
flowchart LR
    M1[M1 Core API and auth] --> M2[M2 AI analysis pipeline]
    M2 --> M3[M3 Complaint lifecycle and routing]
    M3 --> M4[M4 Worker assignment and dashboards]
    M4 --> M5[M5 Triage and analytics]
    M5 --> M6[M6 Security and resilience]
    M6 --> M7[M7 Production compose and docs]
```

## Current Status Summary

- Core delivery complete.
- Production-style deployment artifacts complete.
- Security and load test runbooks complete.
- Remaining work is primarily environment-specific UAT and operational rollout execution.
