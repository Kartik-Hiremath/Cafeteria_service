# Cafeteria Service - Blu-Reserve

Cafeteria seat booking with IBM W3ID authentication, Blu-Dollar charging, and admin dashboard.

## Quick Start

### 1. Setup

```bash
cd features
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

Create `features/.env` (copy from `features/.env.example`):

```bash
cp features/.env.example features/.env
```

Ensure these are set for Real W3ID:

```env
IBM_CLIENT_ID=your_client_id
IBM_CLIENT_SECRET=your_client_secret
IBM_REDIRECT_URI=http://localhost:8000/auth/callback
IBM_DISCOVERY_URL=https://login.w3.ibm.com/oidc/endpoint/default/.well-known/openid-configuration
FRONTEND_URL=http://localhost:3000
```

### 3. Run

**Terminal 1 – Backend**
```bash
cd features && uvicorn app.main:app --reload --port 8000
```

**Terminal 2 – Frontend**
```bash
cd features/Frontend && npm install && npm run dev
```

### 4. Access

- App: http://localhost:3000
- Swagger: http://localhost:8000/docs
- Admin: http://localhost:3000/admin

## Login Options

1. **Real W3ID** – IBM SSO (requires IBM credentials)
2. **Dummy W3ID** – Demo with managers (Manager 1–10, Admin, Manager with 0 points) and 10 employees (emp001–emp010)

## Tests

```bash
cd features
pytest -v
```

See [features/TESTING.md](features/TESTING.md), [features/API_DOCUMENTATION.md](features/API_DOCUMENTATION.md), [features/DATABASE.md](features/DATABASE.md), and [features/ARCHITECTURE.md](features/ARCHITECTURE.md).
