#!/bin/bash

# Setup API Gateway for Travel Planner Proxy
# Creates REST API with routes that match frontend expectations

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

echo "🌐 Setting up API Gateway for Travel Planner..."

# Configuration
API_NAME="TravelPlannerAPI"
PROXY_FUNCTION_NAME="travel-planner-proxy"
REGION="${AWS_REGION:-us-west-2}"
STAGE_NAME="prod"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Configuration:"
echo "  - API Name: $API_NAME"
echo "  - Lambda Function: $PROXY_FUNCTION_NAME"
echo "  - Region: $REGION"
echo "  - Account: $ACCOUNT_ID"
echo "  - Stage: $STAGE_NAME"

# Check if API already exists
EXISTING_API=$(aws apigateway get-rest-apis --region $REGION --query "items[?name=='$API_NAME'].id" --output text)

if [ -n "$EXISTING_API" ]; then
    echo "⚠️  API '$API_NAME' already exists with ID: $EXISTING_API"
    echo -n "Do you want to delete and recreate it? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Deleting existing API..."
        aws apigateway delete-rest-api --rest-api-id $EXISTING_API --region $REGION
        sleep 5
    else
        API_ID=$EXISTING_API
        ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/'].id" --output text)
    fi
fi

# Create REST API if needed
if [ -z "$API_ID" ]; then
    echo "🆕 Creating REST API..."
    API_ID=$(aws apigateway create-rest-api \
        --name $API_NAME \
        --description "Travel Planner API Gateway" \
        --endpoint-configuration types=REGIONAL \
        --region $REGION \
        --query 'id' \
        --output text)
    
    echo "API created with ID: $API_ID"
    
    # Get root resource ID
    ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/'].id" --output text)
fi

# Create /api resource
echo "📁 Creating API resources..."
API_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part "api" \
    --region $REGION \
    --query 'id' \
    --output text)

# Create /api/planning resource
PLANNING_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $API_RESOURCE \
    --path-part "planning" \
    --region $REGION \
    --query 'id' \
    --output text)

# Create /api/planning/start resource
START_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PLANNING_RESOURCE \
    --path-part "start" \
    --region $REGION \
    --query 'id' \
    --output text)

# Create /api/planning/continue resource
CONTINUE_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PLANNING_RESOURCE \
    --path-part "continue" \
    --region $REGION \
    --query 'id' \
    --output text)

# Create /api/planning/{plan_id} resource
PLAN_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PLANNING_RESOURCE \
    --path-part "{plan_id}" \
    --region $REGION \
    --query 'id' \
    --output text)

# Create /api/planning/{plan_id}/status resource
STATUS_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PLAN_ID_RESOURCE \
    --path-part "status" \
    --region $REGION \
    --query 'id' \
    --output text)

# Create /api/planning/{plan_id}/finalize resource
FINALIZE_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PLAN_ID_RESOURCE \
    --path-part "finalize" \
    --region $REGION \
    --query 'id' \
    --output text)

# Function to create method and integration
create_method() {
    local RESOURCE_ID=$1
    local HTTP_METHOD=$2
    local RESOURCE_PATH=$3
    
    echo "🔧 Creating $HTTP_METHOD method for $RESOURCE_PATH..."
    
    # Create method
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method $HTTP_METHOD \
        --authorization-type NONE \
        --region $REGION
    
    # Create integration
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method $HTTP_METHOD \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$PROXY_FUNCTION_NAME/invocations" \
        --region $REGION
    
    # Create method response
    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method $HTTP_METHOD \
        --status-code 200 \
        --response-models '{"application/json": "Empty"}' \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin": false}' \
        --region $REGION
    
    # Create integration response
    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method $HTTP_METHOD \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}' \
        --region $REGION
}

# Function to create OPTIONS method for CORS
create_options_method() {
    local RESOURCE_ID=$1
    local RESOURCE_PATH=$2
    
    echo "🔧 Creating OPTIONS method for $RESOURCE_PATH (CORS)..."
    
    # Create OPTIONS method
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION
    
    # Create mock integration for OPTIONS
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
        --region $REGION
    
    # Create method response for OPTIONS
    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-models '{"application/json": "Empty"}' \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Origin": false}' \
        --region $REGION
    
    # Create integration response for OPTIONS
    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'", "method.response.header.Access-Control-Allow-Methods": "'"'"'GET,POST,OPTIONS'"'"'", "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}' \
        --region $REGION
}

# Create methods for each endpoint
echo "🛠️  Creating API methods..."
create_method $START_RESOURCE "POST" "/api/planning/start"
create_options_method $START_RESOURCE "/api/planning/start"

create_method $CONTINUE_RESOURCE "POST" "/api/planning/continue"
create_options_method $CONTINUE_RESOURCE "/api/planning/continue"

create_method $STATUS_RESOURCE "GET" "/api/planning/{plan_id}/status"
create_options_method $STATUS_RESOURCE "/api/planning/{plan_id}/status"

create_method $FINALIZE_RESOURCE "POST" "/api/planning/{plan_id}/finalize"
create_options_method $FINALIZE_RESOURCE "/api/planning/{plan_id}/finalize"

# Grant Lambda permission for API Gateway to invoke
echo "🔐 Granting API Gateway permission to invoke Lambda..."
aws lambda add-permission \
    --function-name $PROXY_FUNCTION_NAME \
    --statement-id apigateway-invoke-$(date +%s) \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
    --region $REGION 2>/dev/null || true

# Deploy API
echo "🚀 Deploying API to stage: $STAGE_NAME..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --description "Initial deployment" \
    --region $REGION

# Get the invoke URL
INVOKE_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME"

echo ""
echo "✅ API Gateway setup complete!"
echo ""
echo "🌐 API Endpoint: $INVOKE_URL"
echo ""
echo "📋 Frontend Configuration:"
echo "Add these to your frontend .env file:"
echo ""
echo "REACT_APP_API_ENDPOINT=$INVOKE_URL"
echo "REACT_APP_USE_BACKEND_STRANDS=true"
echo ""

# Save configuration
cat > api_config.json <<EOF
{
  "api_id": "$API_ID",
  "api_endpoint": "$INVOKE_URL",
  "region": "$REGION",
  "stage": "$STAGE_NAME",
  "proxy_function": "$PROXY_FUNCTION_NAME"
}
EOF

echo "📄 API configuration saved to api_config.json"