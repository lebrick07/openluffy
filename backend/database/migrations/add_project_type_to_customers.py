"""
Migration: Add project_type to customers table

This migration adds a project_type column to distinguish between:
- control-plane: OpenLuffy infrastructure (special reserved project)
- customer-project: Regular customer workloads

Date: 2026-03-09
"""

from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker
from database.connection import get_connection_string
from database.models import Base, Customer
from datetime import datetime


def run_migration():
    """Add project_type column and create control-plane project"""
    engine = create_engine(get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔧 Starting migration: add_project_type_to_customers")
        
        # Add project_type column via raw SQL (SQLAlchemy doesn't support ALTER TABLE directly)
        connection = engine.raw_connection()
        cursor = connection.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='customers' AND column_name='project_type'
        """)
        
        if cursor.fetchone() is None:
            print("  Adding project_type column...")
            cursor.execute("""
                ALTER TABLE customers 
                ADD COLUMN project_type VARCHAR(50) DEFAULT 'customer-project' NOT NULL
            """)
            connection.commit()
            print("  ✅ project_type column added")
        else:
            print("  ℹ️  project_type column already exists")
        
        cursor.close()
        connection.close()
        
        # Create or update control-plane project
        control_plane = session.query(Customer).filter(Customer.id == 'control-plane').first()
        
        if not control_plane:
            print("  Creating control-plane project...")
            control_plane = Customer(
                id='control-plane',
                name='Control Plane',
                stack='platform',
                github_repo='lebrick07/openluffy',
                created_from_env='all',  # Special: accessible from all envs
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(control_plane)
            print("  ✅ control-plane project created")
        else:
            print("  ℹ️  control-plane project already exists")
        
        # Set project_type for control-plane
        if control_plane:
            engine.execute("""
                UPDATE customers 
                SET project_type = 'control-plane' 
                WHERE id = 'control-plane'
            """)
            print("  ✅ control-plane project_type set")
        
        # Update existing customers to customer-project type
        result = engine.execute("""
            UPDATE customers 
            SET project_type = 'customer-project' 
            WHERE id != 'control-plane' AND project_type != 'customer-project'
        """)
        if result.rowcount > 0:
            print(f"  ✅ Updated {result.rowcount} customer projects")
        
        session.commit()
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
