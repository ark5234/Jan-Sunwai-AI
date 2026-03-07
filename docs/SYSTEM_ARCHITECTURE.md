# Jan-Sunwai AI — System Architecture

---

## 1. Full System Overview

```
CITIZEN
  │
  │  Opens browser → http://localhost:5173
  ▼
┌────────────────────────────────────┐
│   FRONTEND  (React 18 + Vite 4)   │
│                                    │
│  • Login / Register page          │
│  • Upload photo + language select │
│  • Pin location on MapLibre map   │
│  • Shows AI-generated complaint   │
│  • Street / Satellite map toggle  │
│  • Submit → tracks status         │
│  • SLA badge + resolution date    │
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
│   6. GENERATE   — complaint letter drafted (+ language)   │
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
┌──────────┐    ┌──────────────────────────────────────────┐
│ MongoDB  │    │  Ollama  (localhost:11434)                │
│          │    │                                          │
│ users    │    │  STEP 1 — Vision Cascade                 │
│ complaints│   │    qwen2.5vl:3b    (primary,  3.2 GB)   │
│           │   │    granite3.2-vision:2b  (mid-tier)      │
│           │   │    → structured JSON image description   │
└──────────┘    │                                          │
                │  STEP 2 — Rule Engine  (zero VRAM)       │
                │    deterministic keyword scoring         │
                │    stops here when result is confident   │
                │                                          │
                │  STEP 3 — Reasoning  (llama3.2:1b)      │
                │    only invoked when ambiguous           │
                │    → picks best civic category           │
                │                                          │
                │  STEP 4 — Complaint Writer               │
                │    llama3.2:1b  (text-only, 60-90 words) │
                └──────────────────────────────────────────┘
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
 STEP 1 — Vision (qwen2.5vl:3b, 3-tier cascade)
   Reads the image and returns structured JSON:
   { description, visible_objects, primary_issue, hazards, setting }
   Falls back to granite3.2-vision:2b → moondream if primary model
   times out or runs out of VRAM.
      │
      ▼
 STEP 2 — Rule Engine (Python, zero VRAM)
   Deterministic keyword scoring across all 10 civic categories.
   Fast and always runs. Flags result as "ambiguous" if score is low.
   → "Municipal - PWD (Roads)"  (confident — done here, no LLM needed)
      │   OR
      ▼  (ambiguous)
 STEP 3 — Optional Reasoning (llama3.2:1b)
   Only invoked when Rule Engine is not confident.
   Reads the vision JSON and picks the best category.
   Vision model is unloaded first to free VRAM.
      │
      ▼
 STEP 4 — Complaint Writer (llama3.2:1b, text-only)
   Uses vision description + category + location to draft
   a 60-90 word formal civic complaint (no image re-read).
   Supports multilingual output via `language` parameter
   (e.g. Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati).
      │
      ▼
 Citizen sees: category + location + draft letter
 (can edit the draft before submitting)
      │
      ▼
 Saved to MongoDB → Routed to the correct authority
```

### Why the Hybrid Approach

| | Old Method (CLIP / LLaVA 7B) | Current Method (Vision + Rule Engine + Llama) |
|---|---|---|
| Accuracy | Low — guesses keywords | High — vision understands scene context |
| VRAM Usage | High — crashed 4 GB cards | Low — rule engine is zero-VRAM |
| Determinism | Non-deterministic | Rule engine is fully deterministic; reasoning uses temperature=0 |
| Speed | Slow (model swapping) | Fast — LLM reasoning skipped for clear cases |
| Flexibility | Rigid | 10 civic categories, easy to extend rule weights |

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
| **Citizen** | Upload photo, select language, get AI analysis, submit complaint, track own complaints |
| **Dept Head** | See all complaints assigned to their department, update status |
| **Admin** | See everything, manage live triage queue, review uncertain classifications |

---

## 5. Hardware Utilisation

```
┌─────────────────────────────────────────────────────────────┐
│  RTX 3050  —  4 GB VRAM                                     │
│                                                             │
│  Step 1: qwen2.5vl:3b  (3.2 GB)  ← vision inference        │
│          unloaded via keep_alive=0 after classify()         │
│  Step 2: Rule Engine (Python)    ← zero VRAM                │
│  Step 3: llama3.2:1b   (1.3 GB)  ← only if ambiguous       │
│  Step 4: llama3.2:1b   (reused)  ← complaint text draft    │
│                                                             │
│  Ollama loads ONE model at a time (serialised via lock)     │
│  For clear cases: only qwen + rule engine → no Llama load   │
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

### Frontend Map Library

The frontend uses **react-map-gl v7 + MapLibre GL v3** for all maps (complaint submission pin-drop + admin complaints map).

| Feature | Detail |
|---|---|
| Default tiles | CARTO Voyager — English labels, full India coverage, no API key needed |
| Satellite tiles | ESRI World Imagery — switchable via Street/Satellite toggle button |
| Official GoI tiles | Set `VITE_MAPPLS_API_KEY` in `frontend/.env` to use MapmyIndia/Mappls survey tiles (correct J&K/Ladakh borders) |
| India bounds | Map locked to `[[67,6],[98,38]]` — cannot pan outside India |
| Vite compat | maplibre-gl v3 (CJS build) required for Vite 4 — v5 dropped default export |

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
| `mid_vision_model` | `granite3.2-vision:2b` | `MID_VISION_MODEL` |
| `fallback_vision_model` | `granite3.2-vision:2b` | `FALLBACK_VISION_MODEL` |
| `reasoning_model` | `llama3.2:1b` | `REASONING_MODEL` |
| `vision_timeout_seconds` | `240` | `VISION_TIMEOUT_SECONDS` |
| `llm_inline_timeout_seconds` | `15` | `LLM_INLINE_TIMEOUT_SECONDS` |
| `llm_queue_workers` | `2` | `LLM_QUEUE_WORKERS` |
| `rule_engine_only` | `false` | `RULE_ENGINE_ONLY` |
| `unload_after_reasoning` | `true` | `UNLOAD_AFTER_REASONING` |
| `mongodb_url` | `mongodb://localhost:27017` | `MONGODB_URL` |

---

## 10. Installed Ollama Models

| Model | Size | Role |
|---|---|---|
| `qwen2.5vl:3b` | 3.2 GB | Primary vision — structured JSON image analysis |
| `granite3.2-vision:2b` | ~2.4 GB | Mid/fallback vision — used when qwen2.5vl times out or OOMs |
| `llama3.2:1b` | 1.3 GB | Reasoning (ambiguous cases) + complaint text writer (multilingual) |
| `llava:latest` | 4.7 GB | Legacy (no longer used by API) |

---

## 11. Triage Queue

The Human Review (Triage) queue surfaces complaints where the AI classification is uncertain.

```
Complaint submitted
      │
      ▼
ai_metadata.confidence_score < 0.65 ?
      │ YES                  │ NO
      ▼                      ▼
Appears in              Routed directly
Triage Queue            to dept_head
(GET /triage/review-queue)
      │
      ▼
Admin reviews — Approve / Reject
(POST /triage/review-queue/decision)
      │
      ├─ Optional: override department assignment
      ├─ Stamps triage_decision on MongoDB complaint doc
      └─ CSV audit trail in triage_output/
```

- The queue queries **MongoDB live** — not a static CSV file
- Filter: `ai_metadata.confidence_score < 0.65` AND `triage_decision: {$exists: false}`
- Once a decision is made the complaint leaves the queue automatically

---

## 12. Language Pipeline

Citizens can select the output language of the AI-generated complaint letter:

```
POST /complaints/analyze
  └── language: "hi" | "ta" | "te" | "bn" | "mr" | "gu" | "en" (default)
                        │
                        ▼
              LLMJob.language stored in job queue
                        │
                        ▼
              generator.generate_complaint(language=...)
                        │
              _LANG_NAMES dict maps code → language name
                        │
              lang_instruction prepended to prompt:
              "Write the complaint in Hindi."
                        │
                        ▼
              Draft returned to frontend in selected language
```

Regenerate endpoint (`POST /complaints/analyze/regenerate`) also accepts `language` in the JSON body.
