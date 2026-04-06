# Jan-Sunwai AI - Daily Project Report & Plan

> **Font:** Times New Roman throughout all printed / PDF versions of this document.
> **Last Updated:** 06 April 2026
> **Current Status:** Security/performance hardening, password reset/profile editing, API versioning, production compose artifacts, and deployment docs are implemented. Remaining work is full UAT/load/security audit and release operations.

**Project Duration:** January 28, 2026 – May 27, 2026
**Schedule Logic:** Monday to Saturday work weeks. Sundays are always OFF. 2nd & 4th Saturdays are OFF.

---

### Phase 1: Foundation & Core Backend (Weeks 1-6)

#### Week 1: Jan 28 (Wed) – Jan 31 (Sat)
*   **Jan 28 (Wed):** **Project Inception & Repository Setup** - [COMPLETED]
    *   Initialize the master Git repository, establish the folder structure for Backend/Frontend, and configure a comprehensive `.gitignore`.
    *   Draft the initial project roadmap and technology stack document, researching optimal versions for FastAPI and React integration.
*   **Jan 29 (Thu):** **Development Environment Configuration** - [COMPLETED]
    *   Install and configure Python 3.10+, Node.js, and essential CLI tools; set up virtual environments and dependency managers (pip, npm).
    *   Configure VS Code workspace extensions (Pylance, ESLint, Prettier) and define strict linting rules to ensure code quality.
*   **Jan 30 (Fri):** **System Architecture & Requirements** - [COMPLETED]
    *   Create detailed architectural diagrams (Data Flow, Entity Relationship) to visualize the interaction between AI models and usage.
    *   Formalize the System Requirements Specification (SRS), detailing functional requirements for the Grievance Classification module.
*   **Jan 31 (Sat):** **Backend Skeleton Implementation** - [COMPLETED]
    *   Develop the base FastAPI application shell, including standard boilerplate for CORS, Middleware, and Exception handling.
    *   Write and execute initial "Hello World" API tests to verify the server implementation and environment stability.
*   **Feb 01 (Sun):** *OFF*

#### Week 2: Feb 02 (Mon) – Feb 07 (Sat)
*   **Feb 02 (Mon):** **Database Connectivity & Setup** - [COMPLETED]
    *   Install MongoDB locally and provision the `jan_sunwai_db`; write a robust database connection handler using `Motor` (Async driver).
    *   Troubleshoot connection timeouts and configure connection pooling to ensure the backend handles concurrent requests efficiently.
*   **Feb 03 (Tue):** **User Authentication Schema Design** - [COMPLETED]
    *   Design Pydantic data models for User entities; implement strict type validation for emails, passwords, and role management.
    *   Research JWT (JSON Web Tokens) best practices and sketch out the authentication flow logic for future implementation.
*   **Feb 04 (Wed):** **Grievance Data Modeling** - [COMPLETED]
    *   Define complex Pydantic schemas for the `Complaint` object, including nested fields for Geolocation (`lat`/`long`) and Image Metadata.
    *   Write unit tests to validate schema behavior against malformed data inputs, ensuring data integrity at the API layer.
*   **Feb 05 (Thu):** **CRUD API Implementation** - [COMPLETED]
    *   Develop core API endpoints (`POST /complaint`, `GET /complaint/{id}`) to handle basic complaint creation and retrieval.
    *   Implement Dependency Injection for database sessions within the API routes to maintain clean and testable code.
*   **Feb 06 (Fri):** **File Handling & Storage System** - [COMPLETED]
    *   Implement secure file upload logic using `python-multipart`, ensuring images are sanitized and stored with unique identifiers.
    *   Develop a local file management service class to abstract filesystem operations, laying groundwork for cloud storage migration.
*   **Feb 07 (Sat):** **Code Refactoring & Router Organization** - [COMPLETED]
    *   Refactor the growing `main.py` by splitting routes into dedicated modules (`complaints.py`, `users.py`) using `APIRouter`.
    *   Review code structure against PEP-8 standards and optimize import statements to improve application startup time.
*   **Feb 08 (Sun):** *OFF*

#### Week 3: Feb 09 (Mon) – Feb 14 (Sat)
*   **Feb 09 (Mon):** **AI Model Research (CLIP → replaced by Ollama pipeline)** - [COMPLETED]
    *   Conducted research into OpenAI CLIP and Hugging Face `transformers` for Zero-Shot classification.
    *   *Note: CLIP was ultimately replaced by the Ollama-based hybrid pipeline (qwen2.5vl:3b + rule engine + llama3.2:1b) due to VRAM constraints and lower accuracy on civic images.*
*   **Feb 10 (Tue):** **AI Environment & Dependency Integration** - [COMPLETED]
    *   Installed initial AI libraries (`torch`, `transformers`, `Pillow`) for CLIP prototype; resolved CUDA/CPU version conflicts.
    *   *Note: `torch` and `transformers` were later removed in favour of the Ollama client (`ollama` Python package), significantly reducing memory footprint.*
*   **Feb 11 (Wed):** **JWT Authentication & Security Implementation** - [COMPLETED]
    *   Implemented full JWT token-based authentication system using python-jose and OAuth2PasswordBearer flow.
    *   Created `auth.py` module with token generation, validation, and user dependency injection.
    *   Updated `/login` endpoint to return secure access tokens with 24-hour expiration.
    *   Modified `/register` endpoint to auto-generate JWT tokens for seamless onboarding.
    *   Secured `/analyze` and `/complaints` endpoints with `get_current_user` dependency.
    *   Updated frontend AuthContext to validate token presence and handle session expiration.
    *   Implemented bearer token authentication in frontend API calls.
    *   Shortened AI complaint generation prompts to max 150 words for better UX.
    *   Added passlib[bcrypt] for secure password hashing.
    *   Updated test suite with dependency overrides for JWT testing.
*   **Feb 12 (Thu):** **Zero-Shot Classifier Implementation (CLIP → later replaced)** - [COMPLETED]
    *   Developed the initial `classifier.py` module using CLIP for Zero-Shot image classification.
    *   *Note: Replaced with the Ollama-based CivicClassifier (Vision → Rule Engine → Optional Reasoning) for better accuracy and VRAM efficiency.*
*   **Feb 13 (Fri):** **Classification Accuracy Testing** - [COMPLETED]
    *   Benchmarked CLIP model on 50+ test images; identified accuracy issues on Indian civic scenes.
    *   Findings directly motivated the switch to the qwen2.5vl:3b vision model + deterministic rule engine hybrid.
*   **Feb 14 (Sat):** *OFF (2nd Saturday)*
*   **Feb 15 (Sun):** *OFF*

#### Week 4: Feb 16 (Mon) – Feb 21 (Sat)
*   **Feb 16 (Mon):** **Metadata & EXIF Research** - [COMPLETED]
    *   Study the EXIF standard and `Pillow` library documentation to understand how GPS tags are encoded in image files.
    *   Experiment with different sample images to identify variations in how Android and iOS devices store location data.
*   **Feb 17 (Tue):** **GPS Coordinate Parsing Logic** - [COMPLETED]
    *   Write complex mathematical utility functions to convert GPS Degrees/Minutes/Seconds (DMS) tuples into standard Decimal Degrees.
    *   Implement robust error handling for the parser to prevent crashes when dealing with corrupted or partial EXIF headers.
*   **Feb 18 (Wed):** **Reverse Geocoding Integration** - [COMPLETED]
    *   Register for OpenStreetMap/Nominatim services and implement the `geopy` client to translate coordinates into human-readable addresses.
    *   Implement request rate limiting and caching strategies for the geocoder to respect API usage policies and improve speed.
*   **Feb 19 (Thu):** **Geotagging Module Development** - [COMPLETED]
    *   Integrate the EXIF parser and Geocoder into a unified `extract_location` service function within the backend.
    *   Write unit tests specifically for the location module, verifying it correctly handles images from different hemispheres.
*   **Feb 20 (Fri):** **Edge Case Management** - [COMPLETED]
    *   Develop logic to handle images strictly stripped of metadata (e.g., WhatsApp images) by returning "Location Unknown" without errors.
    *   Implement value sanitization to ensure "None" or invalid coordinates don't corrupt the database or crash the geocoder.
*   **Feb 21 (Sat):** **AI Pipeline Integration** - [COMPLETED]
    *   Merge the Classification and Geotagging modules into the main `/analyze` API endpoint, orchestrating sequential execution.
    *   Conduct end-to-end reliability tests of the `/analyze` endpoint, ensuring it returns both Dept and Location within acceptable time limits.
*   **Feb 22 (Sun):** *OFF*

#### Week 5: Feb 23 (Mon) – Feb 28 (Sat)
*   **Feb 23 (Mon):** **Generative AI Environment Setup** - [COMPLETED]
    *   Install and configure `Ollama` locally; pull `qwen2.5vl:3b` (vision), `granite3.2-vision:2b` (mid-tier vision fallback), and `llama3.2:1b` (reasoning + writer) models.
    *   Verify hardware resource usage (RAM/VRAM); confirmed sequential model loading fits within 4 GB VRAM on RTX 3050. Note: initial approach used `llava` which was later replaced in favour of the qwen2.5vl + rule engine hybrid.
*   **Feb 24 (Tue):** **GenAI Prompt Engineering** - [COMPLETED]
    *   Design and iterate on system prompts for `qwen2.5vl:3b` (vision JSON extraction) and `llama3.2:1b` (complaint writing).
    *   Developed the hybrid Vision → Rule Engine → Optional Reasoning pipeline to reduce VRAM usage and improve determinism.
*   **Feb 25 (Wed):** **Complaint Generator Service** - [COMPLETED]
    *   Develop `generator.py` to wrap the Ollama API calls, handling inputs (Department, Location, Image context) dynamically.
    *   Implement text post-processing to clean up AI artifacts (extra quotes, hallucinations) before sending the draft to the user.
*   **Feb 26 (Thu):** **Draft Generation API** - [COMPLETED]
    *   Expose the generation logic via a FastAPI endpoint, allowing the frontend to request a fresh draft based on analysis results.
    *   Implement timeout management for the generation endpoint, as LLM inference can be slow, adding async `await` patterns.
*   **Feb 27 (Fri):** **Quality Assurance for Generated Text** - [COMPLETED]
    *   Manually review 20+ generated complaints for coherence, checking if variables like "Location" are correctly inserted.
    *   Refine the prompt based on review findings to eliminate repetitive phrases or overly aggressive language.
*   **Feb 28 (Sat):** *OFF (4th Saturday)*
*   **Mar 01 (Sun):** *OFF*

#### Week 6: Mar 02 (Mon) – Mar 07 (Sat) [Frontend Implementation]
*   **Mon:** **Frontend Initialization & Dependencies** - [COMPLETED]
    *   Verify React/Vite setup and install core UI libraries (`react-router-dom`, `tailwindcss`, `lucide-react`).
    *   Configure Tailwind CSS for consistent styling across the application.
*   **Tue:** **Application Routing & Layout** - [COMPLETED]
    *   Set up the main Router (Home, Analysis, Result, Register, Login).
    *   Create the shell layout (Navbar, Footer) using Tailwind components with responsive design.
*   **Wed:** **Image Upload Component** - [COMPLETED]
    *   Build a drag-and-drop file upload zone with visual feedback (hover states, file previews).
    *   Connect this component to the `useAnalyze` hook with proper validation and error handling.
*   **Thu:** **API Integration (Analysis Hook)** - [COMPLETED]
    *   Develop `hooks/useAnalyze.js` to handle the communication with the Python Backend (`/analyze`).
    *   Display loading states (spinners) while the Ollama pipeline (Vision + Rule Engine + optional Reasoning) is running with JWT authentication.
*   **Fri:** **Result Display Page** - [COMPLETED]
    *   Create the "Complaint Preview" page showing: The Image, The Map, The Classification, and the AI-Drafted Letter.
    *   Add "Copy to Clipboard" and "Edit" functionality (textarea) for the generated text.
*   **Sat:** **End-to-End Test (Frontend -> Backend)** - [COMPLETED]
    *   Manual walkthrough: Upload image -> See AI result -> Verify Letter content.
    *   Confirmed full integration with JWT authentication, Ollama vision classification (qwen2.5vl:3b + rule engine), and llama3.2:1b complaint generation. 

*(Original Backend Security tasks moved to Week 7)*
*   **Mar 08 (Sun):** *OFF*

---

### Phase 2: Security, NDMC Features & Production Readiness (Weeks 7-14)

> **Context:** This project is currently a fully offline local deployment (Ollama + MongoDB on developer machine).
> Target handover: **NDMC (New Delhi Municipal Council)** for real live civic use on their infrastructure.
> All work from this phase onwards is designed with that production handover in mind.

> **Note on acceleration:** Frontend work originally planned for Weeks 8-11
> (ImageUpload, useAnalyze hook, Result page, AdminDashboard, DeptHeadDashboard,
> CitizenDashboard, Notifications, Profile — all fully functional) was completed
> **5 weeks ahead of schedule** during Weeks 2-6. Week 7 closes the remaining gaps
> and locks in the foundation before security and NDMC-specific work begins.

#### Week 7: Mar 09 (Mon) – Mar 14 (Sat) [Close Remaining Gaps]
*   **Mar 09 (Mon):** **Leaflet Map Integration** - [COMPLETED]
    *   Implement `MapContainer`, `TileLayer`, and `Marker` in `Result.jsx` using the `react-leaflet` library (already installed).
    *   Fix Leaflet default icon issue in Vite/React environments; render map with EXIF coordinates when available.
*   **Mar 10 (Tue):** **Draggable Marker & Browser GPS Fallback** - [COMPLETED]
    *   Enable draggable marker so citizens can fine-tune location if EXIF GPS is inaccurate or missing.
    *   Add "Use My Location" button using `navigator.geolocation` as a manual GPS fallback.
*   **Mar 11 (Wed):** **LocalStorage Draft Backup** - [COMPLETED]
    *   Save complaint text + location to `localStorage` on every edit; restore automatically on page refresh.
    *   Add "Clear draft" button so users can start fresh without being locked into a saved draft.
*   **Mar 12 (Thu):** **Global Error Boundary & 404 Page** - [COMPLETED]
    *   Wrap the React app in an `ErrorBoundary` component to catch unhandled render errors gracefully.
    *   Add a styled 404 page for unknown routes with a navigation link back to Home.
*   **Mar 13 (Fri):** **Full End-to-End Walkthrough** - [COMPLETED]
    *   Manual walkthrough of all 3 user journeys: Citizen (upload → analyze → map → submit), Dept Head (login → update status), Admin (filter → bulk review).
    *   Confirm all 10 dept_head accounts and notification chain work end-to-end.
*   **Mar 14 (Sat):** **Phase 1 & 2 Closure Commit** - [COMPLETED]
    *   Tag commit `v0.9-beta`; document all known remaining TODOs (security, NDMC features, production config).
    *   Confirm `docker compose up` starts backend + MongoDB cleanly; frontend runs via `npm run dev`.
*   **Mar 15 (Sun):** *OFF*

#### Week 8: Mar 16 (Mon) – Mar 21 (Sat) [Security Layer]
*   **Mar 16 (Mon):** **File Magic Number Validation** - [PARTIAL — size limit done, magic byte check pending]
    *   5 MB file size limit enforced at FastAPI layer.
    *   Magic byte content-type verification still pending.
*   **Mar 17 (Tue):** **Rate Limiting on Critical Endpoints** - [COMPLETED]
    *   Added limiter integration on critical endpoints with safe fallback mode for local/offline runs.
*   **Mar 18 (Wed):** **Input Sanitization & XSS Prevention** - [COMPLETED]
    *   Added sanitization service and applied to complaint/user free-text fields.
*   **Mar 19 (Thu):** **CORS Lockdown & Security Headers** - [COMPLETED]
    *   CORS allowlist plus security headers middleware implemented.
*   **Mar 20 (Fri):** **JWT Security Review** - [COMPLETED]
    *   Production defaults now use 8-hour token expiry (480 minutes); development can still override via env.
*   **Mar 21 (Sat):** **MongoDB Indexing for Production Queries** - [COMPLETED]
    *   Added index creation helper script and password-reset indexes (including TTL expiry).
*   **Mar 22 (Sun):** *OFF*

#### Week 9: Mar 23 (Mon) – Mar 28 (Sat) [NDMC Feature Pack]

> **Acceleration Note:** Several Week 9+ features were completed ahead of schedule during weeks 7-9 alongside the Worker Panel implementation.

*   **Mar 23 (Mon):** **Complaint Status Audit Trail** - [COMPLETED]
    *   `status_history` array added to every complaint document: `{status, from, to, changed_by_user_id, timestamp, note}`.
    *   History exposed in `/complaints/{id}` GET response.
    *   `_do_assign()` in `assignment.py` now appends a status_history entry on every worker assignment.
*   **Mar 24 (Tue):** **Worker Panel & Assignment System** - [COMPLETED — ahead of schedule]
    *   Built full Field Worker Panel: `WorkerDashboard.jsx`, `WorkerRegister.jsx` (now collects department + service area).
    *   Implemented `assignment.py` auto-assignment service with Haversine geo-filter and load balancing.
    *   Added `GET /workers/assignment-debug` and `POST /workers/reassign-unassigned` admin endpoints.
    *   Admin Dashboard: Re-assign All button, manual per-worker assignment dropdown, pending approvals UI, service area warnings.
    *   `create_test_users.py` update logic now patches all worker-specific fields (is_approved, worker_status, service_area).
*   **Mar 24 (Tue):** **Escalation Timeline UI** - [COMPLETED]
    *   Status history timeline component added and wired into CitizenDashboard.
*   **Mar 25 (Wed):** **Analytics & Heatmap** - [COMPLETED — ahead of schedule]
    *   `/analytics/complaints` and `/analytics/heatmap` endpoints implemented.
    *   AdminDashboard heatmap tab renders complaint density on map using heat circles.
    *   Per-department stats cards (Open / In Progress / Resolved / Avg Duration) in AdminDashboard and DeptHeadDashboard.
*   **Mar 26 (Thu):** **SLA Badges** - [COMPLETED — ahead of schedule]
    *   `SLABadge.jsx` component shows per-department SLA countdowns; overdue complaints show red badge.
    *   Complaint cards across all dashboards include SLA badge.
*   **Mar 27 (Fri):** **Bulk Status Update & CSV Export** - [COMPLETED]
    *   Backend bulk/status/export endpoints are implemented and Admin Dashboard bulk selection UI is present.
*   **Mar 28 (Sat):** *OFF (4th Saturday)*
*   **Mar 29 (Sun):** *OFF*

#### Week 10: Mar 30 (Mon) – Apr 04 (Sat) [Notification System & Communication]
*   **Mar 30 (Mon):** **Wire Notifications to Navbar** - [COMPLETED]
    *   Connect `Notifications.jsx` (already built) to the Navbar — show a live unread badge count that updates after each status change.
    *   Add polling (every 30s) or SSE stub to keep the badge count fresh without requiring a page refresh.
*   **Mar 31 (Tue):** **Auto-Notify on Status Change** - [COMPLETED]
    *   Trigger an in-app notification automatically when a `dept_head` changes a complaint status via `PATCH /complaints/{id}/status`.
    *   Citizen receives: "Your complaint #{id} has been updated to In Progress by {department}."
*   **Apr 01 (Wed):** **Notification Email Stub (NDMC-Ready)** - [COMPLETED]
    *   Create an `email_service.py` module with a `send_status_update_email()` function — logs to file in dev, ready to wire to NDMC's SMTP server in production.
    *   Add `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM` to `env.local` so NDMC IT can plug in their mail relay.
*   **Apr 02 (Thu):** **Password Reset Flow** - [COMPLETED]
    *   Implement `POST /users/forgot-password` and `POST /users/reset-password` endpoints with time-limited token.
    *   Required for NDMC deployment where officers can't rely on a developer to manually reset credentials.
*   **Apr 03 (Fri):** **Profile Editing** - [COMPLETED]
    *   Allow citizens to update their display name and phone number via `PATCH /users/me`.
    *   Wire `Profile.jsx` (already built) edit form to this endpoint; phone number is critical for NDMC contact follow-ups.
*   **Apr 04 (Sat):** **Notification Chain End-to-End Test** - [PARTIAL]
    *   Test the full chain: Citizen submits → dept_head updates status → notification appears in Navbar → email logged.
    *   Confirm no duplicate notifications and that `mark-all-read` clears the badge correctly.
    *   Added `tests/test_notification_chain.py` and `scripts/run_notification_chain_test.py`; live environment execution is still pending.
*   **Apr 05 (Sun):** *OFF*

#### Week 11: Apr 06 (Mon) – Apr 11 (Sat) [Performance & Reliability]
*   **Apr 06 (Mon):** **Client-Side Image Compression** - [COMPLETED]
    *   Install `browser-image-compression` and compress images to ≤1 MB before POSTing to `/analyze`.
    *   Show the compressed file size and dimensions in the upload UI so citizens understand what's being sent.
*   **Apr 07 (Tue):** **Frontend Bundle Optimisation** - [PARTIAL]
    *   Run Lighthouse performance audit on production build; target score ≥ 80.
    *   Implement React `lazy()` + `Suspense` code splitting for heavy pages (AdminDashboard, Result) to reduce initial bundle size.
    *   Lazy loading is implemented in `App.jsx`; Lighthouse benchmark run is pending.
*   **Apr 08 (Wed):** **Ollama Failure Graceful Degradation** - [COMPLETED]
    *   Ensure the `/analyze` endpoint returns a user-friendly `503` JSON error (not a crash) if all 3 vision model tiers fail or Ollama is unreachable.
    *   Frontend shows: "AI analysis unavailable — please try again in a few minutes" with a retry button.
*   **Apr 09 (Thu):** **Backend Performance Profiling** - [PARTIAL]
    *   Profile the `/analyze` request lifecycle using Python's `cProfile`; identify the slowest non-Ollama step.
    *   Add structured timing logs (`vision_ms`, `rule_engine_ms`, `reasoning_ms`) to every analyze response for NDMC monitoring.
    *   Added `backend/profile_analyze.py` and response timing fields; manual report extraction from real NDMC workloads is pending.
*   **Apr 10 (Fri):** **Resilience Test** - [PARTIAL]
    *   Simulate failures: MongoDB down, Ollama unreachable, image upload with corrupted file.
    *   Verify the app degrades gracefully at each failure point with correct HTTP codes and frontend error messages.
    *   Added automated resilience checks in `tests/test_resilience_security.py`; full browser-level validation remains.
*   **Apr 11 (Sat):** *OFF (2nd Saturday)*
*   **Apr 12 (Sun):** *OFF*

#### Week 12: Apr 13 (Mon) – Apr 18 (Sat) [NDMC Production Hardening]
*   **Apr 13 (Mon):** **Docker Production Config** - [COMPLETED]
    *   Create `Dockerfile.prod` for the backend — use `gunicorn` with `uvicorn` workers (not `--reload`), set worker count to CPU cores.
    *   Build a multi-stage frontend `Dockerfile` (Node build → Nginx serve) with gzip compression enabled.
*   **Apr 14 (Tue):** **Docker Compose Production Profile** - [COMPLETED]
    *   Add a `docker-compose.prod.yml` with proper healthchecks, `restart: always` policies, named volume mounts, and log rotation.
    *   Test the full stack via `docker compose -f docker-compose.prod.yml up --build`.
*   **Apr 15 (Wed):** **NDMC Deployment Environment Config** - [COMPLETED]
    *   Write a production `env.production` with every variable NDMC IT needs to set (MongoDB URI, JWT secret, CORS domain, SMTP, Ollama host).
    *   Document NDMC server requirements: Ubuntu 22.04, NVIDIA GPU with CUDA, Docker 24+, 16 GB RAM.
*   **Apr 16 (Thu):** **API Versioning** - [COMPLETED]
    *   Add `/api/v1` prefix to all backend routes using FastAPI's `APIRouter(prefix="/api/v1")`.
    *   Update frontend API base URL to `/api/v1`; document versioning strategy so future NDMC API consumers are not broken by changes.
*   **Apr 17 (Fri):** **MongoDB Backup Strategy** - [COMPLETED]
    *   Write a `backup_db.sh` script using `mongodump` with timestamp-named output directories.
    *   Document the recommended NDMC backup schedule (daily dumps, 30-day retention) and recovery procedure.
*   **Apr 18 (Sat):** **UI/UX Audit & NDMC Branding Pass** - [PARTIAL]
    *   Review the full app for font/colour consistency; replace placeholder logos with NDMC branding placeholders.
    *   Standardize all Tailwind spacing, heading hierarchy, and button styles for a professional government portal look.
*   **Apr 19 (Sun):** *OFF*

#### Week 13: Apr 20 (Mon) – Apr 25 (Sat) [Testing Sprint]
*   **Apr 20 (Mon):** **Backend Unit Tests (pytest)** - [PARTIAL]
    *   Write `pytest` cases for: JWT auth, complaint CRUD, classifier (mock Ollama), geotagging, rule engine, rate limiter.
    *   Use `mongomock` to run tests against an in-memory MongoDB; no real DB required.
    *   Added targeted tests for resilience/security and notification chain; broader unit coverage is still pending.
*   **Apr 21 (Tue):** **API Integration Tests** - [PARTIAL]
    *   Test all REST endpoints with `httpx.AsyncClient` against a seeded test database.
    *   Assert correct HTTP codes, response schemas, and role-based access control for citizen / dept_head / admin.
    *   Integration smoke now covers core health and `/api/v1` alias checks; full endpoint matrix is pending.
*   **Apr 22 (Wed):** **Security Penetration Test** - [PARTIAL]
    *   Attempt: JWT token manipulation, auth bypass on protected routes, file upload with malicious MIME, XSS in remarks field.
    *   Document findings and patch any vulnerabilities before NDMC handover.
    *   Added `docs/SECURITY_TESTING.md` checklist and automated security-oriented tests; external scanner run pending.
*   **Apr 23 (Thu):** **Load Test** - [PARTIAL]
    *   Use `locust` to simulate 50 concurrent citizen logins + 20 concurrent `/analyze` uploads.
    *   Document queue behavior (Ollama serialises via lock), API latency P95, and MongoDB query times under load.
    *   Added `backend/locustfile.py`, `backend/requirements-loadtest.txt`, and run scripts; benchmark execution report pending.
*   **Apr 24 (Fri):** **Mobile Responsiveness Fixes** - [COMPLETED]
    *   Test on 375px viewport (iPhone SE) — fix overflowing tables, navbar collapses, map containers.
    *   Add `viewport` meta tag optimisation; ensure tap targets are ≥ 44px for NDMC field officers on mobile.
*   **Apr 25 (Sat):** *OFF (4th Saturday)*
*   **Apr 26 (Sun):** *OFF*

#### Week 14 (Partial): Apr 27 (Mon) – Apr 30 (Thu) [Pre-Handover Sprint]
*   **Apr 27 (Mon):** **NDMC Handover Guide** - [COMPLETED]
    *   Write `docs/NDMC_DEPLOYMENT.md`: step-by-step guide for NDMC IT (clone repo → configure env → docker compose → seed first admin → verify GPU).
    *   Include troubleshooting section: Ollama VRAM errors, MongoDB auth, CORS for production domain.
*   **Apr 28 (Tue):** **Final API Reference Documentation** - [COMPLETED]
    *   Enhance all OpenAPI endpoint descriptions with request/response examples and error code tables.
    *   Export Swagger JSON; publish as `docs/API_REFERENCE.md` for NDMC developers integrating with the backend.
*   **Apr 29 (Wed):** **Repository Cleanup** - [PARTIAL]
    *   Remove all `console.log` statements, `# TODO`, dead-code branches, and stale comments from every file.
    *   Run final `isort` + `black` (Python) and `Prettier` (JS) formatting pass; ensure zero lint errors.
    *   Added ESLint config and CI lint gate; full formatting and dead-code cleanup pass remains.
*   **Apr 30 (Thu):** **Release Tag v1.0-rc1** - [PARTIAL]
    *   Tag `v1.0-rc1` on `main`; write a GitHub Release with a changelog summarising all features.
    *   Set up a basic GitHub Actions CI workflow: run `pytest` and ESLint on every push to `main`.
*   **May 01 (Fri):** *Phase 2 Buffer / Spillover*
*   **May 02 (Sat):** **Code Freeze**
    *   Lock `requirements.txt` and `package.json` dependency versions; no new packages without explicit approval.
    *   Final line-by-line review of all critical paths (auth, analyze, status update).
*   **May 03 (Sun):** *OFF*

---

### Phase 3: UAT, Report & Final Submission (Weeks 15-18)

#### Week 15: May 04 (Mon) – May 09 (Sat) [Containerization — Already Partially Done]
*   **May 04 (Mon):** **Docker Production Verification** - [COMPLETED IN WEEK 12]
    *   Backend `Dockerfile` + `docker-compose.yml` already in place; verify production config (`Dockerfile.prod`, `gunicorn` init) works cleanly on a clean machine.
    *   Confirm `docker compose up --build` produces a clean production stack with no dev-only dependencies.
*   **May 05 (Tue):** **Nginx SPA Routing Verification**
    *   Verify the frontend `Dockerfile` multi-stage build correctly falls back to `index.html` for all React routes (SPA mode).
    *   Test direct-URL access (e.g., `http://ndmc-server/dashboard`) does not return 404.
*   **May 06 (Wed):** **NDMC Network Config**
    *   Configure Ollama to be accessible within the NDMC Docker network (`host.docker.internal` on Linux alternative).
    *   Test container-to-Ollama connectivity; document the `OLLAMA_BASE_URL` override for NDMC's server topology.
*   **May 07 (Thu):** **Production Stack Stress Test**
    *   Run `docker compose -f docker-compose.prod.yml up` and execute the locust load test against the containerised stack.
    *   Verify MongoDB named volumes persist data across `docker compose down/up` cycles.
*   **May 08 (Fri):** **Deployment Simulation on Clean Machine**
    *   Follow the `NDMC_DEPLOYMENT.md` guide on a fresh environment to verify the instructions are accurate and complete.
    *   Time the full cold-start (clone → running app) and document it in the handover guide.
*   **May 09 (Sat):** *OFF (2nd Saturday)*
*   **May 10 (Sun):** *OFF*

#### Week 16: May 11 (Mon) – May 16 (Sat)
*   **May 11 (Mon):** **UAT Setup**
    *   Prepare a fresh "Staging" database environment with clean data for the final walkthrough.
    *   Create a script for UAT testers (friends/colleagues) outlining task flows to perform.
*   **May 12 (Tue):** **UAT: Citizen Persona**
    *   Execute the "Citizen" test script: Take photo of mock issue -> Upload -> Verify Map -> Submit.
    *   Note down any friction points (e.g., "Upload took too long", "Button wasn't clear").
*   **May 13 (Wed):** **UAT: Admin Persona**
    *   Execute the "Admin" test script: Log in -> Find new complaint -> Update Status to Resolved.
    *   Verify that the workflow is logical and efficient for a municipal officer.
*   **May 14 (Thu):** **Feedback Loop Implementation**
    *   Implement quick fixes for the specific UX friction points identified during the UAT sessions.
    *   Adjust notification text or button colors based on tester feedback for better clarity.
*   **May 15 (Fri):** **Resilience Testing**
    *   Test the application's behavior when the AI service is down (simulate Ollama crash).
    *   Ensure the application degrades gracefully (shows specific error) rather than crashing the whole UI.
*   **May 16 (Sat):** **Final Visual Polish**
    *   Fine-tune UI details: standardize border radii, ensure consistent shadow depth, and check alignment.
    *   Verify favicon, page titles, and meta descriptions are correct.
*   **May 17 (Sun):** *OFF*

#### Week 17: May 18 (Mon) – May 23 (Sat)
*   **May 18 (Mon):** **Report: Introduction & Literature**
    *   Draft the "Introduction" and "Literature Review" chapters of the final project report.
    *   Cite research papers on Vision-Language Models (VLMs), civic AI, and local LLM inference for smart city applications.
*   **May 19 (Tue):** **Report: System Design & Architecture**
    *   Write the technical chapters detailing the MERN+FastAPI architecture and Microservices approach.
    *   Insert the finalized Architecture Diagrams and Entity Relationship Diagrams (ERD).
*   **May 20 (Wed):** **Documentation Screenshots**
    *   Capture high-resolution screenshots of every screen in the application for the report appendices.
    *   Annotate screenshots to explain specific features (e.g., arrows pointing to the "AI Analysis" results).
*   **May 21 (Thu):** **User Manual Creation**
    *   Create a PDF "User Guide" for the end-users (Citizens) and the Admins, explaining how to use the tool.
    *   Include troubleshooting steps for common issues (e.g., "What if GPS is disabled?").
*   **May 22 (Fri):** **Project Presentation**
    *   Design the final Powerpoint presentation summarizing the problem, solution, tech stack, and live demo flow.
    *   Rehearse the presentation timing to ensure it fits within the allotted defense slot.
*   **May 23 (Sat):** *OFF (4th Saturday)*
*   **May 24 (Sun):** *OFF*

#### Week 18: May 25 (Mon) – May 27 (Wed)
*   **May 25 (Mon):** **GitHub README & Portfolio**
    *   Update the repository `README.md` with a professional badge, screenshots, and setup usage.
    *   Write a "Contribution" guide, even though it's a academic project, to show best practices.
*   **May 26 (Tue):** **Repository Lifecycle Management**
    *   Perform a final `git squash` to clean up the commit history into meaningful milestones.
    *   Tag the repository with `v1.0-release` to mark the submission version.
*   **May 27 (Wed):** **Final Submission**
    *   Verify all submitted artifacts (Code, Report, PPT) match the university requirements.
    *   Submit the project and backup the entire workspace to an external drive.