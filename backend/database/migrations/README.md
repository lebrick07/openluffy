# Database Migrations

This directory contains database migration scripts for OpenLuffy.

## Running Migrations

Migrations run automatically when the backend starts if the `RUN_MIGRATIONS` environment variable is set.

### Automatic (Recommended)

Set environment variable in your deployment:
```yaml
env:
  - name: RUN_MIGRATIONS
    value: "true"
```

### Manual

Run migrations directly:
```bash
cd backend/database/migrations
python add_created_from_env.py
```

## Migration History

### 2026-03-07: Add `created_from_env` column

**Purpose:** Customer isolation across OpenLuffy environments

**What it does:**
- Adds `created_from_env` column to `customers` table
- Tags customers with the OpenLuffy environment that created them (dev/preprod/prod)
- Enables proper filtering: dev.openluffy.local only shows customers created from dev

**Files:**
- `add_created_from_env.py`

**SQL:**
```sql
ALTER TABLE customers 
ADD COLUMN created_from_env VARCHAR(20) NOT NULL DEFAULT 'dev';
```

**Backward compatible:** Yes (uses DEFAULT 'dev' for existing rows)
