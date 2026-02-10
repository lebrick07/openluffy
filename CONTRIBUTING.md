# Contributing to OpenLuffy

## ⚠️ CRITICAL: GitOps Workflow

**NEVER push directly to `main` branch.**

All changes MUST go through feature branches and pull requests.

## Branch Workflow

```
main (protected) ← PR merge only
  ↑
develop (integration) ← feature branches merge here
  ↑
feature/* (your work)
fix/* (bug fixes)
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
- Wait for CI checks to pass
- Request review if needed

### 5. Merge to Develop

Once approved and CI passes:
- Merge PR to `develop`
- Delete feature branch

### 6. Promote to Main (Production)

When ready for production:
- Create PR from `develop` → `main`
- Full CI/CD runs
- On merge, images are built and ArgoCD syncs

## CI/CD Pipeline

### CI Pipeline (Pull Requests)

Runs when you create a PR:

1. **Security Scan**
   - GitLeaks (secrets detection)
   - Trivy (vulnerability scan)

2. **Code Quality**
   - Backend: Ruff (linter), Black (formatter), pytest
   - Frontend: ESLint, unit tests

3. **Build Validation**
   - Docker images built (not pushed)
   - Validates Dockerfiles work

**PR must pass all checks before merge is allowed.**

### Release Pipeline (Merge to Main)

Runs automatically after merge to `main`:

1. **Build & Push Images**
   - Backend image → `ghcr.io/lebrick07/openluffy-backend:main-<sha>`
   - Frontend image → `ghcr.io/lebrick07/openluffy-frontend:main-<sha>`

2. **Update Manifests**
   - Helm values.yaml updated with new image tags
   - Committed back to main with `[skip ci]`

3. **ArgoCD Deployment**
   - ArgoCD detects manifest changes
   - Auto-syncs to K8s cluster
   - New pods deployed automatically

**From code commit → production deployment: ~3-5 minutes**

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

## Testing

### Backend Tests

```bash
cd backend
pytest -v
```

### Frontend Tests

```bash
cd openluffy-ui
npm run test:unit
```

## Branch Protection Rules

**`main` branch:**
- ❌ Direct pushes blocked
- ✅ Require PR approval
- ✅ Require CI checks to pass
- ✅ Require up-to-date branch

**`develop` branch:**
- ⚠️ Direct pushes allowed (but discouraged)
- ✅ Require CI checks to pass

## Questions?

Read the docs or ask in Discord: https://discord.com/invite/clawd
