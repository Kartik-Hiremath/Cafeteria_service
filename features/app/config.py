"""Configuration for Cafeteria Service. Supports IBM_* and OIDC_* env vars."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before reading any env vars (from features/ or project root)
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # features/.env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")  # project root .env

# IBM SSO (W3) - prefer IBM_* if set, fallback to OIDC_*
IBM_CLIENT_ID = os.getenv("IBM_CLIENT_ID") or os.getenv("OIDC_CLIENT_ID")
IBM_CLIENT_SECRET = os.getenv("IBM_CLIENT_SECRET") or os.getenv("OIDC_CLIENT_SECRET")
IBM_REDIRECT_URI = os.getenv("IBM_REDIRECT_URI") or os.getenv("OIDC_REDIRECT_URI") or "http://localhost:8000/auth/callback"
IBM_DISCOVERY_URL = os.getenv("IBM_DISCOVERY_URL") or os.getenv(
    "OIDC_DISCOVERY_URL",
    "https://login.w3.ibm.com/oidc/endpoint/default/.well-known/openid-configuration",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SESSION_SECRET = os.getenv("APP_SESSION_SECRET", "dev-secret-key-change-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cafeteria.db")

# Use mock auth when explicitly set (bypasses Real W3 even when configured)
USE_MOCK_AUTH = os.getenv("USE_MOCK_AUTH", "true").lower() == "true"


def is_w3_configured() -> bool:
    """Check if Real W3 OAuth is properly configured."""
    return bool(IBM_CLIENT_ID and IBM_CLIENT_SECRET and IBM_REDIRECT_URI and IBM_DISCOVERY_URL)
