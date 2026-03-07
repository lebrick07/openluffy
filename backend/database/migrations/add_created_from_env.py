"""
Migration: Add created_from_env column to customers table

This column tracks which OpenLuffy environment (dev/preprod/prod) created the customer.
Allows proper customer isolation across OpenLuffy deployments.
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def run_migration():
    """Add created_from_env column to customers table"""
    
    # Get database connection from environment
    # Derive host from DATABASE_URL if available, or use default
    database_url = os.getenv('DATABASE_URL', '')
    if database_url and '@' in database_url:
        # Extract host from DATABASE_URL: postgresql://user:pass@host:port/db
        host_part = database_url.split('@')[1].split('/')[0]
        db_host = host_part.split(':')[0] if ':' in host_part else host_part
    else:
        # Fall back to individual env vars
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
    
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'openluffy')
    db_user = os.getenv('POSTGRES_USER', 'openluffy')
    db_password = os.getenv('POSTGRES_PASSWORD', 'openluffy123')
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("ℹ️  Checking if migration is needed...")
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='customers' AND column_name='created_from_env'
        """)
        
        if cursor.fetchone():
            print("✅ Column 'created_from_env' already exists, skipping migration")
            return
        
        print("🔨 Adding 'created_from_env' column to customers table...")
        
        # Add the column with default value 'dev'
        cursor.execute("""
            ALTER TABLE customers 
            ADD COLUMN created_from_env VARCHAR(20) NOT NULL DEFAULT 'dev'
        """)
        
        print("✅ Migration completed successfully")
        
        # Log current environment
        current_env = os.getenv('OPENLUFFY_ENV', 'dev')
        print(f"ℹ️  Current environment: {current_env}")
        print(f"ℹ️  Future customers will be tagged with: created_from_env='{current_env}'")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == '__main__':
    run_migration()
