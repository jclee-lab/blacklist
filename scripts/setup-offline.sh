#!/bin/bash
set -e

echo "🚀 Offline Development Environment Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check for offline packages
if [ ! -d "dist/dependencies" ]; then
    print_error "Offline dependencies not found!"
    echo ""
    echo "Please run one of the following:"
    echo "  1. On internet-connected server: ./scripts/package-dependencies.sh"
    echo "  2. Transfer dist/blacklist-dependencies-*.tar.gz to this server"
    echo "  3. Extract: tar -xzf blacklist-dependencies-*.tar.gz -C dist/"
    exit 1
fi

echo "📦 Installing from offline packages..."
cd dist/dependencies
./install-offline.sh
cd ../..

echo ""
echo "📦 Setting up Git hooks..."
if [ -d ".git" ]; then
    if [ -f "scripts/install-git-hooks.sh" ]; then
        bash scripts/install-git-hooks.sh
        print_status "Git hooks installed"
    fi
fi

echo ""
echo "📦 Creating required directories..."
mkdir -p dist/images backups logs
print_status "Directories created"

echo ""
echo "📦 Setting up environment file..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    print_status ".env file created"
    print_warning "Please edit .env file with your credentials"
else
    print_status ".env file already exists"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✅ Offline setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your credentials"
echo "  2. Run 'make dev' to start development environment"
echo ""
