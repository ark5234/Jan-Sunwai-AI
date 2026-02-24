# Civic-Vision AI (Jan-Sunwai)

**Automated Visual Classification & Geospatial Routing of Civic Grievances using Zero-Shot Learning**

civic-vision-ai is a cutting-edge platform designed to streamline civic grievance redressal. By leveraging advanced AI models like CLIP for zero-shot image classification and LLaVA for generative content, along with intelligent geotagging, it automates the categorization and routing of citizen complaints to the appropriate authorities.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Automated Triage Workflow](#automated-triage-workflow)
- [Current ML Pipeline](#current-ml-pipeline)
- [Mobile Responsiveness](#mobile-responsiveness)

---

## Overview

Managing civic grievances often suffers from manual data entry errors, misclassification, and delays. Civic-Vision AI addresses these challenges by allowing citizens to simply upload a photo of a civic issue. The system automatically identifies the category (e.g., Pothole, Garbage, Street Light), extracts the location, and drafts a formal complaint, which is then routed to the relevant department head.

## Key Features

-   **Zero-Shot Image Classification**: Utilizes the OpenAI CLIP model to categorize images into civic departments (Sanitation, Roads, Electricity, etc.) without training on specific datasets.
-   **Intelligent Geotagging**: Automatically extracts EXIF GPS data and converts coordinates into readable addresses.
-   **AI-Powered Drafting**: Uses LLaVA (via Ollama) to generate professional, formal complaint letters based on image analysis.
-   **Role-Based Access Control**: Secure JWT authentication supporting three user roles:
    -   **Citizen**: Report issues, track status.
    -   **Department Head**: View and manage complaints for their specific department.
    -   **Admin**: System-wide oversight and user management.
-   **Fully Responsive**: Optimized UI/UX for Mobile, Tablet, and Desktop using Tailwind CSS.

## Tech Stack

### Backend
-   **Framework**: Python (FastAPI)
-   **AI Models**:
    -   **CLIP** (Contrastive Language-Image Pre-Training) for classification.
    -   **LLaVA** (Large Language-and-Vision Assistant) via Ollama for text generation.
-   **Database**: MongoDB (AsyncIOMotorClient)
-   **Authentication**: OAuth2 with JWT (JSON Web Tokens)
-   **Image Processing**: Pillow (PIL)

### Frontend
-   **Framework**: React.js
-   **Build Tool**: Vite
-   **Styling**: Tailwind CSS
-   **State Management**: React Context API
-   **HTTP Client**: Axios

## System Architecture

The application follows a client-server architecture:

1.  **Client (Frontend)**: Captures image input and user interactions.
2.  **API Layer (Backend)**: FastAPI routes handle requests, validate authentication, and manage file uploads.
3.  **AI Engine**:
    -   Processing pipeline extracts image embeddings.
    -   Computes similarity scores against predefined civic categories.
    -   Generates descriptive text for valid complaints.
4.  **Data Persistence**: Stores user profiles, encoded images, and complaint metadata in MongoDB.

## Getting Started

### Prerequisites

Ensure you have the following installed:
-   **Python 3.8+**
-   **Node.js 16+** & **npm**
-   **MongoDB**: Installed locally or access to a cloud cluster.
-   **Ollama**: Required for local LLM inference.
    -   Install from [ollama.ai](https://ollama.ai/)
    -   Pull the required model: `ollama pull llava`

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/ark5234/Jan-Sunwai-AI.git
    cd Jan-Sunwai-AI
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```
    *Note: Ensure your MongoDB service is running.*

3.  **Frontend Setup**
    ```bash
    cd ../frontend
    npm install
    ```

### Running the Application

We have provided convenient scripts in the `scripts/` directory to get you up and running quickly.

**From the project root:**

*   **Start Backend**:
    ```cmd
    scripts\run_backend.bat
    ```
    *Server runs on `http://localhost:8000`*

*   **Start Frontend**:
    ```cmd
    scripts\run_frontend.bat
    ```
    *App runs on `http://localhost:5173`*

*   **Run Tests**:
    ```cmd
    scripts\run_tests.bat
    ```

## Project Structure

```text
Jan-Sunwai-AI/
├── backend/                # FastAPI application
│   ├── app/                # Core application logic
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic (Storage, AI)
│   │   └── classifier.py   # CLIP model integration
│   ├── requirements.txt
│   └── main.py             # App entry point
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Application views
│   │   └── context/        # Global state
│   └── vite.config.js
├── docs/                   # Documentation & assets
├── notebooks/              # Jupyter notebooks for experiments
├── reports/                # Evaluation datasets and CSVs
├── scripts/                # Helper batch scripts for Windows
└── README.md
```

## Automated Triage Workflow

To auto-clean, auto-sort, and generate a review queue for dataset labeling:

```bash
cd backend
python automated_triage.py --dataset-dir dataset --output-dir triage_output --prune-ratio 0.15 --clip-min-conf 0.45 --clip-min-margin 0.08
```

This runs the 4-stage pipeline:
- CleanVision audit for low-quality/duplicate candidates
- CLIP zero-shot category sorting
- LLaVA fallback for uncertain CLIP predictions
- Human-review exports (`review_queue.csv`) for quick validation

Generated outputs:
- `backend/triage_output/triaged_dataset/` (sorted folders)
- `backend/triage_output/audit_issues.csv`
- `backend/triage_output/triage_labels.csv`
- `backend/triage_output/triage_labels.json`
- `backend/triage_output/review_queue.csv`

## Current ML Pipeline

The maintained backend ML flow is:

1. `backend/sort_dataset.py` — keyword-based initial folder sorting into `backend/sorted_dataset/`
2. `backend/train_custom_classifier.py` — CLIP embedding extraction + Logistic Regression head training (`custom_classifier_head.pkl`)
3. `backend/automated_triage.py` — quality audit + CLIP sorting + LLaVA fallback + review artifacts
4. `backend/app/classifier.py` — runtime inference (custom head first, CLIP zero-shot fallback)
5. `backend/app/routers/complaints.py` — API-level annotation (classification + geotagging + complaint draft generation)

### Evaluation scripts

- Preferred: `backend/evaluate_sorted_dataset.py` (folder-vs-prediction evaluation on sorted datasets)
- Legacy: `backend/evaluate_dataset.py` and `backend/test_accuracy.py` (kept for ad-hoc checks)

## Mobile Responsiveness

The interface is rigorously tested across devices:

| Device Type | Viewport | Features |
| :--- | :--- | :--- |
| **Mobile** | 320px - 767px | Touch-optimized, stacked layouts, bottom navigation friendly |
| **Tablet** | 768px - 1023px | Adaptive grids, comfortable touch targets |
| **Desktop** | 1024px+ | Expanded dashboards, multi-column data views |

---

*Verified on iPhone SE, iPhone 12/13, iPad, and major Desktop browsers.*
