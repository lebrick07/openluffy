#!/bin/bash
# OpenLuffy Database Backup Script
# Backs up all PostgreSQL databases to /mnt/openluffy-backups

set -e

BACKUP_DIR="/mnt/openluffy-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "🔄 Starting OpenLuffy database backups..."

# Backup dev
echo "Backing up openluffy-dev..."
kubectl exec -n openluffy-dev deployment/openluffy-dev-postgres -- \
  pg_dump -U openluffy openluffy | gzip > "$BACKUP_DIR/dev_${TIMESTAMP}.sql.gz"

# Backup preprod
echo "Backing up openluffy-preprod..."
kubectl exec -n openluffy-preprod deployment/openluffy-preprod-postgres -- \
  pg_dump -U openluffy openluffy | gzip > "$BACKUP_DIR/preprod_${TIMESTAMP}.sql.gz"

# Backup prod (if exists)
if kubectl get namespace openluffy-prod >/dev/null 2>&1; then
  echo "Backing up openluffy-prod..."
  kubectl exec -n openluffy-prod deployment/openluffy-prod-postgres -- \
    pg_dump -U openluffy openluffy | gzip > "$BACKUP_DIR/prod_${TIMESTAMP}.sql.gz"
fi

echo "✅ Backups complete!"
echo ""
echo "Backup files:"
ls -lh "$BACKUP_DIR"/*_${TIMESTAMP}.sql.gz

# Keep only last 7 days of backups
echo ""
echo "🧹 Cleaning old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo ""
echo "✅ Done! Backups stored in: $BACKUP_DIR"
