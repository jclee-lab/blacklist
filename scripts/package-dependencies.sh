#!/bin/bash
set -e

echo "📦 Packaging Dependencies for Offline Installation"
echo "=================================================="
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

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create dist directory (clean start)
DIST_DIR="dist/dependencies"
if [ -d "$DIST_DIR" ]; then
    print_warning "Removing existing dependencies directory..."
    rm -rf "$DIST_DIR"
fi
mkdir -p "$DIST_DIR"
print_status "Clean dependencies directory created"

echo "📦 Step 1: Packaging Python dependencies..."
if [ -f "requirements.txt" ]; then
    print_status "Downloading Python packages..."
    
    # Create temp venv to ensure clean downloads
    python3 -m venv /tmp/blacklist-pkg-venv
    # shellcheck disable=SC1091
    source /tmp/blacklist-pkg-venv/bin/activate
    
    pip install --upgrade pip
    pip download -r requirements.txt -d "$DIST_DIR/python-packages"
    
    if [ -f "requirements-dev.txt" ]; then
        pip download -r requirements-dev.txt -d "$DIST_DIR/python-packages"
    fi
    
    deactivate
    rm -rf /tmp/blacklist-pkg-venv
    
    # Create requirements files
    cp requirements.txt "$DIST_DIR/requirements.txt"
    [ -f "requirements-dev.txt" ] && cp requirements-dev.txt "$DIST_DIR/requirements-dev.txt"
    
    print_status "Python packages downloaded: $(find "$DIST_DIR/python-packages" -type f | wc -l) files"
else
    print_warning "requirements.txt not found, skipping Python packages"
fi

echo ""
echo "📦 Step 2: Packaging Node.js dependencies (Frontend)..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    if command -v npm &> /dev/null; then
        print_status "Downloading Node.js packages..."
        
        cd frontend
        
        # Clean install to get fresh node_modules
        rm -rf node_modules package-lock.json
        npm install
        
        # Package node_modules
        tar -czf "../$DIST_DIR/frontend-node_modules.tar.gz" node_modules
        
        # Copy package files
        cp package.json package-lock.json "../$DIST_DIR/"
        
        cd ..
        
        print_status "Frontend packages packaged"
    else
        print_warning "npm not found, skipping frontend packages"
    fi
else
    print_warning "frontend/package.json not found, skipping frontend packages"
fi

echo ""
echo "📦 Step 3: Packaging VSCode settings..."
if [ -d ".vscode" ]; then
    print_status "Copying VSCode settings..."
    cp -r .vscode "$DIST_DIR/.vscode"
    print_status "VSCode settings packaged"
else
    print_warning ".vscode directory not found"
fi

echo ""
echo "📦 Step 4: Creating installation script for offline environment..."
cat > "$DIST_DIR/install-offline.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
set -e

echo "🚀 Installing Dependencies from Offline Packages"
echo "================================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the dist/dependencies directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the dist/dependencies directory"
    exit 1
fi

echo "📦 Installing Python dependencies..."
if command -v python3 &> /dev/null; then
    # Create/activate virtual environment
    if [ ! -d "../../.venv" ]; then
        cd ../..
        python3 -m venv .venv
        cd dist/dependencies
    fi
    
    # shellcheck disable=SC1091
    source ../../.venv/bin/activate
    
    # Install from local packages
    pip install --upgrade pip --no-index --find-links python-packages
    pip install --no-index --find-links python-packages -r requirements.txt
    
    if [ -f "requirements-dev.txt" ]; then
        pip install --no-index --find-links python-packages -r requirements-dev.txt
    fi
    
    deactivate
    print_status "Python dependencies installed"
else
    print_error "Python3 not found"
    exit 1
fi

echo ""
echo "📦 Installing Node.js dependencies..."
if [ -f "frontend-node_modules.tar.gz" ]; then
    if command -v npm &> /dev/null; then
        cd ../../frontend
        
        # Copy package files
        cp ../dist/dependencies/package.json .
        cp ../dist/dependencies/package-lock.json .
        
        # Extract node_modules
        tar -xzf ../dist/dependencies/frontend-node_modules.tar.gz
        
        cd ..
        print_status "Frontend dependencies installed"
    else
        echo "npm not found, skipping frontend installation"
    fi
fi

echo ""
echo "================================================"
echo -e "${GREEN}✅ Offline installation complete!${NC}"
INSTALL_SCRIPT

chmod +x "$DIST_DIR/install-offline.sh"
print_status "Offline installation script created"

echo ""
echo "📦 Step 4: Creating package archive..."
cd dist
ARCHIVE_NAME="blacklist-dependencies-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$ARCHIVE_NAME" dependencies/

ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
print_status "Archive created: $ARCHIVE_NAME ($ARCHIVE_SIZE)"

cd ..

echo ""
echo "================================================"
echo -e "${GREEN}✅ Dependency packaging complete!${NC}"
echo ""
echo "Package location: dist/$ARCHIVE_NAME"
echo ""
echo "To install on offline server:"
echo "  1. Transfer dist/$ARCHIVE_NAME to offline server"
echo "  2. Extract: tar -xzf $ARCHIVE_NAME"
echo "  3. cd dependencies"
echo "  4. ./install-offline.sh"
echo ""
