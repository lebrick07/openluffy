# Contributing to OpenLuffy

## ⚠️ CRITICAL: GitOps Workflow

**NEVER push directly to `develop` or `main` branches.**

All changes MUST go through feature branches and pull requests.

## Multi-Environment Architecture

```
Dev (develop branch)      → http://dev.openluffy.local
  ↓ auto-promotes (30s)
Preprod (develop branch)  → http://preprod.openluffy.local
  ↓ manual PR
Prod (main branch)        → http://openluffy.local
```

## Branch Workflow

```
develop (integration) ← feature branches merge here
  ↓
main (production) ← PR from develop after testing
```

## Step-by-Step Process

### 1. Create a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

**Branch naming:**
- `feature/*` - New features
- `fix/*` - Bug fixes
- `chore/*` - Maintenance, refactoring
- `docs/*` - Documentation

### 2. Make Your Changes

Work on your feature, commit frequently:

```bash
git add .
git commit -m "feat: add new feature"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `chore:` - Maintenance
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring

### 3. Push to Your Branch

```bash
git push origin feature/your-feature-name
```

### 4. Create a Pull Request

- Go to GitHub
- Create PR from your branch → `develop`
- **CI Pipeline runs automatically:**
  - Security scans (GitLeaks, Trivy)
  - Code quality (Ruff, Black, ESLint)
  - Docker build validation
  - Integration tests
- Wait for CI checks to pass
- Request review if needed

### 5. Merge to Develop

Once approved and CI passes:
- Merge PR to `develop`
- Delete feature branch

### 6. Development Deployment (Automatic)

**Release-Dev pipeline triggers:**
1. Builds images with `dev-<sha>` tags
2. Pushes to registry
3. Updates dev manifests
4. ArgoCD syncs to `openluffy-dev` namespace
5. **Auto-promotes to preprod after 30 seconds**

**Deployments:**
- Dev: http://dev.openluffy.local
- Preprod: http://preprod.openluffy.local (auto-promoted)

### 7. Test on Preprod

Validate the changes on preprod environment before promoting to production.

### 8. Promote to Production

When ready for production:
- Create PR from `develop` → `main`
- **CI Pipeline runs again** (full validation)
- Captain reviews and approves
- Merge to `main`

### 9. Production Deployment (Automatic)

**Release-Prod pipeline triggers:**
1. Builds images with `main-<sha>` and `latest` tags
2. Pushes to registry
3. Updates prod manifests
4. ArgoCD syncs to `openluffy-prod` namespace

**Production:** http://openluffy.local

---

## CI/CD Pipeline

### CI Pipeline (Pull Requests)

Runs when you create a PR:

1. **Security Scans**
   - GitLeaks (secrets detection)
   - Trivy (vulnerability scan)

2. **Code Quality - Backend**
   - Ruff (linter)
   - Black (formatter)

3. **Code Quality - Frontend**
   - ESLint

4. **Docker Build Validation**
   - Build backend image (not pushed)
   - Build frontend image (not pushed)

5. **Integration Tests**
   - Backend: AI Triage Engine tests
   - Frontend: Unit tests

**PR must pass all checks before merge is allowed.**

### Release-Dev Pipeline (Merge to Develop)

Runs automatically after merge to `develop`:

1. **Build & Push Images**
   - Backend image → `ghcr.io/lebrick07/openluffy-backend:dev-<sha>`
   - Frontend image → `ghcr.io/lebrick07/openluffy-frontend:dev-<sha>`

2. **Update Dev Manifests**
   - helm/openluffy/values/dev.yaml updated with new image tags

3. **Auto-Promote to Preprod** (30s delay)
   - helm/openluffy/values/preprod.yaml updated with same tags

4. **ArgoCD Deployment**
   - Dev environment syncs automatically
   - Preprod environment syncs automatically

**From code commit → dev/preprod deployment: ~3-5 minutes**

### Release-Prod Pipeline (Merge to Main)

Runs automatically after merge to `main`:

1. **Build & Push Images**
   - Backend image → `ghcr.io/lebrick07/openluffy-backend:main-<sha>` + `latest`
   - Frontend image → `ghcr.io/lebrick07/openluffy-frontend:main-<sha>` + `latest`

2. **Update Prod Manifests**
   - helm/openluffy/values/prod.yaml updated with new image tags

3. **ArgoCD Deployment**
   - Production environment syncs automatically

**From merge to main → production deployment: ~3-5 minutes**

---

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd openluffy-ui
npm install
npm run dev
```

---

## Testing

### Backend Tests

```bash
cd backend
python test_triage.py
```

### Frontend Tests

```bash
cd openluffy-ui
npm run test:unit
```

---

## Environment URLs

- **Dev:** http://dev.openluffy.local
- **Preprod:** http://preprod.openluffy.local
- **Production:** http://openluffy.local
- **ArgoCD:** http://argocd.local

---

## Branch Protection Rules

**`main` branch:**
- ❌ Direct pushes blocked
- ✅ Require PR approval
- ✅ Require CI checks to pass
- ✅ Require up-to-date branch

**`develop` branch:**
- ❌ Direct pushes blocked (use feature branches)
- ✅ Require CI checks to pass

---

## Questions?

Read the docs or ask in Discord: https://discord.com/invite/clawd
