#!/bin/bash

# Complete deployment script: Package and Deploy Lambda with DSQL integration
set -e

echo "🚀 Complete Travel Planner Lambda Deployment"
echo "============================================="

# Change to project root
cd "$(dirname "$0")/.."

# Step 1: Package the Lambda
echo ""
echo "📦 Step 1: Packaging Lambda function..."
./scripts/package.sh

# Step 2: Deploy the Lambda
echo ""
echo "🚀 Step 2: Deploying Lambda function..."
./scripts/deploy.sh

echo ""
echo "🎉 Complete deployment finished!"
echo ""
echo "📚 Usage Examples:"
echo "  Find hotels: /usr/local/bin/aws lambda invoke --function-name travel-planner-orchestrator --payload '{\"prompt\":\"Find luxury hotels in Paris\"}' /tmp/response.json"
echo "  Search destinations: /usr/local/bin/aws lambda invoke --function-name travel-planner-orchestrator --payload '{\"prompt\":\"Recommend romantic destinations in Europe\"}' /tmp/response.json"
echo "  Plan trip: /usr/local/bin/aws lambda invoke --function-name travel-planner-orchestrator --payload '{\"prompt\":\"Plan a 5-day trip to Tokyo for $3000\"}' /tmp/response.json"