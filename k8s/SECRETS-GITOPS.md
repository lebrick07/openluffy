# GitOps Secrets Management with Sealed Secrets

## ✅ COMPLETE AUTOMATION - THE RIGHT WAY

Secrets are encrypted with Sealed Secrets, committed to git, and automatically decrypted in the cluster.

## How It Works

1. **You encrypt secrets locally** with the cluster's public key
2. **Encrypted secrets are committed to git** (safe - only the cluster can decrypt)
3. **ArgoCD syncs them** like any other manifest
4. **SealedSecret controller decrypts them** in-cluster

NO manual `kubectl` secret creation needed after initial setup!

## Initial Setup (ONE TIME)

### Step 1: Get Your API Key from GitHub

Go to: https://github.com/lebrick07/openluffy/settings/secrets/actions

Copy the value of `ANTHROPIC_API_KEY`

### Step 2: Run the Seal Script

```bash
cd /home/user/projects/openluffy

# Export your API key (from GitHub Secrets UI)
export ANTHROPIC_API_KEY="sk-ant-paste-your-key-here"

# Optional: GitHub token for repo operations
export GITHUB_TOKEN="ghp_your-token"

# Run the seal script
./k8s/seal-secrets.sh
```

This creates encrypted `SealedSecret` files in `k8s/sealed-secrets/`

### Step 3: Apply the Sealed Secrets

```bash
kubectl apply -f k8s/sealed-secrets/
```

### Step 4: Commit to Git

```bash
git add k8s/sealed-secrets/
git commit -m "chore: Add sealed secrets for automated deployment"
git push origin develop
```

### Step 5: Verify Decryption

```bash
# Check that regular secrets were created by the controller
kubectl get secrets -n openluffy-dev openluffy-dev-api-keys
kubectl get secrets -n openluffy-preprod openluffy-preprod-api-keys
```

### Step 6: Restart Backends

```bash
kubectl rollout restart deployment/openluffy-dev-backend -n openluffy-dev
kubectl rollout restart deployment/openluffy-preprod-backend -n openluffy-preprod
```

## ✅ DONE! From Now On...

**Future secret updates:**

1. Update secret → Run `./k8s/seal-secrets.sh`
2. Commit the new sealed secret
3. Push to git
4. ArgoCD syncs it automatically
5. SealedSecret controller decrypts it

NO manual `kubectl create secret` commands needed!

## How Sealed Secrets Work

### Public Key Cryptography

- **Public key** (`k8s/pub-sealed-secrets-cert.pem`) - Safe to commit to git, can only ENCRYPT
- **Private key** - Stays in cluster, only the controller has it, can DECRYPT

### Architecture

```
Developer                       Git                     Cluster
---------                       ---                     -------
1. Has secret                                          
   |                                                   
2. Encrypts with                                       
   public key ─────────────────────>                  
                              3. Stores encrypted      
                                 SealedSecret          
                                 (safe in git)         
                                       |               
                                       |               
                              4. ArgoCD syncs ────────> 5. Creates
                                                           SealedSecret
                                                           resource
                                                              |
                                                         6. Controller
                                                            decrypts
                                                            with private
                                                            key
                                                              |
                                                         7. Creates
                                                            regular
                                                            Secret
                                                              |
                                                         8. Pods mount
                                                            the secret
```

### Security

✅ **Safe to commit:** Encrypted SealedSecrets in git
✅ **Safe to commit:** Public key (can only encrypt, not decrypt)
❌ **NEVER commit:** Plain Secret resources
❌ **NEVER commit:** Private key (stays in cluster)

## Files

```
k8s/
├── seal-secrets.sh                    # Script to encrypt secrets
├── pub-sealed-secrets-cert.pem        # Public key (safe to commit)
└── sealed-secrets/                    # Generated encrypted secrets
    ├── dev-api-keys-sealed.yaml       # ✅ Safe to commit
    ├── preprod-api-keys-sealed.yaml   # ✅ Safe to commit
    └── prod-api-keys-sealed.yaml      # ✅ Safe to commit
```

## Troubleshooting

### "secret not found" in pods

The SealedSecret controller hasn't decrypted yet. Check:

```bash
kubectl get sealedsecret -n openluffy-dev
kubectl describe sealedsecret openluffy-dev-api-keys -n openluffy-dev
kubectl logs -n kube-system deployment/sealed-secrets-controller
```

### "cannot fetch certificate"

The sealed-secrets controller isn't running:

```bash
kubectl get pods -n kube-system | grep sealed-secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.0/controller.yaml
```

### Need to rotate the sealing key?

The controller generates a new key every 30 days by default. Old keys are kept to decrypt existing secrets.

```bash
# Fetch the current public key
kubeseal --fetch-cert > k8s/pub-sealed-secrets-cert.pem

# Re-seal all secrets with the new key
./k8s/seal-secrets.sh
```

## GitHub Actions (Future)

The `.github/workflows/sync-secrets.yaml` workflow can automate this further:

1. Secrets change in GitHub Secrets
2. Workflow triggers
3. Seals secrets with cluster public key
4. Commits encrypted SealedSecrets to git
5. ArgoCD syncs them
6. Controller decrypts them

**Setup required:**
- Add sealed-secrets public cert to GitHub Secrets
- Configure workflow trigger

## Comparison: Manual vs Sealed Secrets

### Manual (OLD WAY - DON'T DO THIS)
```bash
# Every deploy, every environment:
kubectl create secret generic api-keys --from-literal=key=$KEY
# Secrets not in git
# Must remember to create them
# Hard to audit
# Manual process
```

### Sealed Secrets (RIGHT WAY ✅)
```bash
# One time:
./k8s/seal-secrets.sh
git commit && git push

# That's it!
# Secrets in git (encrypted)
# ArgoCD applies them
# Controller decrypts them
# Fully automated
# Auditable
# GitOps native
```

## For Your Demo

**"How do you handle secrets in GitOps?"**

> "We use Sealed Secrets - industry standard for GitOps secret management.
> Secrets are encrypted with the cluster's public key, safely committed to git,
> and automatically decrypted by the SealedSecret controller in-cluster.
> This gives us the security of encrypted secrets with the convenience of GitOps."

Show them:
- `k8s/sealed-secrets/*.yaml` (encrypted, safe to view)
- `kubectl get sealedsecret -A` (see them in cluster)
- `kubectl get secret -A | grep api-keys` (decrypted by controller)

## Production Considerations

1. **Key backup:** Back up the sealing key from kube-system
2. **Key rotation:** Plan for key rotation (30-day default)
3. **Multi-cluster:** Each cluster has its own keys (good for isolation)
4. **Audit:** All secret changes are in git history
5. **Disaster recovery:** Restore sealing keys first, then apply sealed secrets

---

**This is the professional, production-ready way to manage secrets in Kubernetes + GitOps.**
