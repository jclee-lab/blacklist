# Blacklist Air-Gap Bundle Downloader (PowerShell)
# Downloads the latest release from GitHub via jump3 (for air-gapped networks)
#
# Usage: .\download.ps1
#
# Prerequisites:
#   - SSH access to jump3 configured
#   - jump3 has internet access to GitHub

$OWNER = "jclee-homelab"
$REPO = "blacklist"
$JUMP_HOST = "jump3"

Write-Host "Fetching latest release via $JUMP_HOST..." -ForegroundColor Cyan

# Get latest tag from GitHub API via jump3 (no jq required)
$TAG = ssh $JUMP_HOST "curl -s 'https://api.github.com/repos/$OWNER/$REPO/releases/latest' | grep 'tag_name' | sed -E 's/.*`"([^`"]+)`".*/\1/'"
$TAG = $TAG.Trim()

if (-not $TAG -or $TAG -eq "null") {
    Write-Host "Error: Failed to get latest release tag" -ForegroundColor Red
    exit 1
}

Write-Host "Latest version: $TAG" -ForegroundColor Green

$filename = "blacklist-$TAG-airgap.tar.gz"
$url = "https://github.com/$OWNER/$REPO/releases/download/$TAG/$filename"

Write-Host "Downloading $filename via $JUMP_HOST..." -ForegroundColor Cyan

# Download on jump3, then scp to local
ssh $JUMP_HOST "cd /tmp && curl -sL '$url' -o '$filename'"
scp "${JUMP_HOST}:/tmp/$filename" .

# Cleanup remote file
ssh $JUMP_HOST "rm -f /tmp/$filename"

Write-Host "Done! Downloaded: $filename" -ForegroundColor Green
Write-Host ""
Write-Host "Next: tar -xzf $filename && cd blacklist-$TAG && ./install.sh" -ForegroundColor Yellow
