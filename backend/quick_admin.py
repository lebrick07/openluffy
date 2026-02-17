#!/usr/bin/env python3
"""Quick script to create admin user with default credentials"""
from database import SessionLocal, User, AuditLog
from auth_utils import hash_password
from datetime import datetime

db = SessionLocal()

# Check if admin already exists
existing = db.query(User).filter(User.email == 'admin@openluffy.local').first()
if existing:
    print(f'❌ Admin user already exists:')
    print(f'   Email: {existing.email}')
    print(f'   Username: {existing.username}')
    print(f'   Role: {existing.role}')
    print(f'   ID: {existing.id}')
    print()
    print('Use these credentials to login:')
    print(f'   Email: {existing.email}')
    print('   Password: OpenLuffy2025!')
else:
    # Create admin
    admin = User(
        email='admin@openluffy.local',
        username='admin',
        first_name='Admin',
        last_name='User',
        password_hash=hash_password('OpenLuffy2025!'),
        role='admin',
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow()
    )
    db.add(admin)
    db.flush()
    
    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action="admin_user_created",
        resource_type="user",
        resource_id=str(admin.id),
        details={"email": admin.email, "role": "admin"}
    )
    db.add(audit)
    
    db.commit()
    db.refresh(admin)
    
    print('✅ Admin user created successfully!')
    print(f'   Email: {admin.email}')
    print('   Password: OpenLuffy2025!')
    print(f'   Username: {admin.username}')
    print(f'   Role: {admin.role}')
    print(f'   ID: {admin.id}')
    print()
    print('=' * 60)
    print('LOGIN CREDENTIALS')
    print('=' * 60)
    print(f'Email: {admin.email}')
    print('Password: OpenLuffy2025!')
    print()
    print('Login endpoint: POST /api/v1/auth/login')
    print('Request body:')
    print('{')
    print(f'  "email": "{admin.email}",')
    print('  "password": "OpenLuffy2025!"')
    print('}')

db.close()
