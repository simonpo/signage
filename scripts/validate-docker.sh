#!/bin/bash
# Validate Docker configuration files

set -e

echo "🔍 Validating Docker configuration..."

# Check required files exist
echo "✓ Checking Docker files exist..."
required_files=("Dockerfile" "docker-compose.yml" ".dockerignore" "DOCKER.md")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
    echo "  ✓ $file"
done

# Validate Dockerfile syntax (basic)
echo "✓ Validating Dockerfile syntax..."
if grep -q "FROM python:" Dockerfile; then
    echo "  ✓ Base image defined"
else
    echo "❌ Invalid Dockerfile: no FROM statement"
    exit 1
fi

# Check docker-compose.yml syntax (requires docker-compose or basic YAML check)
echo "✓ Validating docker-compose.yml..."
if grep -q "version:" docker-compose.yml && grep -q "services:" docker-compose.yml; then
    echo "  ✓ Basic YAML structure valid"
else
    echo "❌ Invalid docker-compose.yml structure"
    exit 1
fi

# Check .dockerignore has common excludes
echo "✓ Validating .dockerignore..."
if grep -q "__pycache__" .dockerignore && grep -q ".git" .dockerignore; then
    echo "  ✓ Common exclusions present"
else
    echo "⚠️  .dockerignore may be missing common exclusions"
fi

# Check that required Python files exist for Docker build
echo "✓ Checking required application files..."
required_app_files=("requirements.txt" "generate_signage.py" "src/config.py")
for file in "${required_app_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done
echo "  ✓ All required application files present"

echo ""
echo "✅ Docker configuration validation passed!"
echo ""
echo "To build and run (requires Docker):"
echo "  docker-compose up -d"
echo ""
echo "See DOCKER.md for complete deployment guide."
