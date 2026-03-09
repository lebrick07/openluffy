#!/bin/bash

# Auto-resolve Helm values conflicts when merging develop → main
#
# Strategy:
# - dev.yaml and preprod.yaml: Accept version from develop (incoming)
# - prod.yaml: Keep version from main (current)

echo "🔧 Auto-resolving Helm values conflicts..."

# Check if we're in a merge
if ! git rev-parse -q --verify MERGE_HEAD >/dev/null; then
    echo "❌ Not in a merge. Run this during a merge conflict."
    exit 1
fi

CONFLICTS=0

# For dev.yaml and preprod.yaml: accept incoming (develop) version
for file in helm/openluffy/values/dev.yaml helm/openluffy/values/preprod.yaml; do
    if git ls-files -u | grep -q "$file"; then
        echo "  Resolving $file (accepting develop version)..."
        git checkout --theirs "$file"
        git add "$file"
        ((CONFLICTS++))
    fi
done

# For prod.yaml: keep current (main) version
if git ls-files -u | grep -q "helm/openluffy/values/prod.yaml"; then
    echo "  Resolving prod.yaml (keeping main version)..."
    git checkout --ours "helm/openluffy/values/prod.yaml"
    git add "helm/openluffy/values/prod.yaml"
    ((CONFLICTS++))
fi

if [ $CONFLICTS -eq 0 ]; then
    echo "✅ No Helm values conflicts found"
else
    echo "✅ Resolved $CONFLICTS Helm values conflicts"
    echo ""
    echo "Next steps:"
    echo "  git commit"
    echo "  git push origin main"
fi
