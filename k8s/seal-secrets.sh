#!/bin/bash
# Seal secrets for GitOps deployment
# This encrypts secrets so they can be safely committed to git

set -e

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌ ERROR: ANTHROPIC_API_KEY environment variable not set"
  echo ""
  echo "Export your API key first:"
  echo "  export ANTHROPIC_API_KEY='sk-ant-your-key-here'"
  echo ""
  echo "Get it from: https://github.com/lebrick07/openluffy/settings/secrets/actions"
  exit 1
fi

GITHUB_TOKEN="${GITHUB_TOKEN:-}"

echo "🔐 Creating SealedSecrets for GitOps deployment..."
echo ""

mkdir -p k8s/sealed-secrets

for ENV in dev preprod prod; do
  NAMESPACE="openluffy-${ENV}"
  SECRET_NAME="openluffy-${ENV}-api-keys"
  
  echo "📦 Sealing secrets for $NAMESPACE..."
  
  # Create the raw secret (not applied, just used for sealing)
  kubectl create secret generic "$SECRET_NAME" \
    --namespace "$NAMESPACE" \
    --from-literal=claude-api-key="$ANTHROPIC_API_KEY" \
    --from-literal=github-token="$GITHUB_TOKEN" \
    --from-literal=github-webhook-secret="" \
    --from-literal=openai-api-key="" \
    --dry-run=client -o yaml | \
    kubeseal --format=yaml > "k8s/sealed-secrets/${ENV}-api-keys-sealed.yaml"
  
  echo "✅ Created k8s/sealed-secrets/${ENV}-api-keys-sealed.yaml"
done

echo ""
echo "✅ All secrets sealed!"
echo ""
echo "📝 These encrypted files can now be safely committed to git:"
ls -lh k8s/sealed-secrets/
echo ""
echo "Next steps:"
echo "  1. git add k8s/sealed-secrets/"
echo "  2. git commit -m 'chore: Add sealed secrets for automated deployment'"
echo "  3. git push"
echo "  4. kubectl apply -f k8s/sealed-secrets/"
echo ""
echo "The SealedSecret controller will decrypt them automatically in the cluster."
