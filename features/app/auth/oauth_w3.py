"""W3 IBM SSO OAuth flow - adapted from root app for Real W3ID authentication."""
import secrets
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import (
    IBM_CLIENT_ID,
    IBM_CLIENT_SECRET,
    IBM_DISCOVERY_URL,
    IBM_REDIRECT_URI,
)

# Cache for OIDC discovery document
_oidc_config_cache: Optional[Dict[str, Any]] = None


async def get_oidc_config() -> Dict[str, Any]:
    """Fetch and cache the OIDC discovery document from IBM."""
    global _oidc_config_cache

    if _oidc_config_cache:
        return _oidc_config_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(IBM_DISCOVERY_URL)
            response.raise_for_status()
            _oidc_config_cache = response.json()
            return _oidc_config_cache
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch IBM SSO configuration: {e}",
        ) from e


def generate_state() -> str:
    """Generate a random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


async def get_authorization_url(state: str) -> str:
    """Build the IBM SSO authorization URL."""
    oidc_config = await get_oidc_config()
    auth_endpoint = oidc_config.get("authorization_endpoint")

    if not auth_endpoint:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authorization endpoint not found in OIDC configuration",
        )

    params = {
        "client_id": IBM_CLIENT_ID,
        "redirect_uri": IBM_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{auth_endpoint}?{query}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token and id_token."""
    oidc_config = await get_oidc_config()
    token_endpoint = oidc_config.get("token_endpoint")

    if not token_endpoint:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token endpoint not found in OIDC configuration",
        )

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": IBM_REDIRECT_URI,
        "client_id": IBM_CLIENT_ID,
        "client_secret": IBM_CLIENT_SECRET,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange authorization code for token",
        ) from e


def decode_id_token(id_token: str) -> Dict[str, Any]:
    """Decode IBM-issued ID token. For production, validate signature via JWKS."""
    try:
        decoded = jwt.decode(
            id_token,
            key="",
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_exp": False,
                "verify_at_hash": False,
            },
            algorithms=["RS256"],
        )
        return decoded
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid ID token: {e}",
        ) from e


def extract_user_info(id_token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user info from ID token for features User model (employee_uid, manager_name)."""
    sub = id_token_payload.get("sub")
    name = id_token_payload.get("name") or id_token_payload.get("preferred_username") or ""
    email = id_token_payload.get("email") or f"{sub}@ibm.com"
    # Real W3 token may not include manager; default to Manager 1 (must exist in seed)
    manager_name = "Manager 1"
    return {
        "employee_uid": sub,
        "email": email,
        "name": name,
        "manager_name": manager_name,
    }
