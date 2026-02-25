# 🐳 Docker Setup Guide

## Quick Start with Docker

Docker provides a containerized, consistent environment for running Jan-Sunwai AI, eliminating dependency issues and MongoDB setup complexity.

### Prerequisites

1. **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop)
   - Ensure Docker Desktop is running (check system tray)

### Running with Docker

**Option 1: One-Click Start (Windows)**
```cmd
.\scripts\docker-start.bat
```

**Option 1 (Linux/macOS):**
```bash
chmod +x scripts/docker-start.sh
./scripts/docker-start.sh
```

**Option 2: Manual Commands**
```bash
# Start all services (backend + MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### What Gets Deployed

The `docker-compose.yml` runs:
- **MongoDB** (Port 27017) - Database with persistent volume
- **Backend API** (Port 8000) - FastAPI server with hot-reload

### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` with your settings (optional for local dev)

### Docker Commands Cheat Sheet

```bash
# Build and start
docker-compose up -d --build

# Stop services
docker-compose down

# View backend logs
docker-compose logs -f backend

# Restart backend only
docker-compose restart backend

# Execute commands inside container
docker-compose exec backend python -c "print('Hello')"

# Clean up everything (including volumes)
docker-compose down -v
```

### Troubleshooting

**Port Already in Use**
- If port 8000 or 27017 is busy, stop local MongoDB/backend first
- Or modify ports in `docker-compose.yml`

**Changes Not Reflecting**
- Backend code auto-reloads with volume mounts
- For dependency changes: `docker-compose up -d --build`

**View Container Status**
```bash
docker-compose ps
```

### Production Notes

For production deployment:
1. Remove `--reload` flag in Dockerfile CMD
2. Set strong `JWT_SECRET_KEY` in `.env`
3. Use environment-specific MongoDB URLs
4. Consider using Docker Swarm or Kubernetes for scaling
