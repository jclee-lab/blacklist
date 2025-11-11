#!/bin/bash
set -e

echo "📦 Downloading VSCode Extensions for Offline Installation"
echo "=========================================================="
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
if [ ! -f ".vscode/extensions.json" ]; then
    print_error "Please run this script from the project root directory"
    print_error ".vscode/extensions.json not found"
    exit 1
fi

# VSCode CLI is optional - we'll download directly from marketplace

# Check if jq is available
if ! command -v jq &> /dev/null; then
    print_error "jq not found"
    print_error "Please install jq: sudo dnf install jq"
    exit 1
fi

# Create extensions directory
EXTENSIONS_DIR=".vscode/extensions"
mkdir -p "$EXTENSIONS_DIR"
print_status "Extensions directory created: $EXTENSIONS_DIR"

echo ""
echo "📦 Step 1: Reading extensions.json..."

# Extract extension IDs
extensions=$(jq -r '.recommendations[]' .vscode/extensions.json)
total=$(echo "$extensions" | wc -l)

print_status "Found $total extensions to download"

echo ""
echo "📦 Step 2: Downloading .vsix files from VS Code Marketplace..."

count=0
success=0
failed=0

for ext in $extensions; do
    count=$((count + 1))
    echo ""
    echo "[$count/$total] Processing: $ext"

    # Parse publisher and extension name
    publisher=$(echo "$ext" | cut -d'.' -f1)
    extension=$(echo "$ext" | cut -d'.' -f2)

    echo "   → Fetching latest version from Marketplace..."

    # Query Marketplace API for latest version
    api_response=$(curl -s -X POST \
        'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery' \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json;api-version=7.2-preview.1' \
        -d "{
            \"filters\": [{
                \"criteria\": [{
                    \"filterType\": 7,
                    \"value\": \"$ext\"
                }]
            }],
            \"flags\": 914
        }")

    # Extract version using jq
    version=$(echo "$api_response" | jq -r '.results[0].extensions[0].versions[0].version' 2>/dev/null)

    if [ -n "$version" ] && [ "$version" != "null" ]; then
        echo "   → Latest version: $version"
        echo "   → Downloading .vsix file..."

        # Download from VS Code marketplace
        vsix_url="https://${publisher}.gallery.vsassets.io/_apis/public/gallery/publisher/${publisher}/extension/${extension}/${version}/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage"

        output_file="$EXTENSIONS_DIR/${ext}-${version}.vsix"

        if curl -L -f -o "$output_file" "$vsix_url" 2>/dev/null; then
            size=$(du -h "$output_file" | cut -f1)
            print_status "   ✓ Downloaded: ${ext}-${version}.vsix ($size)"
            success=$((success + 1))
        else
            print_error "   ✗ Failed to download .vsix"
            failed=$((failed + 1))
        fi
    else
        print_error "   ✗ Failed to fetch version info from Marketplace"
        failed=$((failed + 1))
    fi
done

echo ""
echo "=========================================================="
echo "📊 Download Summary"
echo "=========================================================="
echo "Total extensions:     $total"
echo "Successfully downloaded: $success"
echo "Failed:               $failed"
echo ""

if [ $success -gt 0 ]; then
    echo "📂 Extensions saved to: $EXTENSIONS_DIR"
    echo ""
    echo "File list:"
    # shellcheck disable=SC2012
    ls -lh "$EXTENSIONS_DIR"/*.vsix 2>/dev/null | awk '{printf "   %s  %s\n", $5, $9}'
    echo ""

    total_size=$(du -sh "$EXTENSIONS_DIR" | cut -f1)
    print_status "Total size: $total_size"
fi

echo ""
if [ $failed -gt 0 ]; then
    print_warning "Some extensions failed to download"
    print_warning "You may need to download them manually or install online"
else
    print_status "All extensions downloaded successfully!"
fi

echo ""
echo "=========================================================="
echo "📦 Next Steps:"
echo "=========================================================="
echo "1. Commit .vsix files to Git:"
echo "   git add .vscode/extensions/*.vsix"
echo "   git commit -m 'feat: Add offline VSCode extensions'"
echo ""
echo "2. On offline server, install extensions:"
echo "   cd .vscode/extensions"
echo "   for ext in *.vsix; do code --install-extension \$ext; done"
echo ""
