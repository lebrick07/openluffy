# OpenLuffy Deployment Guide

## Deployment Model

**OpenLuffy is a self-hosted, multi-tenant DevOps platform.** Each organization deploys their own independent instance.

### Key Principles

1. **One Deployment = One Organization**
   - Each deployment is completely isolated
   - No shared users, data, or configuration between deployments
   - Each deployment has its own PostgreSQL database

2. **Independent Instances**
   - Like ArgoCD, Grafana, or Jenkins - every company runs their own server
   - Your dev/preprod/prod environments are separate deployments for testing the platform itself
   - End users deploy ONE instance (e.g., `openluffy.theircompany.com`) to manage their customers

3. **Database Isolation**
   - Each deployment = separate PostgreSQL database
   - Users created in one deployment DO NOT exist in other deployments
   - Customers created in one deployment DO NOT exist in other deployments

## First-Time Setup (Bootstrap)

### Step 1: Deploy Infrastructure

Deploy using Helm:

```bash
helm install openluffy ./helm/openluffy \
  -f values/production.yaml \
  --namespace openluffy \
  --create-namespace
```

### Step 2: Bootstrap First Admin User

The bootstrap endpoint creates the FIRST admin user when the database is empty:

```bash
curl -X POST https://openluffy.yourcompany.com/v1/auth/bootstrap/create-admin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "password": "YourSecurePassword123!",
    "first_name": "Admin",
    "last_name": "User"
  }'
```

**Important:**
- This endpoint ONLY works when the database is empty (zero users)
- After the first admin is created, the endpoint returns 403
- Each deployment must bootstrap independently

### Step 3: Create Additional Users

After bootstrap, use the admin UI or API to create additional users:

```bash
curl -X POST https://openluffy.yourcompany.com/v1/auth/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@yourcompany.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "viewer"
  }'
```

## Multi-Environment Setup (Development)

If you're developing OpenLuffy itself, you might run dev/preprod/prod:

### Each Environment is Independent

```yaml
# Dev deployment (dev.openluffy.local)
- Separate PostgreSQL database: openluffy-dev-postgres
- Separate users (must bootstrap separately)
- Used for testing new features

# Preprod deployment (preprod.openluffy.local)  
- Separate PostgreSQL database: openluffy-preprod-postgres
- Separate users (must bootstrap separately)
- Used for staging/validation

# Prod deployment (openluffy.local)
- Separate PostgreSQL database: openluffy-prod-postgres
- Separate users (must bootstrap separately)
- Used for running the platform
```

### Bootstrap Each Environment

```bash
# Bootstrap dev
curl -X POST http://dev.openluffy.local/v1/auth/bootstrap/create-admin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dev.local","password":"DevPassword123!"}'

# Bootstrap preprod (completely separate)
curl -X POST http://preprod.openluffy.local/v1/auth/bootstrap/create-admin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@preprod.local","password":"PreprodPassword123!"}'

# Bootstrap prod (completely separate)
curl -X POST http://openluffy.local/v1/auth/bootstrap/create-admin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@prod.local","password":"ProdPassword123!"}'
```

## Authentication Architecture

### Local Authentication (Default)

- Email/password authentication
- JWT tokens (3-hour access, 7-day refresh)
- Role-based access control (admin, viewer)
- API token support for automation

### SSO Integration (Future)

Production deployments should integrate SSO:
- OIDC (OpenID Connect)
- SAML 2.0
- LDAP/Active Directory

## Database Schema Management

### Automatic Migration

OpenLuffy uses SQLAlchemy with declarative models:

```python
# On startup, tables are created automatically
Base.metadata.create_all(bind=engine)
```

### Schema Updates

When upgrading OpenLuffy versions:
1. New columns are added automatically
2. Old data is preserved
3. No manual migration scripts needed (for now)

**Future:** Alembic migrations for production-grade schema evolution.

## Backup & Recovery

### Backup Strategy

Each deployment should back up its PostgreSQL database:

```bash
# Backup dev environment
kubectl exec -n openluffy-dev openluffy-dev-postgres-xxx -- \
  pg_dump -U openluffy openluffy > backup-dev-$(date +%Y%m%d).sql

# Backup prod environment
kubectl exec -n openluffy-prod openluffy-prod-postgres-xxx -- \
  pg_dump -U openluffy openluffy > backup-prod-$(date +%Y%m%d).sql
```

### Restore

```bash
kubectl exec -i -n openluffy-prod openluffy-prod-postgres-xxx -- \
  psql -U openluffy openluffy < backup-prod-20260218.sql
```

## Monitoring Each Deployment

Each deployment runs independently:

```bash
# Check dev deployment
kubectl get pods -n openluffy-dev

# Check preprod deployment  
kubectl get pods -n openluffy-preprod

# Check prod deployment
kubectl get pods -n openluffy-prod
```

## Security Considerations

### Per-Deployment Security

1. **Separate credentials** for each deployment
2. **Separate API tokens** for automation
3. **Separate ArgoCD access** per environment
4. **Separate GitHub tokens** per customer (stored encrypted in each deployment's database)

### Network Isolation

```yaml
# Each deployment in its own namespace
- openluffy-dev (dev network policies)
- openluffy-preprod (preprod network policies)
- openluffy-prod (prod network policies, stricter)
```

## Troubleshooting

### "Bootstrap already complete" Error

```json
{
  "detail": "Bootstrap already complete. This instance has been initialized."
}
```

**Solution:** This deployment already has users. Use `/v1/auth/users` with admin credentials.

### "Database connection failed"

Check PostgreSQL is running:

```bash
kubectl get pods -n openluffy-dev | grep postgres
kubectl logs -n openluffy-dev openluffy-dev-postgres-xxx
```

### "Login fails in preprod but works in dev"

**Expected behavior!** Each deployment has separate users.

- Create user in dev → works in dev only
- Create user in preprod → works in preprod only
- Create user in prod → works in prod only

## Deployment Checklist

- [ ] Deploy Helm chart with correct namespace
- [ ] Verify PostgreSQL is running
- [ ] Bootstrap first admin user
- [ ] Verify login works
- [ ] Create additional users via admin UI
- [ ] Configure GitHub integration
- [ ] Configure ArgoCD integration
- [ ] Set up backup schedule
- [ ] Configure monitoring/alerts

---

**Remember:** Each deployment is independent. Treat it like deploying your own Grafana or ArgoCD server.
