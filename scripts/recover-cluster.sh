#!/bin/bash
set -e

# OpenLuffy K3s Cluster Recovery Script
# Orchestrates full cluster rebuild and recovery

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GITHUB_PAT="${GITHUB_PAT:-}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
SKIP_ARGOCD="${SKIP_ARGOCD:-false}"
SKIP_RUNNERS="${SKIP_RUNNERS:-false}"
SKIP_APPS="${SKIP_APPS:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Install K3s first."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Is K3s running?"
        exit 1
    fi
    
    if [ -z "$GITHUB_PAT" ]; then
        log_error "GITHUB_PAT environment variable not set"
        echo ""
        echo "Usage:"
        echo "  GITHUB_PAT='ghp_xxx...' ./scripts/recover-cluster.sh"
        exit 1
    fi
    
    log_info "✅ Prerequisites OK"
}

install_argocd() {
    if [ "$SKIP_ARGOCD" = "true" ]; then
        log_warn "Skipping ArgoCD installation"
        return
    fi
    
    log_info "Installing ArgoCD..."
    
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    log_info "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s
    
    log_info "Patching ArgoCD for insecure mode..."
    kubectl patch configmap argocd-cmd-params-cm -n argocd \
        --type merge \
        -p '{"data":{"server.insecure":"true"}}'
    kubectl rollout restart deployment argocd-server -n argocd
    
    log_info "Creating ArgoCD ingress..."
    kubectl apply -f "$PROJECT_ROOT/k8s/argocd-ingress.yaml"
    
    # Get initial password
    ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    log_info "✅ ArgoCD installed"
    log_info "ArgoCD admin password: $ARGOCD_PASSWORD"
}

bootstrap_github_runners() {
    if [ "$SKIP_RUNNERS" = "true" ]; then
        log_warn "Skipping GitHub runners bootstrap"
        return
    fi
    
    log_info "Bootstrapping GitHub runners..."
    
    GITHUB_PAT="$GITHUB_PAT" "$SCRIPT_DIR/bootstrap-github-runner.sh"
    
    log_info "✅ GitHub runners bootstrapped"
}

deploy_applications() {
    if [ "$SKIP_APPS" = "true" ]; then
        log_warn "Skipping application deployment"
        return
    fi
    
    log_info "Deploying ArgoCD Applications..."
    
    # Deploy GitHub runner infrastructure
    kubectl apply -f "$PROJECT_ROOT/argocd/github-runner-controller.yaml"
    kubectl apply -f "$PROJECT_ROOT/argocd/github-runner-scale-set.yaml"
    
    # Deploy OpenLuffy environments
    kubectl apply -f "$PROJECT_ROOT/argocd/openluffy-dev.yaml"
    kubectl apply -f "$PROJECT_ROOT/argocd/openluffy-preprod.yaml"
    
    log_info "Waiting for applications to sync..."
    sleep 10
    
    log_info "✅ Applications deployed"
}

inject_api_keys() {
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        log_warn "ANTHROPIC_API_KEY not set, skipping API key injection"
        log_warn "AI features will be disabled until keys are injected"
        return
    fi
    
    log_info "Injecting API keys..."
    
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" "$PROJECT_ROOT/k8s/secrets-bootstrap.sh" dev
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" "$PROJECT_ROOT/k8s/secrets-bootstrap.sh" preprod
    
    log_info "✅ API keys injected"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    echo ""
    echo "=== ArgoCD Applications ==="
    kubectl get application -n argocd
    
    echo ""
    echo "=== GitHub Runners ==="
    kubectl get pods -n arc-systems
    
    echo ""
    echo "=== OpenLuffy Dev ==="
    kubectl get pods -n openluffy-dev
    
    echo ""
    echo "=== OpenLuffy Preprod ==="
    kubectl get pods -n openluffy-preprod
    
    echo ""
    log_info "✅ Deployment verification complete"
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "  OpenLuffy Cluster Recovery Complete"
    echo "=========================================="
    echo ""
    echo "Access URLs:"
    echo "  Dev:     http://dev.openluffy.local"
    echo "  Preprod: http://preprod.openluffy.local"
    echo "  ArgoCD:  http://argocd.local"
    echo ""
    echo "Default Credentials:"
    echo "  OpenLuffy: admin / Admin123!"
    echo "  ArgoCD:    admin / $ARGOCD_PASSWORD"
    echo ""
    echo "Next Steps:"
    echo "  1. Verify all pods are running: kubectl get pods --all-namespaces"
    echo "  2. Check ArgoCD sync status: kubectl get application -n argocd"
    echo "  3. Test OpenLuffy UI: curl http://dev.openluffy.local"
    echo "  4. Restore database backups if needed: ./scripts/restore-database.sh"
    echo ""
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "⚠️  AI features are disabled (no ANTHROPIC_API_KEY)"
        echo "   To enable: ANTHROPIC_API_KEY='sk-ant-xxx...' ./k8s/secrets-bootstrap.sh dev"
        echo ""
    fi
}

main() {
    log_info "Starting OpenLuffy cluster recovery..."
    log_info "Project root: $PROJECT_ROOT"
    
    check_prerequisites
    install_argocd
    bootstrap_github_runners
    deploy_applications
    inject_api_keys
    verify_deployment
    print_summary
    
    log_info "🎉 Recovery complete!"
}

# Show usage
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "OpenLuffy K3s Cluster Recovery Script"
    echo ""
    echo "Usage:"
    echo "  GITHUB_PAT='ghp_xxx...' ./scripts/recover-cluster.sh"
    echo ""
    echo "Optional environment variables:"
    echo "  GITHUB_PAT          - GitHub Personal Access Token (required)"
    echo "  ANTHROPIC_API_KEY   - Claude API key (optional, enables AI features)"
    echo "  SKIP_ARGOCD=true    - Skip ArgoCD installation"
    echo "  SKIP_RUNNERS=true   - Skip GitHub runners bootstrap"
    echo "  SKIP_APPS=true      - Skip application deployment"
    echo ""
    echo "Example:"
    echo "  GITHUB_PAT='ghp_xxx...' ANTHROPIC_API_KEY='sk-ant-xxx...' ./scripts/recover-cluster.sh"
    echo ""
    exit 0
fi

main
