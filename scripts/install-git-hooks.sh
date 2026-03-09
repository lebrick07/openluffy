#!/bin/bash

# Install Git hooks for OpenLuffy repository
# Prevents direct commits to develop and main branches

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing OpenLuffy git hooks..."

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash

# Pre-commit hook to prevent direct commits to develop and main branches
# OpenLuffy requires all changes to go through feature branches and PRs

branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$branch" = "develop" ] || [ "$branch" = "main" ]; then
  echo ""
  echo "❌ ERROR: Direct commits to '$branch' are NOT allowed!"
  echo ""
  echo "OpenLuffy workflow requires feature branches:"
  echo "  1. git checkout -b feature/your-feature-name"
  echo "  2. Make changes and commit to feature branch"
  echo "  3. git push origin feature/your-feature-name"
  echo "  4. Create PR to develop (or develop → main)"
  echo ""
  echo "Your changes were NOT committed."
  echo ""
  exit 1
fi

exit 0
EOF

chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Git hooks installed successfully!"
echo ""
echo "Pre-commit hook will prevent direct commits to develop and main."
echo ""
