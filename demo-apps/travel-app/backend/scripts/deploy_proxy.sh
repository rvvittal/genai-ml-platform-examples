#!/bin/bash

# Deploy Proxy Lambda Function
# This script deploys the proxy Lambda that adapts REST API calls to the orchestrator

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

echo "🚀 Deploying Travel Planner Proxy Lambda..."

# Configuration
FUNCTION_NAME="travel-planner-proxy"
ORCHESTRATOR_FUNCTION_NAME="travel-planner-orchestrator"
ROLE_NAME="travel-planner-proxy-role"
REGION="${AWS_REGION:-us-west-2}"
RUNTIME="python3.11"
TIMEOUT=60
MEMORY_SIZE=512
TABLE_NAME="travel-planner-plans"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Configuration:"
echo "  - Function Name: $FUNCTION_NAME"
echo "  - Orchestrator: $ORCHESTRATOR_FUNCTION_NAME"
echo "  - Region: $REGION"
echo "  - Account: $ACCOUNT_ID"
echo "  - DynamoDB Table: $TABLE_NAME"

# Create DynamoDB table if it doesn't exist
echo "📊 Setting up DynamoDB table..."
if ! aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION >/dev/null 2>&1; then
    echo "Creating DynamoDB table: $TABLE_NAME"
    aws dynamodb create-table \
        --table-name $TABLE_NAME \
        --attribute-definitions AttributeName=plan_id,AttributeType=S \
        --key-schema AttributeName=plan_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region $REGION
    
    echo "Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION
else
    echo "Table $TABLE_NAME already exists"
fi

# Create IAM role if it doesn't exist
echo "🔐 Setting up IAM role..."
if ! aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
    echo "Creating IAM role: $ROLE_NAME"
    
    # Create trust policy
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Create and attach custom policy for Lambda invoke and DynamoDB
    cat > /tmp/proxy-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$ORCHESTRATOR_FUNCTION_NAME"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$TABLE_NAME"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name ProxyLambdaPolicy \
        --policy-document file:///tmp/proxy-policy.json
    
    echo "Waiting for role to propagate..."
    sleep 10
else
    echo "Role $ROLE_NAME already exists"
fi

# Package Lambda function
echo "📦 Packaging Lambda function..."
cd lambda
zip -q /tmp/proxy-lambda.zip proxy_handler.py

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb:///tmp/proxy-lambda.zip \
        --region $REGION
    
    # Wait for code update to complete
    echo "⏳ Waiting for code update to complete..."
    aws lambda wait function-updated \
        --function-name $FUNCTION_NAME \
        --region $REGION
    
    # Update configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --environment Variables="{ORCHESTRATOR_FUNCTION_NAME=$ORCHESTRATOR_FUNCTION_NAME,PLANS_TABLE_NAME=$TABLE_NAME}" \
        --region $REGION
    
    # Wait for configuration update to complete
    echo "⏳ Waiting for configuration update to complete..."
    aws lambda wait function-updated \
        --function-name $FUNCTION_NAME \
        --region $REGION
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME \
        --handler proxy_handler.handler \
        --zip-file fileb:///tmp/proxy-lambda.zip \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --environment Variables="{ORCHESTRATOR_FUNCTION_NAME=$ORCHESTRATOR_FUNCTION_NAME,PLANS_TABLE_NAME=$TABLE_NAME}" \
        --region $REGION
fi

# Clean up
rm -f /tmp/proxy-lambda.zip /tmp/trust-policy.json /tmp/proxy-policy.json

echo "✅ Proxy Lambda deployment complete!"
