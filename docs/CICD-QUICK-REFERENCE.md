# GitLab CI/CD Quick Reference

**Fast reference for common CI/CD operations**

---

## Pipeline Stages

```
validate → security → build → deploy → verify → cleanup
  (5s)      (2-5m)    (10-15m)  (2-3m)   (1-2m)   (manual)
```

---

## Quick Commands

### Trigger Pipeline

```bash
# Push to trigger automatic pipeline
git push origin main              # Production
git push origin develop           # Development

# Manual trigger via GitLab CLI
glab ci run --branch main
```

### View Pipeline Status

```bash
# GitLab UI
https://gitlab.jclee.me/jclee/blacklist/-/pipelines

# CLI
glab ci status
glab ci view
```

### Manual Deployment

```bash
# Via GitLab UI
# Pipelines → Select pipeline → Play button on deploy:production

# Via SSH (emergency)
ssh jclee@192.168.50.100
cd /opt/blacklist
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

## Required Variables

**Essential 7**:
1. `SSH_PRIVATE_KEY` (File, Protected, Masked)
2. `SSH_KNOWN_HOSTS` (Variable, Protected)
3. `DEPLOY_HOST` (Variable, Protected)
4. `DEPLOY_USER` (Variable, Protected)
5. `POSTGRES_PASSWORD` (Variable, Protected, Masked)
6. `FLASK_SECRET_KEY` (Variable, Protected, Masked)
7. `GITLAB_API_TOKEN` (Variable, Protected, Masked)

**Application Secrets**:
8. `REGTECH_ID`, `REGTECH_PW`
9. `SECUDIUM_ID`, `SECUDIUM_PW`

**Configure at**: https://gitlab.jclee.me/jclee/blacklist/-/settings/ci_cd

---

## Common Operations

### Rollback

```bash
# Via GitLab UI
# Pipelines → Find previous successful pipeline → Note commit SHA
# Current pipeline → Play rollback:production
# Set variable: ROLLBACK_COMMIT_SHA=<previous-commit-sha>
```

### Registry Cleanup

```bash
# Manual trigger
# Pipelines → Run Pipeline → Manual Jobs → cleanup:registry

# Or schedule (weekly)
# CI/CD → Schedules → New Schedule
# Cron: "0 2 * * 0" (Sunday 2 AM)
```

### View Logs

```bash
# Production server logs
ssh jclee@192.168.50.100
cd /opt/blacklist
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose logs -f blacklist-app
```

---

## Health Checks

### Production

```bash
# Application health
curl https://blacklist.nxtd.co.kr/health

# API stats
curl https://blacklist.nxtd.co.kr/api/stats

# Metrics
curl https://blacklist.nxtd.co.kr/api/monitoring/metrics
```

### Development

```bash
curl https://blacklist.jclee.me/health
```

---

## Troubleshooting

### Pipeline Failed - SSH Connection

```bash
# Test SSH manually
ssh -i ~/.ssh/gitlab-ci-blacklist jclee@192.168.50.100

# Re-run setup script
./scripts/setup-gitlab-cicd.sh
```

### Pipeline Failed - Registry Login

```bash
# Login to registry on server
ssh jclee@192.168.50.100
docker login registry.jclee.me
```

### Pipeline Failed - Health Check

```bash
# Check service status on server
ssh jclee@192.168.50.100
cd /opt/blacklist
docker-compose ps
docker-compose logs blacklist-app
```

### Image Not Found

```bash
# Check registry
https://gitlab.jclee.me/jclee/blacklist/container_registry

# Manually pull
docker pull registry.jclee.me/jclee/blacklist/blacklist-app:latest
```

---

## Build Optimization

### Cache Strategy

```yaml
# Current: Single layer cache
--cache-from ${IMAGE_APP}:latest

# Future: Multi-stage cache
--cache-from ${IMAGE_APP}:cache-builder
--cache-from ${IMAGE_APP}:latest
```

### Parallel Builds

**Current**: 5 parallel builds (postgres, redis, collector, app, frontend)

**Duration**:
- Postgres: 2-3 min
- Redis: 1-2 min
- Collector: 3-4 min
- App: 4-5 min
- Frontend: 3-4 min

**Total**: ~10-15 min (parallel execution)

---

## Security Checklist

- [ ] All secrets in GitLab CI/CD variables (not code)
- [ ] Protected variables enabled for production
- [ ] SSH key rotated quarterly
- [ ] Registry login credentials secure
- [ ] .env file on server has 600 permissions
- [ ] Health checks passing before deployment completion

---

## URLs

| Environment | URL | Status |
|-------------|-----|--------|
| Production | https://blacklist.nxtd.co.kr | Deploy: main branch |
| Development | https://blacklist.jclee.me | Deploy: develop branch |
| GitLab CI/CD | https://gitlab.jclee.me/jclee/blacklist/-/pipelines | View pipelines |
| Container Registry | https://gitlab.jclee.me/jclee/blacklist/container_registry | View images |
| GitLab API Tokens | https://gitlab.jclee.me/-/profile/personal_access_tokens | Generate tokens |

---

## Emergency Contacts

**Pipeline Failures**: Check GitLab pipeline logs first
**Deployment Issues**: SSH to server and check container logs
**Registry Issues**: Verify GitLab Container Registry status
**Security Incidents**: Rotate secrets via GitLab CI/CD variables

---

**Full Documentation**: docs/GITLAB-CICD-AUTODEVOPS.md
**Setup Script**: ./scripts/setup-gitlab-cicd.sh
**Last Updated**: 2025-11-08
