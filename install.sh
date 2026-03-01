#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Quiz-App – One-Command Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Yankeesti/syp/refs/heads/master/install.sh | bash
# ============================================================

REPO_URL="https://github.com/Yankeesti/syp.git"
INSTALL_DIR="$(pwd)/quiz-app"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_section() { echo -e "\n${BLUE}==> $*${NC}"; }

# sudo wrapper (robust even when sudo is not available, e.g. on root systems)
SUDO=""
command -v sudo &>/dev/null && SUDO="sudo"

# -------------------------------------------------------
# 1. Install Docker
# -------------------------------------------------------
install_docker() {
    log_section "Checking / installing Docker"

    if command -v docker &>/dev/null; then
        log_info "Docker is already installed: $(docker --version)"
        return
    fi

    # shellcheck source=/dev/null
    [[ -f /etc/os-release ]] && . /etc/os-release || { log_error "/etc/os-release not found."; exit 1; }

    case "${ID:-}" in
        ubuntu|debian)
            log_info "Installing Docker via get.docker.com ..."
            curl -fsSL https://get.docker.com | sh
            $SUDO systemctl enable --now docker
            ;;
        fedora)
            log_info "Installing Docker for Fedora ..."
            $SUDO dnf -y install dnf-plugins-core
            $SUDO dnf config-manager --add-repo \
                https://download.docker.com/linux/fedora/docker-ce.repo
            $SUDO dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
            $SUDO systemctl enable --now docker
            ;;
        arch|manjaro)
            log_info "Installing Docker for Arch Linux ..."
            $SUDO pacman -Sy --noconfirm docker docker-compose
            $SUDO systemctl enable --now docker
            ;;
        *)
            log_warn "Unknown OS '${ID:-}'. Trying universal installation via get.docker.com ..."
            curl -fsSL https://get.docker.com | sh
            ;;
    esac

    $SUDO usermod -aG docker "$USER" 2>/dev/null || true
    log_info "Docker installed. Note: To use without sudo, please log in again."
}

# -------------------------------------------------------
# 2. Install Git
# -------------------------------------------------------
install_git() {
    log_section "Checking / installing Git"

    if command -v git &>/dev/null; then
        log_info "Git is already installed: $(git --version)"
        return
    fi

    log_info "Installing Git ..."
    # shellcheck source=/dev/null
    [[ -f /etc/os-release ]] && . /etc/os-release || true
    case "${ID:-}" in
        ubuntu|debian)  $SUDO apt-get update -qq && $SUDO apt-get install -y git ;;
        fedora)         $SUDO dnf -y install git ;;
        arch|manjaro)   $SUDO pacman -Sy --noconfirm git ;;
        *)              log_warn "Unknown OS – trying apt-get ..."; $SUDO apt-get install -y git ;;
    esac
    log_info "Git installed."
}

# -------------------------------------------------------
# 3. Clone repository
# -------------------------------------------------------
clone_repo() {
    log_section "Cloning repository"

    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log_info "Directory $INSTALL_DIR already exists – skipping git clone."
        return
    fi

    log_info "Cloning $REPO_URL into $INSTALL_DIR ..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    log_info "Repository cloned."
}

# -------------------------------------------------------
# 4. Prompt for and validate .env
# -------------------------------------------------------


# Global variable for the validated path (used by copy_env())
ENV_FILE_PATH=""

ask_for_env() {
    log_section "Specify .env file"

    echo ""
    log_info "Required variables (.env.example):"
    echo "---------------------------------------------------"
    cat "$INSTALL_DIR/.env.example"
    echo "---------------------------------------------------"
    echo ""
    log_info "Fill a .env file with these variables and then provide the path."
    echo ""

    local env_path
    while true; do
        # Read interactive input via /dev/tty – works even with curl | bash
        printf "Please enter the path to your .env file: " >/dev/tty
        read -r env_path </dev/tty

        # Expand tilde
        env_path="${env_path/#\~/$HOME}"

        if [[ ! -f "$env_path" ]]; then
            log_error "File not found: $env_path"
            echo -e "Please check the path and try again.\n" >&2
            continue
        fi

        ENV_FILE_PATH="$env_path"
        break
    done
}

# -------------------------------------------------------
# 5. Copy .env
# -------------------------------------------------------
copy_env() {
    log_section "Installing .env"
    cp "$ENV_FILE_PATH" "$INSTALL_DIR/.env"
    log_info ".env copied to $INSTALL_DIR/.env"
}

# -------------------------------------------------------
# 6. Start Docker Compose
# -------------------------------------------------------
start_services() {
    log_section "Starting services"
    log_info "Running docker compose up --build -d ..."

    if docker compose version &>/dev/null 2>&1; then
        $SUDO docker compose -f "$INSTALL_DIR/docker-compose.yml" up --build -d
    elif command -v docker-compose &>/dev/null; then
        $SUDO docker-compose -f "$INSTALL_DIR/docker-compose.yml" up --build -d
    else
        log_error "Neither 'docker compose' (v2) nor 'docker-compose' (v1) found."
        exit 1
    fi
}

# -------------------------------------------------------
# 8. Success output
# -------------------------------------------------------
print_success() {
    local env_file="$INSTALL_DIR/.env"
    local frontend_url backend_url
    frontend_url=$(grep -E '^FRONTEND_BASE_URL=' "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2- || echo "http://localhost:3000")
    backend_url=$(grep -E '^VITE_API_BASE_URL=' "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2- || echo "http://localhost:8000")

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║       Quiz-App started successfully!             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BLUE}Frontend:${NC}   ${frontend_url}"
    echo -e "  ${BLUE}Backend:${NC}    ${backend_url}"
    echo -e "  ${BLUE}API-Docs:${NC}   ${backend_url}/docs"
    echo ""
    echo -e "${YELLOW}Check status:${NC}"
    echo "  cd quiz-app && docker compose ps"
    echo "  curl ${backend_url}/health"
    echo ""
}

# -------------------------------------------------------
# Main
# -------------------------------------------------------
main() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Quiz-App Installation Script             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""

    install_docker
    install_git
    clone_repo
    ask_for_env
    copy_env
    start_services
    print_success
}

main "$@"
