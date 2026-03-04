#!/bin/bash
# OpenLuffy Database Restore Script
# Restores a database from backup

set -e

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <environment> <backup-file>"
  echo ""
  echo "Example:"
  echo "  $0 dev /mnt/openluffy-backups/dev_20260304_041500.sql.gz"
  echo ""
  echo "Environments: dev, preprod, prod"
  exit 1
fi

ENV=$1
BACKUP_FILE=$2

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

NAMESPACE="openluffy-${ENV}"

echo "⚠️  WARNING: This will REPLACE all data in $NAMESPACE!"
echo ""
echo "Environment: $ENV"
echo "Namespace: $NAMESPACE"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Restore cancelled."
  exit 0
fi

echo ""
echo "🔄 Restoring database..."

# Drop and recreate database
kubectl exec -n "$NAMESPACE" deployment/openluffy-${ENV}-postgres -- \
  psql -U openluffy -c "DROP DATABASE IF EXISTS openluffy;"

kubectl exec -n "$NAMESPACE" deployment/openluffy-${ENV}-postgres -- \
  psql -U openluffy -c "CREATE DATABASE openluffy;"

# Restore from backup
gunzip -c "$BACKUP_FILE" | kubectl exec -i -n "$NAMESPACE" deployment/openluffy-${ENV}-postgres -- \
  psql -U openluffy openluffy

echo ""
echo "✅ Database restored successfully!"
echo ""
echo "You may need to restart the backend pod:"
echo "  kubectl rollout restart deployment/openluffy-${ENV}-backend -n $NAMESPACE"
