# Jan-Sunwai AI — System Architecture

---

## 1. Full System Overview

```
CITIZEN
  │
  │  Opens browser → http://localhost:5173
  ▼
┌────────────────────────────────────┐
│   FRONTEND  (React + Vite)        │
│                                    │
│  • Login / Register page          │
│  • Upload photo + pin location    │
│  • Shows AI-generated complaint   │
│  • Submit → tracks status         │
└──────────────┬─────────────────────┘
               │  REST API calls (JSON)
               ▼  http://localhost:8000
┌────────────────────────────────────────────────────────────┐
│   BACKEND  (FastAPI + Python)                              │
│                                                            │
│  On startup:                                               │
│   • Connects to MongoDB                                    │
│   • Starts LLM queue (2 async worker threads)             │
│                                                            │
│  Every /analyze request:                                   │
│   1. AUTH       — JWT token verified                       │
│   2. SAVE       — image saved to backend/uploads/         │
│   3. GEOTAGGING — PIL reads EXIF GPS from the photo       │
│   4. CLASSIFY   — CivicClassifier (Ollama pipeline)       │
│   5. ENQUEUE    — LLM queue picks up the job              │
│   6. GENERATE   — complaint letter drafted                │
│   7. RETURN     — classification + location + draft       │
│                                                            │
│  After user edits & submits /complaints:                   │
│   • Saved to MongoDB with status = "Open"                 │
│   • Routed to the correct authority (dept_head)           │
│   • Status tracked: Open → In Progress → Resolved        │
└──────────────┬─────────────────────────────────────────────┘
               │
     ┌─────────┴──────────┐
     ▼                    ▼
┌──────────┐    ┌──────────────────────────────────────┐
│ MongoDB  │    │  Ollama  (localhost:11434)            │
│          │    │                                      │
│ users    │    │  STEP 1 — qwen2.5vl:3b  (3.2 GB)    │
│ complaints│   │   "Eyes" — reads the image           │
│ triage   │    │   → outputs a 2-3 sentence narration │
│          │    │                                      │
└──────────┘    │  STEP 2 — llama3.2:1b  (1.3 GB)     │
                │   "Brain" — reads the narration      │
                │   → picks one of 10 civic categories │
                │                                      │
                │  STEP 3 — qwen2.5vl:3b  (reused)    │
                │   "Writer" — drafts the formal       │
                │    grievance letter (80-100 words)   │
                └──────────────────────────────────────┘
```

---

## 2. The AI Pipeline — Step by Step

```
Photo uploaded
      │
      ▼
 EXIF check ──→ GPS coords found? → address via reverse geocoding (geopy)
      │              No GPS? → "Unknown location" (user pins manually on map)
      ▼
 qwen2.5vl:3b reads image
 e.g. "A large pothole on a concrete road near a footpath.
       Water has collected in the hole. Risk to vehicles."
      │
      ▼
 llama3.2:1b reads description + category list
 → "Municipal - PWD (Roads)"
      │
      ▼
 qwen2.5vl:3b writes complaint letter:
 "Subject: Dangerous Pothole on Main Road...
  To The Municipal Officer, ... Respectfully submitted"
      │
      ▼
 Citizen sees: category + location + draft letter
 (can edit the draft before submitting)
      │
      ▼
 Saved to MongoDB → Routed to PWD department head
```

### Why Two Models Instead of One

| | Old Method (CLIP / LLaVA 7B) | Current Method (Qwen + Llama) |
|---|---|---|
| Accuracy | Low — guesses keywords | High — understands context & actions |
| VRAM Usage | High — crashed 4 GB cards | Low — perfect for RTX 3050 |
| Flexibility | Rigid categories | Easy to add new folder rules |
| Speed | Slow (model swapping) | Fast (models stay in memory) |

---

## 3. Civic Categories

The system routes complaints to 10 canonical categories:

| Category | Example Issues |
|---|---|
| Municipal - PWD (Roads) | Potholes, cracked pavement, bridge damage |
| Municipal - Sanitation | Garbage dumps, overflowing bins, dirty toilets |
| Municipal - Horticulture | Fallen trees, unmaintained parks |
| Municipal - Street Lighting | Broken lamp posts, dark roads |
| Municipal - Water & Sewerage | Waterlogging, blocked drains, pipe leaks |
| Utility - Power (DISCOM) | Dangling wires, open transformers |
| State Transport | Damaged bus shelters, broken state buses |
| Pollution Control Board | Thick smoke, industrial waste dumping |
| Police - Local Law Enforcement | Illegal parking, encroachment, public nuisance |
| Police - Traffic | Signal failure, road blockages |

---

## 4. The 3 User Roles

| Role | Permissions |
|---|---|
| **Citizen** | Upload photo, get AI analysis, submit complaint, track own complaints |
| **Dept Head** | See all complaints assigned to their department, update status |
| **Admin** | See everything, manage triage queue, review uncertain classifications |

---

## 5. Hardware Utilisation

```
┌─────────────────────────────────────────────────────────────┐
│  RTX 3050  —  4 GB VRAM                                     │
│                                                             │
│  qwen2.5vl:3b  (3.2 GB)  ← loaded when /analyze is called  │
│  ─────────────────────── ← unloaded after ~5 min idle       │
│  llama3.2:1b   (1.3 GB)  ← loaded right after              │
│                                                             │
│  Ollama loads ONE at a time — never both simultaneously     │
│  (sequential pipeline, not parallel)                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  16 GB RAM                                                  │
│                                                             │
│  FastAPI + uvicorn     ~  80 MB                             │
│  MongoDB (local)       ~ 200 MB                             │
│  Python venv (lean)    ~ 150 MB  (no torch anymore)         │
│  Ollama daemon         ~ 500 MB                             │
│                                                             │
│  Total system load     < 1 GB — 15 GB stays free            │
└─────────────────────────────────────────────────────────────┘
```

Ollama automatically offloads a model from VRAM to RAM if memory is
full, but with 3.2 GB + 1.3 GB running sequentially on 4 GB VRAM,
each model fits on its own. GPU is always preferred over CPU.

---

## 6. Where Everything Lives

| Component | Location | Port |
|---|---|---|
| Frontend | `frontend/src/` | `5173` |
| Backend API | `backend/main.py` | `8000` |
| MongoDB | Docker container | `27017` |
| Ollama | Windows service (native) | `11434` |
| Uploaded images | `backend/uploads/` | served at `/uploads/` |
| Logs | `backend/logs/app.log` | rotates at 5 MB |
| AI models | `C:\Users\<user>\.ollama\models\` | ~4.5 GB on disk |

---

## 7. How to Run (Local Development)

### Step 1 — Start MongoDB
```powershell
docker run -d -p 27017:27017 --name mongo mongo:latest
```
Skip if already running via Docker Desktop.

### Step 2 — Start Backend
```powershell
cd "c:\Users\Vikra\OneDrive\Desktop\Jan-Sunwai AI"
.\.venv\Scripts\Activate.ps1
cd backend
$env:PYTHONPATH = "."
uvicorn main:app --reload --port 8000
```

### Step 3 — Start Frontend
```powershell
cd "c:\Users\Vikra\OneDrive\Desktop\Jan-Sunwai AI\frontend"
npm run dev
```

Ollama runs automatically in the background after installation.

---

## 8. Verification Endpoints

Once the backend is running, test these in a browser or PowerShell:

```powershell
# Is the API alive?
curl http://localhost:8000/health/live

# Is MongoDB connected?
curl http://localhost:8000/health/ready

# Are Ollama models present?
curl http://localhost:8000/health/models

# Is GPU being used? (run after uploading one image)
curl http://localhost:8000/health/gpu
```

Interactive API docs (all endpoints + built-in test form):
**http://localhost:8000/docs**

### GPU Health Response Example
```json
{
  "gpu_active": true,
  "configured_models": {
    "vision": "qwen2.5vl:3b",
    "reasoning": "llama3.2:1b"
  },
  "running_models": [
    {
      "name": "qwen2.5vl:3b",
      "size_mb": 3200,
      "vram_mb": 3100,
      "on_gpu": true
    }
  ]
}
```
`vram_mb > 0` → model is on GPU.
`vram_mb = 0` → model fell back to CPU RAM (happens only if VRAM exhausted).

---

## 9. Key Configuration (backend/app/config.py)

| Setting | Default | Override via env |
|---|---|---|
| `vision_model` | `qwen2.5vl:3b` | `VISION_MODEL` |
| `reasoning_model` | `llama3.2:1b` | `REASONING_MODEL` |
| `llm_inline_timeout_seconds` | `8` | `LLM_INLINE_TIMEOUT_SECONDS` |
| `llm_queue_workers` | `2` | `LLM_QUEUE_WORKERS` |
| `mongodb_url` | `mongodb://localhost:27017` | `MONGODB_URL` |

---

## 10. Installed Ollama Models

| Model | Size | Role |
|---|---|---|
| `qwen2.5vl:3b` | 3.2 GB | Vision — image narration + complaint writing |
| `llama3.2:1b` | 1.3 GB | Reasoning — category selection |
| `llava:latest` | 4.7 GB | Legacy (kept, no longer used by API) |
