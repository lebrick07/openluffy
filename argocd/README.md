# ArgoCD Applications

## Quick Start

### 1. Create Secrets First

Before deploying, create secrets in each namespace:

```bash
# Set your API keys
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GITHUB_TOKEN="ghp_your-token-here"  # Optional

# Run bootstrap script
./k8s/secrets-bootstrap.sh
```

Or manually:
```bash
kubectl create namespace openluffy-dev

kubectl create secret generic openluffy-dev-api-keys \
  --namespace openluffy-dev \
  --from-literal=claude-api-key="$ANTHROPIC_API_KEY" \
  --from-literal=github-token="$GITHUB_TOKEN" \
  --from-literal=github-webhook-secret="" \
  --from-literal=openai-api-key=""
```

### 2. Deploy Applications

```bash
kubectl apply -f argocd/openluffy-dev.yaml
kubectl apply -f argocd/openluffy-preprod.yaml
kubectl apply -f argocd/openluffy-prod.yaml
```

## How Secrets Work

The Helm chart creates a secret from `values.yaml`:
```yaml
secrets:
  claudeApiKey: ""  # Populated by pre-existing Kubernetes secret
```

ArgoCD syncs the Helm chart, which references the pre-created secret.

The secret MUST exist before ArgoCD syncs, otherwise pods will fail with `CreateContainerConfigError`.

## Production Setup

For production, use External Secrets Operator:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: openluffy-prod-api-keys
  namespace: openluffy-prod
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: openluffy-prod-api-keys
  data:
  - secretKey: claude-api-key
    remoteRef:
      key: /openluffy/prod/claude-api-key
  - secretKey: github-token
    remoteRef:
      key: /openluffy/prod/github-token
```

Deploy External Secret, then deploy ArgoCD Application.

## Updating Secrets

```bash
# Update secret
kubectl create secret generic openluffy-dev-api-keys \
  --namespace openluffy-dev \
  --from-literal=claude-api-key="NEW-KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods
kubectl rollout restart deployment/openluffy-dev-backend -n openluffy-dev
```

## Troubleshooting

**CreateContainerConfigError**
- Secret doesn't exist yet
- Run `./k8s/secrets-bootstrap.sh` first

**Configuration Error in UI**
- Secret exists but is empty
- Update secret with real API key value
