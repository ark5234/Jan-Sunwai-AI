# Jan-Sunwai AI: Production Deployment Plan

## 1. Introduction
Currently, Jan-Sunwai AI operates as a **fully localized system**. The frontend (Vite), backend (FastAPI), database (MongoDB), and AI inference (Ollama) all run on a single host machine. While this is excellent for development, privacy, and cost-control, taking this system "live" for thousands of citizens requires significant architectural changes to ensure **scalability, high availability, security, and data persistence**.

This document outlines the changes required to transition from the current local environment to a production-grade live deployment.

---

## 2. Key Architectural Changes for Production

### 2.1. Frontend Hosting
*   **Current:** Served locally via Vite Dev Server (`npm run dev` at `localhost:5173`).
*   **Production:** The React code will be compiled into static HTML/CSS/JS (`npm run build`) and hosted on a **Global CDN** (e.g., Vercel, AWS S3 + CloudFront, or Nginx). This ensures fast loading times for citizens across different geographic locations.

### 2.2. Backend API Server
*   **Current:** Runs via Uvicorn on a single terminal process (`localhost:8000`).
*   **Production:**
    *   Deploy on cloud compute instances (AWS EC2, DigitalOcean Droplets, or Kubernetes).
    *   Run multiple worker processes using **Gunicorn** with Uvicorn worker classes.
    *   Place a **Reverse Proxy / Application Load Balancer** (Nginx, Traefik, AWS ALB) in front of the backend to distribute incoming traffic, handle SSL termination (HTTPS), and defend against DDoS attacks.

### 2.3. Image Storage
*   **Current:** Images are saved directly to the host machine's local file system (e.g., an `uploads/` folder).
*   **Production:** 
    *   Migrate to **Cloud Object Storage** (e.g., AWS S3, Cloudinary, or DigitalOcean Spaces).
    *   Instead of sending images through the backend, the backend will generate a *Presigned URL*, allowing the citizen's browser to upload the heavy image directly to the cloud bucket, saving backend bandwidth and storage space.

### 2.4. Database Management
*   **Current:** Local Dockerized MongoDB instance without persistent volume backups or replication.
*   **Production:** Use a managed database service like **MongoDB Atlas**. This provides automated daily backups, horizontal scaling, multi-region replica sets (ensuring the system stays up if one server crashes), and encrypted data at rest.

### 2.5. AI Inference & Queueing (The Heaviest Modification)
*   **Current:** FastAPI utilizes `asyncio.Queue` in memory and directly queries a local `Ollama` instance on the same machine. If the server restarts, the queue is lost.
*   **Production:**
    *   **Message Broker:** Introduce a persistent queue system like **Redis (via Celery/ARQ)** or **RabbitMQ**. When a citizen submits an issue, the task is safely stored in the broker.
    *   **GPU Worker Nodes:** Separate the API servers from the AI servers. Deploy dedicated GPU instances (e.g., AWS EC2 `g5.xlarge`, RunPod) running Ollama or `vLLM`. These instances will consume jobs from the Redis queue. If traffic spikes, auto-scaling groups can spin up multiple GPU nodes to drain the queue faster.

### 2.6. Security and Domain
*   **Current:** Running on unencrypted `http://localhost`.
*   **Production:** Purchase a domain (e.g., `www.jansunwai.gov`). Enforce strict HTTPS using SSL certificates (Let's Encrypt). Implement Cloudflare WAF (Web Application Firewall) to block malicious traffic.

---

## 3. Diagrammatic Differences

The structural diagrams evolve heavily from a simple, tightly-coupled monolithic box into a distributed, decoupled microservices network.

### 3.1. Current vs. Production Deployment Diagram

**Current Local Deployment:**
```mermaid
graph TB
    subgraph Host Machine
        Browser["Local Browser"] --> FE["Vite Dev Server (:5173)"]
        FE --> BE["FastAPI (:8000)"]
        BE --> DB[("Local MongoDB")]
        BE --> AI["Local Ollama Service"]
    end
```

**Production Deployment Diagram:**
```mermaid
graph TB
    Client["Citizen / Worker Browser"] -->|HTTPS| Cloudflare["Cloudflare (WAF / CDN)"]
    Cloudflare -->|Static Assets| S3_Static[("CDN Cloud Storage\n(Frontend React)")]
    Cloudflare -->|API Requests| ALB["Load Balancer (Nginx / AWS ALB)"]

    subgraph "API Tier (CPU Instances)"
        ALB --> API1["FastAPI Node 1"]
        ALB --> API2["FastAPI Node 2"]
    end

    subgraph "Storage Tier"
        API1 --> Atlas[("MongoDB Atlas\n(Managed Replica Set)")]
        API2 --> Atlas
        Client -.->|Direct Image Upload| S3_Images[("AWS S3 Bucket\n(Complaint Images)")]
    end

    subgraph "AI / Worker Tier (Asynchronous)"
        API1 --> Redis[("Redis Message Queue")]
        API2 --> Redis
        Redis --> GPU1["GPU Node 1\n(Celery/ARQ + Ollama)"]
        Redis --> GPU2["GPU Node n\n(Auto-scaled)"]
    end
```

### 3.2. Production Sequence Diagram: Complaint Submission

In the local environment, the API blocks or uses a local background task. In production, the workflow becomes truly asynchronous computing.

```mermaid
sequenceDiagram
    actor Citizen
    participant FE as Frontend (CDN)
    participant API as FastAPI Load Balanced
    participant S3 as AWS S3 Storage
    participant Redis as Redis Queue
    participant GPU as GPU Worker Node (Ollama)
    participant DB as MongoDB Atlas

    Citizen->>FE: Selects Photo
    FE->>API: GET /upload-url (Request Upload Token)
    API->>S3: Generate Presigned URL
    S3-->>API: URL Generated
    API-->>FE: Return Presigned URL
    
    Citizen->>S3: Upload heavy image file directly
    S3-->>Citizen: Upload Success
    
    Citizen->>FE: Submits Complaint Meta (Image URL, Language)
    FE->>API: POST /complaints/analyze
    API->>Redis: Publish Job { image_url, language }
    API-->>FE: Return Job ID (Status: Processing)

    Note over Redis, GPU: Fully decoupled AI processing
    
    GPU->>Redis: Consume AI Job
    GPU->>S3: Fetch Image via internal network
    GPU->>GPU: Vision + Rule Engine + LLM Drafting
    GPU->>DB: Save Generated Draft & Category
    GPU->>Redis: Mark Job Completed

    FE->>API: Poll /complaint/status/{job_id}
    API->>DB: Fetch Result
    API-->>FE: Draft Ready!
```

### 3.3. Production DFD Level 0 (Context Diagram)
The boundaries of the system expand to represent reliance on enterprise managed services.

```
                                    Jan-Sunwai AI (Production Cloud)
                  ┌────────────────────────────────────────────────────────┐
                  │                                                        │
Citizen ─────────►│  App Request                                           │
        ◄─────────│  React Frontend served via Global CDN                  │
                  │                                                        │
Citizen ─────────►│  Complaint Image (Sent Directed to Cloud Storage)      │
        ◄─────────│  AI Draft generated by GPU Cluster via Message Queue   │
                  │                                                        │
Workers/Admins ──►│  Access via Role-Based Load Balanced Gateways          │
               ◄──│  Real-time Sync via Cloud Replica Databases            │
                  │                                                        │
                  └─────────────┬──────────────────────────┬───────────────┘
                                │                          │
                      ┌─────────┴────────┐        ┌────────┴────────┐
                      ▼                  ▼        ▼                 ▼
                  Cloudflare          AWS S3     Redis          MongoDB Atlas
                    (WAF)            (Media)    (Queue)         (Managed DB)
```

### 3.4. Production System Architecture Diagram
A high-level view of how the decoupled modules interact.

```mermaid
flowchart TD
    subgraph Client 
        Browser[Citizen Browser]
        Worker[Field Worker App]
    end

    subgraph Security Layer
        WAF[Cloudflare WAF / CDN]
    end

    subgraph Cloud Infrastructure VPC
        ALB[Application Load Balancer]
        
        subgraph Compute Tier
            API[FastAPI Server Cluster]
        end
        
        subgraph Queue Tier
            Queue[(Redis Message Broker)]
        end
        
        subgraph AI Inference Tier
            AIWorker[AI Worker Service]
            vLLM[Dedicated vLLM / Ollama]
        end
    end

    subgraph Managed Data Services
        S3[(Cloud Object Storage)]
        Atlas[(MongoDB Atlas)]
    end

    Browser -->|HTTPS| WAF
    Worker -->|HTTPS| WAF
    WAF -->|API Calls| ALB
    ALB --> API
    API -->|Read/Write| Atlas
    Browser -.->|Direct Upload via Presigned URL| S3
    Worker -.->|Direct Upload via Presigned URL| S3
    API -->|Submit Job| Queue
    AIWorker -->|Consume Job| Queue
    AIWorker -->|Fetch Image| S3
    AIWorker -->|Vision + Language Inference| vLLM
    AIWorker -->|Save Generated Draft & Labels| Atlas
```

## 4. Summary

Taking the system live transitions Jan-Sunwai AI from a "research and development" profile to an "enterprise-grade" topology. By decoupling system components (separating the API from the heavy AI processing) and utilizing cloud-managed services (Cloud Object Storage, MongoDB Atlas, Redis message broker, and CDNs), the platform guarantees that thousands of citizens can concurrently report civic issues without dropping data, crashing models, or overwhelming the backend architecture.
