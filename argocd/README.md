# OpenLuffy ArgoCD Configuration

## 2 Deployment Pipelines

### 1. Nonprod Pipeline (develop branch)
**Managed by:** `release-dev.yaml` workflow

**ArgoCD Applications:**
- `openluffy-dev` (dev.openluffy.local)
- `openluffy-preprod` (preprod.openluffy.local)

**Workflow:**
```
Merge to develop
  ↓
release-dev.yaml triggers
  ↓
Build multi-arch images (dev-<sha>)
  ↓
Update dev values → ArgoCD syncs dev
  ↓
Wait 30s
  ↓
Update preprod values → ArgoCD syncs preprod
```

### 2. Production Pipeline (main branch)
**Managed by:** `release-prod.yaml` workflow

**ArgoCD Application:**
- `openluffy-prod` (openluffy.local)

**Workflow:**
```
Merge to main
  ↓
release-prod.yaml triggers
  ↓
Build multi-arch images (main-<sha>)
  ↓
Update prod values → ArgoCD syncs prod
```

---

## Apply ArgoCD Applications

```bash
# Nonprod pipeline apps
kubectl apply -f openluffy-dev.yaml
kubectl apply -f openluffy-preprod.yaml

# Prod pipeline app
kubectl apply -f openluffy-prod.yaml
```

---

## Customer Apps (Same Pattern)

Each customer should have:
- **Nonprod pipeline:** 2 apps (dev, preprod) watching develop branch
- **Prod pipeline:** 1 app (prod) watching main branch

Example for Acme Corp:
```yaml
# Nonprod pipeline (develop branch)
- acme-corp-dev
- acme-corp-preprod

# Prod pipeline (main branch)
- acme-corp-prod
```
