#!/bin/bash
# Setup script for signage project
# Creates virtual environment and installs dependencies

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🖼️  Signage System Setup${NC}"
echo ""

# Detect project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON=$(command -v python3)
    VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
    echo "Found Python $VERSION"
else
    echo "Error: Python 3 not found"
    exit 1
fi

# Create virtual environment
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists at $VENV_DIR${NC}"
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
    else
        echo "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Determine which requirements to install
echo ""
read -p "Install development tools (black, ruff, pytest)? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
    echo -e "${GREEN}✓ Development dependencies installed${NC}"

    # Install pre-commit hooks
    echo "Installing pre-commit hooks..."
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo "Installing production dependencies..."
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Production dependencies installed${NC}"
fi

# Install Playwright browsers if needed
if grep -q "playwright" requirements.txt; then
    echo ""
    read -p "Install Playwright browsers for marine traffic screenshots? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        playwright install chromium
    fi
fi

# Check for .env
echo ""
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found${NC}"
    read -p "Copy .env.example to .env? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env - please edit it with your API keys${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create background directories
echo ""
echo "Creating background image directories..."
mkdir -p backgrounds/weather/{sunny,rainy,cloudy,default}
mkdir -p backgrounds/tesla
mkdir -p backgrounds/stock
mkdir -p backgrounds/ferry
mkdir -p backgrounds/sports

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys and configuration"
echo "  2. Activate venv: source venv/bin/activate"
echo "  3. Test: python generate_signage.py --source tesla"
echo "  4. Run daemon: python generate_signage.py --daemon"
echo "  5. Setup cron: ./scripts/setup_cron.sh"
echo ""
echo "To activate the virtual environment in the future:"
echo "  source venv/bin/activate"
