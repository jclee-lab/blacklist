# TESTS KNOWLEDGE BASE

**Generated:** 2026-02-01
**Role:** Test Infrastructure & Patterns
**Parent:** [../AGENTS.md](../AGENTS.md)

---

## OVERVIEW

Multi-layer testing: Backend (pytest) + Frontend (Vitest/Playwright).
**Coverage target**: 80% on `app/core/`.

---

## STRUCTURE

```
tests/
├── unit/                   # Fast isolated tests
│   ├── app/                # Backend unit tests
│   ├── collector/          # Collector unit tests
│   └── components/         # Frontend component tests (Vitest)
├── integration/            # Tests with real DB/Redis
│   ├── app/                # Backend integration
│   └── collector/          # Collector integration
├── e2e/                    # End-to-end (Playwright)
│   ├── homepage.spec.ts
│   ├── ip-management.spec.ts
│   ├── collection.spec.ts
│   ├── accessibility.spec.ts
│   ├── performance.spec.ts
│   └── visual-regression.spec.ts
└── test_config.py          # MOCK_CREDENTIALS, fixtures
```

---

## COMMANDS

```bash
# All tests
make test                    # Backend + Frontend

# Backend
make test-backend-unit       # Unit tests only
make test-backend-integration # With DB/Redis

# By marker (backend)
make test-security           # @pytest.mark.security
make test-db                 # @pytest.mark.db
make test-api                # @pytest.mark.api

# Single test (backend)
docker compose exec -T blacklist-app python -m pytest tests/unit -v -k "test_function_name"

# Frontend
make test-frontend           # Vitest unit tests
make test-frontend-e2e       # Playwright E2E

# Single test (frontend)
cd frontend && npm run test -- --testNamePattern="test name"

# E2E with UI
cd frontend && npx playwright test --ui
```

---

## MARKERS (Backend)

| Marker | Purpose | Example |
|--------|---------|---------|
| `@pytest.mark.unit` | Fast, no external deps | `test_validate_ip()` |
| `@pytest.mark.integration` | Requires DB/Redis | `test_create_blacklist()` |
| `@pytest.mark.security` | Auth/credential tests | `test_jwt_validation()` |
| `@pytest.mark.db` | Database operations | `test_migration()` |
| `@pytest.mark.api` | API endpoint tests | `test_get_blacklist()` |

---

## CONVENTIONS

| Convention | Description |
|------------|-------------|
| **File naming** | `test_*.py` (backend), `*.test.tsx` (frontend) |
| **Auth** | Use `MOCK_CREDENTIALS` from `test_config.py` |
| **Fixtures** | `app`, `client`, `db_service`, `redis_client` |
| **Assertions** | Use pytest assertions, not `assert` keyword |
| **Cleanup** | Tests must clean up created data |

---

## FIXTURES (Backend)

```python
# Access via pytest fixtures
def test_example(app, client, db_service, redis_client):
    # app: Flask application context
    # client: Test client for HTTP requests
    # db_service: Database service instance
    # redis_client: Redis connection
    response = client.get('/api/blacklist')
    assert response.status_code == 200
```

---

## E2E PATTERNS (Playwright)

```typescript
// tests/e2e/my-feature.spec.ts
import { test, expect } from '@playwright/test';

test.describe('My Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/my-feature');
  });

  test('should display list', async ({ page }) => {
    await expect(page.getByRole('heading')).toContainText('My Feature');
  });
});
```

---

## VISUAL REGRESSION

Snapshots stored in `e2e/visual-regression.spec.ts-snapshots/`.

```bash
# Update snapshots after intentional UI changes
cd frontend && npx playwright test --update-snapshots
```

---

## ANTI-PATTERNS

| ❌ Forbidden | ✅ Alternative | Reason |
|--------------|----------------|--------|
| Real credentials in tests | `MOCK_CREDENTIALS` | Security |
| `time.sleep()` in tests | `pytest.mark.timeout` | Flaky tests |
| Shared test state | Isolated fixtures | Test pollution |
| Skipping cleanup | `yield` fixtures | Data leaks |

---

## NOTES

- **No conftest.py** — Fixtures defined inline in test files
- **Visual snapshots** — Multi-browser (Chromium, Firefox, Mobile Chrome)
- **Coverage** — Run `make coverage` to generate HTML report
