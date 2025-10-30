# Blacklist Management Platform - User Manual v2025.10.21

## Table of Contents
1. [Getting Started](#getting-started)
2. [Web Interface Overview](#web-interface-overview)
3. [Managing Blacklist IPs](#managing-blacklist-ips)
4. [Managing Whitelist IPs](#managing-whitelist-ips)
5. [Data Collection Management](#data-collection-management)
6. [Monitoring & Statistics](#monitoring--statistics)
7. [FortiGate Integration](#fortigate-integration)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Getting Started

### Accessing the System

**Web Interface:**
- **URL:** https://192.168.50.100/ (or your configured domain)
- **Supported Browsers:** Chrome, Firefox, Safari, Edge (latest versions)
- **Default Port:** 443 (HTTPS)

**API Access:**
- **Base URL:** http://192.168.50.100:2542/api
- **API Documentation:** See API Reference section
- **Authentication:** None required (internal network)

### First Login

1. Open web browser
2. Navigate to https://192.168.50.100/
3. You will see the Blacklist Management Platform home page
4. No login required for current version

---

## Web Interface Overview

### Home Page (`/`)

**Features:**
- System overview
- Quick statistics (total blacklist/whitelist IPs)
- Recent activity summary
- Navigation menu to all sections

**Quick Stats Display:**
- Active Blacklist IPs
- Protected Whitelist IPs
- Last Collection Date
- System Health Status

### Navigation Menu

| Menu Item | URL | Purpose |
|-----------|-----|---------|
| Home | `/` | System overview and quick stats |
| Dashboard | `/dashboard` | Pipeline monitoring dashboard |
| Collection Panel | `/collection-panel/` | Manage data collection sources |
| Statistics | `/statistics` | Detailed analytics and trends |

---

## Managing Blacklist IPs

### Checking if an IP is Blacklisted

**Method 1: Via Web UI**
1. Navigate to Statistics page (`/statistics`)
2. Enter IP address in search box
3. Click "Check IP"
4. Result shows:
   - ✅ **Not Blocked** - IP is safe
   - ⚠️ **Whitelisted** - IP is protected (whitelist)
   - ❌ **Blocked** - IP is blacklisted

**Method 2: Via API**
```bash
curl "http://192.168.50.100:2542/api/blacklist/check?ip=1.2.3.4"
```

**Response Format:**
```json
{
  "blocked": true,
  "reason": "blacklisted",
  "ip": "1.2.3.4",
  "metadata": {
    "country": "CN",
    "detection_date": "2025-10-15",
    "removal_date": "2026-01-15",
    "source": "REGTECH"
  }
}
```

### Understanding Blacklist Status

**Status Values:**
- **"not_found"** - IP is not in blacklist, safe to allow
- **"whitelist"** - IP is whitelisted, always allowed regardless of blacklist
- **"blacklisted"** - IP is in blacklist, should be blocked

**Important: Whitelist Priority**
> If an IP appears in both whitelist AND blacklist, whitelist always takes precedence. This ensures whitelisted IPs are never blocked.

### Manually Adding IPs to Blacklist

**Use Case:** Block a known malicious IP not yet in automated collections

**Via API:**
```bash
curl -X POST http://192.168.50.100:2542/api/blacklist/manual-add \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "5.6.7.8",
    "country": "CN",
    "reason": "Attempted brute force attack on 2025-10-20",
    "notes": "Detected in firewall logs, 1000+ failed login attempts"
  }'
```

**Required Fields:**
- `ip_address` - IP to block (format: xxx.xxx.xxx.xxx)
- `country` - 2-letter country code (e.g., "CN", "KR", "US")
- `reason` - Why this IP is being blocked

**Optional Fields:**
- `notes` - Additional context
- `detection_date` - When threat was detected (defaults to today)
- `removal_date` - When to auto-remove (defaults to 90 days from detection)

### Viewing Blacklist Data

**Method 1: Statistics Dashboard**
1. Navigate to `/statistics`
2. View charts:
   - Blacklist growth over time
   - Top countries by IP count
   - Detection date distribution

**Method 2: API Query**
```bash
# Get active blacklist IPs (paginated)
curl "http://192.168.50.100:2542/api/fortinet/active-ips?page=1&per_page=50"
```

---

## Managing Whitelist IPs

### Understanding Whitelist

**Purpose:**
- Protect whitelisted IPs from being blocked
- Ensure critical services never get blacklisted
- Override any automated blacklist additions

**Priority Logic:**
> **Whitelist is ALWAYS checked BEFORE blacklist**
>
> Even if an IP appears in the blacklist (from automated collection or manual add), if it's in the whitelist, it will NEVER be blocked.

### Adding IPs to Whitelist

**Via API:**
```bash
curl -X POST http://192.168.50.100:2542/api/whitelist/manual-add \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "192.168.1.100",
    "country": "KR",
    "reason": "whitelisted IP - Protected Account #12345",
    "notes": "CEO office IP - never block"
  }'
```

**Required Fields:**
- `ip_address` - IP to protect
- `country` - 2-letter country code
- `reason` - Business justification for whitelist

**Best Practices:**
- Always include detailed reason
- Include customer account number in notes
- Review whitelist monthly
- Remove IPs when customer relationship ends

### Viewing Whitelist

```bash
# Get all whitelist entries
curl "http://192.168.50.100:2542/api/whitelist/list"
```

**Response:**
```json
{
  "total": 27,
  "page": 1,
  "per_page": 50,
  "items": [
    {
      "ip_address": "192.168.1.100",
      "country": "KR",
      "reason": "whitelisted IP",
      "created_at": "2025-10-15T09:30:00",
      "is_active": true
    }
  ]
}
```

### Removing from Whitelist

**When to Remove:**
- Customer account terminated
- IP no longer belongs to customer
- Regular whitelist review/cleanup

**Via Database Access:**
```bash
docker exec -it blacklist-postgres psql -U postgres -d blacklist
DELETE FROM whitelist_ips WHERE ip_address='192.168.1.100';
```

---

## Data Collection Management

### Overview

The system automatically collects threat intelligence from two sources:
1. **REGTECH** - Korean Financial Security Institute
2. **SECUDIUM** - Additional threat intelligence provider

### Accessing Collection Panel

1. Navigate to `/collection-panel/`
2. View current collection status
3. Manage credentials
4. Trigger manual collections
5. Review collection history

### Configuring Collection Credentials

**REGTECH Credentials:**
1. Go to Collection Panel → Credential Management
2. Find "REGTECH" section
3. Enter your REGTECH username
4. Enter your REGTECH password
5. Click "Save REGTECH Credentials"

**SECUDIUM Credentials:**
1. In same Credential Management section
2. Find "SECUDIUM" section
3. Enter your SECUDIUM username
4. Enter your SECUDIUM password
5. Click "Save SECUDIUM Credentials"

**Verify Credentials Saved:**
```bash
curl http://192.168.50.100:2542/api/collection/credentials/REGTECH | jq
curl http://192.168.50.100:2542/api/collection/credentials/SECUDIUM | jq
```

### Manual Collection Trigger

**When to Trigger Manually:**
- Immediately after configuring credentials
- When you need latest threat data urgently
- Testing collection functionality
- After collection failure

**Trigger REGTECH Collection:**
```bash
curl -X POST http://192.168.50.100:2542/api/collection/regtech/trigger
```

**Trigger SECUDIUM Collection:**
```bash
curl -X POST http://192.168.50.100:2542/api/collection/trigger/SECUDIUM
```

**Expected Response:**
```json
{
  "status": "started",
  "message": "REGTECH collection started in background",
  "timestamp": "2025-10-21T10:30:00"
}
```

**Collection Duration:**
- Typical: 2-3 minutes per source
- Network dependent
- Database insertion depends on record count

### Monitoring Collection Progress

**Via Collection History:**
```bash
curl http://192.168.50.100:2542/api/collection/history | jq
```

**Response Shows:**
```json
[
  {
    "service_name": "REGTECH",
    "collection_date": "2025-10-21T10:30:00",
    "items_collected": 12450,
    "success": true,
    "error_message": null
  },
  {
    "service_name": "SECUDIUM",
    "collection_date": "2025-10-21T10:35:00",
    "items_collected": 1507,
    "success": true,
    "error_message": null
  }
]
```

### Understanding Collection Status

**Success Indicators:**
- `success: true`
- `items_collected > 0`
- `error_message: null`

**Failure Indicators:**
- `success: false`
- `items_collected: 0`
- `error_message: "Authentication failed"` or similar

**Common Error Messages:**
| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Authentication failed" | Wrong credentials | Update credentials in Collection Panel |
| "Network timeout" | API unreachable | Check internet connectivity |
| "Invalid file format" | Excel parsing failed | Contact support |
| "Database error" | DB connection issue | Check database health |

### Automated Collection Schedule

**Default Schedule:**
- REGTECH: Daily at 2:00 AM
- SECUDIUM: Daily at 3:00 AM

**Note:** Automated scheduling is configured in the collector service. Manual triggers are always available.

---

## Monitoring & Statistics

### Dashboard Page (`/dashboard`)

**Pipeline Monitoring Dashboard:**
- Real-time collection status
- Active collectors
- Last collection timestamp
- Success/failure rates

**Key Metrics Displayed:**
- Total blacklist IPs (active)
- Total whitelist IPs
- Collections today
- System health

### Statistics Page (`/statistics`)

**Analytics Features:**
1. **Blacklist Growth Chart**
   - Daily IP additions
   - Trend over last 30 days
   - Source breakdown (REGTECH vs SECUDIUM)

2. **Country Distribution**
   - Top 10 countries by IP count
   - Geographic heatmap
   - Country risk score

3. **Detection Timeline**
   - When threats were first detected
   - Removal date distribution
   - Active vs expired IPs

4. **IP Search**
   - Quick lookup tool
   - Check any IP status
   - View IP details

### API Statistics Endpoint

```bash
curl http://192.168.50.100:2542/api/stats
```

**Response:**
```json
{
  "active_ips": 13957,
  "categories": {
    "blacklist": 13957,
    "whitelist": 27
  },
  "last_update": "2025-10-21T10:35:00",
  "sources": {
    "REGTECH": 12450,
    "SECUDIUM": 1507
  },
  "countries": {
    "CN": 5234,
    "US": 2100,
    "RU": 1850
  }
}
```

---

## FortiGate Integration

### Overview

The system can export blacklist data in FortiGate firewall-compatible format.

### Getting Active IPs for FortiGate

**Endpoint:** `/api/fortinet/active-ips`

```bash
curl "http://192.168.50.100:2542/api/fortinet/active-ips?page=1&per_page=1000"
```

**Response Format:**
```json
{
  "total": 13957,
  "page": 1,
  "per_page": 1000,
  "ips": [
    {
      "ip_address": "1.2.3.4",
      "country": "CN",
      "detection_date": "2025-10-15",
      "removal_date": "2026-01-15",
      "source": "REGTECH"
    }
  ]
}
```

### FortiGate Blocklist Format

**Endpoint:** `/api/fortinet/blocklist`

```bash
curl "http://192.168.50.100:2542/api/fortinet/blocklist"
```

**Response Format (FortiGate CLI commands):**
```
config firewall address
  edit "blacklist_1.2.3.4"
    set subnet 1.2.3.4/32
    set comment "Detected: 2025-10-15, Source: REGTECH"
  next
end
```

### Automating FortiGate Sync

**Option 1: Scheduled Script on FortiGate**
```bash
#!/bin/bash
# Run daily at 4:00 AM (after collections complete)

# Fetch blocklist
curl http://192.168.50.100:2542/api/fortinet/blocklist > /tmp/blacklist.conf

# Apply to FortiGate (requires SSH access)
ssh admin@fortigate.local < /tmp/blacklist.conf
```

**Option 2: FortiGate External Dynamic List**
Configure FortiGate to periodically fetch from:
`http://192.168.50.100:2542/api/fortinet/active-ips`

**Important: Whitelist Handling**
> IPs in the whitelist are AUTOMATICALLY EXCLUDED from FortiGate exports. You don't need to manually filter whitelisted IPs.

---

## Common Tasks

### Task 1: Add Protected customer to Whitelist

**Scenario:** New premium customer needs guaranteed access

**Steps:**
```bash
# 1. Add to whitelist
curl -X POST http://192.168.50.100:2542/api/whitelist/manual-add \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "203.0.113.50",
    "country": "KR",
    "reason": "Protected customer - Account #9876",
    "notes": "Premium support customer, never block"
  }'

# 2. Verify addition
curl "http://192.168.50.100:2542/api/blacklist/check?ip=203.0.113.50"
# Expected: {"blocked": false, "reason": "whitelist"}

# 3. Document in customer account
# Add note: "IP 203.0.113.50 whitelisted on 2025-10-21"
```

### Task 2: Block Malicious IP Immediately

**Scenario:** Security team detected attack from specific IP

**Steps:**
```bash
# 1. Add to blacklist
curl -X POST http://192.168.50.100:2542/api/blacklist/manual-add \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "198.51.100.25",
    "country": "US",
    "reason": "DDoS attack detected",
    "notes": "Incident #2025-1021-001, 10K req/sec attack"
  }'

# 2. Verify blocking
curl "http://192.168.50.100:2542/api/blacklist/check?ip=198.51.100.25"
# Expected: {"blocked": true, "reason": "blacklisted"}

# 3. Trigger FortiGate sync immediately
curl "http://192.168.50.100:2542/api/fortinet/blocklist" > /tmp/update.conf
# Apply to firewall
```

### Task 3: Review Collection Results

**Scenario:** Daily morning check of overnight collections

**Steps:**
```bash
# 1. Check collection history
curl "http://192.168.50.100:2542/api/collection/history" | \
  jq '.[] | select(.collection_date | startswith("2025-10-21"))'

# 2. Verify success
# Look for: "success": true, "items_collected" > 0

# 3. Check new IP count
curl "http://192.168.50.100:2542/api/stats" | jq '.active_ips'

# 4. Review top countries
curl "http://192.168.50.100:2542/api/stats" | jq '.countries'
```

### Task 4: Troubleshoot Collection Failure

**Scenario:** REGTECH collection failed this morning

**Steps:**
```bash
# 1. Check error message
curl "http://192.168.50.100:2542/api/collection/history" | \
  jq '.[] | select(.service_name=="REGTECH") | select(.success==false) | .error_message'

# 2. If "Authentication failed":
# - Go to /collection-panel/
# - Update REGTECH credentials
# - Click Save

# 3. Retry collection
curl -X POST http://192.168.50.100:2542/api/collection/regtech/trigger

# 4. Wait 3-5 minutes, verify success
curl "http://192.168.50.100:2542/api/collection/history" | \
  jq '.[] | select(.service_name=="REGTECH") | select(.success==true)'
```

### Task 5: Export Blacklist for Reporting

**Scenario:** Security audit requires list of all blocked IPs

**Steps:**
```bash
# 1. Get all active IPs (paginated)
curl "http://192.168.50.100:2542/api/fortinet/active-ips?page=1&per_page=5000" > blacklist_page1.json
curl "http://192.168.50.100:2542/api/fortinet/active-ips?page=2&per_page=5000" > blacklist_page2.json
curl "http://192.168.50.100:2542/api/fortinet/active-ips?page=3&per_page=5000" > blacklist_page3.json

# 2. Convert to CSV
cat blacklist_page1.json | jq -r '.ips[] | [.ip_address, .country, .detection_date, .source] | @csv' > blacklist.csv

# 3. Get summary statistics
curl "http://192.168.50.100:2542/api/stats" > blacklist_stats.json
```

---

## Troubleshooting

### Problem: Cannot Access Web UI

**Symptoms:**
- Browser shows "Connection refused"
- https://192.168.50.100/ doesn't load

**Diagnosis:**
```bash
# Check if containers are running
docker compose ps

# Check nginx specifically
docker ps | grep blacklist-nginx

# Check port 443
sudo lsof -i :443
```

**Solutions:**
1. If nginx not running:
   ```bash
   docker compose up -d blacklist-nginx
   ```

2. If port 443 in use by another service:
   ```bash
   # Access frontend directly (temporary)
   curl http://192.168.50.100:2543
   ```

3. If all containers down:
   ```bash
   docker compose up -d
   ```

### Problem: IP Check Returns "error"

**Symptoms:**
```json
{
  "error": "Internal server error",
  "blocked": null
}
```

**Diagnosis:**
```bash
# Check app container logs
docker compose logs blacklist-app | tail -50

# Check database connection
docker exec blacklist-postgres pg_isready -U postgres -d blacklist
```

**Solutions:**
1. If database connection failed:
   ```bash
   docker compose restart blacklist-postgres
   docker compose restart blacklist-app
   ```

2. If Redis connection failed:
   ```bash
   docker compose restart blacklist-redis
   docker compose restart blacklist-app
   ```

### Problem: Collection Always Fails

**Symptoms:**
- Collection history shows `success: false`
- Error message: "Authentication failed"

**Solutions:**
1. Verify credentials via UI:
   - Go to `/collection-panel/`
   - Check REGTECH username/password
   - Check SECUDIUM username/password
   - Click Save

2. Verify credentials in database:
   ```bash
   docker exec blacklist-postgres psql -U postgres -d blacklist -c \
     "SELECT service_name, username, is_active FROM collection_credentials;"
   ```

3. Test network connectivity:
   ```bash
   docker exec blacklist-collector curl -I https://regtech.fsec.or.kr
   docker exec blacklist-collector curl -I https://rest.secudium.net
   ```

### Problem: FortiGate Export Shows 0 IPs

**Symptoms:**
```json
{
  "total": 0,
  "ips": []
}
```

**Diagnosis:**
```bash
# Check if blacklist has data
docker exec blacklist-postgres psql -U postgres -d blacklist -c \
  "SELECT COUNT(*) FROM blacklist_ips WHERE is_active=true;"
```

**Solutions:**
1. If count is 0, trigger collection:
   ```bash
   curl -X POST http://192.168.50.100:2542/api/collection/regtech/trigger
   curl -X POST http://192.168.50.100:2542/api/collection/trigger/SECUDIUM
   ```

2. If count > 0 but API returns 0:
   ```bash
   docker compose restart blacklist-app
   ```

---

## FAQ

### Q1: How often should I run collections?

**A:** Collections run automatically daily. Manual triggers are useful for:
- Immediately after credential configuration
- When urgent threat intelligence needed
- Testing system functionality

**Recommendation:** Let automated schedule handle daily updates. Manually trigger only when needed.

---

### Q2: What happens if an IP is in both whitelist and blacklist?

**A:** Whitelist ALWAYS takes priority. The IP will never be blocked.

**Example:**
```bash
# IP 1.2.3.4 is in both lists
curl "http://192.168.50.100:2542/api/blacklist/check?ip=1.2.3.4"

# Response will be:
{
  "blocked": false,
  "reason": "whitelist"  # Not "blacklisted"
}
```

---

### Q3: Can I remove IPs from the blacklist?

**A:** Blacklist IPs auto-expire based on `removal_date`. Manual removal requires database access:

```bash
docker exec -it blacklist-postgres psql -U postgres -d blacklist
UPDATE blacklist_ips SET is_active=false WHERE ip_address='1.2.3.4';
```

**Recommendation:** Use whitelist instead of deleting from blacklist. This preserves historical records while allowing access.

---

### Q4: How do I know if collections are working?

**A:** Check collection history:
```bash
curl "http://192.168.50.100:2542/api/collection/history" | \
  jq '.[] | {service: .service_name, date: .collection_date, success: .success, count: .items_collected}'
```

**Good indicators:**
- Recent timestamps (within 24 hours)
- `success: true`
- `items_collected > 0`

---

### Q5: What's the difference between REGTECH and SECUDIUM?

**A:**
- **REGTECH:** Korean Financial Security Institute - focuses on financial security threats
- **SECUDIUM:** General threat intelligence - broader threat coverage

Both provide complementary data. Running both ensures comprehensive protection.

---

### Q6: Can I integrate with other firewalls besides FortiGate?

**A:** Yes, via the `/api/fortinet/active-ips` endpoint.

**For Palo Alto:**
```bash
# Get IP list
curl "http://192.168.50.100:2542/api/fortinet/active-ips" | \
  jq -r '.ips[].ip_address' > paloalto_blocklist.txt

# Import into Palo Alto external block list
```

**For Cisco ASA:**
```bash
# Convert to Cisco format
curl "http://192.168.50.100:2542/api/fortinet/active-ips" | \
  jq -r '.ips[] | "object network BLACKLIST_\(.ip_address | gsub("\\."; "_"))\n host \(.ip_address)"'
```

---

### Q7: How long does data remain in the blacklist?

**A:** Each IP has a `removal_date` (typically 90 days from detection). The system automatically deactivates IPs when removal date passes.

**Check removal dates:**
```bash
curl "http://192.168.50.100:2542/api/fortinet/active-ips?page=1&per_page=10" | \
  jq '.ips[] | {ip: .ip_address, removal: .removal_date}'
```

---

### Q8: What if I need to back up the data?

**A:** Database backups preserve all data:

```bash
# Create backup
docker exec blacklist-postgres pg_dump -U postgres -d blacklist > backup.sql

# Restore backup
cat backup.sql | docker exec -i blacklist-postgres psql -U postgres -d blacklist
```

**Recommendation:** Schedule daily backups via cron job.

---

### Q9: How do I update credentials?

**A:** Two methods:

**Method 1: Via Web UI (Recommended)**
1. Go to `/collection-panel/`
2. Update credentials
3. Click Save

**Method 2: Via API**
```bash
curl -X PUT http://192.168.50.100:2542/api/collection/credentials/REGTECH \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_username",
    "password": "new_password"
  }'
```

---

### Q10: Can I see which source (REGTECH vs SECUDIUM) an IP came from?

**A:** Yes, via the API:

```bash
curl "http://192.168.50.100:2542/api/fortinet/active-ips?page=1&per_page=50" | \
  jq '.ips[] | {ip: .ip_address, source: .source}'
```

**Response:**
```json
{
  "ip": "1.2.3.4",
  "source": "REGTECH"
}
{
  "ip": "5.6.7.8",
  "source": "SECUDIUM"
}
```

---

## Quick Reference

### Essential API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System health check |
| `/api/blacklist/check?ip={ip}` | GET | Check if IP is blocked |
| `/api/whitelist/manual-add` | POST | Add IP to whitelist |
| `/api/blacklist/manual-add` | POST | Add IP to blacklist |
| `/api/collection/history` | GET | View collection audit log |
| `/api/collection/regtech/trigger` | POST | Trigger REGTECH collection |
| `/api/collection/trigger/SECUDIUM` | POST | Trigger SECUDIUM collection |
| `/api/fortinet/active-ips` | GET | Get active blacklist IPs |
| `/api/stats` | GET | System statistics |

### Essential Web Pages

| Page | URL | Purpose |
|------|-----|---------|
| Home | `/` | System overview |
| Dashboard | `/dashboard` | Monitoring dashboard |
| Collection Panel | `/collection-panel/` | Manage collections |
| Statistics | `/statistics` | Analytics and trends |

### Container Management

```bash
# View all container status
docker compose ps

# View logs
docker compose logs -f blacklist-app
docker compose logs -f blacklist-collector

# Restart specific container
docker compose restart blacklist-app

# Restart all containers
docker compose restart
```

---

**END OF USER MANUAL**
