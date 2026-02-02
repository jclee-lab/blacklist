# Blacklist Air-Gap Bundle Downloader (PowerShell)
# Downloads the latest release from GitHub

$OWNER = "jclee-homelab"
$REPO = "blacklist"

Write-Host "Fetching latest release..." -ForegroundColor Cyan
$release = Invoke-RestMethod "https://api.github.com/repos/$OWNER/$REPO/releases/latest"
$TAG = $release.tag_name

Write-Host "Latest version: $TAG" -ForegroundColor Green

$filename = "blacklist-$TAG-airgap.tar.gz"
$url = "https://github.com/$OWNER/$REPO/releases/download/$TAG/$filename"

Write-Host "Downloading $filename..." -ForegroundColor Cyan
Invoke-WebRequest $url -OutFile $filename

Write-Host "Done! Downloaded: $filename" -ForegroundColor Green
