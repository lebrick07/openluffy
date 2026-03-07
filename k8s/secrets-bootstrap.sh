#!/bin/bash
# Bootstrap script to create secrets from environment variables
# Run this once per environment before deploying

set -e

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "⚠️  WARNING: ANTHROPIC_API_KEY not set"
  echo "AI features will not work without this key"
  echo ""
  echo "To set it:"
  echo "  export ANTHROPIC_API_KEY='your-key-here'"
  echo ""
  read -p "Continue without API key? (yes/no): " CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    exit 1
  fi
  ANTHROPIC_API_KEY=""
fi

GITHUB_TOKEN="${GITHUB_TOKEN:-}"

echo "Creating secrets for environments..."

for ENV in dev preprod prod; do
  NAMESPACE="openluffy-${ENV}"
  
  echo ""
  echo "📦 Creating secret for $NAMESPACE..."
  
  kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
  
  kubectl create secret generic openluffy-${ENV}-api-keys \
    --namespace "$NAMESPACE" \
    --from-literal=claude-api-key="$ANTHROPIC_API_KEY" \
    --from-literal=github-token="$GITHUB_TOKEN" \
    --from-literal=github-webhook-secret="" \
    --from-literal=openai-api-key="" \
    --dry-run=client -o yaml | kubectl apply -f -
  
  echo "✅ Secret created in $NAMESPACE"
done

echo ""
echo "✅ All secrets created!"
echo ""
echo "Now deploy via ArgoCD:"
echo "  kubectl apply -f argocd/openluffy-dev.yaml"
echo "  kubectl apply -f argocd/openluffy-preprod.yaml"
echo "  kubectl apply -f argocd/openluffy-prod.yaml"
