#!/bin/bash

# dBank Data Layer Setup Script
# Automates the entire setup process

set -e  # Exit on error

echo "=========================================="
echo "🏦 dBank Data Layer Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
print_step "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker found"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose found"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi
print_success "Python 3 found"

# Check if .env exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success ".env file created. Please update it with your settings."
    else
        print_error ".env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Step 1: Start PostgreSQL
print_step "Step 1: Starting PostgreSQL database..."
docker-compose up -d

echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is ready
if docker exec dbank_postgres pg_isready -U dbank_user -d dbank &> /dev/null; then
    print_success "PostgreSQL is running"
else
    print_error "PostgreSQL failed to start. Check logs: docker-compose logs postgres"
    exit 1
fi

# Step 2: Create database schema
print_step "Step 2: Creating database schema..."
if [ -f data_layer/sql/01_create_schema.sql ]; then
    docker exec -i dbank_postgres psql -U dbank_user -d dbank < data_layer/sql/01_create_schema.sql > /dev/null 2>&1
    print_success "Database schema created"
else
    print_error "Schema file not found: data_layer/sql/01_create_schema.sql"
    exit 1
fi

# Step 3: Set up Python environment
print_step "Step 3: Setting up Python environment..."

if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
if [ -f requirements.txt ]; then
    print_step "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Step 4: Generate sample data
print_step "Step 4: Generating sample data..."
if [ -f data_layer/scripts/generate_sample_data.py ]; then
    cd data_layer/scripts
    python generate_sample_data.py
    cd ../..
    print_success "Sample data generated"
else
    print_error "Data generator script not found"
    exit 1
fi

# Step 5: Load data into PostgreSQL
print_step "Step 5: Loading data into PostgreSQL..."
if [ -f data_layer/scripts/load_data_to_postgres.py ]; then
    cd data_layer/scripts
    python load_data_to_postgres.py
    cd ../..
    print_success "Data loaded successfully"
else
    print_error "Data loader script not found"
    exit 1
fi

# Step 6: Verify data
print_step "Step 6: Verifying data..."
if [ -f data_layer/scripts/verify_data.py ]; then
    cd data_layer/scripts
    python verify_data.py
    cd ../..
else
    print_warning "Verification script not found, skipping verification"
fi

echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Database Info:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: dbank"
echo "   User: dbank_user"
echo "   Password: dbank_pass_2025"
echo ""
echo "🔗 Connect:"
echo "   docker exec -it dbank_postgres psql -U dbank_user -d dbank"
echo ""
echo "📁 Data files: data_layer/sample_data/"
echo ""
echo "🚀 Next Steps:"
echo "   1. Set up dbt transformations"
echo "   2. Create knowledge base documents"
echo "   3. Build vector store"
echo "   4. Implement MCP server"
echo "   5. Create FastAPI RAG system"
echo ""
echo "💡 To stop the database:"
echo "   docker-compose stop"
echo ""
echo "💡 To restart:"
echo "   docker-compose start"
echo ""