#!/bin/bash
set -e

echo "Setting up development environment..."

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is not installed. This should have been installed during Docker build."
    exit 1
fi

# Create and activate virtual environment
echo "Creating virtual environment..."
uv venv --python 3.14 .venv --clear

# Activate virtual environment
source .venv/bin/activate

# Install project dependencies
echo "Installing project dependencies..."
uv pip install -e .

# Install development dependencies if available
if [ -f requirements-dev.txt ]; then
    echo "Installing development dependencies..."
    uv pip install -r requirements-dev.txt
fi

echo "Setup complete! Virtual environment is ready at .venv"
echo "Python interpreter: $(which python)"
echo "To activate the environment, run: source .venv/bin/activate"
