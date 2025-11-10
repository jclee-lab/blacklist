#!/bin/bash
################################################################################
# Prepare Offline Package - Build images and package for Git LFS
################################################################################

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OFFLINE_DIR="${PROJECT_ROOT}/offline-packages"

echo "========================================="
echo "Prepare Offline Package"
echo "========================================="

# Create offline-packages directory
mkdir -p "${OFFLINE_DIR}"

# Step 1: Build all images
echo ""
echo "[1/3] Building Docker images..."
cd "${PROJECT_ROOT}"
make build

# Step 2: Package images
echo ""
echo "[2/3] Packaging images to offline-packages/..."
./scripts/package-all-sequential.sh

# Step 3: Move to offline-packages/
echo ""
echo "[3/3] Moving packages to offline-packages/..."
mv dist/images/*.tar.gz "${OFFLINE_DIR}/"

# Generate checksums
echo ""
echo "Generating checksums..."
cd "${OFFLINE_DIR}"
for file in *.tar.gz; do
    sha256sum "$file" > "$file.sha256"
    echo "✓ $file"
done

# Create load script
cat > "${OFFLINE_DIR}/load-images.sh" <<'EOF'
#!/bin/bash
# Load all Docker images from offline packages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Loading Docker images..."
echo "========================================="

for file in "${SCRIPT_DIR}"/*.tar.gz; do
    if [ -f "$file" ]; then
        echo ""
        echo "[LOAD] $(basename "$file")"
        gunzip -c "$file" | docker load
    fi
done

echo ""
echo "========================================="
echo "✓ All images loaded successfully"
echo "========================================="
docker images | grep blacklist
EOF

chmod +x "${OFFLINE_DIR}/load-images.sh"

echo ""
echo "========================================="
echo "✓ Offline package ready!"
echo "========================================="
echo ""
echo "Location: ${OFFLINE_DIR}"
echo ""
echo "Contents:"
ls -lh "${OFFLINE_DIR}"/*.tar.gz
echo ""
echo "Next steps:"
echo "  1. git add offline-packages/*.tar.gz"
echo "  2. git lfs track 'offline-packages/*.tar.gz'"
echo "  3. git commit -m 'Add offline packages'"
echo "  4. git push"
echo ""
