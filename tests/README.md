# Test Suite Documentation

Comprehensive test suite for the Blacklist IP Management System with 80% code coverage target.

## Quick Start

```bash
# Run all tests with coverage
./scripts/run-tests.sh

# Run specific category
./scripts/run-tests.sh security
./scripts/run-tests.sh cache
./scripts/run-tests.sh unit
```

## Test Categories

### Security Tests (`tests/security/`)
- SQL Injection Prevention
- CSRF Protection  
- Rate Limiting
- Input Validation
- Security Headers

### Cache Tests (`tests/unit/test_redis_cache.py`)
- Redis caching (5min TTL)
- Cache hit/miss behavior
- Graceful degradation

### Unit Tests (`tests/unit/`)
- Whitelist priority
- Blacklist logic
- Health checks

### Integration Tests (`tests/integration/`)
- API endpoints
- Error handling
- Response formats

## Coverage Report

View HTML coverage report after running tests:
```bash
./scripts/run-tests.sh coverage
open htmlcov/index.html
```

**Target**: 80% code coverage

For detailed documentation, see full README in this directory.
