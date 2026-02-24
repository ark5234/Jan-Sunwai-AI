# Jan-Sunwai AI

**Automated Visual Classification & Routing of Civic Grievances using Local Vision-Language Models**

Jan-Sunwai AI is a full-stack civic complaint platform that lets citizens photograph a civic issue -- pothole, garbage dump, broken street light, etc. -- and automatically classifies it, extracts the location, drafts a formal complaint letter, and routes it to the correct government department. Everything runs locally: no cloud API keys required.

---

## Table of Contents

- [How It Works](#how-it-works)
- [AI Pipeline](#ai-pipeline)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Windows](#windows-setup-script)
  - [Linux / Ubuntu](#linux--ubuntu-setup-script)
  - [Manual Setup](#manual-setup)
- [Running the Project](#running-the-project)
- [Civic Categories](#civic-categories)
- [User Roles](#user-roles)
- [API Endpoints](#api-endpoints)
- [Dataset Tools](#dataset-tools)
- [Environment Variables](#environment-variables)
- [Hardware Requirements](#hardware-requirements)

---

## How It Works

1. Citizen uploads a photo of a civic problem via the web app
2. Backend saves the image and sends it through the two-step AI pipeline
3. AI identifies the issue, picks a department, and drafts a formal complaint letter
4. GPS coordinates are extracted from the image's EXIF data (if available)
5. Complaint is stored in MongoDB and routed to the relevant department head
6. Department head logs in, reviews, and updates the complaint status
7. Citizen can track the status of their complaint in real time

---

## AI Pipeline

The system uses a **two-step Vision-to-Reasoning pipeline**, both running locally via Ollama:

```
Image File
    |
    v
+-----------------------------------+
|  Step 1 -- Vision (Eyes)          |
|  Model: qwen2.5vl:3b  (3.2 GB)   |
|  Describes what's wrong in the    |
|  image in 2-3 factual sentences   |
+----------------+------------------+
                 |  text description
                 v
+-----------------------------------+
|  Step 2 -- Reasoning (Brain)      |
|  Model: llama3.2:1b   (1.3 GB)   |
|  Maps description to one of 11    |
|  canonical civic categories       |
+----------------+------------------+
                 |  category + confidence
                 v
         Department routed OK
```

**Why two models instead of one?**
- `qwen2.5vl:3b` understands *actions and context* in images (e.g. "overflowing drain near a road"), not just visual similarity
- `llama3.2:1b` applies *rule-based reasoning* to map descriptions to categories, preventing model confusion
- Both models fit in 4 GB VRAM and run sequentially -- no simultaneous loading required

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, Uvicorn |
| Frontend | React 18, Vite, Tailwind CSS |
| Database | MongoDB (via Docker), Motor (async driver) |
| AI Runtime | Ollama (local GPU inference) |
| Vision Model | `qwen2.5vl:3b` -- image narration |
| Reasoning Model | `llama3.2:1b` -- category selection |
| Auth | JWT (OAuth2 password flow) |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
Jan-Sunwai-AI/
+-- backend/
|   +-- app/
|   |   +-- classifier.py        # Two-step vision-to-reasoning pipeline
|   |   +-- generator.py         # Formal complaint letter generation
|   |   +-- geotagging.py        # EXIF GPS extraction
|   |   +-- category_utils.py    # Canonical category definitions
|   |   +-- config.py            # Settings (env vars)
|   |   +-- database.py          # MongoDB connection
|   |   +-- auth.py              # JWT auth
|   |   +-- schemas.py           # Pydantic models
|   |   +-- routers/
|   |       +-- complaints.py    # /complaints -- main submission flow
|   |       +-- users.py         # /users -- auth + profile
|   |       +-- triage.py        # /triage -- offline batch triage
|   |       +-- health.py        # /health + /health/gpu
|   +-- automated_triage.py      # CLI: batch-sort images via Ollama
|   +-- evaluate_sorted_dataset.py  # CLI: evaluate sorting quality
|   +-- download_models.py       # CLI: pull Ollama models
|   +-- create_test_users.py     # CLI: seed test users
|   +-- requirements.txt
|   +-- Dockerfile
+-- frontend/
|   +-- src/
|   |   +-- pages/               # Home, Login, Dashboard, etc.
|   |   +-- components/          # UI components
|   |   +-- context/             # Auth + complaint context
|   +-- package.json
+-- docs/
|   +-- SYSTEM_ARCHITECTURE.md  # Full system documentation
+-- scripts/
|   +-- run_backend.bat / .sh    # Start backend
|   +-- run_frontend.bat / .sh   # Start frontend
|   +-- run_triage.bat / .sh     # Run batch triage
|   +-- run_tests.bat / .sh      # Run tests
+-- setup.ps1                    # Windows one-command setup
+-- setup.sh                     # Linux/Ubuntu one-command setup
+-- check_gpu.ps1                # Windows GPU check + driver install
+-- check_gpu.sh                 # Linux GPU check
+-- docker-compose.yml           # MongoDB container
```

---

## Quick Start

### Windows (Setup Script)

```powershell
git clone https://github.com/ark5234/Jan-Sunwai-AI.git
cd Jan-Sunwai-AI
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

The script automatically:
- Checks GPU / offers NVIDIA driver install (`check_gpu.ps1`)
- Installs Python 3.13 + creates `.venv` + installs all pip packages
- Installs Node.js LTS + `npm install` for frontend
- Installs Docker Desktop + starts MongoDB container
- Installs Ollama + pulls `qwen2.5vl:3b` and `llama3.2:1b` (~4.5 GB total)

**Only prerequisite:** NVIDIA drivers (any modern gaming PC already has these).

---

### Linux / Ubuntu (Setup Script)

```bash
git clone https://github.com/ark5234/Jan-Sunwai-AI.git
cd Jan-Sunwai-AI
chmod +x setup.sh check_gpu.sh
./setup.sh
```

The script automatically:
- Checks GPU via `nvidia-smi` / offers CUDA driver install (`check_gpu.sh`)
- Installs Python 3.13 + creates `.venv` + installs all pip packages
- Installs Node.js LTS + `npm install` for frontend
- Installs Docker + starts MongoDB container
- Installs Ollama + pulls both models

---

### Manual Setup

<details>
<summary>Click to expand</summary>

**1. Prerequisites**
- Python 3.11+, Node.js 18+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker + Compose (Linux)
- [Ollama](https://ollama.com/download) installed and running

**2. Pull AI models**
```bash
ollama pull qwen2.5vl:3b
ollama pull llama3.2:1b
```

**3. Start MongoDB**
```bash
docker compose up -d mongodb
```

**4. Backend**
```bash
cd backend
python -m venv ../.venv
# Windows:  ..\.venv\Scripts\activate
# Linux:    source ../.venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit JWT_SECRET_KEY at minimum
```

**5. Frontend**
```bash
cd frontend
npm install
```

</details>

---

## Running the Project

After setup, open **3 terminals**:

**Terminal 1 -- MongoDB:**
```bash
docker compose up -d mongodb
```

**Terminal 2 -- Backend:**
```bash
# Windows
scripts\run_backend.bat

# Linux
bash scripts/run_backend.sh
```

**Terminal 3 -- Frontend:**
```bash
# Windows
scripts\run_frontend.bat

# Linux
bash scripts/run_frontend.sh
```

Open **http://localhost:5173** in your browser.

**Verify:**
| URL | What it checks |
|---|---|
| http://localhost:8000/health | Backend + MongoDB connection |
| http://localhost:8000/health/gpu | GPU status + loaded Ollama models |
| http://localhost:8000/docs | Swagger UI (full API reference) |

---

## Civic Categories

| Category | Examples |
|---|---|
| Municipal - PWD (Roads) | Potholes, cracked pavement, bridge damage |
| Municipal - Sanitation | Garbage dumps, overflowing bins, dirty toilets |
| Municipal - Horticulture | Fallen trees, overgrown parks, uprooted plants |
| Municipal - Street Lighting | Broken lamp posts, dark roads |
| Municipal - Water & Sewerage | Waterlogging, blocked drains, sewer overflow |
| Utility - Power (DISCOM) | Dangling wires, open transformers |
| State Transport | Damaged bus shelters, broken state buses |
| Pollution Control Board | Industrial smoke, open burning, waste dumping |
| Police - Local Law Enforcement | Encroachment, illegal parking |
| Police - Traffic | Failed traffic signals, road blockage |
| Uncategorized | Does not match any above category |

---

## User Roles

| Role | Capabilities |
|---|---|
| `citizen` | Submit complaints, upload photos, track status |
| `dept_head` | View and manage complaints for their department |
| `admin` | Full system access, user management, all complaints |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/complaints/analyze` | Submit image -- classify + generate complaint |
| `GET` | `/complaints/` | List complaints (filtered by role) |
| `PATCH` | `/complaints/{id}/status` | Update complaint status |
| `POST` | `/users/register` | Register new user |
| `POST` | `/users/login` | Get JWT token |
| `GET` | `/health` | Backend + DB health check |
| `GET` | `/health/gpu` | GPU / Ollama model status |
| `GET` | `/docs` | Swagger UI |

---

## Dataset Tools

CLI scripts for offline dataset work -- not needed for normal app usage:

```bash
# Batch-sort a folder of images into category subfolders using the AI pipeline
python backend/automated_triage.py --input <image_folder> --output <output_folder>

# Evaluate how accurately a pre-sorted dataset was labeled (sample 20 per folder)
python backend/evaluate_sorted_dataset.py --sample 20

# Pull Ollama models
python backend/download_models.py
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and edit as needed:

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `JWT_SECRET_KEY` | *(change this)* | Secret for signing JWT tokens |
| `VISION_MODEL` | `qwen2.5vl:3b` | Ollama model for image narration |
| `REASONING_MODEL` | `llama3.2:1b` | Ollama model for category selection |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS whitelist |
| `LLM_INLINE_TIMEOUT_SECONDS` | `8` | Timeout for synchronous AI calls |

---

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| GPU VRAM | 4 GB (models run sequentially) | 6+ GB |
| System RAM | 12 GB free | 16 GB |
| Storage | 10 GB free (models + images) | 20 GB |
| OS | Windows 10+ or Ubuntu 20.04+ | Windows 11 / Ubuntu 22.04 |

> Models run **sequentially**, never simultaneously -- each fits in 4 GB VRAM alone.