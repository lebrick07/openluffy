# OpenLuffy Scripts

Automation scripts for deployment, backup, and disaster recovery.

## Recovery & Bootstrap

### `recover-cluster.sh` - Full Cluster Recovery
**Use case:** After K3s rebuild or complete system failure

**What it does:**
1. Installs ArgoCD
2. Bootstraps GitHub runner authentication
3. Deploys all ArgoCD Applications
4. Injects API keys (optional)
5. Verifies deployment

**Usage:**
```bash
GITHUB_PAT='ghp_xxx...' ./scripts/recover-cluster.sh

# With API keys
GITHUB_PAT='ghp_xxx...' ANTHROPIC_API_KEY='sk-ant-xxx...' ./scripts/recover-cluster.sh

# Partial recovery (skip steps)
GITHUB_PAT='ghp_xxx...' SKIP_ARGOCD=true ./scripts/recover-cluster.sh
```

**Time:** ~10 minutes

---

### `bootstrap-github-runner.sh` - GitHub Runner Authentication
**Use case:** After K3s rebuild, before deploying runner scale set

**What it does:**
- Creates `github-runner-token` secret in `arc-runners` namespace
- Required for GitHub Actions runners to register

**Usage:**
```bash
GITHUB_PAT='ghp_xxx...' ./scripts/bootstrap-github-runner.sh
```

**Time:** <30 seconds

---

## Database Management

### `backup-databases.sh` - Create Database Backup
**Use case:** Manual backup before risky changes, or runs automatically via CronJob

**What it does:**
- Dumps PostgreSQL database
- Compresses with gzip
- Saves to `/mnt/openluffy-backups/`

**Usage:**
```bash
./scripts/backup-databases.sh dev
./scripts/backup-databases.sh preprod
./scripts/backup-databases.sh prod
```

**Automatic:** Runs daily at 02:00 via `k8s/backup-cronjob.yaml`

---

### `restore-database.sh` - Restore from Backup
**Use case:** After data corruption, accidental deletion, or testing recovery

**What it does:**
- Restores PostgreSQL database from gzipped SQL dump
- Drops existing database first (destructive!)
- Recreates database and restores data

**Usage:**
```bash
# Restore specific backup
./scripts/restore-database.sh dev /mnt/openluffy-backups/dev_20260304_042426.sql.gz

# Restore latest backup
LATEST=$(ls -t /mnt/openluffy-backups/dev_*.sql.gz | head -1)
./scripts/restore-database.sh dev "$LATEST"
```

**Time:** ~1-5 minutes (depends on database size)

---

## Deployment Workflow

**Normal Development:**
1. Create feature branch: `git checkout -b feat/my-feature`
2. Make changes, commit
3. Create PR to `develop`
4. Merge PR → GitHub Actions runs:
   - `build-and-push` → Build images, update dev.yaml
   - `inject-secrets` → Patch ArgoCD with secrets (on K8s runner)
   - `promote-to-preprod` → Update preprod.yaml
5. ArgoCD auto-syncs dev & preprod

**Production Release:**
1. Create PR from `develop` → `main`
2. Review & merge → `release-prod.yaml` runs
3. Manual sync in ArgoCD UI for prod deployment

**After K3s Rebuild:**
1. Run `recover-cluster.sh` (one command, full recovery)
2. Done

---

## Quick Reference

| Task | Script | Time |
|------|--------|------|
| Full cluster recovery | `recover-cluster.sh` | ~10 min |
| Bootstrap runners | `bootstrap-github-runner.sh` | <30 sec |
| Backup database | `backup-databases.sh <env>` | ~1 min |
| Restore database | `restore-database.sh <env> <file>` | ~5 min |

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GITHUB_PAT` | Yes (recovery) | GitHub Personal Access Token for runner registration |
| `ANTHROPIC_API_KEY` | No | Claude API key for AI features |
| `KUBECONFIG` | Auto-set | Path to K3s kubeconfig (defaults to `/etc/rancher/k3s/k3s.yaml`) |

---

## Troubleshooting

### "kubectl: command not found"
```bash
# Install K3s first
curl -sfL https://get.k3s.io | sh -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

### "GITHUB_PAT not set"
```bash
# Get PAT from: https://github.com/settings/tokens
# Scopes needed: repo, admin:org
export GITHUB_PAT='ghp_xxx...'
```

### "Backup file not found"
```bash
# List available backups
ls -lh /mnt/openluffy-backups/

# Check CronJob status
kubectl get cronjob -n openluffy-dev
kubectl logs -n openluffy-dev job/backup-dev-manual
```

---

## See Also

- [DISASTER-RECOVERY.md](../docs/DISASTER-RECOVERY.md) - Detailed recovery procedures
- [BACKUP-STRATEGY.md](../docs/BACKUP-STRATEGY.md) - Backup architecture and schedules
- [SECRETS.md](../helm/openluffy/SECRETS.md) - Secrets management guide
