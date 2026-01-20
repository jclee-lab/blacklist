# GitHub/Gitea Actions Workflows

## 📋 Available Workflows

### 1. `offline-package-build.yml` (NEW)

**Purpose**: Automatically create offline package on push

**Triggers**:
- Push to `main` or `release/**` branches
- Tag creation (`v*`)
- Manual dispatch

**What it does**:
1. ✅ Builds all Docker images from Dockerfiles
2. ✅ Creates offline package (blacklist.tar.gz + install.sh)
3. ✅ Verifies package integrity (checksum)
4. ✅ Uploads artifacts (90-day retention)
5. ✅ Creates GitHub/Gitea release (if tagged)

**Artifacts**:
- `blacklist.tar.gz` (~800MB)
- `blacklist.tar.gz.sha256` (checksum)
- `install.sh` (~20KB)

**Usage**:
```bash
# Automatic trigger
git push origin main                    # Build on push
git tag v3.3.9 && git push origin v3.3.9  # Build + Release

# Manual trigger
# Go to Actions tab → Select workflow → Run workflow
```

---

### 2. `docker-build-portainer-deploy.yml`

**Purpose**: Build Docker images and deploy to Portainer

**Status**: Existing workflow

---

### 3. `xwiki-auto-sync.yml`

**Purpose**: Sync documentation to XWiki

**Status**: Existing workflow

---

### 4. `cloudflare-workers-deploy.yml`

**Purpose**: Deploy to Cloudflare Workers

**Status**: Existing workflow

---

## 🔧 Gitea-Specific Configuration

### Gitea Actions Support

Gitea Actions is compatible with GitHub Actions syntax. Use `.github/workflows/` directory.

### Required Secrets (Gitea Settings)

Navigate to: **Repository Settings → Secrets → Actions**

Add these secrets:
```
GITEA_TOKEN           # For releases (auto-provided by Gitea)
DOCKER_USERNAME       # (if pushing to registry)
DOCKER_PASSWORD       # (if pushing to registry)
```

### Gitea Runner Setup

```bash
# Install Gitea Runner (on build server)
wget -O act_runner https://dl.gitea.com/act_runner/0.2.6/act_runner-0.2.6-linux-amd64
chmod +x act_runner

# Register runner
./act_runner register \
  --instance https://git.jclee.me \
  --token <RUNNER_TOKEN>

# Run as daemon
./act_runner daemon
```

### Enable Gitea Actions

Repository Settings → Actions → Enable Repository Actions

---

## 🧪 Testing Workflow Locally

Use `act` to test workflows locally:

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflow locally
act push -W .github/workflows/offline-package-build.yml

# Run with secrets
act push --secret-file .secrets
```

---

## 📊 Build Status

Check build status at:
- **Gitea**: https://git.jclee.me/gitadmin/blacklist/actions
- **GitHub**: (if mirrored) https://github.com/user/blacklist/actions

---

## 🐛 Troubleshooting

### Build fails with "No space left on device"

**Solution**: Clean up runner cache
```bash
docker system prune -af --volumes
```

### Artifacts not uploading

**Gitea**: Check Actions → Storage → Artifacts quota

### Release creation fails

**Check**: `GITEA_TOKEN` secret exists and has correct permissions

---

## 📚 References

- [Gitea Actions Documentation](https://docs.gitea.com/next/usage/actions/overview)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [act - Local testing tool](https://github.com/nektos/act)

---

**Last Updated**: 2025-10-30
**Workflow Version**: 1.0.0
