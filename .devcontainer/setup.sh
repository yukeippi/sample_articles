#!/bin/bash
set -e

echo "Setting up development environment..."

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is not installed. This should have been installed during Docker build."
    exit 1
fi

# Sync dependencies using uv
echo "Syncing project dependencies..."
uv sync --dev

echo "Setup complete! Virtual environment is ready at .venv"
echo "Python interpreter: $(which python)"
echo "To activate the environment, run: source .venv/bin/activate"
