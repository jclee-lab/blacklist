# Git LFS Setup Guide

This directory contains pre-built Docker images tracked by Git LFS for offline deployment.

## Initial Setup (Maintainer)

### 1. Install Git LFS

```bash
# Rocky Linux / RHEL / CentOS
sudo dnf install git-lfs

# Ubuntu / Debian
sudo apt-get install git-lfs

# macOS
brew install git-lfs

# Initialize Git LFS
git lfs install
```

### 2. Build and Package Images

```bash
# Build all images and create packages
./scripts/prepare-offline-package.sh
```

This will:
- Build all 5 Docker images
- Package them as .tar.gz files
- Generate SHA-256 checksums
- Place everything in `offline-packages/`

### 3. Track with Git LFS

```bash
# Track packages (already configured in .gitattributes)
git lfs track "offline-packages/*.tar.gz"

# Add packages
git add offline-packages/*.tar.gz
git add offline-packages/*.sha256
git add .gitattributes

# Commit
git commit -m "Add offline packages for air-gapped deployment"

# Push (Git LFS uploads automatically)
git push origin main
```

## End User (Clone Only)

### 1. Clone Repository

```bash
# Clone with LFS objects
git clone https://gitlab.jclee.me/jclee/blacklist.git
cd blacklist

# Verify LFS files downloaded
ls -lh offline-packages/*.tar.gz
```

### 2. Quick Start

```bash
# One-command deployment
chmod +x quick-start.sh
./quick-start.sh
```

This will:
- Load pre-built Docker images from `offline-packages/`
- Setup `.env` file
- Start all services
- Health check

## Verification

### Check Git LFS Status

```bash
# List tracked files
git lfs ls-files

# Check file status
git lfs status
```

### Verify Checksums

```bash
cd offline-packages
sha256sum -c *.sha256
```

## File Sizes (Compressed)

| Image | Size (Compressed) |
|-------|-------------------|
| blacklist-postgres | ~185 MB |
| blacklist-redis | ~28 MB |
| blacklist-collector | ~156 MB |
| blacklist-app | ~311 MB |
| blacklist-frontend | ~135 MB |
| **Total** | **~815 MB** |

Original uncompressed size: ~2.4 GB (66% reduction)

## Updating Images

```bash
# Rebuild images
make rebuild

# Repackage
./scripts/prepare-offline-package.sh

# Commit and push
git add offline-packages/*.tar.gz offline-packages/*.sha256
git commit -m "Update offline packages (version X.Y.Z)"
git push origin main
```

## Troubleshooting

### Issue: "This exceeds Git's file size limit of 100 MB"

**Solution**: Ensure Git LFS is installed and tracking configured.

```bash
git lfs install
git lfs track "offline-packages/*.tar.gz"
```

### Issue: Git LFS quota exceeded

**Solution**: Check GitLab LFS storage limits.

```bash
# Check quota
curl --header "PRIVATE-TOKEN: <your_token>" \
  "https://gitlab.jclee.me/api/v4/projects/<project_id>/statistics"
```

### Issue: Clone doesn't download LFS files

**Solution**: Explicitly fetch LFS objects.

```bash
git lfs fetch --all
git lfs checkout
```

## Best Practices

1. **Always generate checksums** after building
2. **Test load before committing** to ensure packages work
3. **Tag releases** for version tracking
4. **Document changes** in commit messages
5. **Clean old versions** periodically to save storage

## Alternative: Manual Transfer

If Git LFS is not available:

```bash
# On build server
./scripts/prepare-offline-package.sh
cd offline-packages
tar czf blacklist-offline-$(date +%Y%m%d).tar.gz *.tar.gz *.sha256

# Transfer via USB/SCP
scp blacklist-offline-*.tar.gz target-server:/opt/

# On target server
cd /opt/blacklist
tar xzf /opt/blacklist-offline-*.tar.gz
./offline-packages/load-images.sh
docker-compose up -d
```

---

**Last Updated**: 2025-11-10
**Version**: 3.4.1
