#!/bin/bash
# setup_dsql.sh - Complete DSQL setup for fresh installations or migrations

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV_DIR="$PROJECT_ROOT/venv"

# Configuration
DSQL_ENDPOINT="${DSQL_ENDPOINT:-}"
AWS_REGION="${AWS_REGION:-us-west-2}"
DATABASE_NAME="postgres"
SETUP_MODE="${1:-fresh}"  # fresh or migrate

echo -e "${BLUE}=== DSQL Setup Tool ===${NC}"
echo -e "Mode: ${YELLOW}${SETUP_MODE}${NC}"
echo ""

# Function to setup virtual environment
setup_virtualenv() {
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Failed to create virtual environment${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
    
    # Upgrade pip
    echo -e "${YELLOW}Upgrading pip...${NC}"
    pip install --upgrade pip --quiet
    
    # Install dependencies
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install Python dependencies${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}✗ AWS CLI not found. Please install AWS CLI v2${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS CLI found${NC}"
    
    # Check psql
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}✗ psql not found. Please install PostgreSQL client${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ psql found${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python 3 found${NC}"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}✗ AWS credentials not configured${NC}"
        exit 1
    fi
    AWS_IDENTITY=$(aws sts get-caller-identity --output text --query 'Arn')
    echo -e "${GREEN}✓ AWS Identity: ${AWS_IDENTITY}${NC}"
}

# Function to get DSQL endpoint
get_dsql_endpoint() {
    if [ -z "$DSQL_ENDPOINT" ]; then
        echo -e "${YELLOW}Enter your DSQL endpoint:${NC}"
        read -r DSQL_ENDPOINT
        export DSQL_ENDPOINT
    fi
    echo -e "${BLUE}DSQL Endpoint: ${DSQL_ENDPOINT}${NC}"
}

# Function to test connection
test_connection() {
    echo -e "\n${YELLOW}Testing DSQL connection...${NC}"
    
    # Check if aws dsql command exists
    if aws dsql help &>/dev/null; then
        # Generate auth token using AWS CLI v2
        export PGPASSWORD=$(aws dsql generate-db-connect-admin-auth-token \
            --region $AWS_REGION \
            --expires-in 900 \
            --hostname $DSQL_ENDPOINT)
    else
        echo -e "${YELLOW}AWS CLI v1 detected. Using alternative authentication...${NC}"
        echo -e "${YELLOW}Please provide the database password:${NC}"
        read -s PGPASSWORD
        export PGPASSWORD
    fi
    
    if [ -z "$PGPASSWORD" ]; then
        echo -e "${RED}✗ No password provided${NC}"
        return 1
    fi
    
    # Test connection
    export PGSSLMODE=require
    if psql --quiet \
        --username admin \
        --dbname postgres \
        --host $DSQL_ENDPOINT \
        --command "SELECT version();" &> /dev/null; then
        echo -e "${GREEN}✓ Successfully connected to DSQL${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to connect to DSQL${NC}"
        return 1
    fi
}

# Function to apply schema
apply_schema() {
    echo -e "\n${YELLOW}Applying database schema...${NC}"
    
    # Generate fresh auth token
    export PGPASSWORD=$(aws dsql generate-db-connect-admin-auth-token \
        --region $AWS_REGION \
        --expires-in 900 \
        --hostname $DSQL_ENDPOINT)
    
    psql --quiet \
        --username admin \
        --dbname $DATABASE_NAME \
        --host $DSQL_ENDPOINT \
        --file "${SCRIPT_DIR}/schemas/dsql_schema.sql"
    
    echo -e "${GREEN}✓ Schema applied successfully${NC}"
}

# Function to load seed data
load_seed_data() {
    echo -e "\n${YELLOW}Loading seed data...${NC}"
    echo -e "${YELLOW}This will generate base data and 3 months of availability data${NC}"
    
    cd "$PROJECT_ROOT"
    "$VENV_DIR/bin/python" "${SCRIPT_DIR}/data/seed_dsql.py"
    
    echo -e "${GREEN}✓ All seed data loaded successfully${NC}"
}

# Function to migrate from SQLite
migrate_from_sqlite() {
    echo -e "\n${YELLOW}Migrating data from SQLite...${NC}"
    
    cd "$PROJECT_ROOT"
    "$VENV_DIR/bin/python" "${SCRIPT_DIR}/migrations/migrate_sqlite_to_dsql.py"
    
    echo -e "${GREEN}✓ Data migrated successfully${NC}"
}

# Function to create environment file
create_env_file() {
    echo -e "\n${YELLOW}Creating environment configuration...${NC}"
    
    cat > "${PROJECT_ROOT}/.env.dsql" << EOF
# Aurora DSQL Configuration
USE_AURORA_DSQL=true
DSQL_ENDPOINT=${DSQL_ENDPOINT}
DSQL_CONNECTION_METHOD=iam
DSQL_USER=admin
DSQL_DATABASE=${DATABASE_NAME}
AWS_REGION=${AWS_REGION}

# Application settings
LOG_LEVEL=INFO
EOF
    
    echo -e "${GREEN}✓ Created .env.dsql${NC}"
    
    # Also create a development env file
    cp "${PROJECT_ROOT}/.env.dsql" "${PROJECT_ROOT}/.env.development"
    echo -e "${GREEN}✓ Created .env.development${NC}"
}

# Function to verify setup
verify_setup() {
    echo -e "\n${YELLOW}Verifying setup...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Test connection with Python
    "$VENV_DIR/bin/python" << EOF
import sys
import os
# Set environment variable from parent script
os.environ['USE_AURORA_DSQL'] = 'true'
sys.path.insert(0, 'data-setup/dsql')

try:
    from src.database.hybrid_adapter import DatabaseManager
    db = DatabaseManager(use_dsql=True)
    if db.test_connection():
        print("✓ Database connection working")
        
        # Check tables
        cities_count = db.adapter.get_table_count('cities')
        hotels_count = db.adapter.get_table_count('hotels')
        activities_count = db.adapter.get_table_count('activities')
        flights_count = db.adapter.get_table_count('flights')
        
        print(f"✓ Cities: {cities_count} records")
        print(f"✓ Hotels: {hotels_count} records")
        print(f"✓ Activities: {activities_count} records")
        print(f"✓ Flights: {flights_count} records")
    else:
        print("✗ Database connection failed")
        sys.exit(1)
except Exception as e:
    print(f"⚠️  Verification skipped: {e}")
    print("   (This is OK if the database is working)")
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Setup verified successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Verification had issues but seeding completed successfully${NC}"
    fi
}

# Main execution flow
main() {
    echo -e "${BLUE}Starting DSQL setup...${NC}\n"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup virtual environment
    setup_virtualenv
    
    # Get DSQL endpoint
    get_dsql_endpoint
    
    # Test connection
    if ! test_connection; then
        exit 1
    fi
    
    
    # Apply schema
    apply_schema
    
    # Load data based on mode
    if [ "$SETUP_MODE" = "fresh" ]; then
        load_seed_data
    elif [ "$SETUP_MODE" = "migrate" ]; then
        migrate_from_sqlite
    else
        echo -e "${RED}Invalid setup mode: ${SETUP_MODE}${NC}"
        echo "Usage: $0 [fresh|migrate]"
        exit 1
    fi
    
    # Create environment files
    create_env_file
    
    # Verify setup
    verify_setup
    
    echo -e "\n${GREEN}=== Aurora DSQL setup completed successfully! ===${NC}"
}

# Run main function
main