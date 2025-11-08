# GitLab CI/CD Setup Guide

## Overview

This guide walks you through setting up GitLab CI/CD for automated Docker builds and Portainer deployments using GitLab Container Registry.

**Pipeline Features**:
- Security scanning (Python + JavaScript dependencies)
- Parallel Docker image builds (5 components)
- GitLab Container Registry integration
- Portainer webhook deployment
- Health checks and verification

---

## Prerequisites

1. **GitLab Repository**: https://gitlab.jclee.me/jclee/blacklist
2. **GitLab Container Registry**: Enabled (auto-configured)
3. **Portainer**: Running with webhook configured
4. **Production Environment**: Accessible via URL

---

## Step 1: Configure GitLab CI/CD Variables

### Required Variables

Go to **GitLab > Settings > CI/CD > Variables** and add the following:

| Variable Name | Value | Protected | Masked |
|---------------|-------|-----------|--------|
| `PORTAINER_WEBHOOK_URL` | `https://portainer.jclee.me/api/stacks/webhooks/YOUR_WEBHOOK_ID` | ✅ | ✅ |
| `PRD_URL` | `https://blacklist.jclee.me` (or `https://blacklist.nxtd.co.kr`) | ✅ | ❌ |

**How to get Portainer Webhook URL**:
1. Go to Portainer > Stacks > Your Stack
2. Click "Webhook" icon
3. Copy the webhook URL
4. Example: `https://portainer.jclee.me/api/stacks/webhooks/d05ec9bc-d49b-4b1f-9d01-7377f36abd2c`

### Auto-Configured Variables (No Action Required)

GitLab automatically provides these variables:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CI_REGISTRY` | GitLab Container Registry URL | `registry.jclee.me` |
| `CI_REGISTRY_USER` | Registry username | `gitlab-ci-token` |
| `CI_REGISTRY_PASSWORD` | Registry password | `$CI_JOB_TOKEN` |
| `CI_REGISTRY_IMAGE` | Full image path | `registry.jclee.me/jclee/blacklist` |
| `CI_COMMIT_SHA` | Commit hash | `abc123...` |
| `CI_COMMIT_BRANCH` | Branch name | `main` or `master` |

---

## Step 2: Enable GitLab Container Registry

GitLab Container Registry is **automatically enabled** for all projects.

**Verify it's enabled**:
1. Go to GitLab > Packages & Registries > Container Registry
2. You should see: `registry.jclee.me/jclee/blacklist`

**Container Images After Build**:
```
registry.jclee.me/jclee/blacklist/blacklist-postgres:latest
registry.jclee.me/jclee/blacklist/blacklist-redis:latest
registry.jclee.me/jclee/blacklist/blacklist-collector:latest
registry.jclee.me/jclee/blacklist/blacklist-app:latest
registry.jclee.me/jclee/blacklist/blacklist-frontend:latest
```

---

## Step 3: Verify Pipeline Configuration

The `.gitlab-ci.yml` file is already configured with:

### Pipeline Stages

1. **security** - Dependency scanning and tests
   - Python dependencies (safety)
   - JavaScript dependencies (npm audit)
   - Pytest test suite with coverage

2. **build** - Parallel Docker image builds
   - 5 components built simultaneously
   - Push to GitLab Container Registry
   - Tags: `latest` and `{commit-sha-8}`

3. **deploy** - Portainer webhook deployment
   - Automatic deployment trigger
   - 3 retry attempts
   - Waits for successful deployment

4. **verify** - Health checks
   - Production endpoint verification
   - API functionality check
   - Auto-rollback on failure

### Trigger Conditions

**Automatic Triggers**:
- Push to `main` or `master` branch
- Changes in: `app/`, `collector/`, `postgres/`, `redis/`, `frontend/`, `Dockerfile*`, `docker-compose.yml`
- Merge request events

**Manual Trigger**:
- Go to GitLab > CI/CD > Pipelines
- Click "Run pipeline"
- Select branch and run

---

## Step 4: Test the Pipeline

### Method 1: Push to Main Branch

```bash
# Make a small change
echo "# Test GitLab CI/CD" >> README.md

# Commit and push
git add .
git commit -m "test: Verify GitLab CI/CD pipeline"
git push origin main
```

### Method 2: Manual Pipeline Run

1. Go to **GitLab > CI/CD > Pipelines**
2. Click **"Run pipeline"**
3. Select branch: `main`
4. Click **"Run pipeline"**

### Monitor Pipeline Progress

1. Go to **GitLab > CI/CD > Pipelines**
2. Click on the running pipeline
3. View each stage:
   - ✅ Security (3 jobs: python-scan, javascript-scan, run-tests)
   - ✅ Build (5 jobs: postgres, redis, collector, app, frontend)
   - ✅ Deploy (1 job: portainer-webhook)
   - ✅ Verify (1 job: health-check)

**Expected Timeline**:
- Security: 2-3 minutes
- Build (parallel): 5-7 minutes
- Deploy: 1-2 minutes
- Verify: 2-3 minutes
- **Total**: 10-15 minutes

---

## Step 5: Verify Deployment

### Check Container Registry

```bash
# List images in GitLab Container Registry
curl -s --header "PRIVATE-TOKEN: YOUR_GITLAB_TOKEN" \
  "https://gitlab.jclee.me/api/v4/projects/jclee%2Fblacklist/registry/repositories" | jq
```

Or visit: **GitLab > Packages & Registries > Container Registry**

### Check Production Deployment

```bash
# Health check
curl https://blacklist.jclee.me/health

# Expected response
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "collector": "running"
  }
}

# API check
curl https://blacklist.jclee.me/api/stats

# Expected response
{
  "success": true,
  "data": {
    "total_ips": 12345,
    "blacklisted": 1234,
    "whitelisted": 56
  }
}
```

### View Logs

```bash
# GitLab CI/CD logs
# Go to: GitLab > CI/CD > Pipelines > Click on pipeline > Click on job

# Portainer logs
# Go to: Portainer > Containers > blacklist-app > Logs
```

---

## Troubleshooting

### Issue 1: "PORTAINER_WEBHOOK_URL not configured"

**Solution**:
1. Go to GitLab > Settings > CI/CD > Variables
2. Add variable: `PORTAINER_WEBHOOK_URL`
3. Value: `https://portainer.jclee.me/api/stacks/webhooks/YOUR_WEBHOOK_ID`
4. Check "Protected" and "Masked"
5. Save

### Issue 2: Docker build fails with "unauthorized"

**Solution**:
```bash
# Verify GitLab Container Registry is enabled
# Go to: GitLab > Settings > General > Visibility
# Ensure "Container Registry" is enabled
```

### Issue 3: Health check fails

**Possible causes**:
1. Containers not started yet (wait longer)
2. Wrong `PRD_URL` configured
3. Portainer deployment failed

**Debug**:
```bash
# Check Portainer container status
docker ps | grep blacklist

# Check application logs
docker logs blacklist-app

# Manual health check
curl -v https://blacklist.jclee.me/health
```

### Issue 4: Pipeline stuck in "pending"

**Solution**:
1. Check if GitLab Runner is available
2. Go to: GitLab > Settings > CI/CD > Runners
3. Ensure at least one runner is active
4. If using shared runners, ensure they're enabled

### Issue 5: Build stage takes too long

**Optimization**:
- Builds run in parallel (5 jobs simultaneously)
- Uses Docker layer caching
- Timeline should be 5-7 minutes

If slower:
1. Check runner resources (CPU/memory)
2. Verify network speed to registry
3. Review Docker build logs for bottlenecks

---

## Comparison: GitHub Actions vs GitLab CI/CD

| Feature | GitHub Actions | GitLab CI/CD |
|---------|----------------|--------------|
| **Registry** | `registry.jclee.me` | `registry.jclee.me` (GitLab Container Registry) |
| **Authentication** | Manual secrets | Auto (`CI_JOB_TOKEN`) |
| **Parallel Builds** | Matrix strategy | Native parallel jobs |
| **Security Scan** | safety + npm audit | safety + npm audit |
| **Deployment** | Portainer webhook | Portainer webhook |
| **Health Check** | Curl + retry | Curl + retry |
| **Cost** | GitHub-hosted runners | Self-hosted GitLab + runners |
| **Integration** | External | Native GitLab |

**Migration Benefits**:
- ✅ Tighter integration with GitLab
- ✅ Auto-configured registry auth
- ✅ Native parallel builds
- ✅ Built-in Container Registry UI
- ✅ No external secrets management

---

## Advanced Configuration

### Custom Docker Build Args

Edit `.gitlab-ci.yml` build jobs:

```yaml
build:app:
  script:
    - |
      docker build \
        --build-arg PYTHON_VERSION=3.11 \
        --build-arg APP_ENV=production \
        --tag ${IMAGE_APP}:${VERSION_TAG} \
        --file ./app/Dockerfile \
        ./app
```

### Environment-Specific Deployments

Add staging environment:

```yaml
deploy:portainer-webhook-staging:
  stage: deploy
  variables:
    PORTAINER_WEBHOOK_URL: "${PORTAINER_WEBHOOK_URL_STAGING}"
    PRD_URL: "https://blacklist-staging.jclee.me"
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
```

### Scheduled Pipelines

Create nightly security scans:

1. Go to **GitLab > CI/CD > Schedules**
2. Click **"New schedule"**
3. Description: "Nightly security scan"
4. Interval pattern: `0 2 * * *` (2 AM daily)
5. Target branch: `main`
6. Save

---

## Next Steps

### Disable GitHub Actions (Optional)

Since GitLab CI/CD is now primary:

```bash
# Rename GitHub Actions workflows to .bak
mv .github/workflows/docker-build-portainer-deploy.yml \
   .github/workflows/docker-build-portainer-deploy.yml.bak

# Or disable specific workflows in GitHub UI
# Go to: GitHub > Actions > Select workflow > Disable workflow
```

### Monitor CI/CD Performance

Track metrics:
- Pipeline duration (target: <15 minutes)
- Success rate (target: >95%)
- Security scan findings
- Test coverage (target: >80%)

### Set Up Notifications

Configure Slack/email notifications:

1. Go to **GitLab > Settings > Integrations**
2. Select notification service
3. Configure webhook URL
4. Test integration

---

## Resources

- **GitLab CI/CD Docs**: https://docs.gitlab.com/ee/ci/
- **Container Registry Docs**: https://docs.gitlab.com/ee/user/packages/container_registry/
- **Pipeline Configuration**: https://docs.gitlab.com/ee/ci/yaml/
- **Portainer Webhooks**: https://docs.portainer.io/user/docker/stacks/webhooks

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
**Maintainer**: jclee
