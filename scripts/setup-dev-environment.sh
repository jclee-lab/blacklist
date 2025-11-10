#!/bin/bash
set -e

echo "🚀 Blacklist Intelligence Platform - Development Environment Setup"
echo "=================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

echo "📦 Step 1: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    if command -v python3 &> /dev/null; then
        # Create virtual environment if not exists
        if [ ! -d ".venv" ]; then
            print_status "Creating Python virtual environment..."
            python3 -m venv .venv
        fi
        
        print_status "Activating virtual environment..."
        # shellcheck disable=SC1091
        source .venv/bin/activate
        
        print_status "Installing Python packages..."
        pip install --upgrade pip
        pip install -r requirements.txt
        
        if [ -f "requirements-dev.txt" ]; then
            print_status "Installing development dependencies..."
            pip install -r requirements-dev.txt
        fi
        
        print_status "Python dependencies installed"
    else
        print_warning "Python3 not found, skipping Python setup"
    fi
else
    print_warning "requirements.txt not found, skipping Python setup"
fi

echo ""
echo "📦 Step 2: Installing Node.js dependencies (Frontend)..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    if command -v npm &> /dev/null; then
        print_status "Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
        print_status "Frontend dependencies installed"
    else
        print_warning "npm not found, skipping frontend setup"
    fi
else
    print_warning "frontend/package.json not found, skipping frontend setup"
fi

echo ""
echo "📦 Step 3: Installing VSCode extensions..."
if command -v code &> /dev/null; then
    if [ -f ".vscode/extensions.json" ]; then
        print_status "Reading recommended extensions..."
        
        # Extract extension IDs from extensions.json
        extensions=$(grep -oP '"[^"]+\.[^"]+"' .vscode/extensions.json | tr -d '"')
        
        total=$(echo "$extensions" | wc -l)
        current=0
        
        for ext in $extensions; do
            current=$((current + 1))
            echo -ne "\r  Installing $current/$total: $ext..."
            code --install-extension "$ext" --force &> /dev/null || true
        done
        echo ""
        
        print_status "VSCode extensions installed"
    else
        print_warning ".vscode/extensions.json not found, skipping VSCode setup"
    fi
else
    print_warning "VSCode CLI not found, skipping extension installation"
    print_warning "Install VSCode extensions manually via: Ctrl+Shift+P → 'Extensions: Show Recommended Extensions'"
fi

echo ""
echo "📦 Step 4: Setting up Git hooks..."
if [ -d ".git" ]; then
    if [ -f "scripts/install-git-hooks.sh" ]; then
        print_status "Installing Git hooks..."
        bash scripts/install-git-hooks.sh
        print_status "Git hooks installed"
    else
        print_warning "Git hooks script not found, skipping"
    fi
else
    print_warning "Not a Git repository, skipping Git hooks"
fi

echo ""
echo "📦 Step 5: Creating required directories..."
mkdir -p dist/images
mkdir -p backups
mkdir -p logs
print_status "Directories created"

echo ""
echo "📦 Step 6: Copying environment template..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    print_status ".env file created from template"
    print_warning "Please edit .env file with your credentials"
else
    print_status ".env file already exists"
fi

echo ""
echo "=================================================================="
echo -e "${GREEN}✅ Development environment setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your credentials"
echo "  2. Run 'make dev' to start development environment"
echo "  3. Run 'make test' to verify setup"
echo ""
echo "VSCode users:"
echo "  - Press F5 to start debugging"
echo "  - Press Ctrl+Shift+B to run build task"
echo "  - Press Ctrl+Shift+P → 'Tasks: Run Task' for other tasks"
echo ""
