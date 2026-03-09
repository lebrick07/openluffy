# Handling Helm Values Merge Conflicts

When merging `develop` → `main`, you may see conflicts in Helm values files:
- `helm/openluffy/values/dev.yaml`
- `helm/openluffy/values/preprod.yaml`  
- `helm/openluffy/values/prod.yaml`

These conflicts happen because CI/CD workflows auto-update these files with image tags.

---

## Quick Fix (Automated)

Run the auto-resolver script:

```bash
./scripts/resolve-values-conflicts.sh
git commit
git push origin main
```

**What it does:**
- `dev.yaml` and `preprod.yaml`: Accepts version from develop ✅
- `prod.yaml`: Keeps version from main ✅

---

## Manual Fix

If you prefer to resolve manually:

### 1. Accept develop version for dev/preprod files

```bash
git checkout --theirs helm/openluffy/values/dev.yaml
git checkout --theirs helm/openluffy/values/preprod.yaml
git add helm/openluffy/values/dev.yaml helm/openluffy/values/preprod.yaml
```

### 2. Keep main version for prod file

```bash
git checkout --ours helm/openluffy/values/prod.yaml
git add helm/openluffy/values/prod.yaml
```

### 3. Commit the merge

```bash
git commit
git push origin main
```

---

## Why This Happens

**The workflow:**
1. Release-Dev updates `dev.yaml` and `preprod.yaml` in `develop` branch
2. Release-Prod updates `prod.yaml` in `main` branch
3. When merging develop → main, Git sees both branches modified these files
4. Git marks them as conflicts (even though they're separate files)

**Why we resolve this way:**
- **dev/preprod files:** Develop has the latest tags → accept incoming
- **prod file:** Main has the latest prod tags → keep current

---

## Prevention (Future)

This is a known limitation of Git with auto-generated files. Options:

1. **Use the script** (recommended) - fastest resolution
2. **Don't track values files in Git** - use ConfigMaps instead (major refactor)
3. **Use GitOps operator** - Flux/ArgoCD manages values directly (complex)

For now, using the script is the simplest solution.

---

**Last Updated:** 2026-03-09
