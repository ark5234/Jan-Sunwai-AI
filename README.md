# Jan-Sunwai AI

Automated Visual Classification & Geospatial Routing of Civic Grievances using Zero-Shot Learning.

## Project Structure
- `backend/`: FastAPI Python server (AI Logic)
- `frontend/`: React + Vite application (User Interface)

## Prerequisites
1. **Python 3.8+**
2. **Node.js 16+**
3. **Ollama** (Required for Generative Complaint Drafting)
   - Download and install [Ollama](https://ollama.ai/)
   - Pull the LLaVA model:
     ```bash
     ollama pull llava
     ```

## Setup Instructions

### 1. Backend Setup
Navigate to the `backend` folder:
```bash
cd backend
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Run the server:
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.

### 2. Frontend Setup
Navigate to the `frontend` folder:
```bash
cd frontend
```
Install dependencies:
```bash
npm install
```
Run the development server:
```bash
npm run dev
```
The app will be available at `http://localhost:5173`.

## Usage
1. Open the frontend in your browser.
2. Enter your name.
3. Upload an image of a civic issue (e.g., garbage, broken road).
   - *Note: Ensure the image contains EXIF GPS data for the map feature to work.*
4. Click "Analyze Complaint".
5. The AI will:
   - Classify the department (CLIP).
   - Extract location (EXIF).
   - Draft a complaint letter (LLaVA/Ollama).
6. Edit the complaint and submit (Submission logic to be connected to database).
