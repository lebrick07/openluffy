"""
Authentication endpoints for OpenLuffy
Handles user registration, login, logout, token refresh, password reset, etc.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import secrets

from database import get_db, User, UserSession, AuditLog
from auth_utils import (
    hash_password, 
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_random_token,
    validate_password_strength,
    extract_bearer_token,
    ACCESS_TOKEN_EXPIRE_HOURS,
    REFRESH_TOKEN_EXPIRE_DAYS
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# Dependency to get current user from JWT
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to extract and validate JWT token, return current user
    """
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Check if session is still valid
    session_token = payload.get("jti")
    if session_token:
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            raise HTTPException(status_code=401, detail="Session expired or revoked")
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        db.commit()
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")
    
    # Update user last activity
    user.last_activity = datetime.utcnow()
    db.commit()
    
    return user


@router.post("/register", response_model=TokenResponse)
async def register(
    request_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password
    """
    # Validate password strength
    is_valid, error = validate_password_strength(request_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username already exists (if provided)
    if request_data.username:
        existing_username = db.query(User).filter(User.username == request_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user = User(
        email=request_data.email,
        username=request_data.username,
        first_name=request_data.first_name,
        last_name=request_data.last_name,
        password_hash=hash_password(request_data.password),
        role='viewer',  # Default role
        is_active=True,
        email_verified=False,  # Will be verified later
        email_verification_token=generate_random_token(),
        email_verification_sent_at=datetime.utcnow()
    )
    
    db.add(user)
    db.flush()  # Get user ID
    
    # Create session
    session_token = generate_random_token()
    refresh_token_str = generate_random_token()
    
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        refresh_token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        refresh_expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        device_name=request.headers.get("user-agent", "Unknown")[:100]
    )
    
    db.add(session)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="user_registered",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(user)
    
    # Create JWT tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "jti": session_token
    })
    
    refresh_token = create_refresh_token({
        "sub": str(user.id),
        "jti": refresh_token_str
    })
    
    # TODO: Send verification email
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user=user.to_dict()
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    """
    # Find user
    user = db.query(User).filter(User.email == request_data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(request_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Create session
    session_token = generate_random_token()
    refresh_token_str = generate_random_token()
    
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        refresh_token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        refresh_expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        device_name=request.headers.get("user-agent", "Unknown")[:100]
    )
    
    db.add(session)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=str(user.id),
        details={"ip": request.client.host if request.client else None}
    )
    db.add(audit)
    
    db.commit()
    
    # Create JWT tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "jti": session_token
    })
    
    refresh_token = create_refresh_token({
        "sub": str(user.id),
        "jti": refresh_token_str
    })
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user=user.to_dict()
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Logout user and revoke current session
    """
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session_token = payload.get("jti")
    if session_token:
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            db.commit()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="user_logout",
        resource_type="user",
        resource_id=str(current_user.id)
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request_data: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    payload = decode_token(request_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    refresh_jti = payload.get("jti")
    
    if not user_id or not refresh_jti:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Check if refresh token session exists and is valid
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_jti,
        UserSession.is_active == True,
        UserSession.refresh_expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")
    
    # Get user
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    
    # Create new session tokens
    new_session_token = generate_random_token()
    new_refresh_token = generate_random_token()
    
    # Update existing session
    session.session_token = new_session_token
    session.refresh_token = new_refresh_token
    session.expires_at = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    session.refresh_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    session.last_activity = datetime.utcnow()
    
    db.commit()
    
    # Create new JWT tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "jti": new_session_token
    })
    
    refresh_token_jwt = create_refresh_token({
        "sub": str(user.id),
        "jti": new_refresh_token
    })
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_jwt,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user=user.to_dict()
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return current_user.to_dict()


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all active sessions for current user
    """
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).all()
    
    return [s.to_dict() for s in sessions]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session
    """
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    session.revoked_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Session revoked successfully"}


# TODO: Implement password reset, email verification, change password
# These will be added in the next iteration
