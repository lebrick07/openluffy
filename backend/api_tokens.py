"""
API Tokens Management
Create, list, revoke, and rotate API tokens for programmatic access
"""
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from passlib.context import CryptContext
import secrets
import os

from database import get_db, APIToken, User, AuditLog
from auth import get_current_user, require_admin

# Password/token hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token prefix for OpenLuffy tokens
TOKEN_PREFIX = "olf_"
TOKEN_ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")  # dev, preprod, prod


# ============================================================================
# SCOPES DEFINITION
# ============================================================================

AVAILABLE_SCOPES = {
    # Customers
    "customers:read": "View customer information",
    "customers:write": "Create and update customers",
    "customers:delete": "Delete customers",
    
    # Deployments
    "deployments:read": "View deployment status",
    "deployments:write": "Deploy and scale applications",
    "deployments:delete": "Delete deployments",
    
    # Secrets & Variables
    "secrets:read": "View secrets and variables",
    "secrets:write": "Create and update secrets",
    "secrets:delete": "Delete secrets",
    
    # Users (admin only)
    "users:read": "View user information",
    "users:write": "Create and update users",
    "users:delete": "Delete users",
    
    # Groups (admin only)
    "groups:read": "View groups",
    "groups:write": "Manage group membership",
    
    # API Tokens
    "tokens:read": "View own API tokens",
    "tokens:write": "Create and revoke own tokens",
    
    # Full access (admin only)
    "admin": "Full administrative access"
}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TokenCreateRequest(BaseModel):
    """Create new API token"""
    name: str = Field(..., min_length=1, max_length=200, description="Friendly name for token")
    scopes: List[str] = Field(..., description="List of permission scopes")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="Token expiry in days (null = never)")


class TokenUpdateRequest(BaseModel):
    """Update token metadata"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TokenResponse(BaseModel):
    """Token metadata (without actual token)"""
    id: int
    name: str
    token_prefix: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[str]
    last_used_at: Optional[str]
    last_used_ip: Optional[str]
    use_count: int
    created_at: str


class TokenCreateResponse(BaseModel):
    """Response when creating token (includes plaintext token)"""
    token: str  # Full plaintext token (shown ONCE)
    token_prefix: str
    metadata: TokenResponse


# ============================================================================
# TOKEN GENERATION & VALIDATION
# ============================================================================

def generate_token() -> tuple[str, str, str]:
    """
    Generate a new API token
    
    Returns:
        (full_token, prefix, hash)
        - full_token: "olf_dev_a8f2d9c3e5f7..." (48 chars total)
        - prefix: "olf_dev_" (for display)
        - hash: bcrypt hash for storage
    """
    # Generate random bytes (32 bytes = 64 hex chars)
    random_part = secrets.token_hex(32)
    
    # Build full token: olf_{env}_{random}
    full_token = f"{TOKEN_PREFIX}{TOKEN_ENVIRONMENT}_{random_part}"
    
    # Prefix for display (first 12 chars)
    prefix = full_token[:12]
    
    # Hash for storage
    token_hash = pwd_context.hash(full_token)
    
    return full_token, prefix, token_hash


def verify_token_hash(plain_token: str, hashed_token: str) -> bool:
    """Verify token against stored hash"""
    return pwd_context.verify(plain_token, hashed_token)


def validate_scopes(scopes: List[str], user: User) -> None:
    """
    Validate that requested scopes are:
    1. Valid scope names
    2. User has permission to request them
    """
    # Check all scopes are valid
    invalid_scopes = [s for s in scopes if s not in AVAILABLE_SCOPES]
    if invalid_scopes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scopes: {', '.join(invalid_scopes)}"
        )
    
    # Non-admins cannot request admin-level scopes
    admin_scopes = {"admin", "users:read", "users:write", "users:delete", "groups:write"}
    if user.role != "admin":
        requested_admin = [s for s in scopes if s in admin_scopes]
        if requested_admin:
            raise HTTPException(
                status_code=403,
                detail=f"Admin role required for scopes: {', '.join(requested_admin)}"
            )


# ============================================================================
# TOKEN AUTHENTICATION MIDDLEWARE
# ============================================================================

async def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Authenticate user via API token (alternative to JWT)
    
    Header: Authorization: Bearer olf_dev_a8f2d9c3...
    
    Returns:
        User object if token is valid, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "").strip()
    
    # Check if it's an API token (starts with olf_)
    if not token.startswith(TOKEN_PREFIX):
        return None
    
    # Find token by checking all active tokens
    # (We can't query by hash directly, must verify each one)
    # In production, consider caching or indexing by prefix
    
    # Get token prefix (first 12 chars)
    prefix = token[:12]
    
    # Query tokens with matching prefix
    potential_tokens = db.query(APIToken).filter(
        APIToken.token_prefix == prefix,
        APIToken.is_active == True
    ).all()
    
    # Verify hash
    for api_token in potential_tokens:
        if verify_token_hash(token, api_token.token_hash):
            # Check expiry
            if api_token.expires_at and api_token.expires_at < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Token expired")
            
            # Update last used
            api_token.last_used_at = datetime.utcnow()
            api_token.use_count += 1
            # Note: We don't have request context here for IP, would need to pass it
            db.commit()
            
            # Get user
            user = db.query(User).filter(User.id == api_token.user_id).first()
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User inactive")
            
            # Store token scopes on user object for later permission checks
            user._token_scopes = api_token.scopes
            
            return user
    
    raise HTTPException(status_code=401, detail="Invalid token")


def require_scope(required_scope: str):
    """
    Dependency to check if current user has required scope
    
    Usage:
        @app.get("/api/v1/customers", dependencies=[Depends(require_scope("customers:read"))])
    """
    async def check_scope(
        current_user: User = Depends(get_current_user)
    ):
        # Check if authenticated via API token
        if hasattr(current_user, '_token_scopes'):
            scopes = current_user._token_scopes
            
            # Admin scope grants everything
            if "admin" in scopes:
                return current_user
            
            # Check specific scope
            if required_scope not in scopes:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required scope: {required_scope}"
                )
        else:
            # JWT authentication - check user role
            if current_user.role != "admin" and required_scope in {
                "users:write", "users:delete", "groups:write", "admin"
            }:
                raise HTTPException(status_code=403, detail="Admin role required")
        
        return current_user
    
    return check_scope


# ============================================================================
# API ENDPOINTS
# ============================================================================

def list_api_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's API tokens
    
    GET /api/v1/tokens
    
    Returns metadata only (not actual tokens)
    """
    tokens = db.query(APIToken).filter(
        APIToken.user_id == current_user.id
    ).order_by(APIToken.created_at.desc()).all()
    
    return [TokenResponse(**token.to_dict()) for token in tokens]


def create_api_token(
    data: TokenCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new API token
    
    POST /api/v1/tokens
    Body: {name, scopes, expires_days?}
    
    Returns plaintext token ONCE (cannot be retrieved again)
    """
    # Validate scopes
    validate_scopes(data.scopes, current_user)
    
    # Generate token
    full_token, prefix, token_hash = generate_token()
    
    # Calculate expiry
    expires_at = None
    if data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_days)
    
    # Create token record
    api_token = APIToken(
        user_id=current_user.id,
        name=data.name,
        token_prefix=prefix,
        token_hash=token_hash,
        scopes=data.scopes,
        expires_at=expires_at
    )
    db.add(api_token)
    db.commit()
    db.refresh(api_token)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="api_token_created",
        resource_type="api_token",
        resource_id=str(api_token.id),
        details={
            "name": data.name,
            "scopes": data.scopes,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    )
    db.add(audit)
    db.commit()
    
    # Return token ONCE
    return TokenCreateResponse(
        token=full_token,
        token_prefix=prefix,
        metadata=TokenResponse(**api_token.to_dict())
    )


def get_api_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get API token details
    
    GET /api/v1/tokens/{token_id}
    """
    token = db.query(APIToken).filter(
        APIToken.id == token_id,
        APIToken.user_id == current_user.id
    ).first()
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return TokenResponse(**token.to_dict())


def update_api_token(
    token_id: int,
    data: TokenUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update API token metadata
    
    PATCH /api/v1/tokens/{token_id}
    Body: {name?, scopes?, is_active?}
    """
    token = db.query(APIToken).filter(
        APIToken.id == token_id,
        APIToken.user_id == current_user.id
    ).first()
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Update fields
    if data.name:
        token.name = data.name
    
    if data.scopes:
        validate_scopes(data.scopes, current_user)
        token.scopes = data.scopes
    
    if data.is_active is not None:
        token.is_active = data.is_active
        if not data.is_active:
            token.revoked_at = datetime.utcnow()
    
    db.commit()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="api_token_updated",
        resource_type="api_token",
        resource_id=str(token_id),
        details=data.dict(exclude_none=True)
    )
    db.add(audit)
    db.commit()
    
    return TokenResponse(**token.to_dict())


def revoke_api_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke API token
    
    DELETE /api/v1/tokens/{token_id}
    
    Marks token as inactive (soft delete)
    """
    token = db.query(APIToken).filter(
        APIToken.id == token_id,
        APIToken.user_id == current_user.id
    ).first()
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token.is_active = False
    token.revoked_at = datetime.utcnow()
    db.commit()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="api_token_revoked",
        resource_type="api_token",
        resource_id=str(token_id),
        details={"name": token.name}
    )
    db.add(audit)
    db.commit()
    
    return {"message": f"Token '{token.name}' revoked successfully"}


def rotate_api_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rotate API token (revoke old, create new with same scopes)
    
    POST /api/v1/tokens/{token_id}/rotate
    
    Returns new token (plaintext shown ONCE)
    """
    # Get existing token
    old_token = db.query(APIToken).filter(
        APIToken.id == token_id,
        APIToken.user_id == current_user.id
    ).first()
    
    if not old_token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Generate new token
    full_token, prefix, token_hash = generate_token()
    
    # Create new token with same scopes
    new_token = APIToken(
        user_id=current_user.id,
        name=f"{old_token.name} (rotated)",
        token_prefix=prefix,
        token_hash=token_hash,
        scopes=old_token.scopes,
        expires_at=old_token.expires_at
    )
    db.add(new_token)
    
    # Revoke old token
    old_token.is_active = False
    old_token.revoked_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_token)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="api_token_rotated",
        resource_type="api_token",
        resource_id=str(token_id),
        details={
            "old_token_id": old_token.id,
            "new_token_id": new_token.id,
            "name": old_token.name
        }
    )
    db.add(audit)
    db.commit()
    
    return TokenCreateResponse(
        token=full_token,
        token_prefix=prefix,
        metadata=TokenResponse(**new_token.to_dict())
    )


def list_available_scopes(
    current_user: User = Depends(get_current_user)
):
    """
    List available scopes for current user
    
    GET /api/v1/tokens/scopes
    """
    # Filter scopes based on user role
    available = {}
    admin_scopes = {"admin", "users:read", "users:write", "users:delete", "groups:write"}
    
    for scope, description in AVAILABLE_SCOPES.items():
        if current_user.role == "admin" or scope not in admin_scopes:
            available[scope] = description
    
    return available
