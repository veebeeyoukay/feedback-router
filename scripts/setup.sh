#!/bin/bash
# Development environment setup script for feedback-router

set -e  # Exit on error

echo "================================================"
echo "Feedback Router Development Setup"
echo "================================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo -e "${YELLOW}Step 1: Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Ensure Python 3.8+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    echo -e "${RED}Error: Python 3.8+ required, got ${PYTHON_VERSION}${NC}"
    exit 1
fi

# Step 2: Create virtual environment
echo ""
echo -e "${YELLOW}Step 2: Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists at ./venv"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Step 3: Install dependencies
echo ""
echo -e "${YELLOW}Step 3: Installing dependencies...${NC}"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "Creating requirements.txt with common dependencies..."
    cat > requirements.txt << 'EOF'
# Core dependencies
pydantic>=2.0.0
python-dotenv>=1.0.0
PyYAML>=6.0

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.20.0
pytest-mock>=3.10.0

# Code quality
black>=23.0.0
flake8>=5.0.0
isort>=5.12.0
mypy>=1.0.0

# Logging and monitoring
structlog>=23.0.0

# API and integrations
httpx>=0.23.0
requests>=2.28.0
slack-sdk>=3.19.0

# Development
ipython>=8.10.0
ipdb>=0.13.0
EOF
    echo -e "${GREEN}✓ Created requirements.txt${NC}"
fi

pip install --upgrade pip setuptools wheel > /dev/null 2>&1 || true
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 4: Create .env file if not exists
echo ""
echo -e "${YELLOW}Step 4: Creating environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f "config/env.example" ]; then
        cp config/env.example .env
        echo -e "${GREEN}✓ Created .env from config/env.example${NC}"
    else
        cat > .env << 'EOF'
# Feedback Router Configuration

# Environment
ENV=development
DEBUG=true

# Slack Configuration (optional)
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
SLACK_APP_TOKEN=

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database (if needed in future)
DATABASE_URL=

# Logging
LOG_LEVEL=INFO

# Feature flags
ENABLE_AUTO_RESPOND=true
ENABLE_ESCALATION=true

# Company settings
COMPANY_NAME=ItsJen.ai
CONTACT_EMAIL=support@itsjen.ai
CONTACT_SLACK_CHANNEL=C_SUPPORT_CHANNEL
EOF
        echo -e "${GREEN}✓ Created .env file${NC}"
    fi
else
    echo "✓ .env file already exists"
fi

# Step 5: Run setup hooks
echo ""
echo -e "${YELLOW}Step 5: Running setup hooks...${NC}"

# Create necessary directories
mkdir -p logs
mkdir -p data

echo -e "${GREEN}✓ Directory structure ready${NC}"

# Step 6: Summary
echo ""
echo "================================================"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Run tests to verify setup:"
echo "   ${YELLOW}pytest tests/ -v${NC}"
echo ""
echo "3. Run specific test suite:"
echo "   ${YELLOW}pytest tests/unit/ -v${NC}"
echo "   ${YELLOW}pytest tests/integration/ -v${NC}"
echo ""
echo "4. Run with coverage:"
echo "   ${YELLOW}pytest --cov=src tests/${NC}"
echo ""
echo "5. Seed test data:"
echo "   ${YELLOW}python scripts/seed_data.py${NC}"
echo ""
echo "6. Start development server:"
echo "   ${YELLOW}python -m src.main${NC}"
echo ""
echo "Documentation:"
echo "- Architecture: docs/ARCHITECTURE.md"
echo "- API Reference: docs/API.md"
echo "- Routing Rules: docs/ROUTING.md"
echo ""
