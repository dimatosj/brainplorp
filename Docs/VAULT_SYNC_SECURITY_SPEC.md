# Vault Sync Security Architecture Spec

## Current Security Issue

**Problem:** Admin credentials are hardcoded in `src/brainplorp/commands/setup.py`:

```python
COUCHDB_ADMIN_USER = "admin"
COUCHDB_ADMIN_PASSWORD = "CZzAQ7wnpPHY-tL0dYu20VY9-vcQHWdvENs0rLkye_0"
```

Anyone with the source code can:
- Access any user's vault database
- Delete databases
- Modify server configuration
- Impersonate users

## Proposed Solution: Registration API

### Architecture Overview

```
┌─────────────┐          ┌──────────────────┐          ┌─────────────┐
│  brainplorp │  HTTPS   │  Registration    │  Local   │  CouchDB    │
│   (client)  ├─────────>│  API Server      ├─────────>│  (private)  │
│             │          │  (fly.io app)    │  admin   │             │
└─────────────┘          └──────────────────┘  access  └─────────────┘
      │                                                        │
      │                    HTTPS (user credentials)           │
      └────────────────────────────────────────────────────────┘
                          Direct CouchDB access
```

**Key Principles:**
1. Admin credentials NEVER leave the server
2. Client only knows about the registration API endpoint
3. After registration, client connects directly to CouchDB with user credentials
4. Registration API runs on same fly.io private network as CouchDB

### Component 1: Registration API Server

**Technology:** Python FastAPI (lightweight, async, easy to deploy on fly.io)

**Endpoint:** `POST https://brainplorp-api.fly.dev/v1/register`

**Request:**
```json
{
  "username": "jsd",
  "password": "sB1p0qA8FosbKfkqB96otg-Ep_wuNasHdy1Xd_3uc9w",
  "email": "user@example.com"  // optional, for recovery
}
```

**Response (Success - 201 Created):**
```json
{
  "status": "success",
  "database": "user-jsd-vault",
  "username": "jsd",
  "server_url": "https://couch-brainplorp-sync.fly.dev"
}
```

**Response (Conflict - 409):**
```json
{
  "status": "error",
  "error": "username_exists",
  "message": "Username 'jsd' is already taken"
}
```

**Response (Invalid - 400):**
```json
{
  "status": "error",
  "error": "invalid_username",
  "message": "Username must be 3-32 chars, alphanumeric + hyphen/underscore"
}
```

**Implementation:**

```python
# api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
import os
import re
from couchdb_admin import CouchDBAdmin

app = FastAPI()

# Admin credentials from environment (fly.io secrets)
COUCHDB_URL = os.environ['COUCHDB_INTERNAL_URL']  # http://couch-brainplorp-sync.internal:5984
COUCHDB_ADMIN_USER = os.environ['COUCHDB_ADMIN_USER']
COUCHDB_ADMIN_PASSWORD = os.environ['COUCHDB_ADMIN_PASSWORD']

class RegistrationRequest(BaseModel):
    username: str
    password: str
    email: str | None = None

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-z][a-z0-9_-]{2,31}$', v):
            raise ValueError('Invalid username format')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 32:
            raise ValueError('Password must be at least 32 characters')
        return v

@app.post("/v1/register")
async def register_user(req: RegistrationRequest):
    """
    Register new user and create vault database.

    Steps:
    1. Validate username/password
    2. Check if username exists
    3. Create user in CouchDB _users database
    4. Create user's vault database
    5. Grant user access to their database
    6. Return credentials
    """
    admin = CouchDBAdmin(COUCHDB_URL, COUCHDB_ADMIN_USER, COUCHDB_ADMIN_PASSWORD)

    # Check if user exists
    if admin.user_exists(req.username):
        raise HTTPException(status_code=409, detail={
            "error": "username_exists",
            "message": f"Username '{req.username}' is already taken"
        })

    database_name = f"user-{req.username}-vault"

    try:
        # Create user
        admin.create_user(req.username, req.password)

        # Create database
        admin.create_database(database_name)

        # Grant access
        admin.grant_database_access(database_name, req.username)

        # Store email if provided (for recovery)
        if req.email:
            admin.store_user_metadata(req.username, {"email": req.email})

        return {
            "status": "success",
            "database": database_name,
            "username": req.username,
            "server_url": "https://couch-brainplorp-sync.fly.dev"
        }

    except Exception as e:
        # Rollback on error
        admin.delete_user(req.username)
        admin.delete_database(database_name)
        raise HTTPException(status_code=500, detail={
            "error": "registration_failed",
            "message": str(e)
        })

@app.get("/health")
async def health_check():
    """Health check endpoint for fly.io monitoring."""
    return {"status": "ok"}
```

**Rate Limiting:**
- 5 registration attempts per IP per hour (prevent spam)
- Implemented via fly.io rate limiting or Redis

**Security Features:**
1. **HTTPS only** - fly.io provides automatic TLS
2. **Input validation** - Pydantic models validate all inputs
3. **Username uniqueness** - Check before creating
4. **Rollback on failure** - Delete user/database if any step fails
5. **No admin creds in logs** - Never log passwords
6. **IP rate limiting** - Prevent abuse

### Component 2: brainplorp Client Changes

**File:** `src/brainplorp/commands/setup.py`

**Before (Insecure):**
```python
# Constants
COUCHDB_SERVER_URL = "https://couch-brainplorp-sync.fly.dev"
COUCHDB_ADMIN_USER = "admin"  # ❌ EXPOSED
COUCHDB_ADMIN_PASSWORD = "CZzAQ7wnpPHY-tL0dYu20VY9-vcQHWdvENs0rLkye_0"  # ❌ EXPOSED

# Create database and user in CouchDB
try:
    client = CouchDBClient(COUCHDB_SERVER_URL, COUCHDB_ADMIN_USER, COUCHDB_ADMIN_PASSWORD)
    client.test_connection()
    client.setup_vault_database(database, username, password)
```

**After (Secure):**
```python
# Constants
REGISTRATION_API_URL = "https://brainplorp-api.fly.dev"
COUCHDB_SERVER_URL = "https://couch-brainplorp-sync.fly.dev"

# Register via API (no admin credentials needed)
try:
    response = requests.post(
        f"{REGISTRATION_API_URL}/v1/register",
        json={
            "username": username,
            "password": password
        },
        timeout=30
    )

    if response.status_code == 201:
        data = response.json()
        database = data['database']
        click.echo("  ✓ Vault database created")
    elif response.status_code == 409:
        click.echo("  ✗ Username already taken - choose a different username")
        return None
    else:
        click.echo(f"  ✗ Registration failed: {response.json().get('message')}")
        return None

except requests.exceptions.RequestException as e:
    click.echo(f"  ✗ Cannot reach registration server: {e}")
    return None
```

**New File:** `src/brainplorp/integrations/registration_api.py`

```python
"""
Registration API client for secure vault setup.

Replaces direct CouchDB admin access with API-based registration.
"""

import requests
from typing import Dict, Optional


class RegistrationError(Exception):
    """Registration API error."""
    pass


class RegistrationClient:
    """Client for brainplorp registration API."""

    def __init__(self, api_url: str):
        """
        Initialize registration client.

        Args:
            api_url: Registration API base URL
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = 30

    def register_user(self, username: str, password: str, email: Optional[str] = None) -> Dict:
        """
        Register new user and create vault database.

        Args:
            username: CouchDB username (must be unique)
            password: Strong password (32+ chars recommended)
            email: Optional email for recovery

        Returns:
            Dict with 'database', 'username', 'server_url' keys

        Raises:
            RegistrationError: If registration fails
        """
        payload = {
            "username": username,
            "password": password
        }

        if email:
            payload["email"] = email

        try:
            response = requests.post(
                f"{self.api_url}/v1/register",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 201:
                return response.json()
            elif response.status_code == 409:
                raise RegistrationError("Username already taken")
            elif response.status_code == 400:
                error = response.json()
                raise RegistrationError(error.get('message', 'Invalid input'))
            else:
                raise RegistrationError(f"Registration failed: HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            raise RegistrationError("Registration request timed out")
        except requests.exceptions.ConnectionError:
            raise RegistrationError("Cannot connect to registration server")
        except requests.exceptions.RequestException as e:
            raise RegistrationError(f"Request failed: {e}")
```

### Component 3: Deployment Configuration

**File:** `api/fly.toml` (new)

```toml
app = "brainplorp-api"
primary_region = "sjc"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"
  COUCHDB_INTERNAL_URL = "http://couch-brainplorp-sync.internal:5984"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

  [[http_service.checks]]
    interval = "30s"
    timeout = "5s"
    grace_period = "10s"
    method = "GET"
    path = "/health"

[[services]]
  protocol = "tcp"
  internal_port = 8080

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

**File:** `api/Dockerfile` (new)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**File:** `api/requirements.txt` (new)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
requests==2.31.0
```

**Fly.io Secrets (set via CLI):**
```bash
flyctl secrets set \
  COUCHDB_ADMIN_USER=admin \
  COUCHDB_ADMIN_PASSWORD=CZzAQ7wnpPHY-tL0dYu20VY9-vcQHWdvENs0rLkye_0 \
  --app brainplorp-api
```

**Private Network:**
- API server and CouchDB on same fly.io private network
- API uses internal URL: `http://couch-brainplorp-sync.internal:5984`
- Only API has admin credentials
- CouchDB port 5984 NOT exposed to public internet

### Component 4: Testing

**Unit Tests:** `tests/test_integrations/test_registration_api.py`

```python
import pytest
import responses
from brainplorp.integrations.registration_api import RegistrationClient, RegistrationError


@responses.activate
def test_register_user_success():
    """Test successful user registration."""
    client = RegistrationClient("https://brainplorp-api.fly.dev")

    responses.add(
        responses.POST,
        "https://brainplorp-api.fly.dev/v1/register",
        json={
            "status": "success",
            "database": "user-testuser-vault",
            "username": "testuser",
            "server_url": "https://couch-brainplorp-sync.fly.dev"
        },
        status=201
    )

    result = client.register_user("testuser", "a" * 32)

    assert result["database"] == "user-testuser-vault"
    assert result["username"] == "testuser"


@responses.activate
def test_register_user_username_taken():
    """Test registration with existing username."""
    client = RegistrationClient("https://brainplorp-api.fly.dev")

    responses.add(
        responses.POST,
        "https://brainplorp-api.fly.dev/v1/register",
        json={
            "error": "username_exists",
            "message": "Username 'testuser' is already taken"
        },
        status=409
    )

    with pytest.raises(RegistrationError, match="Username already taken"):
        client.register_user("testuser", "a" * 32)


@responses.activate
def test_register_user_timeout():
    """Test registration timeout."""
    client = RegistrationClient("https://brainplorp-api.fly.dev")

    responses.add(
        responses.POST,
        "https://brainplorp-api.fly.dev/v1/register",
        body=requests.exceptions.Timeout()
    )

    with pytest.raises(RegistrationError, match="timed out"):
        client.register_user("testuser", "a" * 32)
```

**Integration Test:** `tests/test_integrations/test_registration_flow.py`

```python
import pytest
from pathlib import Path
from brainplorp.integrations.registration_api import RegistrationClient

@pytest.mark.integration
def test_full_registration_flow():
    """
    Integration test for full registration flow.

    Requires:
    - Registration API running at REGISTRATION_API_URL env var
    - CouchDB accessible
    """
    import os
    import uuid

    api_url = os.getenv("REGISTRATION_API_URL", "https://brainplorp-api.fly.dev")
    client = RegistrationClient(api_url)

    # Generate unique username for testing
    test_user = f"test-{uuid.uuid4().hex[:8]}"
    test_password = "test-password-" + uuid.uuid4().hex

    # Register
    result = client.register_user(test_user, test_password)

    assert result["username"] == test_user
    assert result["database"] == f"user-{test_user}-vault"

    # Verify can't register again
    with pytest.raises(RegistrationError, match="already taken"):
        client.register_user(test_user, test_password)

    # TODO: Verify can connect to CouchDB with credentials
    # TODO: Cleanup test user after test
```

### Component 5: Migration Path

**Phase 1: Deploy Registration API (Sprint 10.4)**
- Deploy FastAPI server to fly.io
- Configure secrets and private network
- Test with curl/Postman

**Phase 2: Update brainplorp Client (Sprint 10.5)**
- Add `registration_api.py` integration
- Update `setup.py` to use registration API
- Remove hardcoded admin credentials
- Add fallback for existing users (no re-registration needed)

**Phase 3: Documentation (Sprint 10.6)**
- Update README with public deployment instructions
- Document registration API endpoints
- Add troubleshooting guide
- Security audit and penetration testing

### Component 6: Additional Security Considerations

**Rate Limiting:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/register")
@limiter.limit("5/hour")  # 5 registrations per IP per hour
async def register_user(request: Request, req: RegistrationRequest):
    # ... implementation
```

**Username Validation:**
- Minimum 3 characters
- Maximum 32 characters
- Lowercase alphanumeric + hyphen/underscore
- Must start with letter
- Block reserved names: admin, test, demo, system, etc.

**Password Requirements:**
- Minimum 32 characters (enforced by brainplorp client generation)
- Client-side generation via `secrets.token_urlsafe(32)`
- No maximum length (CouchDB supports long passwords)

**Monitoring:**
- Log all registration attempts (username only, no passwords)
- Alert on suspicious patterns (many failed attempts, automated scripts)
- Metrics: registrations per hour, success rate, error types

**Backup Admin Access:**
- Keep separate emergency admin credentials (not in code)
- Stored in fly.io secrets or password manager
- Only for server maintenance, not exposed to clients

### Component 7: Cost Analysis

**Current Cost (Single Server):**
- CouchDB server: ~$5-10/month (fly.io shared CPU)

**New Cost (Registration API + CouchDB):**
- CouchDB server: ~$5-10/month
- API server: ~$0-5/month (auto-sleep when idle, pay-per-use)
- **Total: ~$5-15/month**

**Scaling:**
- API auto-scales with demand (fly.io machines)
- CouchDB may need vertical scaling with many users
- At 1000+ users, consider dedicated CouchDB instance ($50-100/month)

## Summary

**Security Improvements:**
✅ Admin credentials never exposed to clients
✅ Registration API as single point of control
✅ Rate limiting prevents abuse
✅ Input validation prevents injection attacks
✅ Private network between API and CouchDB
✅ HTTPS everywhere

**Implementation Effort:**
- API server: ~4-6 hours (FastAPI is fast to write)
- Client integration: ~2-3 hours
- Testing: ~2-3 hours
- Deployment: ~1-2 hours
- Documentation: ~2-3 hours
- **Total: ~12-17 hours (1-2 sprints)**

**Trade-offs:**
- ✅ Much more secure
- ✅ Ready for public distribution
- ✅ Professional architecture
- ❌ More moving parts (API server to maintain)
- ❌ Slightly slower setup (network round-trip for registration)
- ❌ Requires fly.io account for API server

**Alternative:** Keep current model but document as "personal use only, deploy your own CouchDB" (much simpler, good enough for you).

---

**Next Steps:**
1. Review this spec
2. Decide: Implement now, or defer and document as personal-use?
3. If implementing: Create Sprint 10.4 spec for Registration API
