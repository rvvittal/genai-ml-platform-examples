#!/bin/bash

# Update orchestrator Lambda to use wrapper and add DynamoDB permissions

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

echo "🔧 Updating Orchestrator Lambda permissions..."

# Configuration
ORCHESTRATOR_FUNCTION_NAME="travel-planner-orchestrator"
REGION="${AWS_REGION:-us-west-2}"
TABLE_NAME="travel-planner-plans"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Configuration:"
echo "  - Function: $ORCHESTRATOR_FUNCTION_NAME"
echo "  - Region: $REGION"
echo "  - Table: $TABLE_NAME"

# Get current role
ROLE_ARN=$(aws lambda get-function-configuration \
    --function-name $ORCHESTRATOR_FUNCTION_NAME \
    --region $REGION \
    --query 'Role' \
    --output text)

ROLE_NAME=$(echo $ROLE_ARN | awk -F'/' '{print $NF}')

echo "  - Role: $ROLE_NAME"

# Add DynamoDB permissions to the role
echo "🔐 Adding DynamoDB permissions..."

cat > /tmp/dynamodb-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$TABLE_NAME"
    }
  ]
}
EOF

# Create or update the policy
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name OrchestratorDynamoDBPolicy \
    --policy-document file:///tmp/dynamodb-policy.json

echo "✅ Permissions updated"

# Update function configuration to add environment variable
echo "🔧 Updating function configuration..."

aws lambda update-function-configuration \
    --function-name $ORCHESTRATOR_FUNCTION_NAME \
    --environment Variables="{$(aws lambda get-function-configuration --function-name $ORCHESTRATOR_FUNCTION_NAME --region $REGION --query 'Environment.Variables' --output text | sed 's/\t/=/g' | tr '\n' ',' | sed 's/,$//')${EXISTING_VARS:+,}PLANS_TABLE_NAME=$TABLE_NAME}" \
    --region $REGION > /dev/null

echo "⏳ Waiting for configuration update to complete..."
aws lambda wait function-updated \
    --function-name $ORCHESTRATOR_FUNCTION_NAME \
    --region $REGION

echo "✅ Environment variables updated"

# Package the wrapper with the existing code
echo "📦 Creating deployment package with wrapper..."

cd lambda
cp orchestrator_wrapper.py /tmp/
cp handler.py /tmp/
cp -r tools /tmp/
cp -r utils /tmp/
cd /tmp

# Create deployment package
zip -r orchestrator-with-wrapper.zip orchestrator_wrapper.py handler.py tools/ utils/ > /dev/null

# Update function code and handler
echo "🚀 Updating function code..."

aws lambda update-function-code \
    --function-name $ORCHESTRATOR_FUNCTION_NAME \
    --zip-file fileb://orchestrator-with-wrapper.zip \
    --region $REGION > /dev/null

echo "⏳ Waiting for code update to complete..."
aws lambda wait function-updated \
    --function-name $ORCHESTRATOR_FUNCTION_NAME \
    --region $REGION

# Update handler to use wrapper
echo "🔧 Updating handler..."
aws lambda update-function-configuration \
    --function-name $ORCHESTRATOR_FUNCTION_NAME \
    --handler orchestrator_wrapper.handler \
    --region $REGION > /dev/null

echo "⏳ Waiting for handler update to complete..."
aws lambda wait function-updated \
    --function-name $ORCHESTRATOR_FUNCTION_NAME \
    --region $REGION

# Clean up
rm -rf /tmp/orchestrator-with-wrapper.zip /tmp/dynamodb-policy.json /tmp/handler.py /tmp/orchestrator_wrapper.py /tmp/tools /tmp/utils

echo "✅ Orchestrator updated successfully!"
echo ""
echo "The orchestrator will now:"
echo "1. Save results to DynamoDB when complete"
echo "2. Update plan status to 'completed' or 'failed'"
echo "3. Store processing duration for monitoring"