# Jan-Sunwai AI

Automated Visual Classification & Geospatial Routing of Civic Grievances using Zero-Shot Learning.

## Project Structure
- `backend/`: FastAPI Python server (AI Logic + JWT Authentication)
- `frontend/`: React + Vite application (User Interface)

## Features
✅ **Zero-Shot Image Classification** - CLIP model identifies civic issues without explicit training
✅ **Intelligent Geotagging** - Extracts GPS coordinates and reverse geocodes to addresses
✅ **AI-Powered Complaint Drafting** - LLaVA generates formal government complaint letters
✅ **JWT Authentication** - Secure token-based authentication with OAuth2
✅ **3-Tier Role System** - Citizen, Department Head, and Admin dashboards with role-based access
✅ **User Management** - Registration, login, and session handling

## Prerequisites
1. **Python 3.8+**
2. **Node.js 16+**
3. **MongoDB** (Database for users and complaints)
   - Install locally or use MongoDB Atlas
   - Default connection: `mongodb://localhost:27017`
4. **Ollama** (Required for Generative Complaint Drafting)
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

**Start MongoDB** (if running locally):
```bash
mongod
```

Run the server:
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.

**Optional:** Use the batch file for Windows:
```bash
run_backend.bat
```

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
1. **Register/Login**: Create an account or sign in at `http://localhost:5173`
2. **Upload Evidence**: Navigate to "New Complaint" and upload an image of a civic issue
   - Supported: Potholes, garbage dumps, waterlogging, broken lights, etc.
   - *Note: Images with EXIF GPS data will show accurate location*
3. **AI Analysis**: The system will:
   - **Classify** the issue type using CLIP zero-shot learning
   - **Extract** GPS coordinates and convert to address
   - **Generate** a formal complaint letter using LLaVA
4. **Review & Submit**: Edit the AI-generated complaint and submit

## Test Accounts
Demo accounts are available for testing the 3-tier role-based dashboard system.

**⚠️ IMPORTANT: Credentials are stored in `TEST_ACCOUNTS_CREDENTIALS.txt` (not committed to git)**

**To create test accounts**, run:
```bash
cd backend
python create_test_users.py
```

This will create three accounts:
- **Citizen** - Regular user who can file and track personal complaints
- **Department Head** - Manages department-specific complaints with status update capabilities
- **Admin** - System-wide access with full oversight and management

See `TEST_ACCOUNTS_CREDENTIALS.txt` for login credentials and detailed role descriptions.

### Dashboard Routes
- **Unified Dashboard**: `/dashboard` - Auto-redirects based on role
- **Citizen Dashboard**: `/citizen` - Personal complaints only
- **Dept Head Dashboard**: `/dept-head` - Department-specific view
- **Admin Dashboard**: `/admin` - System-wide oversight

## Security
- **JWT Authentication**: All API endpoints are protected with Bearer tokens
- **Password Hashing**: Bcrypt encryption for secure password storage
- **Session Management**: Automatic token expiration and renewal
- **Input Validation**: Strict file type and size validation

## Technologies
**Backend:**
- FastAPI (Web Framework)
- PyTorch + Transformers (CLIP Model)
- Ollama (LLaVA Vision-Language Model)
- Motor (Async MongoDB Driver)
- python-jose (JWT Handling)
- passlib (Password Hashing)

**Frontend:**
- React 18 + Vite
- TailwindCSS
- Axios (HTTP Client)
- React Router
