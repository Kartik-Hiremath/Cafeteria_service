"""Authentication routes: Real W3ID (IBM SSO) and Dummy W3ID (demo with managers/employees)."""
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from app.config import (
    FRONTEND_URL,
    IBM_CLIENT_ID,
    IBM_CLIENT_SECRET,
    IBM_DISCOVERY_URL,
    IBM_REDIRECT_URI,
    USE_MOCK_AUTH,
    is_w3_configured,
)
from app.database import get_db
from app.models import Manager, User
from app.schemas import UserResponse

from app.auth.oauth_w3 import (
    exchange_code_for_token,
    extract_user_info,
    decode_id_token,
    generate_state,
    get_authorization_url,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# State store for W3 OAuth CSRF protection
_state_store: dict = {}

# Authlib OAuth (for fallback - uses OIDC_* or IBM_* via env)
oauth = OAuth()
oauth_initialized = False


def _get_oauth_client():
    """Get or register Authlib OAuth client (used when W3 custom flow not used)."""
    global oauth_initialized
    if not oauth_initialized:
        missing = [k for k in ["OIDC_DISCOVERY_URL", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET"]
                   if not (IBM_DISCOVERY_URL and IBM_CLIENT_ID and IBM_CLIENT_SECRET)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OIDC configuration missing: {', '.join(missing)}",
            )
        oauth.register(
            name="w3id",
            server_metadata_url=IBM_DISCOVERY_URL,
            client_id=IBM_CLIENT_ID,
            client_secret=IBM_CLIENT_SECRET,
            client_kwargs={"scope": "openid profile email"},
        )
        oauth_initialized = True
    return oauth.w3id


def _create_or_update_user(
    db: Session,
    employee_uid: str,
    email: str,
    first_name: str,
    last_name: str,
    manager_name: str,
) -> User:
    """Create or update user in database."""
    user = db.query(User).filter(User.employee_uid == employee_uid).first()
    if not user:
        user = User(
            employee_uid=employee_uid,
            email=email,
            first_name=first_name,
            last_name=last_name,
            manager_name=manager_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.email = email
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.manager_name = manager_name
        db.commit()
        db.refresh(user)
    return user


@router.get("/login", summary="Initiate Login")
async def login(
    request: Request,
    mode: Optional[str] = None,
    manager_name: Optional[str] = None,
    employee_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Two W3ID options:
    - **Real W3ID**: No params -> redirects to IBM SSO
    - **Dummy W3ID**: mode=dummy, manager_name, employee_id -> creates session, redirects to frontend
    """
    # Validate employee_id length
    if employee_id and len(employee_id) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID must be 50 characters or less",
        )

    # --- Dummy W3ID flow ---
    if mode == "dummy" and manager_name and employee_id:
        # Ensure manager exists
        manager = db.query(Manager).filter(Manager.manager_name == manager_name).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Manager '{manager_name}' not found. Run seed first.",
            )
        # Create or update user
        name_parts = (manager_name + " " + employee_id).split()
        first = name_parts[0] if name_parts else "Employee"
        last = name_parts[-1] if len(name_parts) > 1 else employee_id
        user = _create_or_update_user(
            db=db,
            employee_uid=f"dummy_{manager_name}_{employee_id}".replace(" ", "_"),
            email=f"{employee_id}@demo.ibm.com",
            first_name=first,
            last_name=last,
            manager_name=manager_name,
        )
        request.session["user_id"] = user.id
        request.session["employee_uid"] = user.employee_uid
        request.session["email"] = user.email
        return RedirectResponse(url=FRONTEND_URL)

    # --- Real W3ID flow ---
    # If USE_MOCK_AUTH and manager/employee provided via session, use authlib mock path
    if USE_MOCK_AUTH and (manager_name or request.session.get("selected_manager_name")):
        request.session["selected_manager_name"] = manager_name or request.session.get("selected_manager_name")
        request.session["selected_employee_id"] = employee_id or request.session.get("selected_employee_id")
        mock_user = {
            "sub": employee_id or "mock_123",
            "email": f"employee{employee_id or 'mock'}@ibm.com",
            "name": f"Employee {employee_id or 'mock'}",
            "given_name": "Employee",
            "family_name": employee_id or "mock",
            "manager_name": manager_name or "Manager 1",
        }
        request.session["mock_user"] = mock_user
        request.session["nonce"] = secrets.token_urlsafe(32)
        return RedirectResponse(url=f"{IBM_REDIRECT_URI}?code=mock_code&state=mock_state")

    # Real W3: redirect to IBM SSO using custom oauth_w3 flow
    if is_w3_configured():
        state = generate_state()
        _state_store[state] = True
        auth_url = await get_authorization_url(state)
        return RedirectResponse(url=auth_url)

    # Fallback: use authlib if configured
    try:
        client = _get_oauth_client()
        nonce = secrets.token_urlsafe(32)
        request.session["nonce"] = nonce
        return await client.authorize_redirect(request, IBM_REDIRECT_URI, nonce=nonce)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"W3 login not configured. Set IBM_* env vars. Error: {e}",
        ) from e


@router.get("/callback", summary="OAuth Callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Handles:
    - Real W3: code + state from IBM SSO
    - Dummy via mock: mock_user in session, code=mock_code
    """
    # Error from IBM
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}?error={error}&error_description={error_description or error}"
        )

    # --- Dummy mock callback ---
    mock_user = request.session.get("mock_user")
    if mock_user:
        user_info = mock_user
        selected_manager = request.session.get("selected_manager_name")
        selected_employee = request.session.get("selected_employee_id")
        if selected_manager and selected_employee:
            manager_name = selected_manager
            sub = selected_employee
            email = f"employee{sub}@ibm.com"
            name = f"Employee {sub}"
            given_name, family_name = "Employee", sub
        else:
            sub = user_info.get("sub")
            email = user_info.get("email", f"{sub}@ibm.com")
            name = user_info.get("name", "")
            given_name = user_info.get("given_name", "")
            family_name = user_info.get("family_name", "")
            manager_name = user_info.get("manager_name", "Manager 1")

        if not sub:
            raise HTTPException(status_code=400, detail="Missing user identifier")

        user = _create_or_update_user(
            db=db,
            employee_uid=sub,
            email=email,
            first_name=given_name or (name.split()[0] if name else "User"),
            last_name=family_name or (name.split()[-1] if name and len(name.split()) > 1 else sub),
            manager_name=manager_name,
        )
        request.session["user_id"] = user.id
        request.session["employee_uid"] = user.employee_uid
        request.session["email"] = user.email
        request.session.pop("mock_user", None)
        request.session.pop("nonce", None)
        request.session.pop("selected_manager_name", None)
        request.session.pop("selected_employee_id", None)
        return RedirectResponse(url=FRONTEND_URL)

    # --- Real W3 callback ---
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter",
        )

    if state not in _state_store:
        raise HTTPException(status_code=401, detail="Invalid state parameter")
    del _state_store[state]

    try:
        token_response = await exchange_code_for_token(code)
        id_token = token_response.get("id_token")
        if not id_token:
            raise HTTPException(status_code=401, detail="No ID token received from IBM SSO")

        payload = decode_id_token(id_token)
        info = extract_user_info(payload)

        user = _create_or_update_user(
            db=db,
            employee_uid=info["employee_uid"],
            email=info["email"],
            first_name=info["name"].split()[0] if info["name"] else "User",
            last_name=info["name"].split()[-1] if info["name"] and len(info["name"].split()) > 1 else info["employee_uid"],
            manager_name=info["manager_name"],
        )
        request.session["user_id"] = user.id
        request.session["employee_uid"] = user.employee_uid
        request.session["email"] = user.email
        return RedirectResponse(url=FRONTEND_URL)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {e}",
        ) from e


@router.get("/me", response_model=UserResponse, summary="Get Current User")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Returns the currently authenticated user from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/manager-balance", summary="Get Manager Balance")
def get_manager_balance(request: Request, db: Session = Depends(get_db)):
    """Get manager balance for current user."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.manager_name:
        raise HTTPException(status_code=404, detail="User or manager not found")

    manager = db.query(Manager).filter(Manager.manager_name == user.manager_name).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    return {
        "manager_name": manager.manager_name,
        "balance": float(manager.balance),
    }


@router.get("/managers", summary="Get All Managers")
def get_all_managers(db: Session = Depends(get_db)):
    """Returns list of all managers with balances (for Dummy W3ID selection)."""
    managers = db.query(Manager).order_by(Manager.manager_name).all()
    return [{"name": m.manager_name, "balance": float(m.balance)} for m in managers]


@router.post("/logout", summary="Logout")
async def logout(request: Request):
    """Clear session."""
    request.session.clear()
    return {"message": "Logged out successfully"}


@router.get("/debug", summary="Debug Configuration")
async def debug_config():
    """Returns auth configuration status (secrets masked)."""
    return {
        "OIDC_DISCOVERY_URL": IBM_DISCOVERY_URL,
        "OIDC_CLIENT_ID": IBM_CLIENT_ID,
        "OIDC_CLIENT_SECRET": "***" + (IBM_CLIENT_SECRET[-4:] if IBM_CLIENT_SECRET else "MISSING"),
        "OIDC_REDIRECT_URI": IBM_REDIRECT_URI,
        "FRONTEND_URL": FRONTEND_URL,
        "USE_MOCK_AUTH": USE_MOCK_AUTH,
        "is_w3_configured": is_w3_configured(),
    }
