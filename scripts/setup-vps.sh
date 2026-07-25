#!/bin/bash
# =============================================================================
# ConnectXperts NMS - VPS Setup Script (run once on the server)
# =============================================================================
# This script prepares a fresh Ubuntu/Debian VPS for automated deployment.
# Run this ONCE on your VPS before the first GitHub Actions deployment.
#
# Usage:
#   ssh root@<your-vps-ip>
#   curl -fsSL https://raw.githubusercontent.com/<your-repo>/main/scripts/setup-vps.sh | bash
#   --- OR ---
#   Copy this file to the VPS and run:
#   chmod +x scripts/setup-vps.sh
#   ./scripts/setup-vps.sh
# =============================================================================

set -euo pipefail

DOMAIN="monitor.connectxperts.in"
DEPLOY_DIR="/var/www/cnms"
# REPO_URL: Set this to your GitHub repository URL BEFORE running the script.
# Example:
#   REPO_URL="git@github.com:your-org/cnms.git" ./scripts/setup-vps.sh
#   --- OR ---
#   export REPO_URL="git@github.com:your-org/cnms.git"
#   ./scripts/setup-vps.sh
REPO_URL="${REPO_URL:-}"

echo "========================================"
echo " ConnectXperts NMS - VPS Setup"
echo "========================================"

# ────────────────────────────────────────────
# 1. System Updates & Prerequisites
# ────────────────────────────────────────────
echo ""
echo "[1/6] Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y -qq \
    curl \
    git \
    ufw \
    fail2ban \
    unattended-upgrades
echo "  ✅ Done"

# ────────────────────────────────────────────
# 2. Install Docker
# ────────────────────────────────────────────
echo ""
echo "[2/6] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "  ✅ Docker installed"
else
    echo "  ⏩ Docker already installed"
fi

# Install Docker Compose v2
if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin
    echo "  ✅ Docker Compose installed"
else
    echo "  ⏩ Docker Compose already installed"
fi

echo "  Docker:    $(docker --version)"
echo "  Compose:   $(docker compose version)"

# ────────────────────────────────────────────
# 3. Create Deploy Directory
# ────────────────────────────────────────────
echo ""
echo "[3/6] Setting up deploy directory..."
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Clone repository (if not already cloned)
if [ ! -d "$DEPLOY_DIR/.git" ]; then
    if [ -z "$REPO_URL" ]; then
        echo ""
        echo "  ERROR: REPO_URL is not set!"
        echo "  Usage: REPO_URL='git@github.com:your-org/cnms.git' $0"
        echo ""
        exit 1
    fi
    git clone "$REPO_URL" .
fi
echo "  ✅ Project ready at $DEPLOY_DIR"

# ────────────────────────────────────────────
# 4. Create .env File
# ────────────────────────────────────────────
echo ""
echo "[4/6] Creating production .env file..."
if [ ! -f "$DEPLOY_DIR/backend/.env.production" ]; then
    cat > "$DEPLOY_DIR/backend/.env.production" << 'ENVEOF'
# ConnectXperts NMS - Production Environment
DEBUG=false
JWT_SECRET_KEY=change-me-to-a-random-secret
POSTGRES_PASSWORD=change-me-to-a-strong-password
REDIS_PASSWORD=change-me-to-a-strong-password
CORS_ORIGINS=https://monitor.connectxperts.in
ENVEOF
    echo ""
    echo "  ⚠️  EDIT THE .env FILE WITH REAL SECRETS:"
    echo "     nano $DEPLOY_DIR/backend/.env.production"
else
    echo "  ⏩ .env.production already exists"
fi

# ────────────────────────────────────────────
# 5. Configure Firewall
# ────────────────────────────────────────────
echo ""
echo "[5/6] Configuring firewall..."
# Reset to clean state, then add rules
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
echo "  ✅ Firewall active (SSH, HTTP, HTTPS only)"

# ────────────────────────────────────────────
# 6. Create SSH Deploy Key
# ────────────────────────────────────────────
echo ""
echo "[6/6] Setting up SSH deploy key..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "ci-deploy@$DOMAIN"
    echo ""
    echo "  ================================================"
    echo "  🔑 PUBLIC KEY FOR GITHUB DEPLOY KEY:"
    echo "  ================================================"
    cat ~/.ssh/id_ed25519.pub
    echo "  ================================================"
    echo ""
    echo "  Add this as a Deploy Key in your GitHub repo:"
    echo "  Settings → Security → Deploy Keys → Add deploy key"
    echo ""
    echo "  Allow write access: ✅ Yes"
    echo "  ================================================"

    # Add to authorized_keys for CI/CD
    cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys

    echo "  ✅ SSH deploy key created"
else
    echo "  ⏩ SSH key already exists"
fi

# ────────────────────────────────────────────
# Summary
# ────────────────────────────────────────────
echo ""
echo "========================================"
echo " ✅ VPS Setup Complete!"
echo "========================================"
echo ""
echo "  Next Steps:"
echo "  1. Edit: nano $DEPLOY_DIR/backend/.env.production"
echo "     - Change JWT_SECRET_KEY to a random 64-char hex string"
echo "     - Change POSTGRES_PASSWORD and REDIS_PASSWORD"
echo ""
echo "  2. Add these GitHub Secrets to your repository:"
echo "     Settings → Secrets and variables → Actions"
echo ""
echo "     Name: VPS_HOST"
echo "     Value: $(curl -s ifconfig.me 2>/dev/null || echo '<your-vps-ip>')"
echo ""
echo "     Name: VPS_USER"
echo "     Value: root"
echo ""
echo "     Name: VPS_SSH_KEY"
echo "     Value: (content of ~/.ssh/id_ed25519)"
echo ""
echo "     Name: VPS_KNOWN_HOST"
echo "     Value: (run 'ssh-keyscan <your-vps-ip>' locally)"
echo ""
echo "     Name: JWT_SECRET_KEY"
echo "     Value: (run 'python3 -c \"import secrets; print(secrets.token_hex(32))\"')"
echo ""
echo "     Name: POSTGRES_PASSWORD"
echo "     Value: (a strong random password)"
echo ""
echo "     Name: REDIS_PASSWORD"
echo "     Value: (a strong random password)"
echo ""
echo "  3. Push to main/master branch to trigger deployment:"
echo "     git push origin main"
echo ""
echo "  4. Visit: https://$DOMAIN"
echo ""
