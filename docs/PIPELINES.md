# OpenLuffy Deployment Pipelines

## Two-Pipeline Architecture

OpenLuffy uses a **two-pipeline approach** for safe, controlled deployments:

---

## Pipeline 1: Dev + Preprod (Automated)

**Trigger:** Merge to `develop` branch

**Flow:**
```
develop branch
  ↓
GitHub Actions: release-dev.yaml
  ↓
Build images (dev-<sha>)
  ↓
Inject secrets to ArgoCD
  ↓
ArgoCD syncs dev (automatic)
  ↓
Wait 30 seconds
  ↓
Auto-promote to preprod
  ↓
ArgoCD syncs preprod (automatic)
```

**Characteristics:**
- ✅ **Fully automated** - No manual approval needed
- ✅ **Fast feedback** - Dev deployed in ~3 minutes
- ✅ **Auto-promotion** - Preprod gets same image 30s later
- ✅ **Self-healing** - ArgoCD auto-corrects drift

**Environments:**
- **Dev:** http://dev.openluffy.local (openluffy-dev namespace)
- **Preprod:** http://preprod.openluffy.local (openluffy-preprod namespace)

**ArgoCD Applications:**
- `openluffy-dev` - autoSync enabled
- `openluffy-preprod` - autoSync enabled

---

## Pipeline 2: Production (Manual Approval)

**Trigger:** Merge to `main` branch

**Flow:**
```
main branch
  ↓
GitHub Actions: release-prod.yaml
  ↓
Build images (main-<sha>)
  ↓
Inject secrets to ArgoCD
  ↓
Update Helm values in git
  ↓
⏸️  WAIT FOR MANUAL APPROVAL
  ↓
Engineer clicks "Sync" in ArgoCD UI
  ↓
ArgoCD deploys to prod
```

**Characteristics:**
- ⏸️  **Manual approval required** - No autoSync
- ✅ **Controlled rollout** - Engineer reviews before sync
- ✅ **Visibility** - ArgoCD UI shows diff before applying
- ✅ **Rollback-ready** - Can revert via ArgoCD UI

**Environment:**
- **Prod:** http://openluffy.local (openluffy-prod namespace)

**ArgoCD Application:**
- `openluffy-prod` - **Manual sync only** (no autoSync)

---

## How to Deploy to Production

### 1. Code Merged to Develop
- Dev + Preprod deploy automatically
- Test in dev.openluffy.local and preprod.openluffy.local

### 2. Create PR: develop → main
- CI validates the changes
- Team reviews the PR
- Merge when ready

### 3. Production Pipeline Runs
- Builds production images (main-<sha>)
- Updates Helm values in git
- **Stops and waits** (no auto-deploy)

### 4. Manual Approval in ArgoCD
1. Open ArgoCD UI: http://argocd.local
2. Find `openluffy-prod` Application
3. Status shows "OutOfSync" (new version available)
4. Click "App Diff" to review changes
5. Click "Sync" to deploy
6. Monitor rollout in real-time

---

## Why Two Pipelines?

### Dev/Preprod Pipeline: Speed
- Developers need fast feedback
- Breaking dev/preprod is low-risk
- Automatic deployment accelerates iteration

### Production Pipeline: Safety
- Production outages are expensive
- Manual approval adds safety gate
- Engineer can review diff before deploying
- Time to notify stakeholders
- Ability to schedule deployments (e.g., during maintenance window)

---

## Comparison

| Feature | Dev/Preprod Pipeline | Production Pipeline |
|---------|---------------------|---------------------|
| **Trigger** | Merge to develop | Merge to main |
| **Approval** | Automatic | Manual (ArgoCD UI) |
| **Speed** | ~3 minutes | Deploy when ready |
| **Risk** | Low | High |
| **Rollback** | Auto via ArgoCD | Manual via ArgoCD |
| **Environments** | 2 (dev, preprod) | 1 (prod) |

---

## Emergency Procedures

### Rollback Dev/Preprod
```bash
# Revert develop branch
git revert <bad-commit>
git push origin develop

# ArgoCD auto-syncs within 3 minutes
```

### Rollback Production
1. Open ArgoCD UI: http://argocd.local
2. Select `openluffy-prod` Application
3. Click "History and Rollback"
4. Select previous good version
5. Click "Rollback"
6. Confirm

---

## Monitoring Deployments

### GitHub Actions
- View runs: https://github.com/lebrick07/openluffy/actions
- Dev pipeline: "Release - Dev"
- Prod pipeline: "Release - Prod"

### ArgoCD UI
- URL: http://argocd.local
- Login: admin / <password>
- Filter: `app:openluffy-*`

### Cluster Status
```bash
# Check all environments
kubectl get pods -n openluffy-dev
kubectl get pods -n openluffy-preprod
kubectl get pods -n openluffy-prod

# Check ArgoCD sync status
kubectl get applications -n argocd | grep openluffy
```

---

## Best Practices

### For Dev/Preprod
- ✅ Merge often to develop
- ✅ Test in dev before promoting features
- ✅ Use preprod to validate release candidates

### For Production
- ✅ Always test in preprod first
- ✅ Review ArgoCD diff before syncing
- ✅ Deploy during low-traffic windows
- ✅ Have rollback plan ready
- ✅ Monitor logs after deployment

---

## Future Enhancements

1. **Slack Notifications** - Notify team when prod sync is ready
2. **Deployment Windows** - Restrict prod deployments to maintenance windows
3. **Progressive Delivery** - Canary/blue-green deployments
4. **Automated Testing Gate** - Block prod if preprod tests fail

---

**This two-pipeline architecture balances velocity (dev/preprod) with safety (production).**
