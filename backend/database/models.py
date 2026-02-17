"""
Database models for OpenLuffy
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Customer(Base):
    """Customer entity"""
    __tablename__ = 'customers'
    
    id = Column(String(100), primary_key=True)  # customer-id (slug)
    name = Column(String(200), nullable=False)  # Display name
    stack = Column(String(50), nullable=False)  # nodejs, python, go
    github_repo = Column(String(200))  # org/repo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integrations = relationship("Integration", back_populates="customer", cascade="all, delete-orphan")
    provisioning_steps = relationship("ProvisioningStep", back_populates="customer", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'stack': self.stack,
            'github_repo': self.github_repo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Integration(Base):
    """Customer integrations (GitHub, ArgoCD, AWS, etc.)"""
    __tablename__ = 'integrations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(100), ForeignKey('customers.id'), nullable=False)
    type = Column(String(50), nullable=False)  # github, argocd, aws, slack
    config = Column(JSON, nullable=False)  # Encrypted/masked config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="integrations")
    
    def to_dict(self, mask_secrets=True):
        config_copy = self.config.copy()
        if mask_secrets and 'token' in config_copy:
            config_copy['token'] = '***'
        if mask_secrets and 'password' in config_copy:
            config_copy['password'] = '***'
        
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'type': self.type,
            'config': config_copy,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProvisioningStep(Base):
    """Track customer provisioning progress (for AWS EKS-style status view)"""
    __tablename__ = 'provisioning_steps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(100), ForeignKey('customers.id'), nullable=False)
    step = Column(String(100), nullable=False)  # repo_created, namespaces_created, argocd_synced, etc.
    status = Column(String(20), nullable=False)  # pending, running, success, error
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="provisioning_steps")
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'step': self.step,
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class User(Base):
    """User accounts for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identity
    email = Column(String(200), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True)  # Optional display name
    
    # Password authentication
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Permissions
    role = Column(String(20), default='viewer')  # admin, editor, viewer
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(64), nullable=True, index=True)
    email_verification_sent_at = Column(DateTime, nullable=True)
    
    # Password reset
    password_reset_token = Column(String(64), nullable=True, index=True)
    password_reset_sent_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    last_activity = Column(DateTime)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        if include_sensitive:
            data['email_verification_token'] = self.email_verification_token
            data['password_reset_token'] = self.password_reset_token
        return data


class UserSession(Base):
    """User sessions for authentication"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Session tracking
    session_token = Column(String(64), unique=True, nullable=False, index=True)  # JWT jti
    refresh_token = Column(String(64), unique=True, nullable=True, index=True)
    
    # Expiry
    expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=True)
    
    # Device/context
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # IPv4 or IPv6
    device_name = Column(String(100))  # "Chrome on Mac", "iOS App", etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_name': self.device_name,
            'ip_address': self.ip_address,
            'is_active': self.is_active,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class AuditLog(Base):
    """Audit trail for all actions"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)  # create_customer, promote_to_prod, etc.
    resource_type = Column(String(50))  # customer, deployment, integration
    resource_id = Column(String(200))
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
