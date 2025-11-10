#!/bin/bash
# Setup GitLab CI/CD Variables and SSH Keys
# Usage: ./scripts/setup-gitlab-cicd.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
DEPLOY_HOST="${DEPLOY_HOST:-192.168.50.100}"
DEPLOY_USER="${DEPLOY_USER:-jclee}"
SSH_KEY_DIR="${HOME}/.ssh/gitlab-ci-blacklist"

echo ""
log_info "═══════════════════════════════════════════════"
log_info "  GitLab CI/CD AutoDevOps Setup"
log_info "═══════════════════════════════════════════════"
echo ""

# Step 1: Generate SSH Key Pair
log_info "Step 1: Generating SSH key pair for GitLab CI/CD..."

if [ -f "${SSH_KEY_DIR}" ]; then
    log_warning "SSH key already exists at ${SSH_KEY_DIR}"
    read -r -p "Regenerate? (y/N): " regenerate
    if [[ ! $regenerate =~ ^[Yy]$ ]]; then
        log_info "Using existing SSH key"
    else
        rm -f "${SSH_KEY_DIR}" "${SSH_KEY_DIR}.pub"
        ssh-keygen -t ed25519 -C "gitlab-ci@blacklist" -f "${SSH_KEY_DIR}" -N ""
        log_success "New SSH key generated"
    fi
else
    ssh-keygen -t ed25519 -C "gitlab-ci@blacklist" -f "${SSH_KEY_DIR}" -N ""
    log_success "SSH key generated at ${SSH_KEY_DIR}"
fi

# Step 2: Install Public Key on Deployment Server
log_info ""
log_info "Step 2: Installing public key on deployment server..."
log_info "Target: ${DEPLOY_USER}@${DEPLOY_HOST}"

read -r -p "Install public key on server? (Y/n): " install_key
if [[ ! $install_key =~ ^[Nn]$ ]]; then
    if ssh-copy-id -i "${SSH_KEY_DIR}.pub" "${DEPLOY_USER}@${DEPLOY_HOST}"; then
        log_success "Public key installed on ${DEPLOY_HOST}"
    else
        log_error "Failed to install public key. Manual installation required:"
        log_info "  ssh ${DEPLOY_USER}@${DEPLOY_HOST}"
        log_info "  mkdir -p ~/.ssh && chmod 700 ~/.ssh"
        log_info "  cat >> ~/.ssh/authorized_keys"
        log_info "  # Paste this key:"
        cat "${SSH_KEY_DIR}.pub"
        log_info "  # Then: chmod 600 ~/.ssh/authorized_keys"
        echo ""
        read -r -p "Press Enter after manual installation..."
    fi
fi

# Step 3: Get SSH Known Hosts
log_info ""
log_info "Step 3: Getting SSH known hosts..."

KNOWN_HOSTS_FILE="/tmp/gitlab-ci-known-hosts-$(date +%s)"
if ssh-keyscan -H "${DEPLOY_HOST}" > "${KNOWN_HOSTS_FILE}"; then
    log_success "Known hosts retrieved"
else
    log_error "Failed to get known hosts. Manual retrieval required:"
    log_info "  ssh-keyscan -H ${DEPLOY_HOST} > known_hosts"
fi

# Step 4: Test SSH Connection
log_info ""
log_info "Step 4: Testing SSH connection..."

if ssh -i "${SSH_KEY_DIR}" -o UserKnownHostsFile="${KNOWN_HOSTS_FILE}" "${DEPLOY_USER}@${DEPLOY_HOST}" "echo 'SSH connection successful'"; then
    log_success "SSH connection test passed"
else
    log_error "SSH connection failed. Please verify:"
    log_info "  1. Public key is installed on server"
    log_info "  2. SSH service is running on server"
    log_info "  3. Firewall allows SSH connections"
    exit 1
fi

# Step 5: Generate Secrets
log_info ""
log_info "Step 5: Generating application secrets..."

POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
FLASK_SECRET_KEY=$(openssl rand -hex 32)

log_success "Secrets generated"

# Step 6: Display GitLab CI/CD Variables
echo ""
log_info "═══════════════════════════════════════════════"
log_info "  GitLab CI/CD Variables Configuration"
log_info "═══════════════════════════════════════════════"
echo ""
log_info "Go to: https://gitlab.jclee.me/jclee/blacklist/-/settings/ci_cd"
log_info "Navigate to: Settings → CI/CD → Variables → Expand → Add Variable"
echo ""

cat <<EOF
${BLUE}1. SSH_PRIVATE_KEY${NC}
   Type: File
   Protected: ✅
   Masked: ✅
   File path: ${SSH_KEY_DIR}
   (Upload this file in GitLab UI)

${BLUE}2. SSH_KNOWN_HOSTS${NC}
   Type: Variable
   Protected: ✅
   Masked: ❌
   Value:
$(cat "${KNOWN_HOSTS_FILE}")

${BLUE}3. DEPLOY_HOST${NC}
   Type: Variable
   Protected: ✅
   Masked: ❌
   Value: ${DEPLOY_HOST}

${BLUE}4. DEPLOY_USER${NC}
   Type: Variable
   Protected: ✅
   Masked: ❌
   Value: ${DEPLOY_USER}

${BLUE}5. POSTGRES_PASSWORD${NC}
   Type: Variable
   Protected: ✅
   Masked: ✅
   Value: ${POSTGRES_PASSWORD}

${BLUE}6. FLASK_SECRET_KEY${NC}
   Type: Variable
   Protected: ✅
   Masked: ✅
   Value: ${FLASK_SECRET_KEY}

${BLUE}7. GITLAB_API_TOKEN${NC}
   Type: Variable
   Protected: ✅
   Masked: ✅
   Value: (Generate at https://gitlab.jclee.me/-/profile/personal_access_tokens)
   Scopes: api, read_registry, write_registry

${YELLOW}Application Credentials (Add from your existing secrets):${NC}
${BLUE}8. REGTECH_ID${NC}
   Type: Variable
   Protected: ✅
   Masked: ✅

${BLUE}9. REGTECH_PW${NC}
   Type: Variable
   Protected: ✅
   Masked: ✅

${BLUE}10. SECUDIUM_ID${NC}
   Type: Variable
   Protected: ✅
   Masked: ❌

${BLUE}11. SECUDIUM_PW${NC}
   Type: Variable
   Protected: ✅
   Masked: ✅

EOF

# Step 7: Save Configuration Summary
log_info ""
log_info "Step 7: Saving configuration summary..."

CONFIG_SUMMARY="/tmp/gitlab-cicd-setup-$(date +%Y%m%d-%H%M%S).txt"

cat > "${CONFIG_SUMMARY}" <<EOF
GitLab CI/CD Setup Summary
Generated: $(date)

SSH Configuration:
- Private Key: ${SSH_KEY_DIR}
- Public Key: ${SSH_KEY_DIR}.pub
- Known Hosts: ${KNOWN_HOSTS_FILE}
- Deploy Host: ${DEPLOY_HOST}
- Deploy User: ${DEPLOY_USER}

Generated Secrets:
- POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
- FLASK_SECRET_KEY: ${FLASK_SECRET_KEY}

GitLab CI/CD Variables URL:
https://gitlab.jclee.me/jclee/blacklist/-/settings/ci_cd

Next Steps:
1. Add all variables to GitLab CI/CD settings (see output above)
2. Prepare deployment server: /opt/blacklist directory
3. Push to main branch to trigger pipeline
4. Monitor pipeline: https://gitlab.jclee.me/jclee/blacklist/-/pipelines

Files to keep secure:
- ${SSH_KEY_DIR} (private key)
- ${CONFIG_SUMMARY} (this file)

Cleanup old keys after rotation:
- rm ${SSH_KEY_DIR}*
- Remove old keys from server: ~/.ssh/authorized_keys
EOF

log_success "Configuration saved to ${CONFIG_SUMMARY}"

# Step 8: Prepare Deployment Server
echo ""
log_info "═══════════════════════════════════════════════"
log_info "  Deployment Server Setup"
log_info "═══════════════════════════════════════════════"
echo ""

read -r -p "Setup deployment server now? (Y/n): " setup_server
if [[ ! $setup_server =~ ^[Nn]$ ]]; then
    log_info "Preparing deployment server at ${DEPLOY_HOST}..."

    ssh -i "${SSH_KEY_DIR}" "${DEPLOY_USER}@${DEPLOY_HOST}" bash <<'SERVER_SETUP_EOF'
# Create deployment directory
sudo mkdir -p /opt/blacklist
sudo chown ${USER}:${USER} /opt/blacklist

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "[INSTALL] Installing Docker..."
    sudo dnf install -y docker docker-compose-plugin
    sudo systemctl enable --now docker
    sudo usermod -aG docker ${USER}
    echo "[OK] Docker installed (re-login required for group membership)"
else
    echo "[OK] Docker already installed"
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose plugin not found"
    exit 1
else
    echo "[OK] Docker Compose available"
fi

echo "[OK] Server preparation completed"
SERVER_SETUP_EOF

    log_success "Deployment server prepared"

    # Copy docker-compose.prod.yml
    log_info "Copying docker-compose.prod.yml to server..."
    scp -i "${SSH_KEY_DIR}" docker-compose.prod.yml "${DEPLOY_USER}@${DEPLOY_HOST}:/opt/blacklist/"
    scp -i "${SSH_KEY_DIR}" -r postgres/migrations "${DEPLOY_USER}@${DEPLOY_HOST}:/opt/blacklist/postgres/"

    # Create .env file
    log_info "Creating .env file on server..."
    ssh -i "${SSH_KEY_DIR}" "${DEPLOY_USER}@${DEPLOY_HOST}" bash <<SERVER_ENV_EOF
cat > /opt/blacklist/.env <<EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
FLASK_SECRET_KEY=${FLASK_SECRET_KEY}

# TODO: Add your REGTECH/SECUDIUM credentials
# REGTECH_ID=
# REGTECH_PW=
# SECUDIUM_ID=
# SECUDIUM_PW=
EOF
chmod 600 /opt/blacklist/.env
echo "[OK] .env file created (remember to add REGTECH/SECUDIUM credentials)"
SERVER_ENV_EOF

    log_success "Deployment server setup completed"
fi

# Final Summary
echo ""
log_info "═══════════════════════════════════════════════"
log_success "  Setup Completed Successfully!"
log_info "═══════════════════════════════════════════════"
echo ""

cat <<EOF
${GREEN}✓${NC} SSH key pair generated and installed
${GREEN}✓${NC} Known hosts configured
${GREEN}✓${NC} SSH connection tested
${GREEN}✓${NC} Application secrets generated
${GREEN}✓${NC} Configuration summary saved

${BLUE}Next Steps:${NC}

1. Add CI/CD variables to GitLab:
   ${BLUE}https://gitlab.jclee.me/jclee/blacklist/-/settings/ci_cd${NC}

2. Review configuration summary:
   ${BLUE}cat ${CONFIG_SUMMARY}${NC}

3. Generate GitLab API token:
   ${BLUE}https://gitlab.jclee.me/-/profile/personal_access_tokens${NC}
   Scopes: api, read_registry, write_registry

4. Add REGTECH/SECUDIUM credentials to server .env:
   ${BLUE}ssh ${DEPLOY_USER}@${DEPLOY_HOST}${NC}
   ${BLUE}vim /opt/blacklist/.env${NC}

5. Test pipeline:
   ${BLUE}git push origin main${NC}
   ${BLUE}https://gitlab.jclee.me/jclee/blacklist/-/pipelines${NC}

${YELLOW}Security Reminders:${NC}
- Keep ${SSH_KEY_DIR} secure (chmod 600)
- Delete ${CONFIG_SUMMARY} after setup
- Rotate SSH keys quarterly
- Never commit secrets to repository

${GREEN}Documentation:${NC}
- Full guide: docs/GITLAB-CICD-AUTODEVOPS.md
- Quick reference: README.md
EOF

echo ""
log_info "═══════════════════════════════════════════════"
echo ""
