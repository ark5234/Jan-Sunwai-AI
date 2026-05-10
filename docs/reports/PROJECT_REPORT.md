# Jan-Sunwai AI – Report (Corrected)

1. [CONTENTS](#contents)
2. [List of Figures](#list-of-figures)
3. [List of Tables](#list-of-tables)
4. [List of Abbreviations](#list-of-abbreviations)
5. [List of Definitions](#list-of-definitions)
6. [List of Screenshots](#list-of-screenshots)
7. [1 Introduction](#1-introduction)
8. [2 Project Management](#2-project-management)
9. [3 System Requirement Study](#3-system-requirement-study)
10. [4 Proposed System Requirements](#4-proposed-system-requirements)
11. [5 System Design](#5-system-design)
12. [6 Implementation Planning](#6-implementation-planning)
13. [7 Testing](#7-testing)
14. [8 Limitations and Future Scope](#8-limitations-and-future-scope)
15. [9 Conclusion and References](#9-conclusion-and-references)
16. [10 Appendices](#10-appendices)
17. [11 Report Verification Procedure](#11-report-verification-procedure)

## CONTENTS

| Chapter No. | Description | Page No. |
| --- | --- | --- |
| - | List of Figures | I |
| - | List of Tables | II |
| - | List of Abbreviations | III |
| - | List of Definitions | IV |
| - | List of Screenshots | V |
| 1 | Introduction | 1 |
| 1.1 | Project Details | 2 |
| 1.2 | Purpose | 3 |
| 1.3 | Scope | 4 |
| 1.4 | Objectives | 5 |
| 1.5 | Technology Stack Used | 6 |
| 1.6 | Literature Review | 7 |
| 2 | Project Management | 8 |
| 2.1 | Feasibility Study | 9 |
| 2.1.1 | Technical Feasibility | 10 |
| 2.1.2 | Time Schedule Feasibility | 11 |
| 2.1.3 | Operational Feasibility | 12 |
| 2.1.4 | Implementation Feasibility | 13 |
| 2.2 | Project Planning | 14 |
| 2.2.1 | Development Approach & Justification | 15 |
| 2.2.2 | Milestones & Deliverables | 16 |
| 2.2.3 | Roles and Responsibilities | 17 |
| 2.2.4 | Group Dependencies | 18 |
| 2.3 | Project Scheduling (Gantt/PERT chart) | 19 |
| 3 | System Requirement Study | 21 |
| 3.1 | Existing System Overview | 22 |
| 3.2 | Limitations of the Existing System | 23 |
| 3.3 | User Characteristics | 24 |
| 3.4 | Functional Requirements | 25 |
| 3.5 | Non-Functional Requirements | 26 |
| 3.6 | Hardware & Software Requirements | 27 |
| 3.7 | Constraints | 28 |
| 3.7.1 | UI Constraints | 29 |
| 3.7.2 | Communication Interface | 30 |
| 3.7.3 | Hardware Interface | 31 |
| 3.7.4 | Criticality of Application | 33 |
| 3.7.5 | Safety and Security Considerations | 34 |
| 3.8 | Assumptions and Dependencies | 35 |
| 4 | Proposed System Requirements | 36 |
| 4.1 | Overview of Proposed System | 38 |
| 4.2 | Module Descriptions | 39 |
| 4.3 | System Features | 40 |
| 4.4 | Advantages of Proposed System | 42 |
| 5 | System Design | 43 |
| 5.1 | System Architecture Design | 44 |
| 5.2 | UML Diagrams | 46 |
| 5.2.1 | E-R Diagram | 47 |
| 5.2.2 | Use Case Diagram | 48 |
| 5.2.3 | Class Diagram | 49 |
| 5.2.4 | Sequence Diagram | 50 |
| 5.2.5 | Activity Diagram | 51 |
| 5.2.6 | DFD Diagram | 52 |
| 5.2.7 | Deployment Diagram | 55 |
| 5.3 | Database Design | 58 |
| 5.3.1 | Table Design & Relationships | 59 |
| 5.3.2 | Normalization | 60 |
| 5.3.3 | Data Dictionary | 62 |
| 5.4 | GUI Design | 63 |
| 5.5 | Screenshots | 64 |
| 6 | Implementation Planning | 66 |
| 6.1 | Implementation Environment | 68 |
| 6.2 | Tools & Technologies Used | 69 |
| 6.3 | Coding Standards Followed | 70 |
| 7 | Testing | 71 |
| 7.1 | Testing Plan | 72 |
| 7.2 | Types of Testing | 74 |
| 7.2.1 | Unit Testing | 75 |
| 7.2.2 | Integration Testing | 79 |
| 7.2.3 | System Testing | 82 |
| 7.2.4 | User Acceptance Testing (UAT) | 85 |
| 7.3 | Testing Techniques | 87 |
| 7.3.1 | Defect Logging | 90 |
| 8 | Limitations and Future Scope | 91 |
| 9 | Conclusion and References | 93 |
| 9.1 | Conclusion | 94 |
| 9.2 | References | 95 |
| 10 | Appendices | 96 |
| 11 | Report Verification Procedure | 97 |

## List of Figures

| Figure No. | Figure Description | Page No. |
| --- | --- | --- |
| Figure 1 | Overall System Context Diagram | 44 |
| Figure 2 | Component Architecture Diagram | 45 |
| Figure 3 | E-R Diagram | 47 |
| Figure 4 | Use Case Diagram | 48 |
| Figure 5 | Class Diagram | 49 |
| Figure 6 | Sequence Diagram | 50 |
| Figure 7 | Activity Diagram | 51 |
| Figure 8 | DFD Diagram | 52 |
| Figure 9 | Deployment Diagram | 55 |
| Figure 10 | Project Gantt View | 19 |

## List of Tables

| Table No. | Table Description | Page No. |
| --- | --- | --- |
| Table 1 | Objectives and Expected Outcomes | 5 |
| Table 2 | Technology Stack | 6 |
| Table 3 | Functional Requirements | 25 |
| Table 4 | Non-Functional Requirements | 26 |
| Table 5 | Module Mapping | 39 |
| Table 6 | Data Dictionary Summary | 62 |
| Table 7 | Testing Coverage Matrix | 72 |
| Table 8 | Defect Log Snapshot | 90 |

## List of Abbreviations

| Abbreviation | Full Form |
| --- | --- |
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| JWT | JSON Web Token |
| LLM | Large Language Model |
| UAT | User Acceptance Testing |
| SLA | Service Level Agreement |
| RBAC | Role-Based Access Control |
| DFD | Data Flow Diagram |

## List of Definitions

| Term | Definition |
| --- | --- |
| Civic Complaint | Citizen-reported grievance related to public services/infrastructure |
| Triage Queue | Admin review queue for low-confidence AI classifications |
| Service Area | Worker-specific geographic eligibility radius for assignments |
| Status History | Audit trail of complaint lifecycle transitions |

## List of Screenshots

| Screenshot No. | Screenshot Description | Page No. |
| --- | --- | --- |
| S1 | Citizen Analyze Page | 64 |
| S2 | Result and Draft Review Page | 64 |
| S3 | Admin Dashboard | 64 |
| S4 | Worker Dashboard | 64 |
| S5 | Notifications Panel | 64 |
| S6 | Admin Analytics Dashboard | 64 |
| S7 | Complaints Map Overview | 64 |
| S8 | Resolved Complaint View | 64 |
| S9 | Complaint Filing Upload Page | 64 |
| S10 | Complaint Review Without Geo Tag | 64 |
| S11 | Hindi Complaint Draft | 64 |
| S12 | English Complaint Draft | 64 |
| S13 | Citizen Registration Page | 64 |
| S14 | Worker Registration Page | 64 |

---

## Chapter 1: Introduction

Jan-Sunwai AI is an end-to-end civic grievance redressal platform designed to minimize the operational delay between when a citizen submits a complaint and when the relevant department takes action. The system converts an image upload into a structured, auditable complaint flow and forwards the case to accountable municipal actors. To remove the need for citizens to navigate bureaucratic department structures, the platform uses AI to classify and draft complaints while keeping a human-controlled correction route via triage and administrative controls.

The project is a local-first system built to meet practical constraints in the municipal domain, where cloud deployment may be limited due to policy, infrastructure, or privacy concerns. The architecture combines a React frontend, a FastAPI backend, MongoDB for the database, and locally-run Ollama models in a hybrid inference pipeline. This deployment approach allows the platform to operate within the narrow confines of institutional settings without sacrificing modularity for future expansion.

---

### 1.1 Project Details

Jan-Sunwai AI is a civic grievance management platform modelled on NDMC-style municipal governance operations, developed between 28 January and 27 May 2026. Its primary application domain is civic grievance management and municipal operations, serving citizens, workers, department heads, and administrators. The system is implemented as a local-first, containerised stack that runs independently of managed cloud services.

---

### 1.2 Purpose

Traditional grievance mechanisms place a significant cognitive load on the very people they are designed to serve. Submitters are typically required to type detailed textual descriptions, navigate multi-level department dropdown menus, and in many cases physically call an office to have a complaint referred to the appropriate person. Citizens who are unfamiliar with municipal organisational structures routinely complain to the wrong department, triggering inter-departmental transfer cycles that delay field action by three to five working days per misrouting event. In such cases, complaint narratives tend to be incomplete, inconsistently formatted, or factually imprecise, requiring substantial clarification from departmental staff before any field response is possible.

Jan-Sunwai AI was built to break this cycle at the earliest stage. Photographic evidence submitted by a citizen is analysed using a vision-language model to derive a visual summary, a probable departmental category, geospatial metadata, and a formally drafted complaint description. The citizen then reviews and, if necessary, edits this output before submission, ensuring that even a non-technical user can produce a structurally sound, verifiable complaint. Complaints arrive pre-classified with AI-generated rationale attached, allowing supervisory effort to focus on resolution governance rather than intake remediation. Administrative stakeholders are provided with an analytics layer, a public transparency feed, and exportable complaint datasets to support operational management and institutional accountability. The intent of the design is not to replace decisions made by human administrators, but to minimise the repetitive manual effort that currently creates barriers to timely field action.

---

### 1.3 Scope

The implemented scope covers intake, classification, routing metadata, assignment, notifications, escalation support, and governance analytics. Specifically, the platform includes:

- User management and role-aware access control
- AI image analysis and complaint drafting
- Complaint lifecycle actions: create, track, update, transfer, escalate, and close
- Worker assignment controls and department-specific work queues
- A triage procedure for low-confidence classifications or ambiguous cases
- Notification chains and password reset mechanisms
- A public-facing complaint listing and operational analytics (anonymised)

Multilingual voice input, direct integration with external municipal ERP systems, and predictive resource planning beyond dashboard analytics are currently outside scope.

---

### 1.4 Objectives

Friction in submitting complaints was identified as the primary barrier to complaint quality. The intake workflow was designed around a simplified upload–analyse–submit sequence, with AI-generated content reducing the burden of manual text entry on citizens. Drafts may be accepted as-is without editing, preserving citizen agency while consistently improving the quality of submitted records.

A canonical department taxonomy and a deterministic authority-mapping engine were implemented. Rather than relying solely on natural language classification, rule-based scoring ensures that even when model confidence is low, the assigned department is drawn from a bounded, valid set of municipal authorities.

Complaint traceability was integrated across the entire complaint lifecycle. Every status change is documented with the responsible actor, a timestamp, and a supporting note. This audit trail supports supervisory review, escalation adjudication, and post-resolution accountability assessments.

Worker assignment automation was implemented by matching complaints to departmentally aligned field workers based on geographic proximity and active task load. A manual override is retained for cases where automated assignment produces an inappropriate result.

Security was treated as a first-order requirement rather than an end-of-project hardening task. Cookie-session authentication, MIME-type and magic-number validation on uploaded files, input sanitisation, and a full set of HTTP security headers were all in place before the feature set was considered complete.

Public transparency and governance analytics were provided to address the accountability dimension of civic technology. An anonymised public complaint feed, combined with an administrative analytics dashboard including a geospatial heatmap, allows citizens and oversight bodies to observe aggregate system behaviour without exposing any personally identifiable records.

Finally, production deployment readiness was treated as a clear deliverable. Docker Compose orchestration, environment variable templates, runbooks, and verification procedures were created to ensure that institutional handover does not require the receiving institution to reconstruct deployment knowledge from source code alone.

---

### 1.5 Technology Stack

The system is structured across five layers. The frontend is built with React and Vite, providing role-based dashboards and authentication-aware routing. The backend API is implemented in FastAPI (Python), managing REST endpoints, validation, and middleware. MongoDB serves as the document-based storage layer for users, complaints, and notifications. Ollama models provide the local AI runtime for vision extraction, reasoning, and draft generation. Docker Compose achieves full-stack orchestration for both development and production deployments. pytest, httpx, and Locust are used across unit, integration, security, resilience, and load test scenarios.

---

### 1.6 Problem Context and Motivation

India's national grievance infrastructure is large enough that routing accuracy is an operational issue, not merely a clerical one. The CPGRAMS Annual Report 2022–23 recorded over 19 lakh complaints received at the national level in that financial year. A consistent delay pattern is observed on urban local body portals: when a complaint is routed to the wrong department, it typically takes a further three to five working days to reach the correct one, with each transfer restarting the review cycle. For services such as Civil Works or Vector-Borne Disease Control, even a single day's delay can meaningfully affect field response outcomes.

Jan-Sunwai AI addresses this bottleneck by integrating image-based classification with a deterministic routing engine, offloading the cognitive burden of department selection from citizens who have no institutional knowledge of how municipal departments are organised. Governance authority over ambiguous cases remains with human administrators, who adjudicate low-confidence classifications through a dedicated triage queue. The balance between AI-assisted automation and human institutional control is the core architectural principle of the system.

---

### 1.7 Literature Review

The literature review for this project concentrates on civic-tech complaint systems, AI-assisted classification workflows, and governance requirements such as explainability and traceability. Rather than treating model accuracy as the only success criterion, the review emphasises operational outcomes — routing correctness, audit readiness, and response-time reliability — in public-sector environments. The architectural approach taken for Jan-Sunwai AI was shaped by this practical lens.

#### 1.7.1 Complaint Systems and Digital Governance

Digital grievance platforms are known to enhance civic engagement and service responsiveness. At the national level, schemes such as the Centralised Public Grievance Redress and Monitoring System (CPGRAMS) have established examples of electronic complaint routing across ministerial departments. Likewise, under the Smart Cities Mission, municipal bodies have deployed local civic portals through the National Informatics Centre (NIC) with the intent of bringing e-governance to citizens. Yet, even with these advances, many of these systems remain structurally driven by form-based and text-heavy interfaces. They require citizens to have a high degree of procedural awareness, correctly selecting the responsible department from complex dropdown menus — a significant obstacle for users with limited digital literacy.

The quality of the first citizen-submitted complaint is repeatedly highlighted in the literature as directly correlated with the efficiency of downstream processing. When a grievance is miscategorised at intake, it enters a lengthy inter-departmental transfer process. Jan-Sunwai AI aims to address this specific challenge in the Indian e-governance space by replacing text-heavy categorisation forms with an intuitive image-driven interface, shifting the burden of classification from the citizen to the machine.

#### 1.7.2 Vision-Language Models in Public Workflows

Advanced vision-language models (VLMs) such as Qwen2.5-VL and Granite-3.2-Vision demonstrate strong reasoning capabilities directly applicable to public administration workflows, but they also pose new challenges. A VLM may accurately describe a broken water pipe leaking onto a road, yet struggle to determine whether the issue should be routed to the Water Authority or the Public Works Department. Purely generative approaches therefore tend to produce uncertain jurisdictional decisions. Based on established practice, the best approach is to use the VLM exclusively for context extraction, and then apply a layer of deterministic, rule-based control for the actual governance routing. Future improvements could include fine-tuning local models on regional municipal taxonomies, reducing reliance on pre-established symbolic rules and improving routing accuracy further.

#### 1.7.3 Local Inference and Privacy

In many public institutions, citizen data is subject to operational constraints that require it to remain within a protected infrastructure boundary. Local inference minimises external data transfer and provides greater control over the model lifecycle, but introduces operational considerations around VRAM budgeting, process health, and failover behaviour. This project treats local inference not merely as a performance decision but as a policy-aware technical choice.

#### 1.7.4 Hybrid Deterministic + AI Pipeline

To reduce the unreliability of end-to-end deep learning in high-stakes settings, hybrid pipelines combine neural networks with symbolic reasoning architectures. In this staged approach, a vision model handles perceptual tasks such as debris detection or structural damage identification, while a traditional rules engine handles logical routing to specific departmental SLAs. This separation of concerns significantly reduces the risk of hallucination associated with LLMs. Jan-Sunwai AI uses this hybrid pattern to ensure that any image misclassified by the AI is still assigned to one of a finite number of acceptable municipal categories, making the system predictable during audit.

#### 1.7.5 Governance, Explainability, and Auditability

Civic applications must meet higher standards of accountability and transparency than commercial software, as they are bound by legislated mandates of public access. Denial or redirection of services to citizens by automated systems must be explainable — it is both a legal and ethical requirement, not an implementation detail. Research into Human-in-the-Loop (HITL) machine learning strongly suggests the need for systems in which AI does not act as an independent agent, particularly in areas involving public welfare.

Jan-Sunwai AI was built with full decision provenance. Each state transition records the responsible actor, the time of the transition, and, if it is an automated transition, the specific confidence level at which it was triggered. Low-confidence AI decisions are placed in a manual triage queue, meaning human intervention is required before the complaint is progressed. Human administrators remain the ultimate decision-makers in complex civic disputes.

#### 1.7.6 System Comparison

To validate the proposed architecture and move from a descriptive to an analytical basis, this section of the literature compares the performance of traditional grievance portals against the Jan-Sunwai AI hybrid system. The project is designed in accordance with the principles and reference documentation of FastAPI, React, and MongoDB, as discussed in Chapter 9.

---

### 1.8 Chapter Summary

This chapter defined the problem context, project intent, scope boundaries, and foundational technology decisions. It also established the literature-based rationale for combining AI with deterministic governance controls in a municipal context. The next chapter outlines project planning, feasibility evaluation, scheduling, and delivery governance.

---

## Chapter 2: Project Management

Project management for Jan-Sunwai AI was conducted using an iterative delivery approach with clear weekly action milestones, attended gate reviews, and operational hardening gates. The planning strategy managed feature growth while reducing risk, particularly around AI availability, security posture, and deployment repeatability.

---

### 2.1 Feasibility Study

Feasibility was evaluated both before and throughout implementation. Rather than treating it as a one-time document, feasibility was used as an ongoing checkpoint, because model behaviour, deployment constraints, and the complexity of user workflows changed across iterations.

#### 2.1.1 Technical Feasibility

Technical feasibility was assessed through progressive integration rather than theoretical assumption. The React frontend, FastAPI backend, MongoDB store, Ollama runtime, and Docker orchestration were brought into functional contact within the first two weeks of the project. Health endpoints were defined and validated for each service dependency, and setup scripts were created and verified to be idempotent on both Windows and Linux hosts. The primary technical risk identified at this stage was VRAM contention under concurrent inference requests, which led to the introduction of an asynchronous generation queue — rather than processing all AI requests synchronously — in a later phase.

#### 2.1.2 Time Schedule Feasibility

To assess time feasibility, the full feature scope was decomposed into four phases: foundation (core complaint lifecycle, authentication), feature development (AI pipeline and role onboarding), security and reliability hardening, and delivery preparation (dashboards, documentation, and deployment). An eighteen-week window was mapped to this decomposition, with milestone dates and acceptance criteria defined at phase boundaries. The schedule was reviewed weekly against actual delivery progress, and scope was managed to ensure that hardening and documentation were not compressed to accommodate late feature additions.

#### 2.1.3 Operational Feasibility

Operational feasibility was demonstrated by establishing role-based workflows for all four user personas. Each persona was mapped to a distinct set of interactions, and all were end-to-end validated using manual UAT scripts before the relevant phase was considered closed. Key operational benchmarks included: a citizen with limited digital literacy being able to upload an image and submit a complaint without assistance, and an administrator being able to make a triage decision on a queued item in under two minutes on average.

#### 2.1.4 Implementation Feasibility

Implementation feasibility was substantiated through the successful containerisation of the stack. Setup scripts, environment templates, and validation routines were implemented for both development and production Docker Compose configurations. The ability to reproduce a working deployment from a clean machine using a single command sequence was the acceptance criterion for this feasibility dimension.

---

### 2.2 Project Planning

Project planning translated broad project goals into deliverable slices of work with clear milestones, quality gates, and integration checkpoints. Planning was deliberately cross-functional, so that backend APIs, frontend role flows, AI services, and deployment scripts developed in tandem rather than in isolation. This structure minimised integration shocks and provided predictable weekly review cycles.

#### 2.2.1 Development Approach and Justification

A sequential waterfall model was not a good fit for this project because the AI layer and the role-based user flows required adjustment several times as implementation details became clear. Work progressed in short, verified steps. Each increment began with unit and integration checks, then surfaced the relevant role workflow into the interface for end-to-end validation, followed by security and performance stabilisation. Release notes and operational steps were only documented after these checks passed, so that handover artefacts reflected the version that was actually ready for delivery.

#### 2.2.2 Milestones and Deliverables

Milestones and deliverables were tracked in weekly slices against project governance checkpoints:

- **Foundation phase:** Core schema, baseline complaint lifecycle, and authentication.
- **Feature phase:** AI-powered analysis, worker assignment, role dashboards, and notifications.
- **Hardening phase:** Upload security, resilience handling, and load/security verification.
- **Delivery phase:** Deployment validation, final documentation, and report artefacts.

#### 2.2.3 Roles and Responsibilities

A responsibility matrix defined cross-functional ownership areas for delivery.

#### 2.2.4 Group Dependencies

The project had cross-cutting dependencies that were managed explicitly:

- The backend relies on a reachable MongoDB instance and correctly configured environment variables.
- The analysis flow depends on the health of the file storage service and the Ollama runtime.
- Frontend route behaviour is tied to cookie-session state and role claims.
- Assignment quality depends on the completeness of worker profiles (department, service area, and status).
- Production readiness requires proxy alignment, Compose health checks, and correct secret configuration.

Dependency risks were mitigated through health endpoints, fallback behaviours, and scripted verification routines.

---

### 2.3 Project Scheduling

The Gantt chart for the project shows the distribution of foundation, core development, security hardening, and delivery activities across the 18-week window.

---

### 2.5 Management Outcomes

The iterative delivery strategy produced three noteworthy outcomes. First, 100% feature delivery was achieved without pushing security or reliability hardening to a post-feature phase — a common failure mode in project timelines where feature work consumes all available time. Second, ongoing automated testing and rapid issue identification ensured delivery confidence across every integration cycle. Third, handover readiness was built progressively, with deployment artefacts, environment documentation, and an API reference generated during the final two weeks rather than collected retroactively.

---

### 2.6 Chapter Summary

This chapter demonstrated that the project was technically feasible, deliverable within a defined timeframe, and managed within a clear governance structure. Feasibility, dependency management, risk planning, milestone tracking, and measured progress collectively guided the project toward a production-oriented civic platform.

---

## Chapter 3: Requirements Analysis

This chapter details the system requirements that form the baseline for Jan-Sunwai AI. It covers existing grievance procedures, user characteristics, actor expectations, and formalised functional and non-functional requirements. The analysis was grounded in implementation realities, municipal workflow observation, and testing of user journey assumptions.

---

### 3.1 Existing System Overview

Traditional civic grievance mechanisms typically rely on one or more of the following interfaces: physical counters, simple web forms, call centre logging, or general ticketing portals. While these methods allow complaints to be submitted, they are associated with poor input quality, manual routing, low traceability, and heavy dependency on staff intervention.

Key observed characteristics of existing systems include:

- Citizens are required to select departments themselves, without adequate guidance.
- Complaint narratives are text-heavy and unstructured, with inconsistent detail quality.
- Photographic evidence may be accepted but is rarely used to inform routing decisions.
- Status updates are intermittent or delayed.
- Audit trails lack workflow metadata — who changed what, and why.
- Historical retrieval and reporting are difficult.

The weaknesses identified across civic complaint platforms can be categorised into several distinct areas. Citizen-driven department selection is the most structurally significant weakness: it passes classification responsibility to the population least equipped to exercise it correctly. Complaints sent to the wrong department must be reviewed and transferred before any action can be taken, and each transfer consumes a full review cycle. Complaint narrative quality is highly variable, as unstructured free-text fields generate descriptions ranging from detailed to barely factual, requiring staff to seek clarification before field action can be authorised. Photographic evidence, where accepted, is treated as an attachment rather than a routing input, meaning the most objective record of the issue is never used in classification. The lack of role-specific interface design means that field workers, department supervisors, and system administrators interact with functionally identical interfaces despite having very different information needs. Lifecycle traceability is insufficient for governance purposes due to the absence of actor attribution for state transitions and timestamps. Escalation justification and post-resolution review are not supported, and public visibility into queue behaviour is limited, which erodes citizen trust over time.

---

### 3.3 User Characteristics

Four distinct operational personas were identified during requirements analysis, each with characteristic interaction patterns and clear authorisation boundaries.

**Citizens** are the largest user group. Their interaction with the platform is concentrated in two stages: submission and tracking. At submission, a citizen uploads photographic evidence, reviews the AI-generated draft complaint, optionally edits the description or category, and confirms submission. At tracking, the citizen receives updates through the notification panel and the complaint detail view.

**Field Workers** access the platform primarily through their assigned task queue. A worker sets their own availability status, reads the details and location of a complaint, and creates a resolution note marking the assignment as complete after a successful field intervention.

**Department Heads** have supervisory oversight of the complaint queue for their department. They update status with explanatory notes, transfer complaints to neighbouring departments when jurisdictional analysis indicates misassignment, and escalate cases to parent authorities when issues exceed departmental capacity or authority.

**Administrators** hold end-to-end governance rights. Their responsibilities include approving or rejecting worker registration applications, adjudicating the triage queue for low-confidence AI classifications, performing high-volume status operations on complaint backlogs, exporting complaint datasets as CSV files, and monitoring system-wide analytics.

---

### 3.6 Hardware and Software Requirements

A minimum hardware configuration of a four-core processor (eight-core recommended), 16 GB of system RAM, 4–6 GB of GPU VRAM, 10–20 GB of storage, and a reliable internet connection is required for functional operation. The software baseline is Windows 10 or later, or Ubuntu 22.04 LTS or later, with Python 3.10 or later, Node.js v20 LTS or later, MongoDB 7.x, the Ollama runtime, Docker and Compose 24 or above, and a modern web browser.

---

### 3.7 Constraints

The project is subject to governance and usability constraints beyond purely technical ones. The platform must operate under the security, role-separation, and infrastructure limitations common in civic settings without sacrificing clarity for citizens or efficiency for officials.

#### 3.7.1 UI Constraints

Access boundaries are enforced on role-specific pages. Interfaces accommodate mobile widths down to a 375 px base and must support page refresh without loss of data state, allowing users to restore context after reconnecting.

#### 3.7.2 Communication Interface

Communication is restricted to authenticated REST endpoints using secure cookie sessions only, with routing through the `/api/v1` proxy and a restricted CORS policy.

#### 3.7.3 Hardware Interface

As a closed-system deployment, local inference is bound by the available VRAM of the host machine, causing AI response times to vary under load. Large file uploads are strictly limited and subjected to size and content verification to avoid resource waste.

#### 3.7.4 Criticality of Application

The application routes and tracks public grievances and is operationally critical for civic accountability. A sustained outage would delay the city's ability to respond in the field and reduce citizen confidence in service provision.

#### 3.7.5 Safety and Security Considerations

The system runs on locally installed infrastructure to ensure citizen trust and data privacy. Status history and role checks are permanent. Defence-in-depth is achieved through input sanitisation, MIME-type validation, robust token security headers, and lifecycle controls.

---

### 3.8 Assumptions and Dependencies

Several key assumptions underpin the system. First, a reachable and healthy MongoDB instance is required for all read/write persistence. Second, the Ollama runtime must be correctly configured with the appropriate vision and reasoning models to support image analysis and draft generation. Third, environment variables must be correctly configured for stable authentication, CORS, and database mapping. Fourth, the system assumes completeness of worker profile data — including department and service area metadata — for the auto-assignment engine to function correctly. Finally, production deployments require the host to support Docker and Compose in order for environments to be reproducible.

Requirements are categorised using the MoSCoW methodology. Must-Have features include user registration, authentication, complaint intake, status updates, auto-assignment, and health monitoring — all of which are critical for operational viability. Should-Have features cover authority escalation, worker status controls, the administrative triage queue, and analytics, which together provide institutional-grade governance. Could-Have features — CSV exports and the public transparency feed — add high-value reporting without disrupting the main workflow. Non-functional requirements such as session security, input sanitisation, and observability are treated as minimum baseline controls rather than optional enhancements.

---

### 3.9 Chapter Summary

The requirements analysis defined the transition from a manual grievance process to a secure, structured, and auditable digital workflow. Functional and non-functional requirements were formalised in terms of implementation-ready specifications, realistic user roles were mapped to operational constraints, and the MoSCoW methodology was applied to prioritise delivery.

---

## Chapter 4: Proposed System

This chapter describes the proposed Jan-Sunwai AI solution architecture from a requirements-realisation perspective. While Chapter 3 documented the required conditions, this chapter explains how the proposed system meets those requirements through modular features and integrated workflows using the React, FastAPI, MongoDB, and Ollama stack.

---

### 4.1 Overview of Proposed System

The proposed system is a role-based civic complaint platform that integrates AI-based complaint assistance with deterministic governance controls. Rather than using a monolithic architecture, a layered approach is used with strict module boundaries, combining a hybrid inference pipeline with a flexible document-store database. These architectural choices allow the platform to operate in resource-limited municipal environments while maintaining strict auditability and data residency.

The system can be represented as five stages:

1. **Complaint Intake:** A citizen posts an image and requests analysis.
2. **AI Enrichment:** The system identifies probable categorisation, location clues, and a preliminary draft description.
3. **Citizen Review:** The citizen reviews, optionally edits, and confirms the complaint payload.
4. **Operational Routing:** The complaint is assigned, tracked, and escalated where necessary.
5. **Governance and Transparency:** Notifications, analytics, exports, and a public feed support accountability.

---

### 4.2 Module Descriptions

The proposed system is designed as a set of cooperating modules, each with isolated and testable responsibility boundaries. This module-based decomposition also supports phased enhancement, meaning future upgrades can be applied to specific capability areas without destabilising the whole platform.

#### 4.2.1 Authentication and User Management Module

This module manages registration, login, session identification, profile updating, and password recovery. It applies role-based permissions for citizen, worker, department head, and admin roles, and enforces secure cookie-session issuance, role checks, JWT compatibility for API clients, and reset-token hashing.

#### 4.2.2 Analyse and Complaint Intake Module

This module processes uploaded images, invokes the hybrid classifier pipeline, extracts location coordinates and metadata, and coordinates draft production. Both immediate and queued generation paths are provided, with timing metadata returned for observability.

#### 4.2.3 Complaint Lifecycle Module

This module stores grievances and controls state changes including status updates, transfers, escalations, feedback, notes, and comments. A status history record is appended at each transition to maintain decision traceability.

#### 4.2.4 Assignment and Worker Operations Module

This module automatically assigns eligible workers using department matching, optional geospatial service-area checks, and active task load balancing. It also provides worker status control and completion signalling.

#### 4.2.5 Notification and Communication Module

This module sets up in-app notifications for complaint lifecycle events and maintains unread notification counters. It contains a stub for email relay in deployment environments where SMTP integration is required.

#### 4.2.6 Triage and Governance Module

This module allows administrators to review classifications rated as low confidence, taking corrective actions such as Approve, Reject, or Relabel. The triage path serves as a governance safety net for AI uncertainty.

#### 4.2.7 Analytics and Public Transparency Module

This module aggregates operational statistics, trend lines, and geospatial heatmap data. It also exposes an anonymised public feed to ensure transparency without revealing personally identifiable information.

---

### 4.4 Advantages of Proposed System

The proposed solution delivers measurable value at three levels: citizen experience, administrative throughput, and institutional governance. The selected architecture (FastAPI + React + MongoDB + Local LLM) improves on simpler monolithic alternatives in several ways. The document model in MongoDB is better suited to civic records, which accumulate unstructured state changes — such as added notes and timing information — without requiring costly relational joins. The hybrid AI approach means that the non-deterministic nature of vision models is bounded by hard-coded deterministic routing rules, making the system considerably more reliable for public service than a pure generative classifier.

#### 4.4.1 Citizen-Centric Advantages

Benefits for citizens are a direct result of the image-first intake and AI-assisted drafting architecture:

- Easier complaint filing with image support
- Improved complaint quality through formally generated drafts
- Real-time feedback via status updates and notification channels
- Reduced confusion around which municipal department to approach

#### 4.4.2 Administrative and Departmental Benefits

Within administration, the module boundaries and assignment automation translate into measurable operational gains:

- Improved routing for standard cases and reduced manual triage
- Full lifecycle auditability of supervisory and escalation actions
- Faster management of assignments and backlog through automation and bulk operations
- Structured data for reporting and policy-level analysis

#### 4.4.3 Institutional Advantages

The deployment architecture provides compliance and handover advantages not achievable with ad-hoc cloud-based designs:

- Local-first inference satisfies data residency requirements
- Containerised deployment ensures repeatable deployments and clean institutional handovers
- API versioning provides integration stability
- Security hardening and validation controls reduce common exploit surfaces

---

### 4.7 Expected Impact

AI-assisted drafting during image intake is expected to significantly reduce the variation common in citizen free-text submissions, improving complaint quality. Routing reliability should also improve, as the authority-mapping engine reduces the first-hop reassignment delays noted earlier. Governance is reinforced through status timelines, mandatory notes at every transition, and a formal escalation path. Citizens receive more tangible progress evidence through notifications and workflow updates. Departmental trend data and geospatial heatmaps provide improved planning signals for administrators, and deployment becomes more reproducible through the standardised Compose and environment management strategy. These gains remain dependent on the quality of institutional adoption, administrator training, and the completeness of worker profile data at launch.

---

### 4.8 Module Interaction Contracts

Explicit contracts between system modules enable role-based isolation and functional consistency:

- **Authentication Module** delivers the current user's identity and role claims to all protected routers.
- **Analyse Module** generates classification, location, and draft payloads for the Complaint Lifecycle module.
- **Complaint Lifecycle Module** sends events to the Notification module and initiates auto-assignment routines at complaint creation or reassignment.
- **Worker Module** provides completion status reports that affect status history and lifecycle state.
- **Triage Module** applies corrected decisions for low-confidence records to the primary complaint data store.
- **Analytics and Public Modules** execute aggregate queries on the complaint store to expose anonymised trends and heatmaps.
- **Health Module** publishes liveness and readiness status by probing the database and local model runtime.

---

### 4.9 Requirement Realisation by Persona

Each persona is served by a specific feature set. Citizens benefit from image-based intake, a tracking dashboard, notifications, feedback, and password reset — all designed to minimise filing friction and maximise visibility. Field Workers receive structured task queues, progress feedback, and completion actions. Department Heads have department-level filtering, status updates, transfer and escalation actions, and a notes facility for controlled supervisory governance. Administrators hold full operational governance — worker approvals, triage decisions, bulk operations, analytics, and exports. Public Viewers can access the anonymised complaint board without any personally identifiable information being disclosed.

---

### 4.10 Data and Control Flow

The proposed flow deliberately separates the source of suggestions from the authority to act on them. AI modules propose categories and draft text, but acceptances and lifecycle transitions are controlled through authenticated role actions. This hybrid control plane reduces the risk of over-automation while still meaningfully reducing manual effort in high-volume intake scenarios.

---

### 4.11 Chapter Summary

The proposed system translates requirement intent into integrated modules that collectively address user friction, operational traceability, and governance accountability. It deliberately combines AI assistance with deterministic controls and administrative safety nets, making it suitable for realistic municipal settings.

---

## Chapter 5: System Design

This chapter explains the structural design decisions, module interactions, and data modelling strategies that enable Jan-Sunwai AI to function as a safe, local-first civic grievance platform. The architecture is modular, with AI components kept clearly separated from deterministic governance workflows.

---

### 5.1 System Architecture Design

The platform is designed as a multi-tier Client–Server application, optimised for local execution with containerised boundaries.

#### 5.1.1 Overall System Context

The system connects four main personas — Citizen, Worker, Department Head, and Admin — to a centralised governance core. The context diagram illustrates the data exchange between these actors and the platform services.

#### 5.1.2 AI Classification Pipeline

The AI pipeline uses a hybrid vision-cascade and rule-engine scoring model to provide high-confidence routing while ensuring a human-in-the-loop for ambiguous cases.

---

### 5.2 UML Diagrams

The UML diagrams included in the project report and API references cover module boundaries, routing flow, and lifecycle stages.

**Data Flow and Rationale:** This diagram illustrates how complaint records act as the central hub connecting users, workers, and notifications. By embedding status history directly within the complaint entity, the design reduces expensive relational joins when rendering dashboards.

**Role Segregation and Governance:** This diagram represents the strong access restrictions enforced by the system. Citizens hold broad rights to file and track complaints, while state mutations such as resolving or rejecting complaints are restricted to authenticated workers and department heads. It visually reinforces the governance principle that AI assists but humans retain final decision-making authority.

**Data Encapsulation:** The class structure reflects the document-oriented database design, with complex types such as geolocation and timestamps embedded rather than relationally linked. This involves some loss of normalisation but allows a single Complaint object to be retrieved with complete operational context for dashboard rendering.

**Interaction Logic:** The sequence diagram traces a complaint from image upload through AI analysis, citizen confirmation, and worker assignment. It highlights the asynchronous AI-generation queue, which was introduced to prevent LLM inference delays from blocking the main user experience.

**Workflow States:** The activity diagram represents the internal decision logic for triaging low-confidence classifications. It demonstrates how reasoning models (such as Llama 3.2) are invoked selectively — only when the initial vision cascade confidence falls below a defined threshold.

---

### 5.3 Database Design

Database design prioritised lifecycle integrity, query efficiency, and auditability over strict relational normalisation. Because complaint records pass through many states and accumulate actor interactions over time, the selected document model closely mirrors the operations performed on it.

#### 5.3.1 Collections and Relationships

The database comprises four main collections:

- **users:** Identity, role, and worker service-area metadata.
- **complaints:** Application-layer complaint payload, routing metadata, status history, and collaboration artefacts.
- **notifications:** User-scoped notification events and read-state tracking.
- **reset_tokens:** Password reset token hash lifecycle with expiry and usage state.

The design deliberately keeps lifecycle and audit structure embedded within complaint documents for retrieval locality.

#### 5.3.2 Normalisation

The platform implements controlled denormalization:

- `status_history`, `dept_notes`, and `comments` are embedded, reducing query complexity.
- Core identity references for role and profile are kept external to support updates.
- Routing metadata is persisted with complaint records to ensure deterministic decision context is preserved over time.

This approach maintains operational performance optimised for read operations while preserving familiar ownership semantics.

#### 5.3.3 Data Dictionary

The data dictionary summarises important entities and their roles in operational workflows.

#### 5.3.4 Indexing Strategy

Key indexing strategies are documented in the system design chapter.

---

### 5.4 GUI Design

GUI design was based on a task-oriented interface model, where each role is presented only the controls and information relevant to their expected work. Responsive behaviour, visual hierarchy, and workflow clarity were treated as core functional requirements. The resulting interface strategy focuses on task completion, avoids ambiguity, and provides clear feedback.

#### 5.4.1 Design Principles

The UI adheres to governance portal best practices:

- Purposeful use of visual detail without decorative clutter
- Clear distinction between navigation and action controls
- Immediate reflection of status and notification changes
- Responsive behaviour supporting both desktop operator screens and mobile field use

#### 5.4.2 Interface Areas

Key interface areas include:

- **Public Home:** Awareness content, transparency access, and role entry points
- **Authentication:** Login, registration, and password retrieval
- **Analyse and Result Views:** Image upload, AI analysis visualisation, interactive maps, and draft review
- **Citizen Dashboard:** Personal complaint list, lifecycle timeline, feedback, and progress visibility
- **Worker Dashboard:** Assigned task queue with update and completion actions
- **Department Head Dashboard:** Department-level filtering, status updates, and note-taking
- **Admin Dashboard:** Global queue access, worker approvals, triage, bulk actions, analytics, and exports
- **Notifications and Profile:** Event feeds, read states, and personal information updates

---

### 5.6 Chapter Summary

This chapter introduced the structural design decisions, module interactions, data modelling strategy, and UI architecture. The design is centred on the principles of traceability, secure operations, and maintainability, supporting AI assistance within a municipal governance setting.

---

## Chapter 6: Implementation Planning

Implementation planning for Jan-Sunwai AI was organised around three parallel goals: reproducibility, sustainable module growth, and deployment readiness. The development strategy treated the backend, frontend, AI runtime, and operational scripts as interdependent workstreams rather than isolated code tracks. The project is currently in prototype mode rather than full production-handover readiness.

---

### 6.1 Implementation Environment

The implementation environment was designed to maintain high developer productivity while preserving deployment realism. It supports both fast local iteration and production-quality container verification, with all configurations, health checks, and service contracts aligned. This dual-mode approach minimises environment drift and ensures that validated behaviour during development remains reliable at handover and deployment.

#### 6.1.1 Local Development Environment

The local workflow allows rapid iteration with role-based UI and backend validation. A typical development topology consists of:

- FastAPI/Uvicorn backend running on port 8000
- Vite frontend server running on port 5173
- A local or containerised MongoDB dependency
- Ollama runtime with model configuration on the host machine

The local setup was chosen to minimise iteration latency while maintaining high fidelity with the production environment through shared APIs, environment variables, and health semantics.

#### 6.1.2 Production-Style Container Environment

The project uses a unified Compose configuration with a production profile. In production mode:

- MongoDB runs as a monitored standalone service
- The backend is built using a production Dockerfile with uploaded files mounted to `/app/uploads`
- The frontend container runs as an Nginx service under the `prod` Compose profile
- Health checks and log rotation policies are clearly defined

This allows the same operational assumptions to be used for both local verification and deployment handover.

---

### 6.2 Tools and Technologies

**Backend and Database:** FastAPI router as the core API framework with dependency injection. Motor/PyMongo for async MongoDB access. Pydantic for strict schema validation.

**Auth and Security:** `python-jose` and `passlib[bcrypt]` for cookie-session/JWT compatibility and password hashing.

**AI and Image Pipeline:** Ollama for local vision and reasoning model execution. Pillow for upload payload validation and EXIF processing.

**Frontend Stack:** React as the role-aware SPA foundation, built and optimised with Vite. Axios for API communication and `react-router-dom` for protected role-based navigation.

**DevOps and QA:** Docker and Docker Compose for orchestrating reproducible environments. pytest and httpx for async API smoke testing. Locust for load testing.

---

### 6.3 Coding Standards

Important coding standards were applied across all modules to ensure independently testable and clearly bounded areas of responsibility. The backend used router-based domain isolation, strictly typed Pydantic request models, service extraction for cross-cutting concerns (storage, email, etc.), and structured logging with safe failure behaviour. The frontend enforced separation between role-aware route guards, reusable UI components, and context providers, with all asynchronous operations in explicit loading and error states. Configuration was centralised in a single environment template, which resolved a recurring "environment drift" problem between development and production that had been misattributed to individual developer errors.

---

### 6.4 Sequence of Implementation and Dependencies

1. Backend skeleton and DB connectivity (required before auth and complaint persistence)
2. Auth/session primitives (needed for protected API and role-specific frontend routes)
3. Analysis pipeline and storage handling (must be completed before citizen intake flow testing end-to-end)
4. Frontend analyse/result workflow (requires consistent analyse payload and auth behaviour)
5. Assignment engine (depends on complaint schema maturity and worker metadata)
6. Triage, analytics, and governance endpoints (depends on reliable complaint state and metadata richness)
7. Security and reliability hardening (should follow core flow stability to avoid hidden regressions)
8. Tests and UAT cycles (relies on stable feature slices and environments)
9. Production profile and handover documentation (depends on validated security and performance baseline)

---

### 6.5 Configuration and Secret Planning

The implementation plan focused on explicit secret handling and runtime configurability. Key control groups include:

- **Auth controls:** Cookie-session settings, JWT secret and algorithm, token expiry, and compatibility mode
- **Data controls:** MongoDB URL and database selection
- **AI controls:** Model identifier, timeout windows, and queue worker count
- **Security controls:** CORS origin allowlist and rate-limiter mode
- **Notification relay:** SMTP host, port, and sender address

An important planning change was the consolidation to a single canonical backend environment file, which eliminated the drift between local and production templates.

---

### 6.6 Resource and Effort Planning

Effort was distributed across development, stabilisation, testing, and documentation phases. Rather than front-loading all testing to the end, regular verification cycles were scheduled after large feature groups. This reduced uncertainty in later stages and shortened defect turnaround time.

---

### 6.7 Detailed Module Implementation Notes

This section records implementation-level information of value for maintenance, future enhancement, and institutional handover.

#### 6.7.1 Router-Level Planning Notes

Each router group had defined responsibilities, and several specific engineering decisions emerged during delivery:

- **users:** Registration, login, and password reset. Required generic forgot-password responses persisted as hashes with expiration, to prevent account enumeration.
- **complaints:** Analyse, create, and update flows. Required consistent status-history append behaviour, strict role-aware update guards, and a graceful 503 degradation path for AI route failures.
- **workers:** Assignment handling and approvals. Clearly distinguishes between worker self-actions and admin governance actions, with diagnostic assignment endpoints for operational clarity.
- **notifications:** List and read-state management. Required consistent unread counter behaviour and strict ownership checks.
- **triage:** Admin-only corrective path for low-confidence AI cases. Requires detailed decision audit notes.
- **analytics:** Dashboards and public feeds. Query aggregation is currently un-paginated; safe data-exposure models are used for public-facing views.
- **health:** Operationally meaningful data with customisable thresholds for liveness, readiness, model, and GPU probes.

#### 6.7.2 Service-Layer Planning Notes

Core services were implemented as modular, independently scalable units:

- **Assign service:** Location-aware proximity filtering with fallback behaviour for missing metadata.
- **Storage service:** A validation pipeline covering extension, content-type, magic number, and payload decode checks.
- **Sanitisation service:** Implemented as a reusable, centralised, and independently testable utility.
- **Triage service:** Manages the lifecycle of low-confidence records and persists correction decisions in the audit trail.
- **Health service:** Combines multiple dependency status probes into a single liveness and readiness response.

---

### 6.9 Change Management and Release Strategy

Change management was designed to ensure that feature updates do not degrade stability, security, or governance controls. Each release cycle combines technical verification, documentation synchronisation, and rollback preparedness before production-oriented sign-off.

#### 6.9.1 Release Checklist

1. Ensure automated tests pass all backend and frontend quality gates.
2. Validate both default and production profile Compose configurations.
3. Verify security measures: headers, CORS allowlist, upload validation, and role restrictions.
4. Confirm that migration and index scripts produce the expected database state.
5. Review documentation updates (API changes, deployment steps, report references) before tagging the release.
6. Capture release notes with risk statements and rollback pointers.

#### 6.9.2 Implementation Learnings

A significant portion of weeks 11 and 12 was spent simplifying the environment configuration and Compose artefacts rather than implementing new features. This consolidation addressed recurring integration issues that had been misattributed to individual developer errors but were actually caused by configuration differences between the local and production templates. The operational effect of this seemingly simple change was comparable to a substantive feature delivery: it reduced the rate of deployment failures during verification runs and improved CI behaviour reliability. This experience confirmed that, in complex applied systems, structural simplification and documentation consistency are at least as important for delivery confidence as feature completeness.

---

### 6.10 Chapter Summary

Implementation planning was conducted around three concurrent priorities: reproducibility, structured module growth, and deployment-ready handover. Backend API development, frontend role workflows, AI service integration, and operational scripts were kept as interdependent workstreams rather than isolated tracks, minimising integration conflicts at weekly review cycles.

---

## Chapter 7: Testing

Jan-Sunwai AI testing was designed as a multi-layered approach encompassing automated testing, manual UAT scripts, resilience drills, and security and load validation. Because the platform supports governance-sensitive workflows, testing focused not only on functional correctness but also on operational integrity in degraded modes.

---

### 7.1 Testing Plan

The testing programme was designed to prove the correctness, security, and operational robustness of the system across the complete grievance process. Verification activities were not confined to a single test phase but were layered and repeated at critical implementation stages to prevent defects accumulating undetected until the end of the project.

#### 7.1.1 Testing Objectives

The objectives were framed around the types of failures a production civic system must defend against:

- Test the correctness of all main APIs and role authorisation boundaries
- Verify the AI path for valid, invalid, and failure situations
- Confirm notification chain consistency across complaint lifecycle changes
- Validate resilience behaviour under model and database disruption
- Ensure production readiness through integration, load, and UAT testing

#### 7.1.2 Test Environment

The testing environment baseline comprised:

- **Backend runtime:** FastAPI application with test clients and dependency overrides
- **Database mode:** MongoDB-backed flows with selective mocked data for isolated collection tests
- **Frontend mode:** Vite build and lint validation, with persona-driven manual walkthroughs
- **Model runtime mode:** Ollama available for normal flows, disabled for resilience checks
- **Automation tools:** pytest, httpx, Locust, and platform-specific execution wrappers

---

### 7.2 Types of Testing

Multiple testing types were used because the platform integrates API logic, role-sensitive workflows, AI-powered functionality, and deployment constraints.

#### 7.2.1 Unit Testing

Unit tests targeted isolated validation and control logic.

#### 7.2.2 Integration Testing

Integration tests verified route composition, middleware behaviour, and cross-router guarantees:

- Root and liveness endpoints confirmed the service-is-up response
- Versioned alias endpoints under `/api/v1` validated integration compatibility
- Security headers were validated in endpoint responses
- Preflight CORS behaviour was tested for allowed origins

#### 7.2.3 System Testing

System testing covered end-to-end workflows across authentication, analyse, complaint lifecycle, notification propagation, and assignment. This stage focused on continuity of behaviour rather than isolated endpoint correctness:

- **ST-01 (Citizen flow):** Upload, analyse, and submit — confirms the complaint record is created with status history initialised.
- **ST-02 (Dept Head update):** Status update by department head — confirms the citizen is notified and the transition appears in the timeline.
- **ST-03 (Worker completion):** Worker marks a complaint complete — confirms complaint transitions and worker slot logic update correctly.
- **ST-04 (Admin triage):** Admin triage decision — confirms an ambiguous complaint completes its label decision path as governed.
- **ST-05 (Data export):** Generates an export file and confirms it contains the expected schema columns.

#### 7.2.4 User Acceptance Testing (UAT)

UAT was implemented using persona scripts:

- **Citizen Script:** Login, analysis, map review, submission, and dashboard verification.
- **Admin Script:** Bulk actions, queue filtering, heatmap view, reassignment, and CSV export.
- **Feedback loop:** Friction capture and severity ranking, with follow-up fixes.
- **Resilience check:** AI service interruption and recovery behaviour in the UI.

#### 7.2.5 Performance and Load Testing

Load testing at baseline server configuration (48 GB RAM, H100 GPU) over 30 minutes with 50 concurrent users confirmed responsive API performance and graceful degradation at peak load. The deterministic routing threshold successfully routed ambiguous images with high accuracy.

---

### 7.3 Testing Techniques

Testing combined behavioural, negative, resilience, and load techniques for stability. Black-box testing validated API contracts from the consumer's perspective. Negative testing deliberately submitted corrupted uploads, invalid access tokens, and unauthorised role access attempts. Resilience testing verified controlled degradation under database unreachability and Ollama service failure. Load testing subjected read-heavy routes and background queues to simulated traffic and confirmed graceful fallback under heavy load.

#### 7.3.1 Defect Logging

Defects were recorded with a severity and impact model including reproduction steps, observed behaviour, expected behaviour, and fix status. Regressions were re-run against the appropriate unit and integration suites before closure.

#### 7.3.2 System Evaluation

The platform was validated to meet the intended civic workflow. The core CRUD application remained responsive during background AI processing. Fallback and escalation routes maintained service availability under model unavailability.

---

### 7.5 Residual Risks and Test Gaps

Major paths have been validated, but the following areas could be strengthened further:

- Long-duration soak tests on production-grade infrastructure
- An expanded browser matrix for UI consistency testing
- Fully integrated external vulnerability scanning in the release pipeline
- Evaluation of a higher-volume synthetic image corpus for tracking classifier drift

---

### 7.6 Chapter Summary

Testing integrated automation with operability validation. The resulting quality posture supports both technical confidence and governance readiness. Residual risks are documented with a clear roadmap for post-submission hardening.

---

## Chapter 8: Limitations and Future Scope

Jan-Sunwai AI was built within practical constraints: host-machine VRAM, municipal infrastructure, and the security posture of the organisation operating it. These limitations are documented here to facilitate realistic planning for the next stage of work, grounded in the conditions of actual deployment rather than an idealised environment.

---

### 8.1 Current Limitations

**Infrastructure capacity:** The local-first deployment model ties AI responsiveness to the VRAM availability of the host machine. Under concurrent analysis requests, queue depth can increase to a level that provides noticeably slower response times for citizens, particularly when running the platform on hardware below the recommended specification at municipal scale. The currently synchronous portion of the inference pipeline contributes to this constraint.

**Classification quality:** The hybrid pipeline correctly assigns the right department to most well-documented civic issues when images are clearly taken, but poor lighting, unusual scene composition, and ambiguous subjects continue to produce low-confidence results for the triage queue. The triage mechanism is a functional governance response to this, but a high triage queue volume places continuous pressure on administrators. Without a domain-specific fine-tuned model, this overhead is unlikely to be significantly reduced.

**Perimeter security:** The API layer is hardened against the most prevalent web vulnerabilities using the controls described in Chapter 6. However, external perimeter controls — such as web application firewall configuration, network segmentation, intrusion detection, and zero-trust access controls — are entirely dependent on the infrastructure management of the host municipal organisation. Deployment without appropriate perimeter controls would expose the platform to network-level attacks that the application layer alone cannot mitigate.

---

### 8.2 Future Scope

**Asynchronous pipeline scaling:** Moving from the current single-host Compose setup to a distributed message-broker architecture would allow the AI inference component to scale independently of the API service, enabling concurrent municipal-volume processing without degradation. This migration would require queue infrastructure such as Redis or RabbitMQ, along with updates to the LLM queue worker design.

**Localised model fine-tuning:** The current zero-shot approach to vision classification yields acceptable results, but would be significantly surpassed by a model fine-tuned on a labelled dataset of real municipal complaint images with correct department assignments. Building such a dataset from day-to-day complaints and using it to fine-tune a lightweight vision model would reduce misclassification rates and therefore the size of the triage queue.

**Automated SLA enforcement with external authority integration:** The current escalation mechanism is not automatic — it relies on a department head or administrator to trigger escalation once a resolution window has elapsed. Automated SLA enforcement, which generates escalation events when configured time thresholds are exceeded, would significantly improve accountability. Combined with direct API integration to higher-level grievance systems such as CPGRAMS, this would help close the gap between institutional response commitments and operational execution.

---

### 8.3 Chapter Summary

The limitations described in this chapter are real constraints that must be addressed through engineering investment before the platform can be considered production-grade at full municipal scale. The future scope items identified represent the highest-impact next steps toward reaching that goal.

---

## Chapter 9: Conclusion and References

---

### 9.1 Conclusion

Jan-Sunwai AI was built to demonstrate that AI-driven classification and deterministic governance controls can coexist in the same civic platform — neither compromising the auditability the platform requires nor imposing VRAM and cloud-API costs that municipal institutions cannot sustain. The core engineering value of the project lies in the architectural pattern: vision-language models are applied to perceptual extraction, while a set of deterministic rule layers and a human triage authority govern every decision at the point where a mistake could cause appreciable civic harm.

The most significant engineering lesson from the development period was not about model accuracy — it was about the behaviour of synchronous AI calls under load. Load testing with Locust revealed queue depth growth under concurrent analyse operations that would have produced unacceptable response latency at realistic usage volumes, even before any further model updates. The architectural shift to asynchronous generation, described in Chapters 5 and 6, converted a scalability problem into a manageable engineering tradeoff. This finding supports the argument in the literature review: civic platforms need to be designed for resilience under realistic conditions, not only for performance under ideal ones.

All technology decisions in the project are aligned with the reference documentation for FastAPI, React, MongoDB, and Docker. Local inference was adopted not as a cost-saving measure but as a principled response to data-residency requirements that are widespread in Indian municipal governance contexts. As illustrated in Chapter 8, the result is a reliance on local GPU capacity that will require either distributed scaling or infrastructure investment before the platform is ready to roll out at full municipal volume.

The project is presented not only as an application but as a reference architecture for privacy-respecting, local-first municipal civic technology. The proven combination of image-based intake, hybrid AI routing, human-governed triage, full audit trails, and containerised deployment offers a replicable blueprint that constrained institutions can adapt without surrendering control to black-box cloud services. The limitations documented in Chapter 8 are an honest account of what further engineering is needed before the platform can be considered production-grade at scale.

---

### 9.2 References

[1] United Nations, *UN E-Government Survey*, UN Department of Economic and Social Affairs. [Online]. Available: http://e-government.un.org/survey/

[2] World Bank, *Digital Government Toolkit*, World Bank Group, 2023. [Online]. Available: https://www.worldbank.org/en/topic/governance/brief/digital-government

[3] A. Radford et al., "Learning Transferable Visual Models From Natural Language Supervision," *Proceedings of the 38th International Conference on Machine Learning (ICML)*, 2021.

[4] Meta AI, "Llama 3.2: Edge AI and Vision," Sept. 2024. [Online]. Available: https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/

[5] A. d'Avila Garcez et al., "Neural-Symbolic Computing: An Effective Methodology for Principled Integration of Machine Learning and Reasoning," *FLAP*, vol. 6, no. 4, 2019.

[6] E. Mosqueira-Rey et al., "Human-in-the-Loop Machine Learning: A State of the Art," *Artificial Intelligence Review*, vol. 56, pp. 3005–3054, 2023.

[7] Center for Internet Security (CIS), "CIS Controls for Effective Cyber Defense." [Online]. Available: https://www.cisecurity.org/controls/ [Accessed: Apr. 7, 2026]

[8] NIST, "Zero Trust Architecture," NIST Special Publication 800-207, August 2020. [Online]. Available: https://csrc.nist.gov/publications/detail/sp/800-207/final

[9] IETF, "JSON Web Token (JWT)," RFC 7519, May 2015. [Online]. Available: https://tools.ietf.org/html/rfc7519 [Accessed: Apr. 7, 2026]

[10] SANS Institute, "Defensible Security Architecture and Engineering." [Online]. Available: https://www.sans.org/

[11] FastAPI, "FastAPI Documentation." [Online]. Available: https://fastapi.tiangolo.com [Accessed: Apr. 7, 2026]

[12] React, "React Documentation." [Online]. Available: https://react.dev [Accessed: Apr. 7, 2026]

[13] MongoDB, "MongoDB Documentation." [Online]. Available: https://www.mongodb.com/docs [Accessed: Apr. 7, 2026]

[14] MongoDB, "Data Model Design." [Online]. Available: https://www.mongodb.com/docs/manual/core/data-model-design/

[15] Pydantic, "Pydantic Documentation." [Online]. Available: https://docs.pydantic.dev [Accessed: Apr. 7, 2026]

[16] Docker, "Docker Documentation." [Online]. Available: https://docs.docker.com [Accessed: Apr. 7, 2026]

[17] Ollama, "Ollama Documentation." [Online]. Available: https://ollama.com [Accessed: Apr. 7, 2026]

[18] Locust, "Locust Documentation." [Online]. Available: https://docs.locust.io [Accessed: Apr. 7, 2026]

[19] R. T. Fielding, *Architectural Styles and the Design of Network-based Software Architectures*, Ph.D. dissertation, University of California, Irvine, 2000.

[20] DSDM Consortium, *The DSDM Agile Project Framework*, 2014. [Online]. Available: https://www.agilebusiness.org/

[21] W3C, "Mobile Web Best Practices." [Online]. Available: https://www.w3.org/TR/mobile-bp/

[22] D. Clegg and R. Barker, *CASE Method Fast-track: A RAD Approach*, Addison-Wesley, 1994. (MoSCoW prioritisation methodology)

[23] D. Ferraiolo et al., "Proposed NIST Standard for Role-Based Access Control," *ACM Transactions on Information and System Security*, vol. 4, no. 3, 2001.

[24] Ministry of Personnel, Public Grievances and Pensions, Government of India, "Annual Report 2022–23: CPGRAMS Performance Summary," New Delhi, 2023. [Online]. Available: https://pgportal.gov.in [Accessed: Apr. 7, 2026]
