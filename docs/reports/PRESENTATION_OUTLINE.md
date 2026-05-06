# Project Presentation Outline

## Slide 1: Title

- Jan-Sunwai AI
- Team/author details
- Date and institution

## Slide 2: Problem Statement

- Manual complaint drafting and department confusion
- Delays due to misrouting and incomplete location details

## Slide 3: Proposed Solution

- Image-first complaint intake
- AI-assisted category and draft generation
- Role-based operational workflow

## Slide 4: Architecture Overview

- Frontend: React + Vite
- Backend: FastAPI
- DB: MongoDB
- AI runtime: Ollama

## Slide 5: AI Pipeline

- Vision model output
- Rule engine routing
- Optional reasoning for ambiguity
- Complaint draft generation

## Slide 6: Key Features

- Worker assignment and service area
- Status history and SLA badges
- Notifications and analytics
- Public transparency board

## Slide 7: Security and Reliability

- Cookie-session auth (httpOnly) + JWT compatibility + RBAC
- Upload validation and sanitization
- Rate limiting and graceful degradation

## Slide 8: Performance and Testing

- Unit/integration/security/resilience coverage
- Load test methodology and benchmark artifacts

## Slide 9: Production Readiness

- Docker production stack
- NDMC deployment runbook
- Backup and restore strategy

## Slide 10: Demo Flow

- Citizen upload -> analyze -> submit
- Dept-head status update
- Admin analytics and worker assignment

## Slide 11: Results and Learnings

- What worked well
- Technical constraints and mitigations

## Slide 12: Future Scope

- Durable queueing
- Managed storage
- Advanced observability and audit dashboards
