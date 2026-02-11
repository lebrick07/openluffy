"""
Initialize GitHub integrations for all customers on startup
Run this once to configure GitHub integrations if they don't exist
"""
import os
import httpx
from database import get_db, Customer, Integration
from sqlalchemy.orm import Session

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_ORG = os.getenv('GITHUB_ORG', 'lebrick07')

# Customer → GitHub repo mapping
CUSTOMER_REPOS = {
    'acme-corp': {'name': 'Acme Corp', 'repo': 'acme-corp-api', 'stack': 'nodejs'},
    'openluffy': {'name': 'OpenLuffy', 'repo': 'openluffy', 'stack': 'nodejs'},
    'philly-cheese-corp': {'name': 'Philly Cheese Corp', 'repo': 'philly-cheese-corp', 'stack': 'nodejs'},
    'techstart': {'name': 'Techstart', 'repo': 'techstart-webapp', 'stack': 'python'},
    'widgetco': {'name': 'Widgetco', 'repo': 'widgetco-api', 'stack': 'golang'},
}

def init_github_integrations(db: Session) -> None:
    """Initialize GitHub integrations for all customers if not already configured"""
    
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN not set - skipping GitHub integration initialization")
        return
    
    print("🔧 Initializing GitHub integrations...")
    
    for customer_id, info in CUSTOMER_REPOS.items():
        try:
            # Ensure customer exists in database first
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            
            if not customer:
                # Create customer record
                customer = Customer(
                    id=customer_id,
                    name=info['name'],
                    stack=info['stack'],
                    github_repo=f"{GITHUB_ORG}/{info['repo']}"
                )
                db.add(customer)
                db.commit()
                print(f"   ✅ Created customer: {customer_id}")
            
            # Check if integration already exists
            existing = db.query(Integration).filter(
                Integration.customer_id == customer_id,
                Integration.type == 'github'
            ).first()
            
            if existing:
                print(f"   ✓ {customer_id} → GitHub already configured")
                continue
            
            # Create new GitHub integration
            config = {
                'org': GITHUB_ORG,
                'repo': info['repo'],
                'token': GITHUB_TOKEN,
                'branch': 'main',
                'enabled': True
            }
            
            integration = Integration(
                customer_id=customer_id,
                type='github',
                config=config
            )
            db.add(integration)
            db.commit()
            
            print(f"   ✅ {customer_id} → {GITHUB_ORG}/{info['repo']} configured")
            
        except Exception as e:
            print(f"   ❌ Failed to configure {customer_id}: {e}")
            db.rollback()
    
    print("✅ GitHub integrations initialization complete")

if __name__ == '__main__':
    # For manual testing
    from database import SessionLocal
    db = SessionLocal()
    try:
        init_github_integrations(db)
    finally:
        db.close()
