#!/usr/bin/env bash
# =============================================================================
#  Jan-Sunwai AI — GPU Check & Driver Setup (Linux/Ubuntu)
#  Automatically called by setup.sh
#  Can also be run standalone: bash check_gpu.sh
# =============================================================================

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
step()  { echo -e "\n${CYAN}>>> $1${NC}"; }
ok()    { echo -e "  ${GREEN}OK${NC}  $1"; }
warn()  { echo -e "  ${YELLOW}!!${NC}  $1"; }

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  GPU Check${NC}"
echo -e "${CYAN}============================================${NC}"

# ── Detect nvidia-smi ─────────────────────────────────────────────────────────
step "Scanning for NVIDIA GPU..."

if command -v nvidia-smi &>/dev/null; then
    echo ""
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader
    echo ""
    ok "NVIDIA GPU detected with working drivers. Ollama will use GPU automatically."
    exit 0
fi

# ── Check if NVIDIA card is present but driver missing ────────────────────────
NVIDIA_CARD=$(lspci 2>/dev/null | grep -i nvidia)
AMD_CARD=$(lspci 2>/dev/null | grep -i "amd\|radeon")
INTEL_CARD=$(lspci 2>/dev/null | grep -i "intel.*graphics\|intel.*vga")

if [ -n "$NVIDIA_CARD" ]; then
    warn "NVIDIA GPU found but drivers not installed:"
    warn "  $NVIDIA_CARD"
    MISSING_DRIVER=true
elif [ -n "$AMD_CARD" ]; then
    warn "AMD GPU detected: $AMD_CARD"
    warn "Ollama supports AMD via ROCm on Linux. Setup will attempt ROCm install."
    AMD_GPU=true
elif [ -n "$INTEL_CARD" ]; then
    warn "Intel integrated graphics: $INTEL_CARD"
    warn "Ollama will run on CPU — slower but functional."
    NO_GPU=true
else
    warn "No GPU detected. Ollama will run on CPU."
    NO_GPU=true
fi

# ── Prompt user ───────────────────────────────────────────────────────────────
echo ""
if [ "$MISSING_DRIVER" = true ]; then
    echo -e "${YELLOW}  NVIDIA GPU found but drivers are missing.${NC}"
    echo -e "${YELLOW}  Install NVIDIA drivers now? (y/n)${NC}"
    read -r choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        step "Installing NVIDIA drivers via ubuntu-drivers..."
        sudo apt-get update -qq
        sudo apt-get install -y ubuntu-drivers-common
        sudo ubuntu-drivers autoinstall
        ok "NVIDIA drivers installed."
        warn "A REBOOT is required. After rebooting, re-run setup.sh"
        echo ""
        read -rp "  Reboot now? (y/n): " reboot_choice
        if [[ "$reboot_choice" =~ ^[Yy]$ ]]; then
            sudo reboot
        else
            warn "Remember to reboot before running the project."
        fi
    else
        warn "Skipping driver install. Ollama will attempt CPU fallback."
    fi
elif [ "$AMD_GPU" = true ]; then
    echo -e "${YELLOW}  Install ROCm for AMD GPU acceleration? (y/n)${NC}"
    read -r choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        step "Installing ROCm (AMD GPU support)..."
        sudo apt-get update -qq
        wget -q https://repo.radeon.com/amdgpu-install/23.40.2/ubuntu/jammy/amdgpu-install_23.40.2.40502-1_all.deb
        sudo apt-get install -y ./amdgpu-install_*.deb
        sudo amdgpu-install --usecase=rocm --no-dkms -y
        sudo usermod -aG render,video "$USER"
        ok "ROCm installed. Reboot may be required."
        rm -f amdgpu-install_*.deb
    else
        warn "Skipping ROCm. Ollama will run on CPU."
    fi
else
    ok "Continuing without GPU. Ollama will run on CPU."
    warn "Expect slower inference (~2-5 min/image vs ~5-10 sec with GPU)."
fi

echo ""
