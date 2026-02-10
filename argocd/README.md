# ArgoCD Setup

## Deploy Luffy Application

Apply the ArgoCD Application to your cluster:

```bash
kubectl apply -f argocd/lebrickbot-application.yaml
```

This will:
- Deploy Luffy from the Helm chart in `helm/lebrickbot/`
- Watch the `main` branch for changes
- Auto-sync on git pushes (automated GitOps)
- Self-heal if resources drift from desired state

## Access ArgoCD UI

```bash
# URL: http://argocd.local
# Username: admin
# Password: uqVa1xRvqz5KIh-2
```

## CI/CD Flow

1. **Push to main** → GitHub Actions builds Docker images
2. **Images pushed** to `ghcr.io/lebrick07/lebrickbot-{backend,frontend}`
3. **Image tags updated** in `helm/lebrickbot/values.yaml`
4. **ArgoCD detects change** → auto-syncs to K8s cluster
5. **New version deployed** automatically

## Manual Sync

Force sync from ArgoCD UI or CLI:

```bash
argocd app sync lebrickbot
```
