#!/bin/bash
# Deploy a new version of Robot Framework User Guide
# Usage: ./deploy-version.sh <version> [alias]
# Example: ./deploy-version.sh 7.0 latest
#          ./deploy-version.sh 6.1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

VERSION=$1
ALIAS=${2:-}

if [ -z "$VERSION" ]; then
    echo "Error: Version is required"
    echo "Usage: $0 <version> [alias]"
    echo "Example: $0 7.0 latest"
    exit 1
fi

cd "$PROJECT_DIR"

# Ensure dependencies are installed
if [ ! -d ".venv" ]; then
    echo "Installing dependencies..."
    uv sync
fi

echo "Deploying version $VERSION..."

if [ -n "$ALIAS" ]; then
    echo "With alias: $ALIAS"
    uv run mike deploy --push --update-aliases "$VERSION" "$ALIAS"
else
    uv run mike deploy --push "$VERSION"
fi

echo "Deployment complete!"
echo "Available versions:"
uv run mike list
