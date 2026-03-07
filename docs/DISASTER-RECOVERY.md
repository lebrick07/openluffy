# Disaster Recovery - K3s Rebuild Workflow

This guide covers full recovery from K3s cluster rebuild or complete system failure.

## Prerequisites

- K3s installed and running
- kubectl configured (`export KUBECONFIG=/etc/rancher/k3s/k3s.yaml`)
- Helm installed
- Access to GitHub PAT token

## Recovery Steps

### 1. Install ArgoCD

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Patch for insecure mode (no TLS)
kubectl patch configmap argocd-cmd-params-cm -n argocd \
  --type merge \
  -p '{"data":{"server.insecure":"true"}}'
kubectl rollout restart deployment argocd-server -n argocd

# Create ingress
kubectl apply -f /home/user/projects/openluffy/k8s/argocd-ingress.yaml
```

### 2. Bootstrap GitHub Runner Secret

**CRITICAL:** This must be done **before** deploying ArgoCD Applications.

```bash
# Set your GitHub PAT
export GITHUB_PAT="ghp_xxx..."

# Run bootstrap script
./scripts/bootstrap-github-runner.sh
```

**Why this matters:**
- GitHub Actions runners need authentication to register
- Secret must exist before ArgoCD deploys runner scale set
- Cannot be stored in Git (sensitive credential)

### 3. Deploy ArgoCD Applications

```bash
cd /home/user/projects/openluffy

# Deploy GitHub runner infrastructure
kubectl apply -f argocd/github-runner-controller.yaml
kubectl apply -f argocd/github-runner-scale-set.yaml

# Deploy OpenLuffy environments
kubectl apply -f argocd/openluffy-dev.yaml
kubectl apply -f argocd/openluffy-preprod.yaml
# kubectl apply -f argocd/openluffy-prod.yaml  # Optional: manual sync required
```

### 4. Verify Deployment

```bash
# Check ArgoCD Applications
kubectl get application -n argocd

# Expected output:
# github-runner-controller   Synced        Healthy
# github-runner-scale-set    Synced        Healthy
# openluffy-dev              Synced        Healthy
# openluffy-preprod          Synced        Healthy
# openluffy-prod             OutOfSync     Missing

# Check runner pods
kubectl get pods -n arc-systems

# Expected output:
# arc-gha-rs-controller-xxx      1/1     Running
# openluffy-runner-xxx-listener  1/1     Running

# Check OpenLuffy pods
kubectl get pods -n openluffy-dev
kubectl get pods -n openluffy-preprod
```

### 5. Inject API Keys (Optional)

If you want AI features enabled immediately:

```bash
# Using kubectl
ANTHROPIC_API_KEY="sk-ant-xxx..." ./k8s/secrets-bootstrap.sh dev
ANTHROPIC_API_KEY="sk-ant-xxx..." ./k8s/secrets-bootstrap.sh preprod

# Or wait for GitHub Actions workflow to inject them
# (happens automatically on next push to develop branch)
```

### 6. Restore Database Backups (If Needed)

```bash
# List available backups
ls -lh /mnt/openluffy-backups/

# Restore specific backup
./scripts/restore-database.sh dev /mnt/openluffy-backups/dev_20260304_042426.sql.gz

# Or restore latest
LATEST=$(ls -t /mnt/openluffy-backups/dev_*.sql.gz | head -1)
./scripts/restore-database.sh dev "$LATEST"
```

## Access URLs

After recovery:

- **Dev:** http://dev.openluffy.local
- **Preprod:** http://preprod.openluffy.local
- **ArgoCD:** http://argocd.local

Default credentials:
- **OpenLuffy:** admin / Admin123!
- **ArgoCD:** admin / (get from `argocd-initial-admin-secret`)

## Automation Goals

**Current state:**
- ✅ ArgoCD applications in Git (deployable via kubectl apply)
- ✅ Bootstrap script for GitHub runner secret
- ✅ Database backup/restore scripts
- ⚠️ Requires manual execution of bootstrap-github-runner.sh

**Future improvements:**
- [ ] Single "recover-cluster.sh" script that orchestrates all steps
- [ ] Store GitHub PAT in password manager, script fetches it
- [ ] Automated testing of recovery process
- [ ] Monitoring alert when backups are >24h old

## Common Issues

### Runners not registering

**Symptom:** `openluffy-runner-xxx-listener` pod crashes or logs show auth errors

**Fix:**
```bash
# Recreate secret with correct PAT
GITHUB_PAT="ghp_xxx..." ./scripts/bootstrap-github-runner.sh

# Restart runner pods
kubectl rollout restart deployment -n arc-systems
```

### ArgoCD Applications stuck in "Unknown" state

**Symptom:** Health status shows "Unknown" for extended period

**Fix:**
```bash
# Manually sync
kubectl patch application openluffy-dev -n argocd \
  --type merge \
  -p '{"operation":{"sync":{}}}'
```

### Database restore fails

**Symptom:** Restore script exits with connection error

**Fix:**
```bash
# Check if postgres pod is ready
kubectl get pods -n openluffy-dev | grep postgres

# Wait for pod to be running
kubectl wait --for=condition=Ready pod -l app=openluffy-dev-postgres -n openluffy-dev --timeout=300s

# Retry restore
./scripts/restore-database.sh dev /path/to/backup.sql.gz
```

## Recovery Time Objectives

| Component | Target RTO | Notes |
|-----------|-----------|-------|
| K3s cluster | 5 minutes | Fresh install + kubectl config |
| ArgoCD | 5 minutes | Install + ingress + initial config |
| GitHub runners | 2 minutes | Bootstrap secret + ArgoCD sync |
| OpenLuffy dev/preprod | 10 minutes | Image pull + database init |
| Database restore | 5 minutes | Small datasets, grows with DB size |
| **Total** | **~30 minutes** | Full cluster recovery |

## Testing Recovery

Periodically test the recovery process:

```bash
# 1. Document current state
kubectl get all --all-namespaces > pre-rebuild-state.txt

# 2. Nuclear rebuild
/usr/local/bin/k3s-uninstall.sh
curl -sfL https://get.k3s.io | sh -

# 3. Follow recovery steps above

# 4. Compare state
kubectl get all --all-namespaces > post-rebuild-state.txt
diff pre-rebuild-state.txt post-rebuild-state.txt

# 5. Run smoke tests
curl http://dev.openluffy.local
curl http://argocd.local
```

## Emergency Contacts

If recovery fails and you need help:
- GitHub: https://github.com/lebrick07/openluffy/issues
- K3s docs: https://docs.k3s.io
- ArgoCD docs: https://argo-cd.readthedocs.io

---

**Last tested:** 2026-03-04  
**Next test due:** 2026-04-04 (monthly)
