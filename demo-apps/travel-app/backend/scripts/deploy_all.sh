#!/bin/bash

# Complete deployment script for Travel Planner Backend
# This script orchestrates all deployment steps in the correct order

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

echo "🚀 Travel Planner Backend - Complete Deployment"
echo "==============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="${AWS_REGION:-us-west-2}"
TABLE_NAME="travel-planner-plans"
KB_ID="${KB_ID:-your-knowledge-base-id}"
DSQL_ENDPOINT="${DSQL_ENDPOINT:-your-dsql-endpoint}"
DSQL_DATABASE="${DSQL_DATABASE:-postgres}"
DSQL_USER="${DSQL_USER:-admin}"

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}✗ AWS CLI not found. Please install AWS CLI v2${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS CLI found${NC}"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}✗ AWS credentials not configured${NC}"
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo -e "${GREEN}✓ AWS configured (Account: $ACCOUNT_ID)${NC}"
    
    # Check if required environment variables are set
    if [ "$KB_ID" = "your-knowledge-base-id" ]; then
        echo -e "${YELLOW}⚠️  KB_ID not set. Please set the Knowledge Base ID:${NC}"
        echo -e "${YELLOW}   export KB_ID=your-actual-kb-id${NC}"
        read -p "Enter Knowledge Base ID (or press Enter to skip): " input_kb_id
        if [ -n "$input_kb_id" ]; then
            KB_ID="$input_kb_id"
        fi
    fi
    
    if [ "$DSQL_ENDPOINT" = "your-dsql-endpoint" ]; then
        echo -e "${YELLOW}⚠️  DSQL_ENDPOINT not set. Please set the DSQL endpoint:${NC}"
        echo -e "${YELLOW}   export DSQL_ENDPOINT=your-cluster.dsql.region.on.aws${NC}"
        read -p "Enter DSQL Endpoint (or press Enter to skip): " input_dsql
        if [ -n "$input_dsql" ]; then
            DSQL_ENDPOINT="$input_dsql"
        fi
    fi
}

# Step 1: Create DynamoDB Table
create_dynamodb_table() {
    echo -e "\n${BLUE}Step 1: Creating DynamoDB Table...${NC}"
    
    # Check if table already exists
    if aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION &>/dev/null; then
        echo -e "${YELLOW}⚠️  Table $TABLE_NAME already exists${NC}"
    else
        echo "Creating table $TABLE_NAME..."
        aws dynamodb create-table \
            --table-name $TABLE_NAME \
            --attribute-definitions \
                AttributeName=plan_id,AttributeType=S \
            --key-schema \
                AttributeName=plan_id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region $REGION \
            --output text
        
        echo "Waiting for table to be active..."
        aws dynamodb wait table-exists \
            --table-name $TABLE_NAME \
            --region $REGION
        
        echo -e "${GREEN}✓ DynamoDB table created${NC}"
    fi
}

# Step 2: Package dependencies
package_lambda() {
    echo -e "\n${BLUE}Step 2: Packaging Lambda dependencies...${NC}"
    cd "$PROJECT_ROOT"
    
    if [ -f "packaging/dependencies.zip" ] && [ -f "packaging/app.zip" ]; then
        echo -e "${YELLOW}Package files already exist. Regenerate? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Using existing packages..."
            return
        fi
    fi
    
    ./scripts/package.sh
    echo -e "${GREEN}✓ Lambda packages created${NC}"
}

# Step 3: Deploy orchestrator Lambda
deploy_orchestrator() {
    echo -e "\n${BLUE}Step 3: Deploying Orchestrator Lambda...${NC}"
    cd "$PROJECT_ROOT"
    
    # Export environment variables for deploy script
    export KB_ID
    export DSQL_ENDPOINT
    export DSQL_DATABASE
    export DSQL_USER
    
    ./scripts/deploy.sh
    echo -e "${GREEN}✓ Orchestrator Lambda deployed${NC}"
}

# Step 4: Deploy proxy Lambda
deploy_proxy() {
    echo -e "\n${BLUE}Step 4: Deploying Proxy Lambda...${NC}"
    cd "$PROJECT_ROOT"
    
    if [ -f "scripts/deploy_proxy.sh" ]; then
        ./scripts/deploy_proxy.sh
        echo -e "${GREEN}✓ Proxy Lambda deployed${NC}"
    else
        echo -e "${YELLOW}⚠️  deploy_proxy.sh not found, skipping...${NC}"
    fi
}

# Step 5: Update permissions
update_permissions() {
    echo -e "\n${BLUE}Step 5: Updating Lambda permissions...${NC}"
    cd "$PROJECT_ROOT"
    
    ./scripts/update_orchestrator_permissions.sh
    echo -e "${GREEN}✓ Permissions updated${NC}"
}

# Step 6: Setup API Gateway
setup_api_gateway() {
    echo -e "\n${BLUE}Step 6: Setting up API Gateway...${NC}"
    cd "$PROJECT_ROOT"
    
    ./scripts/setup_api_gateway.sh
    echo -e "${GREEN}✓ API Gateway configured${NC}"
    
    # Display API endpoint
    if [ -f "api_config.json" ]; then
        API_ENDPOINT=$(cat api_config.json | grep -o '"api_endpoint":[^,]*' | cut -d'"' -f4)
        echo -e "\n${GREEN}API Endpoint: $API_ENDPOINT${NC}"
    fi
}

# Step 7: Update Lambda environment variables
update_env_variables() {
    echo -e "\n${BLUE}Step 7: Updating Lambda environment variables...${NC}"
    
    # Update orchestrator Lambda
    echo "Updating orchestrator Lambda environment..."
    aws lambda update-function-configuration \
        --function-name travel-planner-orchestrator \
        --environment Variables="{
            KB_ID=$KB_ID,
            KB_REGION=$REGION,
            DSQL_ENDPOINT=$DSQL_ENDPOINT,
            DSQL_DATABASE=$DSQL_DATABASE,
            DSQL_USER=$DSQL_USER,
            PLANS_TABLE_NAME=$TABLE_NAME
        }" \
        --region $REGION \
        --output text > /dev/null
    
    # Update proxy Lambda if it exists
    if aws lambda get-function --function-name travel-planner-proxy --region $REGION &>/dev/null; then
        echo "Updating proxy Lambda environment..."
        aws lambda update-function-configuration \
            --function-name travel-planner-proxy \
            --environment Variables="{
                ORCHESTRATOR_FUNCTION_NAME=travel-planner-orchestrator
            }" \
            --region $REGION \
            --output text > /dev/null
    fi
    
    echo -e "${GREEN}✓ Environment variables updated${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting deployment at $(date)${NC}"
    echo -e "${BLUE}Region: $REGION${NC}"
    
    # Check prerequisites
    check_prerequisites
    
    # Confirm deployment
    echo -e "\n${YELLOW}Ready to deploy with:${NC}"
    echo "  - Region: $REGION"
    echo "  - DynamoDB Table: $TABLE_NAME"
    echo "  - Knowledge Base ID: $KB_ID"
    echo "  - DSQL Endpoint: $DSQL_ENDPOINT"
    echo ""
    read -p "Continue with deployment? (Y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [ -n "$REPLY" ]; then
        echo "Deployment cancelled."
        exit 1
    fi
    
    # Execute deployment steps
    create_dynamodb_table
    package_lambda
    deploy_orchestrator
    deploy_proxy
    update_permissions
    setup_api_gateway
    update_env_variables
    
    # Summary
    echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "\n${BLUE}Summary:${NC}"
    echo "  ✓ DynamoDB table: $TABLE_NAME"
    echo "  ✓ Orchestrator Lambda: travel-planner-orchestrator"
    echo "  ✓ Proxy Lambda: travel-planner-proxy"
    echo "  ✓ API Gateway configured"
    
    if [ -f "api_config.json" ]; then
        API_ENDPOINT=$(cat api_config.json | grep -o '"api_endpoint":[^,]*' | cut -d'"' -f4)
        echo -e "\n${BLUE}API Endpoint:${NC}"
        echo "  $API_ENDPOINT"
        
    fi
    
    
    echo -e "\n${GREEN}Deployment completed at $(date)${NC}"
}

# Run main function
main "$@"