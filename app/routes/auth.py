from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User
from app.schemas import TokenResponse, UserResponse
from app.auth.oauth import (
    generate_state,
    get_authorization_url,
    exchange_code_for_token,
    decode_id_token,
    extract_user_info
)
from app.auth.jwt import create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory state storage (use Redis in production)
_state_store = {}


@router.get("/login")
async def login():
    """
    Initiate OAuth 2.0 login flow with IBM SSO.
    Redirects user to IBM login page.
    """
    # Generate state for CSRF protection
    state = generate_state()
    _state_store[state] = True
    
    # Get IBM SSO authorization URL
    auth_url = await get_authorization_url(state)
    
    logger.info(f"Redirecting to IBM SSO with state: {state}")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    OAuth callback endpoint. IBM SSO redirects here after authentication.
    Exchanges authorization code for tokens and creates/updates user.
    """
    # Check for errors from IBM SSO
    if error:
        error_msg = error_description or error
        logger.error(f"OAuth error: {error} - {error_description}")
        
        # Redirect to frontend with error message
        redirect_url = f"/?error={error}&error_description={error_description or 'Authentication failed'}"
        return RedirectResponse(url=redirect_url)
    
    # Validate required parameters
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter"
        )
    
    # Verify state to prevent CSRF attacks
    if state not in _state_store:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid state parameter"
        )
    
    # Remove used state
    del _state_store[state]
    
    try:
        # Exchange authorization code for tokens
        token_response = await exchange_code_for_token(code)
        ibm_access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        
        # Log the IBM SSO access token
        logger.info(f"IBM SSO access token received: {ibm_access_token}")
        
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No ID token received from IBM SSO"
            )
        
        # Decode and validate ID token
        id_token_payload = decode_id_token(id_token)
        
        # Extract user information
        user_info = extract_user_info(id_token_payload)
        w3_id = user_info.get("w3_id")
        name = user_info.get("name")
        manager_w3_id = user_info.get("manager_w3_id")
        
        if not w3_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token missing w3_id (sub claim)"
            )
        
        # Create or update user in database
        user = db.query(User).filter(User.w3_id == w3_id).first()
        
        if not user:
            user = User(
                w3_id=w3_id,
                name=name,
                manager_w3_id=manager_w3_id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {w3_id}")
        else:
            # Update manager info if changed
            if manager_w3_id and user.manager_w3_id != manager_w3_id:
                user.manager_w3_id = manager_w3_id
                db.commit()
            logger.info(f"Updated existing user: {w3_id}")
        
        # Generate our own JWT token for the user
        jwt_token = create_access_token(data={"sub": w3_id, "name": name})
        
        # Log successful authentication with JWT token
        logger.info(f"User {w3_id} ({name}) logged in successfully")
        logger.info(f"Generated JWT token: {jwt_token}")
        
        # Redirect to frontend with JWT token
        # The frontend will be served at the root URL
        redirect_url = f"/?token={jwt_token}&w3_id={w3_id}&name={name or ''}"
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/userinfo", response_model=UserResponse)
async def get_user_info(
    w3_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user information by w3_id.
    Used by frontend after successful authentication.
    """
    user = db.query(User).filter(User.w3_id == w3_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# Made with Bob
