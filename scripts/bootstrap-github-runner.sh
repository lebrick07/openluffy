#!/bin/bash
set -e

# Bootstrap GitHub Runner Token Secret
# Run after K3s rebuild to restore the runner authentication

GITHUB_PAT="${GITHUB_PAT:-}"

if [ -z "$GITHUB_PAT" ]; then
  echo "❌ Error: GITHUB_PAT environment variable not set"
  echo ""
  echo "Usage:"
  echo "  GITHUB_PAT='ghp_xxx...' ./scripts/bootstrap-github-runner.sh"
  echo ""
  echo "Get PAT from: https://github.com/settings/tokens"
  echo "Scopes needed: repo, admin:org"
  exit 1
fi

echo "🔐 Creating github-runner-token secret in arc-runners namespace..."

kubectl create namespace arc-runners --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic github-runner-token \
  --namespace arc-runners \
  --from-literal=github_token="$GITHUB_PAT" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secret created: github-runner-token in arc-runners namespace"
echo ""
echo "Next steps:"
echo "  1. ArgoCD will sync github-runner-controller and github-runner-scale-set"
echo "  2. Runners will auto-register with GitHub"
echo "  3. Verify: kubectl get pods -n arc-systems"
