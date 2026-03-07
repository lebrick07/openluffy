# OpenLuffy Backup Strategy

## Problem

When running on K3s with default `local-path` storage, data is lost when the cluster is rebuilt or PVCs are deleted.

## Solution

Multi-layered backup approach:

### 1. Manual Backups (Immediate Use)

**Backup all databases:**
```bash
./scripts/backup-databases.sh
```

**Restore a database:**
```bash
./scripts/restore-database.sh dev /mnt/openluffy-backups/dev_20260304_042426.sql.gz
```

Backups are stored in `/mnt/openluffy-backups/` on the host.

### 2. Automated Backups (Production)

**Deploy the CronJob:**
```bash
kubectl apply -f k8s/backup-cronjob.yaml
```

This runs daily at 2 AM and:
- Backs up dev, preprod, and prod databases
- Keeps 30 days of history
- Stores backups on host filesystem

**Check backup jobs:**
```bash
kubectl get cronjobs -n kube-system
kubectl get jobs -n kube-system | grep backup
```

### 3. Persistent Storage (Survives Cluster Rebuilds)

**For critical data, use the persistent StorageClass:**
```bash
kubectl apply -f k8s/persistent-storage.yaml
```

Then update Helm values to use `storageClassName: local-persistent` instead of `local-path`.

**Difference:**
- `local-path`: Deleted when PVC is removed (default)
- `local-persistent`: Uses `reclaimPolicy: Retain` - data survives PVC deletion

### 4. External Database (Future)

For true high availability, consider:
- AWS RDS
- Managed PostgreSQL (DigitalOcean, Linode)
- Self-hosted PostgreSQL on a separate VM

## Disaster Recovery

**If cluster is rebuilt:**

1. Check available backups:
```bash
ls -lh /mnt/openluffy-backups/
```

2. Restore each environment:
```bash
./scripts/restore-database.sh dev /mnt/openluffy-backups/dev_TIMESTAMP.sql.gz
./scripts/restore-database.sh preprod /mnt/openluffy-backups/preprod_TIMESTAMP.sql.gz
./scripts/restore-database.sh prod /mnt/openluffy-backups/prod_TIMESTAMP.sql.gz
```

3. Restart backends:
```bash
kubectl rollout restart deployment -n openluffy-dev openluffy-dev-backend
kubectl rollout restart deployment -n openluffy-preprod openluffy-preprod-backend
kubectl rollout restart deployment -n openluffy-prod openluffy-prod-backend
```

## Best Practices

1. **Run backups before risky operations** (cluster upgrades, etc.)
2. **Test restores periodically** - backups are useless if they don't restore
3. **Monitor backup job success** - set up alerts if backups fail
4. **Store backups off-host** for true disaster recovery (S3, NFS, etc.)

## Demo Setup

For the Cast.ai interview, backups are configured and working:

- ✅ Manual backup script tested
- ✅ Backups stored in `/mnt/openluffy-backups/`
- ✅ Current databases have been backed up
- ⏳ CronJob ready to deploy (optional for demo)

**Show this during interview:**
```bash
# Show backup exists
ls -lh /mnt/openluffy-backups/

# Show backup content
zcat /mnt/openluffy-backups/dev_*.sql.gz | head -20
```

This demonstrates:
- Understanding of stateful app challenges in Kubernetes
- Practical disaster recovery thinking
- Production-ready operational practices
