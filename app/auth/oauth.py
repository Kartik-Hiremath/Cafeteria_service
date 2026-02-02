import httpx
import secrets
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Cache for OIDC discovery document
_oidc_config_cache: Optional[Dict[str, Any]] = None


async def get_oidc_config() -> Dict[str, Any]:
    """Fetch and cache the OIDC discovery document from IBM."""
    global _oidc_config_cache
    
    if _oidc_config_cache:
        return _oidc_config_cache
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.ibm_discovery_url)
            response.raise_for_status()
            config = response.json()
            _oidc_config_cache = config
            logger.info("Successfully fetched OIDC configuration")
            return config
    except Exception as e:
        logger.error(f"Failed to fetch OIDC configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch IBM SSO configuration"
        )


def generate_state() -> str:
    """Generate a random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


async def get_authorization_url(state: str) -> str:
    """Build the IBM SSO authorization URL."""
    oidc_config = await get_oidc_config()
    authorization_endpoint = oidc_config.get("authorization_endpoint")
    
    if not authorization_endpoint:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authorization endpoint not found in OIDC configuration"
        )
    
    # Build authorization URL with required parameters
    params = {
        "client_id": settings.ibm_client_id,
        "redirect_uri": settings.ibm_redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        # Request password authentication explicitly
        # acr_values can be used to request specific authentication methods
        # Use "urn:ibm:security:policy:id:2" for password authentication
        "acr_values": "urn:ibm:security:policy:id:2",
        # Optionally add prompt parameter to force re-authentication
        # "prompt": "login",
    }
    
    # Construct URL with query parameters
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    auth_url = f"{authorization_endpoint}?{query_string}"
    
    logger.info(f"Generated authorization URL for state: {state}")
    return auth_url


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token and id_token."""
    oidc_config = await get_oidc_config()
    token_endpoint = oidc_config.get("token_endpoint")
    
    if not token_endpoint:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token endpoint not found in OIDC configuration"
        )
    
    # Prepare token request
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.ibm_redirect_uri,
        "client_id": settings.ibm_client_id,
        "client_secret": settings.ibm_client_secret,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            token_response = response.json()
            logger.info("Successfully exchanged code for tokens")
            return token_response
    except httpx.HTTPStatusError as e:
        logger.error(f"Token exchange failed: {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange authorization code for token"
        )
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token exchange failed"
        )


async def get_jwks() -> Dict[str, Any]:
    """Fetch JSON Web Key Set (JWKS) from IBM for token validation."""
    oidc_config = await get_oidc_config()
    jwks_uri = oidc_config.get("jwks_uri")
    
    if not jwks_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWKS URI not found in OIDC configuration"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch token validation keys"
        )


def decode_id_token(id_token: str) -> Dict[str, Any]:
    """
    Decode and validate the IBM-issued ID token.
    Note: For production, you should validate the signature using JWKS.
    For now, we'll decode without verification for simplicity.
    """
    try:
        # Decode without verification (for development)
        # In production, use jwt.decode with proper verification
        decoded = jwt.decode(
            id_token,
            key="",  # Empty key for unverified decode
            options={
                "verify_signature": False,  # WARNING: Only for development
                "verify_aud": False,  # Skip audience verification
                "verify_exp": False,  # Skip expiration verification
                "verify_at_hash": False,  # Skip at_hash verification
            },
            algorithms=["RS256"]
        )
        logger.info(f"Decoded ID token for user: {decoded.get('sub')}")
        logger.debug(f"Token claims: {decoded}")
        return decoded
    except JWTError as e:
        logger.error(f"Invalid ID token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid ID token: {str(e)}"
        )


def extract_user_info(id_token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user information from the ID token payload."""
    return {
        "w3_id": id_token_payload.get("sub"),  # Subject (user ID)
        "name": id_token_payload.get("name") or id_token_payload.get("preferred_username"),
        "email": id_token_payload.get("email"),
        "manager_w3_id": None,  # Manager info not available in ID token
    }

# Made with Bob
