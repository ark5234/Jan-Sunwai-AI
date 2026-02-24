#!/usr/bin/env bash
# =============================================================================
#  Jan-Sunwai AI — One-Shot Setup Script (Linux/Ubuntu)
#  Run from the project root after cloning or unzipping:
#
#      bash setup.sh
#
#  Prerequisites:
#      - Ubuntu 22.04+ (or Debian-based distro)
#      - Internet connection
#      - NVIDIA drivers (handled by check_gpu.sh if missing)
# =============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
step() { echo -e "\n${CYAN}>>> $1${NC}"; }
ok()   { echo -e "  ${GREEN}OK${NC}  $1"; }
warn() { echo -e "  ${YELLOW}!!${NC}  $1"; }

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Jan-Sunwai AI — Setup${NC}"
echo -e "${CYAN}============================================${NC}"

# ── 0. GPU Check ──────────────────────────────────────────────────────────────
step "Running GPU check..."
bash "$SCRIPT_DIR/check_gpu.sh"

# ── 1. System packages ────────────────────────────────────────────────────────
step "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv curl git build-essential
ok "System packages ready"

# ── 2. Python venv + dependencies ─────────────────────────────────────────────
step "Setting up Python virtual environment..."
VENV="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
    ok "Created .venv"
else
    ok ".venv already exists"
fi

step "Installing Python dependencies..."
"$VENV/bin/pip" install --upgrade pip --quiet
"$VENV/bin/pip" install -r "$SCRIPT_DIR/backend/requirements.txt"
ok "Python dependencies installed"

# ── 3. Node.js ────────────────────────────────────────────────────────────────
step "Checking Node.js..."
if ! command -v node &>/dev/null; then
    warn "Node.js not found. Installing via NodeSource (LTS)..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    ok "Node.js installed: $(node --version)"
else
    ok "Node.js found: $(node --version)"
fi

# ── 4. Frontend npm install ───────────────────────────────────────────────────
step "Installing frontend dependencies..."
cd "$SCRIPT_DIR/frontend" && npm install
cd "$SCRIPT_DIR"
ok "Frontend dependencies installed"

# ── 5. Docker ─────────────────────────────────────────────────────────────────
step "Checking Docker..."
if ! command -v docker &>/dev/null; then
    warn "Docker not found. Installing Docker Engine..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    ok "Docker installed."
    warn "You may need to log out and back in for docker group to take effect."
    warn "Or run: newgrp docker"
else
    ok "Docker found: $(docker --version)"
fi

# ── 6. Start MongoDB via Docker Compose ───────────────────────────────────────
step "Starting MongoDB via Docker Compose..."
cd "$SCRIPT_DIR"
if docker compose up -d mongodb 2>/dev/null || docker-compose up -d mongodb 2>/dev/null; then
    ok "MongoDB container is running on port 27017"
else
    warn "Could not start MongoDB container. Run manually: docker compose up -d mongodb"
fi

# ── 7. Ollama ─────────────────────────────────────────────────────────────────
step "Checking Ollama..."
if ! command -v ollama &>/dev/null; then
    warn "Ollama not found. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
    ok "Ollama installed"
else
    ok "Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
fi

# ── 8. Start Ollama service ───────────────────────────────────────────────────
step "Starting Ollama service..."
if systemctl is-active --quiet ollama 2>/dev/null; then
    ok "Ollama service already running (systemd)"
else
    ollama serve &>/dev/null &
    sleep 4
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        ok "Ollama started"
    else
        warn "Ollama may not have started yet. Models will still be pulled."
    fi
fi

# ── 9. Pull Ollama models ─────────────────────────────────────────────────────
step "Pulling AI models (downloads ~4.5 GB — please wait)..."
echo "  Pulling qwen2.5vl:3b (Vision model — 3.2 GB)..."
ollama pull qwen2.5vl:3b
ok "qwen2.5vl:3b ready"

echo "  Pulling llama3.2:1b (Reasoning model — 1.3 GB)..."
ollama pull llama3.2:1b
ok "llama3.2:1b ready"

# ── 10. Make run scripts executable ───────────────────────────────────────────
step "Setting script permissions..."
chmod +x "$SCRIPT_DIR/scripts/"*.sh 2>/dev/null || true
ok "Run scripts are executable"

# ── 11. Summary ───────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo "  To START the project, open 3 terminals:"
echo ""
echo "  Terminal 1 — MongoDB (Docker):"
echo "      docker compose up -d mongodb"
echo ""
echo "  Terminal 2 — Backend:"
echo "      bash scripts/run_backend.sh"
echo ""
echo "  Terminal 3 — Frontend:"
echo "      bash scripts/run_frontend.sh"
echo ""
echo "  Then open: http://localhost:5173"
echo ""
