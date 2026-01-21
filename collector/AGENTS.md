# COLLECTOR - IP Blacklist Collection Service

## OVERVIEW

Python service on port 8545. Fetches malicious IPs from external sources and stores in PostgreSQL.

## STRUCTURE

```
collector/
├── main.py              # Flask app, /api/force-collection/{source}
├── config.py            # CollectorConfig, credential loading
├── sources/             # Source adapters
│   ├── base.py          # BaseSource abstract class
│   ├── regtech.py       # REGTECH implementation
│   └── secudium.py      # SECUDIUM implementation
├── services/            # DB operations
└── Dockerfile           # Python 3.11
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new source | `sources/` - inherit `BaseSource` |
| Credential config | `config.py` → `collection_credentials` table |
| Collection logic | `sources/{source}.py` |
| Force-collect API | `main.py` |

## ADDING A SOURCE

```python
# sources/newsource.py
from .base import BaseSource

class NewSource(BaseSource):
    name = "NEWSOURCE"
    
    def __init__(self, config):
        self.api_url = config.NEWSOURCE_URL
        self.username = config.get_credential("NEWSOURCE", "username")
        self.password = config.get_credential("NEWSOURCE", "password")
    
    def collect(self) -> list[dict]:
        # Fetch from external API
        # Return list of {"ip": str, "source": str, "threat_type": str, ...}
        pass
```

## CREDENTIALS

Stored in `collection_credentials` table:

| Column | Type | Notes |
|--------|------|-------|
| source | varchar | `REGTECH`, `SECUDIUM`, etc. |
| username | varchar | |
| password | varchar | Plaintext or Fernet-encrypted |
| encrypted | boolean | If `true`, password is Fernet-encrypted |

**IMPORTANT**: App encrypts, Collector has different key. Store with `encrypted=false`.

## API

```
POST /api/force-collection/{source}
```

Triggers immediate collection from specified source. Returns collection stats.

## ANTI-PATTERNS

| Forbidden | Reason |
|-----------|--------|
| Hardcoded credentials | Use `collection_credentials` table |
| `encrypted=true` from App | Collector can't decrypt (key mismatch) |
| Direct psycopg2 in sources | Use services layer |

## NOTES

- Collection runs on schedule (cron in container) + on-demand via API
- Deduplication by IP + source
- `collection_stats` table tracks collection history
