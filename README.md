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

The system uses a **4-step hybrid Vision → Rule Engine → Optional Reasoning → Writer pipeline**, running locally via Ollama with a Python rule engine (zero VRAM):

```
Image File
    |
    v
+---------------------------------------------+
|  Step 1 -- Vision Cascade                   |
|  Primary:   qwen2.5vl:3b      (3.2 GB)      |
|  Mid-tier:  granite3.2-vision:2b            |
|  Reads the image -> structured JSON:        |
|  { description, primary_issue, setting }   |
+--------------------+------------------------+
                     |  vision JSON
                     v
+---------------------------------------------+
|  Step 2 -- Rule Engine  (zero VRAM)          |
|  Deterministic keyword scoring across        |
|  10 civic categories.                        |
|  Confident match -> skip LLM reasoning       |
+--------------------+------------------------+
                     |  (only if ambiguous)
                     v
+---------------------------------------------+
|  Step 3 -- Optional Reasoning               |
|  Model: llama3.2:1b   (1.3 GB)             |
|  Only invoked when Rule Engine uncertain.   |
|  Picks the best civic category.             |
+--------------------+------------------------+
                     |  category
                     v
+---------------------------------------------+
|  Step 4 -- Complaint Writer                  |
|  Model: llama3.2:1b  (text-only)            |
|  Drafts a 60-90 word formal complaint.      |
|  No image re-read.                           |
+---------------------------------------------+
```

**Why the hybrid approach?**
- `qwen2.5vl:3b` understands *scene context* in images (e.g. "overflowing drain near a road"), not just visual similarity; falls back to `granite3.2-vision:2b` if primary times out or VRAM is low
- The **Rule Engine** runs instantly with zero VRAM — skips LLM reasoning entirely for obvious cases (most complaints)
- `llama3.2:1b` is loaded only for genuinely ambiguous images, saving ~1.2 GB VRAM in the common case
- All models fit sequentially in 4 GB VRAM — never loaded simultaneously

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, Uvicorn |
| Frontend | React 18, Vite 4, Tailwind CSS v4 |
| Map | react-map-gl v7 + MapLibre GL v3 (street + satellite toggle) |
| Database | MongoDB (via Docker), Motor (async driver) |
| AI Runtime | Ollama (local GPU inference) |
| Vision Model (primary) | `qwen2.5vl:3b` — image narration, structured JSON output |
| Vision Model (mid-tier) | `granite3.2-vision:2b` — fallback if primary times out or VRAM is low |
| Civic Rule Engine | Python keyword scorer — zero VRAM category selection |
| Reasoning Model | `llama3.2:1b` — ambiguous case classifier + complaint writer |
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
|   |       +-- triage.py        # /triage -- live MongoDB triage queue
|   |       +-- notifications.py # /notifications -- in-app alerts
|   |       +-- health.py        # /health + /health/gpu
|   |   +-- services/
|   |       +-- llm_queue.py     # Async LLM job queue (2 worker threads)
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
- Installs Ollama + pulls `qwen2.5vl:3b`, `granite3.2-vision:2b`, and `llama3.2:1b` (~7 GB total)

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
- Installs Ollama + pulls all three AI models (`qwen2.5vl:3b`, `granite3.2-vision:2b`, `llama3.2:1b`)

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
ollama pull granite3.2-vision:2b
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
| `POST` | `/complaints/analyze` | Submit image — classify + generate complaint (supports `language` param) |
| `POST` | `/complaints/analyze/regenerate` | Regenerate complaint draft (with language selection) |
| `GET` | `/complaints/` | List complaints (filtered by role) |
| `GET` | `/complaints/{id}` | Get single complaint |
| `PATCH` | `/complaints/{id}/status` | Update complaint status |
| `GET` | `/triage/review-queue` | Live queue of low-confidence complaints (confidence < 0.65) |
| `POST` | `/triage/review-queue/decision` | Approve / reject a triage item, optional dept override |
| `GET` | `/notifications/` | List in-app notifications for current user |
| `PATCH` | `/notifications/{id}/read` | Mark notification as read |
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

### Benchmark Results (200-image sample, Kaggle)

Evaluated on 200 civic images (25 sampled per department) using the Vision → Rule Engine → Reasoning pipeline:

| Metric | Result |
|---|---|
| Images processed | 200 |
| Re-labelled | 128 (64.0%) |
| Confirmed (label unchanged) | 72 (36.0%) |
| Errors | 0 |
| Uncategorized | 9 / 200 (4.5%) |

**Classification method breakdown:**

| Method | Count | % |
|---|---|---|
| `reasoning` (LLM) | 194 | 97.0% |
| `keyword_fallback` | 2 | 1.0% |
| `error` | 4 | 2.0% |

**Confidence statistics:**

| Stat | Value |
|---|---|
| Mean | 0.811 |
| Median | 0.900 |
| Min | 0.000 |
| Max | 1.000 |

**Output distribution:**

| Category | Images |
|---|---|
| Municipal - PWD (Roads) | 49 |
| Municipal - Sanitation | 45 |
| Municipal - Street Lighting | 31 |
| Utility - Power (DISCOM) | 26 |
| Municipal - Horticulture | 18 |
| Municipal - Water & Sewerage | 18 |
| Uncategorized | 9 |
| Police - Local Law Enforcement | 2 |
| Police - Traffic | 2 |

> The high re-labelling rate (64%) reflects genuine dataset noise in the original Kaggle labels — the model correctly identifies misclassified images (e.g. broken lamp-posts labelled as "Horticulture", open drains labelled as "Pollution Control Board").

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and edit as needed:

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `JWT_SECRET_KEY` | *(change this)* | Secret for signing JWT tokens |
| `VISION_MODEL` | `qwen2.5vl:3b` | Primary vision model for image narration |
| `MID_VISION_MODEL` | `granite3.2-vision:2b` | Fallback vision model (used if primary times out) |
| `REASONING_MODEL` | `llama3.2:1b` | Reasoning model for ambiguous cases + complaint writer |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS whitelist |
| `VISION_TIMEOUT_SECONDS` | `240` | Per-tier vision model timeout (seconds) |
| `LLM_INLINE_TIMEOUT_SECONDS` | `15` | Timeout for synchronous LLM calls |
| `RULE_ENGINE_ONLY` | `false` | Set `true` to skip LLM reasoning entirely |
| `AMBIGUITY_THRESHOLD` | `2.0` | Min rule engine score to skip the reasoning step |

Frontend environment variables (`frontend/.env`):

| Variable | Default | Description |
|---|---|---|
| `VITE_MAPPLS_API_KEY` | *(unset)* | Optional — MapmyIndia/Mappls API key for official GoI survey map tiles. Get a free key at [developer.mappls.com](https://developer.mappls.com). Without it, CARTO Voyager tiles are used (English labels, full India coverage). |

---

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| GPU VRAM | 4 GB (models run sequentially) | 6+ GB |
| System RAM | 12 GB free | 16 GB |
| Storage | 10 GB free (models + images) | 20 GB |
| OS | Windows 10+ or Ubuntu 20.04+ | Windows 11 / Ubuntu 22.04 |

> Models run **sequentially**, never simultaneously -- each fits in 4 GB VRAM alone.
