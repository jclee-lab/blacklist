# APP - Flask REST API

## OVERVIEW

Flask API service on port 2542. Blueprint-based routing with centralized error handling.

## STRUCTURE

```
app/
├── main.py              # Flask app factory, blueprint registration
├── extensions.py        # db_service, redis_client instances
├── core/
│   ├── routes/api/      # Blueprint routes (one dir per domain)
│   │   ├── blacklist/   # IP list, stats, export
│   │   ├── collection/  # Sources, credentials, force-collect
│   │   ├── database/    # Table browser
│   │   ├── fortinet/    # FortiGate device management
│   │   ├── ip_management/  # Manual IP CRUD
│   │   └── settings/    # System config
│   ├── services/        # Business logic (db_service, etc.)
│   └── exceptions.py    # ValidationError, BadRequestError, DatabaseError
└── Dockerfile           # Python 3.11, gunicorn
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add endpoint | `core/routes/api/{domain}/` |
| DB queries | `core/services/db_service.py` |
| Error types | `core/exceptions.py` |
| Rate limiting | Decorator in route files |
| App config | `main.py`, env vars |

## CONVENTIONS

```python
# Route pattern
from flask import Blueprint, request, jsonify
from app.extensions import db_service
from app.core.exceptions import ValidationError, BadRequestError

bp = Blueprint('domain', __name__, url_prefix='/api/domain')

@bp.route('/endpoint', methods=['GET'])
@rate_limit(limit=100, window=60)
def get_endpoint():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 1000)
    # ...
    return jsonify(result)
```

## ANTI-PATTERNS

| Forbidden | Do Instead |
|-----------|------------|
| `psycopg2.connect()` in routes | Use `db_service.query()` |
| `return {"error": msg}, 500` | Raise `DatabaseError(table="...")` |
| `@bp.route` without rate_limit | Always add `@rate_limit` decorator |
| Pagination >1000 | Validate `per_page` max 1000 |

## ERROR HANDLING

```python
# Exception classes auto-convert to JSON responses
raise ValidationError(field="page", message="must be positive")  # 400
raise BadRequestError(message="invalid request")                 # 400
raise DatabaseError(table="blacklist_ips")                       # 500
```

## NOTES

- All routes return JSON (no HTML)
- `db_service` handles connection pooling
- Redis used for rate limiting state
