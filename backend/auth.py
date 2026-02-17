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

router = APIRouter(prefix="/v1/auth", tags=["authentication"])


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
    Dependency to extract and validate JWT or API token, return current user
    Supports both JWT (standard sessions) and API tokens (programmatic access)
    """
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    # Try API token authentication first (tokens starting with "olf_")
    if token.startswith("olf_"):
        from api_tokens import get_current_user_from_token
        user = await get_current_user_from_token(authorization, db)
        if user:
            return user
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    # Fall back to JWT authentication
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


@router.post("/password-reset/request")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email
    """
    user = db.query(User).filter(User.email == request_data.email).first()
    
    # Always return success even if user doesn't exist (security best practice)
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_random_token()
    user.password_reset_token = reset_token
    user.password_reset_sent_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: Send password reset email
    # For now, we'll just log the token (in production, send via email)
    print(f"Password reset token for {user.email}: {reset_token}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token and set new password
    """
    # Find user with this reset token
    user = db.query(User).filter(
        User.password_reset_token == request_data.token
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token is still valid (24 hours)
    if user.password_reset_sent_at:
        token_age = datetime.utcnow() - user.password_reset_sent_at
        if token_age > timedelta(hours=24):
            raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Validate new password
    is_valid, error = validate_password_strength(request_data.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Update password
    user.password_hash = hash_password(request_data.new_password)
    user.password_reset_token = None
    user.password_reset_sent_at = None
    
    # Revoke all existing sessions for security
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active == True
    ).update({"is_active": False, "revoked_at": datetime.utcnow()})
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="password_reset",
        resource_type="user",
        resource_id=str(user.id)
    )
    db.add(audit)
    
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user
    """
    # Verify current password
    if not verify_password(request_data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    is_valid, error = validate_password_strength(request_data.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Update password
    current_user.password_hash = hash_password(request_data.new_password)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="password_changed",
        resource_type="user",
        resource_id=str(current_user.id)
    )
    db.add(audit)
    
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify email address with token
    """
    user = db.query(User).filter(
        User.email_verification_token == token
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    # Check if token is still valid (7 days)
    if user.email_verification_sent_at:
        token_age = datetime.utcnow() - user.email_verification_sent_at
        if token_age > timedelta(days=7):
            raise HTTPException(status_code=400, detail="Verification token has expired")
    
    # Mark email as verified
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_sent_at = None
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="email_verified",
        resource_type="user",
        resource_id=str(user.id)
    )
    db.add(audit)
    
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resend email verification link
    """
    if current_user.email_verified:
        return {"message": "Email already verified"}
    
    # Generate new verification token
    verification_token = generate_random_token()
    current_user.email_verification_token = verification_token
    current_user.email_verification_sent_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: Send verification email
    # For now, we'll just log the token (in production, send via email)
    print(f"Email verification token for {current_user.email}: {verification_token}")
    
    return {"message": "Verification email sent"}


@router.post("/bootstrap/create-admin")
async def bootstrap_create_admin(
    request_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Bootstrap endpoint to create the first admin user
    Only works if no admin users exist in the system
    """
    # Check if any admin user already exists
    existing_admin = db.query(User).filter(User.role == 'admin').first()
    if existing_admin:
        raise HTTPException(
            status_code=403, 
            detail="Admin user already exists. Use normal registration for additional users."
        )
    
    # Validate password strength
    is_valid, error = validate_password_strength(request_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create admin user
    admin_user = User(
        email=request_data.email,
        username=request_data.username or request_data.email.split('@')[0],
        first_name=request_data.first_name or "Admin",
        last_name=request_data.last_name or "User",
        password_hash=hash_password(request_data.password),
        role='admin',  # Admin role
        is_active=True,
        email_verified=True,  # Auto-verify bootstrap admin
        created_at=datetime.utcnow()
    )
    
    db.add(admin_user)
    db.flush()
    
    # Audit log
    audit = AuditLog(
        user_id=admin_user.id,
        action="admin_user_bootstrapped",
        resource_type="user",
        resource_id=str(admin_user.id),
        details={"email": admin_user.email, "role": "admin"}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(admin_user)
    
    return {
        "message": "Admin user created successfully",
        "user": admin_user.to_dict()
    }


# ============================================================================
# USER MANAGEMENT ENDPOINTS (Admin only)
# ============================================================================

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = "viewer"  # admin | viewer
    username: Optional[str] = None


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all users with their groups and customer access (admin only)
    """
    from database import UserGroup, UserCustomerAccess, Group
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    result = []
    for user in users:
        # Get user's groups
        groups = db.query(Group).join(UserGroup).filter(UserGroup.user_id == user.id).all()
        
        # Get user's direct customer access
        customer_access = db.query(UserCustomerAccess).filter(UserCustomerAccess.user_id == user.id).all()
        
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "groups": [{"id": g.id, "name": g.name} for g in groups],
            "customer_access": [access.customer_id for access in customer_access]
        }
        result.append(user_dict)
    
    return {
        "users": result,
        "total": len(result)
    }


@router.post("/users")
async def create_user(
    request_data: CreateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate role
    if request_data.role not in ["admin", "viewer"]:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'viewer'")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Validate password strength
    if not validate_password_strength(request_data.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with uppercase, lowercase, and number"
        )
    
    # Generate username if not provided
    username = request_data.username or request_data.email.split('@')[0]
    
    # Check username uniqueness
    if db.query(User).filter(User.username == username).first():
        # Append number to make it unique
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
    
    # Create user
    new_user = User(
        email=request_data.email,
        username=username,
        password_hash=hash_password(request_data.password),
        first_name=request_data.first_name,
        last_name=request_data.last_name,
        role=request_data.role,
        is_active=True,
        email_verified=True  # Admin-created users are auto-verified
    )
    
    db.add(new_user)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="user.create",
        resource_type="user",
        resource_id=str(new_user.id),
        details={"email": new_user.email, "role": new_user.role, "created_by": current_user.email}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User created successfully",
        "user": new_user.to_dict()
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    request_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user (admin only)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if request_data.first_name is not None:
        user.first_name = request_data.first_name
    if request_data.last_name is not None:
        user.last_name = request_data.last_name
    if request_data.role is not None:
        if request_data.role not in ["admin", "viewer"]:
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'viewer'")
        user.role = request_data.role
    if request_data.is_active is not None:
        user.is_active = request_data.is_active
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="user.update",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "updated_by": current_user.email}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "User updated successfully",
        "user": user.to_dict()
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Prevent deleting the last admin
    if user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete the only admin user. Create another admin first."
            )
    
    # Audit log before deletion
    audit = AuditLog(
        user_id=current_user.id,
        action="user.delete",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "deleted_by": current_user.email}
    )
    db.add(audit)
    
    # Delete user's sessions
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {
        "message": "User deleted successfully",
        "deleted_user": {
            "id": user_id,
            "email": user.email
        }
    }


# ============================================================================
# GROUP MANAGEMENT ENDPOINTS (Admin only)
# ============================================================================

class CreateGroupRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("/groups")
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all groups (admin only)
    """
    from database import Group, UserGroup
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    groups = db.query(Group).order_by(Group.name).all()
    
    result = []
    for group in groups:
        # Count users in group
        user_count = db.query(UserGroup).filter(UserGroup.group_id == group.id).count()
        
        group_dict = group.to_dict()
        group_dict['user_count'] = user_count
        result.append(group_dict)
    
    return {
        "groups": result,
        "total": len(result)
    }


@router.post("/groups")
async def create_group(
    request_data: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new group (admin only)
    """
    from database import Group
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if group already exists
    existing = db.query(Group).filter(Group.name == request_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group with this name already exists")
    
    # Create group
    new_group = Group(
        name=request_data.name,
        description=request_data.description
    )
    
    db.add(new_group)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="group.create",
        resource_type="group",
        resource_id=str(new_group.id),
        details={"name": new_group.name}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(new_group)
    
    return {
        "message": "Group created successfully",
        "group": new_group.to_dict()
    }


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a group (admin only)
    """
    from database import Group, UserGroup, GroupCustomerAccess
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Audit log before deletion
    audit = AuditLog(
        user_id=current_user.id,
        action="group.delete",
        resource_type="group",
        resource_id=str(group.id),
        details={"name": group.name}
    )
    db.add(audit)
    
    # Delete associations
    db.query(UserGroup).filter(UserGroup.group_id == group_id).delete()
    db.query(GroupCustomerAccess).filter(GroupCustomerAccess.group_id == group_id).delete()
    
    # Delete group
    db.delete(group)
    db.commit()
    
    return {
        "message": "Group deleted successfully",
        "deleted_group": {
            "id": group_id,
            "name": group.name
        }
    }


@router.post("/users/{user_id}/groups/{group_id}")
async def add_user_to_group(
    user_id: int,
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add user to group (admin only)
    """
    from database import Group, UserGroup
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if already member
    existing = db.query(UserGroup).filter(
        UserGroup.user_id == user_id,
        UserGroup.group_id == group_id
    ).first()
    
    if existing:
        return {"message": "User already in group"}
    
    # Add membership
    membership = UserGroup(user_id=user_id, group_id=group_id)
    db.add(membership)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="user.add_to_group",
        resource_type="user",
        resource_id=str(user.id),
        details={"group": group.name}
    )
    db.add(audit)
    
    db.commit()
    
    return {"message": "User added to group"}


@router.delete("/users/{user_id}/groups/{group_id}")
async def remove_user_from_group(
    user_id: int,
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove user from group (admin only)
    """
    from database import Group, UserGroup
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    membership = db.query(UserGroup).filter(
        UserGroup.user_id == user_id,
        UserGroup.group_id == group_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="User not in this group")
    
    group = db.query(Group).filter(Group.id == group_id).first()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="user.remove_from_group",
        resource_type="user",
        resource_id=str(user_id),
        details={"group": group.name if group else str(group_id)}
    )
    db.add(audit)
    
    db.delete(membership)
    db.commit()
    
    return {"message": "User removed from group"}


@router.post("/users/{user_id}/customers/{customer_id}")
async def grant_customer_access(
    user_id: int,
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Grant user access to specific customer (admin only)
    """
    from database import UserCustomerAccess, Customer
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if already granted
    existing = db.query(UserCustomerAccess).filter(
        UserCustomerAccess.user_id == user_id,
        UserCustomerAccess.customer_id == customer_id
    ).first()
    
    if existing:
        return {"message": "Access already granted"}
    
    # Grant access
    access = UserCustomerAccess(user_id=user_id, customer_id=customer_id)
    db.add(access)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="user.grant_customer_access",
        resource_type="user",
        resource_id=str(user.id),
        details={"customer": customer_id}
    )
    db.add(audit)
    
    db.commit()
    
    return {"message": "Customer access granted"}


@router.delete("/users/{user_id}/customers/{customer_id}")
async def revoke_customer_access(
    user_id: int,
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke user access to specific customer (admin only)
    """
    from database import UserCustomerAccess
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    access = db.query(UserCustomerAccess).filter(
        UserCustomerAccess.user_id == user_id,
        UserCustomerAccess.customer_id == customer_id
    ).first()
    
    if not access:
        raise HTTPException(status_code=404, detail="Access not found")
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="user.revoke_customer_access",
        resource_type="user",
        resource_id=str(user_id),
        details={"customer": customer_id}
    )
    db.add(audit)
    
    db.delete(access)
    db.commit()
    
    return {"message": "Customer access revoked"}
