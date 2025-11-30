#!/bin/bash

# setup.sh - Quick setup script for BOT GPT Backend
# Usage: bash setup.sh

set -e

echo "🚀 BOT GPT Backend Setup Script"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo "📦 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file and add your GROQ_API_KEY${NC}"
    echo ""
    echo "Get your free API key from: https://console.groq.com/keys"
    echo ""
    read -p "Press Enter after you've added your GROQ_API_KEY to .env file..."
fi

# Validate GROQ_API_KEY
source .env
if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "your_groq_api_key_here" ]; then
    echo -e "${RED}❌ GROQ_API_KEY is not set in .env file${NC}"
    echo "Please edit .env and add your actual API key"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables configured${NC}"
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p tests
mkdir -p .github/workflows

# Create __init__.py for tests
touch tests/__init__.py

echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Checking API health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is healthy!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for API... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ API failed to start. Check logs with: docker-compose logs api${NC}"
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "================================"
echo "📍 API is running at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📊 Database: localhost:5432"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
echo "  - Run tests: docker-compose exec api pytest tests/ -v"
echo ""
echo "Next steps:"
echo "  1. Visit http://localhost:8000/docs to explore the API"
echo "  2. Use the provided Postman collection for testing"
echo "  3. Check API_TESTING.md for detailed examples"
echo "================================"