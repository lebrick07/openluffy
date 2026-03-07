# Pipeline Architecture - Build Once, Deploy Everywhere

## Philosophy

**Core Principle:** Build artifacts once in develop, promote the tested artifact to production.

**Why:**
- Prod runs the EXACT same artifact that was tested in dev/preprod
- No "rebuild drift" (different timestamps, base image versions, dependencies)
- Faster prod deployments (retag vs rebuild)
- True continuous delivery

## Pipeline Comparison

### Old (Broken) Architecture

**Develop Pipeline:**
```
Build dev-{SHA} → Push → Deploy to dev/preprod
```

**Main Pipeline:**
```
Build main-{SHA} → Security scan → Push → Deploy to prod
```

**Problems:**
- ❌ Prod uses DIFFERENT artifact than what was tested
- ❌ Security scans at prod time (too late!)
- ❌ Rebuild takes 3-4 minutes unnecessarily
- ❌ Potential for environment-specific bugs

---

### New (Correct) Architecture

**Develop Pipeline (Build & Test):**
```
1. Build images (dev-{SHA})
2. Security scan (Trivy - CRITICAL/HIGH)
3. Push to registry
4. Update dev manifests
5. Inject secrets (dev/preprod)
6. ArgoCD auto-syncs dev & preprod
```

**Main Pipeline (Promote Tested Artifact):**
```
1. Find dev-{SHA} from merged commit
2. Pull dev-{SHA} images
3. Retag → prod-{SHA} + latest
4. Push production tags
5. Update prod manifests
6. Inject secrets (prod)
7. ArgoCD auto-syncs prod
```

**Benefits:**
- ✅ Prod runs tested artifact (same binary)
- ✅ Security scans on develop (shift-left)
- ✅ Faster prod deploys (~30 sec vs ~4 min)
- ✅ "Build once, deploy everywhere"

## Security Scanning

### Trivy Integration

**When:** Develop pipeline (after image build)  
**What:** Scans for CRITICAL and HIGH vulnerabilities  
**Output:** SARIF format → GitHub Security tab  
**Blocking:** Warnings only (non-blocking)

**Why on develop:**
- Catch issues early (before preprod testing)
- Developers see results immediately
- No surprises at prod time

**Future improvements:**
- Make scans blocking (fail pipeline on CRITICAL)
- Add container signing/verification
- SBOM generation

## Approval Gates

### Single Gate: PR Merge to Main

**Old model:**
1. PR review (approval #1)
2. Merge to main
3. Manual ArgoCD sync (approval #2) ❌ REDUNDANT

**New model:**
1. PR review + merge to main (single approval) ✅
2. ArgoCD auto-syncs (no second manual gate)

**Why this is safe:**
- PR review is the approval
- Git history shows who approved
- Preprod testing validates artifact
- Second manual sync adds no safety

**When manual sync might be needed:**
- Scheduled maintenance windows
- Coordinated multi-service deploys
- Rollback scenarios

For these cases: disable ArgoCD auto-sync temporarily.

## Image Tagging Strategy

### Develop Branch

**Tags created:**
- `dev-{SHORT_SHA}` (e.g., `dev-abc1234`)
- `dev-latest` (rolling tag)

**Usage:**
- Dev environment uses `dev-{SHA}`
- Preprod promoted from dev after validation

### Main Branch

**Tags created:**
- `prod-{SHORT_SHA}` (e.g., `prod-def5678`)
- `latest` (rolling tag)

**How:**
- Pull `dev-{SHA}` from develop
- Retag as `prod-{SHA}`
- Push production tags

**Traceability:**
- Prod tag points to same digest as dev tag
- Can trace back to original build
- `docker manifest inspect` shows layers match

## Deployment Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Develop Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │  Build   │───▶│  Trivy   │───▶│   Push   │            │
│  │ dev-{SHA}│    │  Scan    │    │ Registry │            │
│  └──────────┘    └──────────┘    └──────────┘            │
│                                        │                   │
│                                        ▼                   │
│                         ┌──────────────────────┐          │
│                         │   Deploy to Dev      │          │
│                         │   (ArgoCD auto-sync) │          │
│                         └──────────────────────┘          │
│                                        │                   │
│                                        ▼                   │
│                         ┌──────────────────────┐          │
│                         │  Promote to Preprod  │          │
│                         │   (ArgoCD auto-sync) │          │
│                         └──────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Test & Validate │
                    │   in Preprod     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   PR to Main     │
                    │   (Approval)     │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Main Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │   Pull   │───▶│  Retag   │───▶│   Push   │            │
│  │ dev-{SHA}│    │prod-{SHA}│    │ Registry │            │
│  └──────────┘    └──────────┘    └──────────┘            │
│                                        │                   │
│                                        ▼                   │
│                         ┌──────────────────────┐          │
│                         │   Deploy to Prod     │          │
│                         │   (ArgoCD auto-sync) │          │
│                         └──────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Rollback Strategy

### Option 1: Revert PR (Recommended)

```bash
# Revert the merge commit on main
git revert <merge-commit-sha>
git push origin main

# Pipeline auto-promotes previous dev image to prod
# ArgoCD syncs automatically
```

### Option 2: Manual Image Rollback

```bash
# Find previous working tag
docker pull ghcr.io/lebrick07/openluffy-backend:prod-abc1234

# Retag as current
docker tag ghcr.io/lebrick07/openluffy-backend:prod-abc1234 \
            ghcr.io/lebrick07/openluffy-backend:latest
docker push ghcr.io/lebrick07/openluffy-backend:latest

# Trigger ArgoCD sync
kubectl patch application openluffy-prod -n argocd \
  --type merge -p '{"operation":{"sync":{}}}'
```

### Option 3: Manual Manifest Rollback

```bash
# Edit helm/openluffy/values/prod.yaml
# Change tag to previous working SHA
git commit -m "rollback: revert to prod-abc1234"
git push origin main

# ArgoCD auto-syncs
```

## Monitoring & Observability

### What to Monitor

**Pipeline Health:**
- Build success rate
- Security scan results (GitHub Security tab)
- Average build time

**Deployment Health:**
- ArgoCD sync status
- Pod restart counts
- Application health checks

**Image Drift:**
- Dev → Preprod promotion lag
- Preprod → Prod promotion lag
- Stale images (>7 days in preprod)

### Key Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dev build time | <4 min | GitHub Actions |
| Prod promotion time | <1 min | GitHub Actions |
| Deploy frequency (dev) | >10/day | Git commits |
| Deploy frequency (prod) | 2-5/week | PR merges |
| Rollback time | <5 min | Manual timing |

## Future Enhancements

### Short Term (Next Sprint)

- [ ] Add unit/integration tests to develop pipeline
- [ ] Make Trivy scans blocking (fail on CRITICAL)
- [ ] Add Slack notifications for prod deployments
- [ ] Implement canary deployments (prod)

### Medium Term (Next Quarter)

- [ ] Blue/green deployments
- [ ] Automated rollback on health check failures
- [ ] Container image signing (cosign)
- [ ] SBOM generation and tracking

### Long Term (Next Year)

- [ ] Multi-region deployments
- [ ] Progressive delivery (Flagger)
- [ ] Chaos engineering automation
- [ ] Policy-as-code (OPA/Kyverno)

## FAQ

### Q: Why not rebuild on main for extra safety?

**A:** Rebuilding introduces drift. Different timestamps, base image updates, dependency changes can cause "works in preprod, breaks in prod" scenarios. Promoting the tested artifact is safer.

### Q: What if security scans find issues after dev deployment?

**A:** PR to main will be blocked during review. Preprod testing catches runtime issues. If critical CVE discovered, create hotfix PR with updated dependencies.

### Q: How do we handle emergency hotfixes?

**A:** Same flow, but faster:
1. Create hotfix branch from main
2. Fix + test locally
3. PR to main (expedited review)
4. Merge → auto-deploys to prod

### Q: Can we still do manual prod deploys?

**A:** Yes. Temporarily disable ArgoCD auto-sync:
```bash
kubectl patch application openluffy-prod -n argocd \
  --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}'
```

Then sync manually when ready. Re-enable auto-sync after.

---

**Last Updated:** 2026-03-04  
**Owner:** DevOps Team  
**Review Cycle:** Quarterly
