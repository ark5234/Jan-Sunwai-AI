# Jan-Sunwai AI - Daily Project Report & Plan
**Project Duration:** January 28, 2026 – May 27, 2026  
**Schedule Logic:** Monday to Saturday work weeks. Sundays are always OFF. 2nd & 4th Saturdays are OFF.

---

### Phase 1: Foundation & Core Backend (Weeks 1-6)

#### Week 1: Jan 28 (Wed) – Jan 31 (Sat)
*   **Jan 28 (Wed):** **Project Inception & Repository Setup**
    *   Initialize the master Git repository, establish the folder structure for Backend/Frontend, and configure a comprehensive `.gitignore`.
    *   Draft the initial project roadmap and technology stack document, researching optimal versions for FastAPI and React integration.
*   **Jan 29 (Thu):** **Development Environment Configuration**
    *   Install and configure Python 3.10+, Node.js, and essential CLI tools; set up virtual environments and dependency managers (pip, npm).
    *   Configure VS Code workspace extensions (Pylance, ESLint, Prettier) and define strict linting rules to ensure code quality.
*   **Jan 30 (Fri):** **System Architecture & Requirements**
    *   Create detailed architectural diagrams (Data Flow, Entity Relationship) to visualize the interaction between AI models and usage.
    *   Formalize the System Requirements Specification (SRS), detailing functional requirements for the Grievance Classification module.
*   **Jan 31 (Sat):** **Backend Skeleton Implementation**
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
*   **Feb 09 (Mon):** **AI Model Research (CLIP)** - [COMPLETED]
    *   Conduct deep-dive research into OpenAI's CLIP architecture to understand its Zero-Shot classification capabilities relevant to civic issues.
    *   Read documentation for `transformers` and `huggingface` libraries to identify the most efficient pre-trained models for local execution.
*   **Feb 10 (Tue):** **AI Environment & Dependency Integration** - [COMPLETED]
    *   Install heavy AI libraries (`torch`, `transformers`, `Pillow`) and resolve CUDA/CPU version conflicts to ensure consistent model loading.
    *   Write a standalone script to download and cache the `openai/clip-vit-base-patch32` model to avoid runtime downloads.
*   **Feb 11 (Wed):** **Taxonomy & Label Engineering** - [COMPLETED]
    *   Define a comprehensive dictionary of prompt labels (e.g., "garbage dump", "pothole", "broken street light") mapped to civic departments.
    *   Iterate on label phrasing, testing synonyms to determine which text descriptions yield the highest confidence scores from CLIP.
*   **Feb 12 (Thu):** **Zero-Shot Classifier Implementation** - [COMPLETED]
    *   Develop the `classifier.py` module, encapsulating the CLIP model loading and prediction logic into a reusable Class structure.
    *   Implement image preprocessing pipelines (resizing, normalization) to prepare raw user uploads for the neural network.
*   **Feb 13 (Fri):** **Classification Accuracy Testing** - [COMPLETED]
    *   Curate a dataset of 50 diverse test images (various lighting, angles) and run batch predictions to benchmark model accuracy.
    *   Analyze misclassification cases and tune the label text prompts to improve distinction between similar categories (e.g., "Road" vs "Footpath").
*   **Feb 14 (Sat):** *OFF (2nd Saturday)*
*   **Feb 15 (Sun):** *OFF*

#### Week 4: Feb 16 (Mon) – Feb 21 (Sat)
*   **Feb 16 (Mon):** **Metadata & EXIF Research**
    *   Study the EXIF standard and `Pillow` library documentation to understand how GPS tags are encoded in image files.
    *   Experiment with different sample images to identify variations in how Android and iOS devices store location data.
*   **Feb 17 (Tue):** **GPS Coordinate Parsing Logic**
    *   Write complex mathematical utility functions to convert GPS Degrees/Minutes/Seconds (DMS) tuples into standard Decimal Degrees.
    *   Implement robust error handling for the parser to prevent crashes when dealing with corrupted or partial EXIF headers.
*   **Feb 18 (Wed):** **Reverse Geocoding Integration**
    *   Register for OpenStreetMap/Nominatim services and implement the `geopy` client to translate coordinates into human-readable addresses.
    *   Implement request rate limiting and caching strategies for the geocoder to respect API usage policies and improve speed.
*   **Feb 19 (Thu):** **Geotagging Module Development**
    *   Integrate the EXIF parser and Geocoder into a unified `extract_location` service function within the backend.
    *   Write unit tests specifically for the location module, verifying it correctly handles images from different hemispheres.
*   **Feb 20 (Fri):** **Edge Case Management**
    *   Develop logic to handle images strictly stripped of metadata (e.g., WhatsApp images) by returning "Location Unknown" without errors.
    *   Implement value sanitization to ensure "None" or invalid coordinates don't corrupt the database or crash the geocoder.
*   **Feb 21 (Sat):** **AI Pipeline Integration**
    *   Merge the Classification and Geotagging modules into the main `/analyze` API endpoint, orchestrating sequential execution.
    *   Conduct end-to-end reliability tests of the `/analyze` endpoint, ensuring it returns both Dept and Location within acceptable time limits.
*   **Feb 22 (Sun):** *OFF*

#### Week 5: Feb 23 (Mon) – Feb 28 (Sat)
*   **Feb 23 (Mon):** **Generative AI Environment Setup**
    *   Install and configure `Ollama` locally; pull the `llava` (Language-and-Vision Assistant) model for multimodal generation.
    *   Verify hardware resource usage (RAM/VRAM) during model inference to ensure the development machine remains responsive.
*   **Feb 24 (Tue):** **GenAI Prompt Engineering**
    *   Design and iterate on system prompts to guide LLaVA in writing formal, polite, and actionable government complaint letters.
    *   Test various "personas" in the prompts to ensure the AI adopts the tone of a concerned but professional citizen.
*   **Feb 25 (Wed):** **Complaint Generator Service**
    *   Develop `generator.py` to wrap the Ollama API calls, handling inputs (Department, Location, Image context) dynamically.
    *   Implement text post-processing to clean up AI artifacts (extra quotes, hallucinations) before sending the draft to the user.
*   **Feb 26 (Thu):** **Draft Generation API**
    *   Expose the generation logic via a FastAPI endpoint, allowing the frontend to request a fresh draft based on analysis results.
    *   Implement timeout management for the generation endpoint, as LLM inference can be slow, adding async `await` patterns.
*   **Feb 27 (Fri):** **Quality Assurance for Generated Text**
    *   Manually review 20+ generated complaints for coherence, checking if variables like "Location" are correctly inserted.
    *   Refine the prompt based on review findings to eliminate repetitive phrases or overly aggressive language.
*   **Feb 28 (Sat):** *OFF (4th Saturday)*
*   **Mar 01 (Sun):** *OFF*

#### Week 6: Mar 02 (Mon) – Mar 07 (Sat)
*   **Mar 02 (Mon):** **Input Validation & Security**
    *   Implement strict file type validation (Magic Numbers) to ensure only valid images are processed, rejecting potential malware.
    *   Enforce file size limits in Nginx/FastAPI layers to prevent Denial of Service (DoS) attacks via massive uploads.
*   **Mar 03 (Tue):** **Global Error Handling**
    *   Create a centralized exception handling architecture to catch unhandled errors and return standard JSON error responses.
    *   Log all exceptions with stack traces to a local file for easier debugging during the development phase.
*   **Mar 04 (Wed):** **API Documentation & Swagger**
    *   Enhance the OpenAPI (Swagger) schema with detailed descriptions, response examples, and data type definitions.
    *   Verify that the "Try it out" feature in Swagger UI works for file uploads, aiding in frontend developer communication.
*   **Mar 05 (Thu):** **Performance Profiling**
    *   Profile the application using Python profiling tools to identify bottlenecks in the image analysis pipeline.
    *   Optimize image loading routines in `Pillow` to reduce memory footprint during concurrent requests.
*   **Mar 06 (Fri):** **Security Middleware (CORS)**
    *   Configure Cross-Origin Resource Sharing (CORS) middleware to allow requests strictly from the frontend development port.
    *   Review API headers to ensure best practices for security (e.g., preventing content-type sniffing).
*   **Mar 07 (Sat):** **Phase 1 System Integration Test**
    *   Perform a complete system test of the entire backend stack, verifying seamless data flow from Upload -> Analyze -> Generate.
    *   Document any known issues or "TODOs" discovered during testing to prioritize them for Phase 2.
*   **Mar 08 (Sun):** *OFF*

---

### Phase 2: Frontend & User Experience (Weeks 7-11)

#### Week 7: Mar 09 (Mon) – Mar 14 (Sat)
*   **Mar 09 (Mon):** **Frontend Initialization**
    *   Initialize the React application using Vite, configuring the `package.json` scripts and installing core dependencies (`axios`, `router`).
    *   Set up the directory structure (`/src/components`, `/src/pages`, `/src/hooks`) for long-term scalability.
*   **Mar 10 (Tue):** **Atomic Design System Setup**
    *   Create a design tokens file (colors, spacing, typography) to ensure visual consistency across the application.
    *   Begin implementing "Atomic" components (Buttons, Inputs, Cards) in isolation to build a reusable UI library.
*   **Mar 11 (Wed):** **Styling Architecture (Tailwind)**
    *   Install and configure Tailwind CSS, setting up the `tailwind.config.js` to match the project's color palette.
    *   Convert the basic atomic components to use Tailwind utility classes, verifying responsiveness on different breakpoints.
*   **Mar 12 (Thu):** **Routing & Navigation**
    *   Implement `react-router-dom` to manage application views (Home, Upload, Admin Dashboard).
    *   Create the shell layouts (Header, Footer, Sidebar) and ensure they persist correctly across route changes.
*   **Mar 13 (Fri):** **Composite Component Development**
    *   Combine atomic components to build more complex UI structures like the "Hero Section" and "Feature Highlights" for the landing page.
    *   Test component interactivity (hover states, click handlers) to ensure a polished feel.
*   **Mar 14 (Sat):** *OFF (2nd Saturday)*
*   **Mar 15 (Sun):** *OFF*

#### Week 8: Mar 16 (Mon) – Mar 21 (Sat)
*   **Mar 16 (Mon):** **Drag & Drop Upload Component**
    *   Design and build a sophisticated file upload zone supporting drag-and-drop functionality using HTML5 Drag and Drop API.
    *   Implement visual feedback cues (highlight on hover, file name display) to improve user confidence during upload.
*   **Mar 17 (Tue):** **Image Preview & Validation UI**
    *   Develop client-side logic to generate and display a thumbnail preview of the selected image immediately.
    *   Add client-side validation messages for invalid file types or sizes before the request is even sent to the server.
*   **Mar 18 (Wed):** **Backend Integration (The Wiring)**
    *   Write a custom React Hook (`useAnalyzeImage`) to manage the `axios` POST request to the `/analyze` endpoint.
    *   Handle server responses, parsing the JSON data (Department, Text, Location) and storing it in the React State.
*   **Mar 19 (Thu):** **Loading State UX**
    *   Design and implement engaging loading animations (spinners or skeleton screens) to keep the user informed during the slow AI processing.
    *   Test the UI application under "Slow 3G" network throttle to ensure the loading states appear correctly.
*   **Mar 20 (Fri):** **Analysis Result Presentation**
    *   Build the "Analysis Result" card component to beautifully display the detected Department and confidence score.
    *   Implement logic to highlight low-confidence predictions, prompting the user to manually verify the category.
*   **Mar 21 (Sat):** **Complaint Editing Feature**
    *   Create a rich text area or expandable input field allowing users to edit the AI-generated complaint letter.
    *   Implement "Reset" functionality to revert the text back to the original AI draft if the user makes a mistake.
*   **Mar 22 (Sun):** *OFF*

#### Week 9: Mar 23 (Mon) – Mar 28 (Sat)
*   **Mar 23 (Mon):** **Map Integration Strategy**
    *   Install `leaflet` and `react-leaflet` libraries; set up the base map component with OpenStreetMap tiles.
    *   Fix common Leaflet CSS issues (missing marker icons) ensuring the map renders correctly in the React DOM.
*   **Mar 24 (Tue):** **Dynamic Map Markers**
    *   Implement logic to dynamically place a marker on the map based on the specific `lat/long` received from the backend.
    *   Add popup tooltips to the marker showing the resolved address for user confirmation.
*   **Mar 25 (Wed):** **Draggable Marker Logic**
    *   Enable "Draggable" functionality on the marker, allowing users to fine-tune the location if the GPS was slightly off.
    *   Capture the "Check End" event from the drag action to retrieve the new coordinates for the updated complaint.
*   **Mar 26 (Thu):** **Address Sync on Interaction**
    *   Trigger a reverse-geocoding API call whenever the user manually moves the marker to update the address text field.
    *   Debounce the API calls to prevent flooding the geocoding service while the user is dragging the pin.
*   **Mar 27 (Fri):** **Map UI Polish & Controls**
    *   Style the map container with rounded corners and shadows to fit the app's aesthetic.
    *   Add custom map controls (Center on Me) using the browser's Geolocation API as a fallback positioning method.
*   **Mar 28 (Sat):** *OFF (4th Saturday)*
*   **Mar 29 (Sun):** *OFF*

#### Week 10: Mar 30 (Mon) – Apr 04 (Sat)
*   **Mar 30 (Mon):** **Final Submission Form**
    *   Aggregate all data (Image, Text, Location, Contact Info) into a final "Review & Submit" form.
    *   Implement rigorous form validation (required fields, email format) to ensure data completeness before submission.
*   **Mar 31 (Tue):** **Backend Persistence Implementation**
    *   Update the backend to accept the final JSON payload and perform the actual INSERT operation into the MongoDB collection.
    *   Return the new Complaint ID in the response to track the submission.
*   **Apr 01 (Wed):** **Submission Wiring & State Management**
    *   Connect the Frontend "Submit" button to the persistence endpoint; manage "Submitting..." states to prevent double-clicks.
    *   Clear temporary form state upon successful submission to reset the application for the next user.
*   **Apr 02 (Thu):** **Success & Failure Journeys**
    *   Design a celebratory "Success" page displaying the Complaint ID and instructions on what happens next.
    *   Build a user-friendly "Error" modal that explains what went wrong (e.g., "Server Timeout") and offers a "Retry" button.
*   **Apr 03 (Fri):** **Local Storage Drafts**
    *   Implement a `localStorage` backup mechanism to save form progress; restore data automatically if the user accidentally refreshes.
    *   Test persistence across browser restarts to ensure data safety.
*   **Apr 04 (Sat):** **Phase 2 Code Review**
    *   Conduct a self-review of the entire Frontend codebase, ensuring component reusability and removing hardcoded strings.
    *   Refactor large components into smaller sub-components (prop drilling cleanup) to improve maintainability.
*   **Apr 05 (Sun):** *OFF*

#### Week 11: Apr 06 (Mon) – Apr 11 (Sat)
*   **Apr 06 (Mon):** **Admin Module Architecture**
    *   Plan the Admin Dashboard structure and route hierarchy (`/admin`, `/admin/dashboard`, `/admin/login`).
    *   Create the layout skeleton for the Admin panel, distinct from the public-facing citizen UI.
*   **Apr 07 (Tue):** **Admin Authentication (MVP)**
    *   Implement a simple login form with a hardcoded credential check (for MVP scope) to gate access to the admin routes.
    *   Use React Context or Session Storage to persist the "LoggedIn" state across admin pages.
*   **Apr 08 (Wed):** **Admin Data Fetching**
    *   Develop the `GET /complaints` endpoint in the backend to return a paginated list of all grievance records.
    *   Create a data fetching hook in React to load this data when the Admin Dashboard mounts.
*   **Apr 09 (Thu):** **Dashboard Table Implementation**
    *   Build a data table component to display grievances with columns for ID, Date, Category, and current Status.
    *   Implement click-to-view functionality, routing the admin to a detailed view of a specific complaint.
*   **Apr 10 (Fri):** **Client-Side Filtering**
    *   Add dropdown filters to the dashboard to allow sorting by Department (Civil vs. VBD) or Status (Open/Closed).
    *   Implement search functionality to filter the list based on Complaint ID or keywords.
*   **Apr 11 (Sat):** *OFF (2nd Saturday)*
*   **Apr 12 (Sun):** *OFF*

---

### Phase 3: Finalization & Deployment (Weeks 12-18)

#### Week 12: Apr 13 (Mon) – Apr 18 (Sat)
*   **Apr 13 (Mon):** **Admin Gallery View**
    *   Create an alternative "Grid View" for the dashboard that focuses on the images, allowing admins to visually scan problems.
    *   Implement "Lazy Loading" for images in the grid to maintain performance with large datasets.
*   **Apr 14 (Tue):** **Status Management Components**
    *   Detailed view: Add action buttons ("Mark Solved", "Reject Guidelines") that trigger status updates.
    *   Add modal confirmations ("Are you sure?") to preventing accidental status changes.
*   **Apr 15 (Wed):** **Status Update Backend Logic**
    *   Implement the `PATCH /complaint/{id}` endpoint to handle partial updates for status and admin remarks.
    *   Update the database timestamp for `updated_at` whenever a status change occurs.
*   **Apr 16 (Thu):** **UI/UX Consistency Audit**
    *   Review the entire application for font consistency, ensuring the Typography hierarchy (H1 vs H2) makes sense.
    *   Standardize padding and margins across all pages using Tailwind utility classes.
*   **Apr 17 (Fri):** **Responsive Web Design (RWD)**
    *   Test the application on mobile emulators (iPhone/Pixel) to ensure the layout stacks correctly on small screens.
    *   Fix specific mobile issues like "overflowing tables" or "hidden menus" in the navigation bar.
*   **Apr 18 (Sat):** **Accessibility (a11y) Check**
    *   Run LightHouse audits to identify accessibility gaps (missing alt tags, poor contrast ratios).
    *   Add ARIA labels to form inputs and buttons to support screen reader users.
*   **Apr 19 (Sun):** *OFF*

#### Week 13: Apr 20 (Mon) – Apr 25 (Sat)
*   **Apr 20 (Mon):** **Backend Unit Testing**
    *   Write comprehensive `pytest` cases for the critical business logic (Model inference, Database storage).
    *   Mock external dependencies (Ollama, Geolocation API) to ensure tests run fast and offline.
*   **Apr 21 (Tue):** **Frontend Integration Testing**
    *   Perform manual "Black Box" testing of the full user journey: Upload -> Analyze -> Edit -> Map -> Submit.
    *   Document bugs found during the process (e.g., "Map pin returns to center on reset") in a tracking sheet.
*   **Apr 22 (Wed):** **Admin Workflow Testing**
    *   Test the Admin lifecyle: Login -> View specific complaint -> Change Status -> Verify update in DB.
    *   Check for data consistency (e.g., does the status update reflect immediately without a refresh?).
*   **Apr 23 (Thu):** **Bug Fixing Sprint**
    *   Dedicate the entire day to squashing the priority bugs identified during the testing sessions.
    *   Fix any race conditions in the UI where state updates might conflict.
*   **Apr 24 (Fri):** **Resource Optimization**
    *   Implement image compression on the client side (using `browser-image-compression`) to reduce upload bandwidth.
    *   Audit the final bundle size of the React app and utilize code splitting if necessary.
*   **Apr 25 (Sat):** *OFF (4th Saturday)*
*   **Apr 26 (Sun):** *OFF*

#### Week 14: Apr 27 (Mon) – May 02 (Sat)
*   **Apr 27 (Mon):** **Security Hardening**
    *   Scan the codebase for accidentally committed secrets (API keys) and move them to `.env` files.
    *   Implement input sanitization libraries to protect against XSS (Cross-Site Scripting) in the "Remarks" fields.
*   **Apr 28 (Tue):** **Performance Audit**
    *   Run Google Lighthouse performance scores on the final build; address "Render Blocking" resources.
    *   Optimize backend query speeds by adding indexes to the MongoDB `department` and `status` fields.
*   **Apr 29 (Wed):** **Frontend Code Cleanup**
    *   Remove all `console.log` statements, commented-out dead code, and unused imports.
    *   Run the final formatting pass (Prettier) to ensure every file is identical in style.
*   **Apr 30 (Thu):** **Backend Code Cleanup**
    *   Add comprehensive Docstrings to all Python functions following the Google/NumPy style guide.
    *   Refactor any "God Functions" (complex functions doing too much) into smaller helpers.
*   **May 01 (Fri):** **Pre-Deployment Freeze**
    *   Lock the `requirements.txt` and `package.json` versions to prevent unexpected updates breaking the build.
    *   Create a "Code Freeze" tag in Git; no new features allowed, only critical hotfixes.
*   **May 02 (Sat):** **Final Code Review**
    *   Conduct a final line-by-line review of the main logic paths to ensure logic soundness.
    *   Verify that all "TODO" comments have been addressed or moved to a future backlog.
*   **May 03 (Sun):** *OFF*

#### Week 15: May 04 (Mon) – May 09 (Sat)
*   **May 04 (Mon):** **Containerization Concepts**
    *   Study Docker fundamentals (Images, Containers, Volumes, Networks) to prepare for deployment.
    *   Install Docker Desktop and verify the installation with the "hello-world" container.
*   **May 05 (Tue):** **Backend Containerization**
    *   Write the `Dockerfile` for the Python API, selecting a slim base image (`python:3.10-slim`) for efficiency.
    *   Build and run the container locally, debugging any missing system dependencies (like `gcc` for some libraries).
*   **May 06 (Wed):** **Frontend Containerization**
    *   Write the `Dockerfile` for the Frontend, using a multi-stage build (Node build -> Nginx serve) to keep images small.
    *   Configure basic Nginx routing rules to handle the React Single Page Application (SPA) history mode.
*   **May 07 (Thu):** **Orchestration (Docker Compose)**
    *   Create `docker-compose.yml` to define services for Backend, Frontend, and the MongoDB database.
    *   Configure network links between containers so the API can talk to the Database using service names.
*   **May 08 (Fri):** **Deployment Simulation**
    *   Run `docker-compose up --build` to launch the entire stack in isolation, simulating a production server environment.
    *   Troubleshoot any inter-container connectivity issues (e.g., CORS issues between containers).
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
    *   Cite the research papers regarding CLIP and LLaVA usage in civic technology.
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