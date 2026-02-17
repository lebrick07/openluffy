#!/usr/bin/env python3
"""
Create an admin user for OpenLuffy
Usage: python create_admin_user.py
"""
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, User, AuditLog
from auth_utils import hash_password, generate_random_token


def create_admin_user(
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
    username: str = "admin"
):
    """
    Create an admin user in the database
    
    Args:
        email: Admin email address
        password: Admin password
        first_name: First name (default: "Admin")
        last_name: Last name (default: "User")
        username: Username (default: "admin")
    
    Returns:
        User object if created successfully, None otherwise
    """
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists")
            return None
        
        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password_hash=hash_password(password),
            role='admin',  # Admin role
            is_active=True,
            email_verified=True,  # Auto-verify admin
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.flush()  # Get user ID
        
        # Audit log
        audit = AuditLog(
            user_id=admin_user.id,
            action="admin_user_created",
            resource_type="user",
            resource_id=str(admin_user.id),
            details={"email": admin_user.email, "role": "admin"}
        )
        db.add(audit)
        
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {admin_user.role}")
        print(f"   ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        return None
    finally:
        db.close()


def main():
    """Main function for CLI usage"""
    import getpass
    
    print("=" * 60)
    print("OpenLuffy - Create Admin User")
    print("=" * 60)
    print()
    
    # Get admin details from user input
    email = input("Admin email: ").strip()
    if not email:
        print("❌ Email is required")
        sys.exit(1)
    
    username = input("Username (default: admin): ").strip() or "admin"
    first_name = input("First name (default: Admin): ").strip() or "Admin"
    last_name = input("Last name (default: User): ").strip() or "User"
    
    # Get password securely
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm password: ")
    
    if not password:
        print("❌ Password is required")
        sys.exit(1)
    
    if password != password_confirm:
        print("❌ Passwords do not match")
        sys.exit(1)
    
    # Validate password strength
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        sys.exit(1)
    
    print()
    print("Creating admin user...")
    print()
    
    # Create admin user
    user = create_admin_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        username=username
    )
    
    if user:
        print()
        print("=" * 60)
        print("Admin user created successfully!")
        print("=" * 60)
        print()
        print("You can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: [the password you entered]")
        print()
        print("Login endpoint: POST /api/v1/auth/login")
        print()
    else:
        print()
        print("=" * 60)
        print("Failed to create admin user")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
