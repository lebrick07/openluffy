# OpenLuffy Secrets Management

## Overview

OpenLuffy requires several API keys and secrets for full functionality. All secrets are optional - the application will run with degraded features if secrets are not provided.

## Required Secrets

### 1. Claude API Key (Optional)
**Purpose:** Enables AI-powered features via Anthropic's Claude API

**Set via Helm:**
```bash
helm install openluffy ./helm/openluffy \
  --set secrets.claudeApiKey="sk-ant-..."
```

**Set via ArgoCD:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
spec:
  source:
    helm:
      parameters:
      - name: secrets.claudeApiKey
        value: "sk-ant-..."
```

**Environment Variable:**
Backend expects `ANTHROPIC_API_KEY`

**If not set:** AI features will show configuration error but app continues to run

---

### 2. GitHub Token (Optional)
**Purpose:** Required for GitHub repository operations and webhooks

**Set via Helm:**
```bash
helm install openluffy ./helm/openluffy \
  --set secrets.githubToken="ghp_..."
```

**Environment Variable:**
Backend expects `GITHUB_TOKEN`

**If not set:** GitHub integration features will be disabled

---

### 3. GitHub Webhook Secret (Optional)
**Purpose:** Validates incoming GitHub webhook payloads

**Set via Helm:**
```bash
helm install openluffy ./helm/openluffy \
  --set secrets.githubWebhookSecret="your-webhook-secret"
```

**If not set:** Webhook validation will be skipped (less secure)

---

### 4. OpenAI API Key (Optional)
**Purpose:** Alternative to Claude for AI features

**Set via Helm:**
```bash
helm install openluffy ./helm/openluffy \
  --set secrets.openaiApiKey="sk-..."
```

**Environment Variable:**
Backend expects `OPENAI_API_KEY`

**If not set:** Falls back to Claude or disables AI features

---

## Deployment Strategies

### Strategy 1: Helm Install with Flags
```bash
helm install openluffy-dev ./helm/openluffy \
  --namespace openluffy-dev \
  --create-namespace \
  --set secrets.claudeApiKey="$ANTHROPIC_API_KEY" \
  --set secrets.githubToken="$GITHUB_TOKEN"
```

### Strategy 2: Values File (NOT for production - secrets in git!)
```yaml
# values-with-secrets.yaml (DO NOT COMMIT)
secrets:
  claudeApiKey: "sk-ant-..."
  githubToken: "ghp_..."
```

```bash
helm install openluffy-dev ./helm/openluffy \
  --values values-with-secrets.yaml
```

### Strategy 3: External Secrets Operator (Recommended for Production)
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: openluffy-api-keys
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: openluffy-dev-api-keys
  data:
  - secretKey: claude-api-key
    remoteRef:
      key: openluffy/claude-api-key
  - secretKey: github-token
    remoteRef:
      key: openluffy/github-token
```

### Strategy 4: Manual Kubernetes Secret (Current Demo Setup)
```bash
# Create secret manually
kubectl create secret generic openluffy-dev-api-keys \
  --namespace openluffy-dev \
  --from-literal=claude-api-key="$ANTHROPIC_API_KEY" \
  --from-literal=github-token="$GITHUB_TOKEN" \
  --from-literal=github-webhook-secret="" \
  --from-literal=openai-api-key=""

# Then deploy without setting secrets in Helm
helm install openluffy-dev ./helm/openluffy \
  --namespace openluffy-dev
```

## Updating Secrets

### Update via kubectl
```bash
kubectl delete secret openluffy-dev-api-keys -n openluffy-dev

kubectl create secret generic openluffy-dev-api-keys \
  --namespace openluffy-dev \
  --from-literal=claude-api-key="NEW-KEY"

# Restart pods to pick up new secret
kubectl rollout restart deployment/openluffy-dev-backend -n openluffy-dev
```

### Update via Helm Upgrade
```bash
helm upgrade openluffy-dev ./helm/openluffy \
  --set secrets.claudeApiKey="NEW-KEY" \
  --reuse-values
```

## Security Best Practices

1. **Never commit secrets to git**
   - Use `.gitignore` for any values files with secrets
   - Always use `--set` flags or external secret management

2. **Use least-privilege API keys**
   - GitHub: Use fine-grained tokens with minimal scopes
   - Claude: Use project-scoped API keys if available

3. **Rotate secrets regularly**
   - Update secrets every 90 days
   - Use external secrets operators for automated rotation

4. **Separate secrets per environment**
   - Dev/preprod/prod should have different API keys
   - Never share production secrets with lower environments

5. **Monitor secret usage**
   - Set up alerts for API key usage spikes
   - Track which services are using which keys

## Troubleshooting

### "ANTHROPIC_API_KEY not provided" Error
**Symptom:** UI shows "Configuration Error" message

**Fix:**
```bash
# Check if secret exists
kubectl get secret openluffy-dev-api-keys -n openluffy-dev

# Check secret content (will be base64 encoded)
kubectl get secret openluffy-dev-api-keys -n openluffy-dev -o yaml

# Update the secret
kubectl create secret generic openluffy-dev-api-keys \
  --namespace openluffy-dev \
  --from-literal=claude-api-key="your-key-here" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart backend
kubectl rollout restart deployment/openluffy-dev-backend -n openluffy-dev
```

### Secret Not Mounting
**Symptom:** Pod shows `CreateContainerConfigError`

**Debug:**
```bash
# Check pod events
kubectl describe pod -n openluffy-dev <pod-name>

# Verify secret exists in same namespace
kubectl get secret -n openluffy-dev openluffy-dev-api-keys

# Check secret keys match deployment expectations
kubectl get secret openluffy-dev-api-keys -n openluffy-dev -o jsonpath='{.data}' | jq keys
```

### Empty Secret Values
**Symptom:** Secret exists but keys are empty

**Fix:**
The secret template now creates empty defaults. Update with real values:
```bash
kubectl patch secret openluffy-dev-api-keys -n openluffy-dev \
  --type merge \
  -p '{"stringData":{"claude-api-key":"your-actual-key"}}'

kubectl rollout restart deployment/openluffy-dev-backend -n openluffy-dev
```

## Demo / Development Setup

For local development or demos without real API keys:

1. Deploy without secrets (AI features will show error but app runs)
2. Or use placeholder keys (features will fail gracefully)
3. Focus demo on infrastructure/GitOps rather than AI features

The application is designed to run without secrets - just with reduced functionality.

## Production Checklist

- [ ] Secrets stored in external secret management system (Vault, AWS Secrets Manager, etc.)
- [ ] Separate API keys per environment
- [ ] Secret rotation schedule configured
- [ ] Monitoring/alerting on secret usage
- [ ] Secrets never committed to git
- [ ] External Secrets Operator or equivalent in place
- [ ] Pod security policies restrict secret access
- [ ] Audit logging enabled for secret access
