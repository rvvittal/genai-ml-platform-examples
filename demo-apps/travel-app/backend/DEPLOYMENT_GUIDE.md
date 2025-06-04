# Travel Planner Backend - Complete Deployment Guide

This guide provides step-by-step instructions for deploying the Travel Planner backend infrastructure and services on AWS.

## Prerequisites

1. **AWS CLI v2** - Installed and configured with appropriate credentials
2. **Python 3.12** - For Lambda runtime compatibility
3. **PostgreSQL client** (`psql`) - For database setup
4. **Node.js** (optional) - If using AWS CDK for infrastructure
5. **AWS Account** with permissions for:
   - Lambda
   - API Gateway
   - DynamoDB
   - DSQL
   - Bedrock (Knowledge Base)
   - IAM

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   API Gateway   │────▶│  Proxy Lambda    │────▶│ Orchestrator    │
└─────────────────┘     └──────────────────┘     │    Lambda       │
                                                  └────────┬────────┘
                                                           │
                                                  ┌────────▼────────┐
                                                  │   Specialist    │
                                                  │     Agents      │
                                                  └────────┬────────┘
                                                           │
                              ┌────────────────────────────┼────────────────────────────┐
                              │                            │                            │
                        ┌─────▼─────┐              ┌──────▼──────┐            ┌────────▼────────┐
                        │ DynamoDB  │              │    DSQL     │            │ Bedrock         │
                        │  (Plans)  │              │ (Travel DB) │            │ Knowledge Base  │
                        └───────────┘              └─────────────┘            └─────────────────┘
```

**Specialist Agents:**
- **Flight Specialist**: Searches and recommends flights from DSQL
- **Hotel Specialist**: Finds accommodations matching preferences from DSQL  
- **Activities Curator**: Discovers experiences and attractions from DSQL
- **Destination Expert**: Provides destination insights via Bedrock Knowledge Base
- **Budget Analyst**: Tracks and optimizes travel expenses
- **Itinerary Builder**: Creates day-by-day travel plans


### API Endpoints

After deployment, the following REST API endpoints will be available:
- `POST /api/planning/start` - Start a new travel plan
- `POST /api/planning/continue` - Continue planning with user input
- `GET /api/planning/{plan_id}/status` - Get plan status
- `POST /api/planning/{plan_id}/finalize` - Finalize the plan

## Testing the Deployment

1. **Test Lambda directly**:
   ```bash
   ./scripts/test.sh "Plan a 5-day trip to Paris with $3000 budget"
   ```

2. **Test via API Gateway**:
   ```bash
   # Get API endpoint from api_config.json after setup
   ./scripts/test_proxy.sh
   ```

3. **Test database connectivity**:
   ```bash
   cd data-setup/dsql
   ./test_dsql_direct.sh
   ```

## Monitoring and Troubleshooting

### CloudWatch Logs

View Lambda logs:
```bash
aws logs tail /aws/lambda/travel-planner-orchestrator --follow --region $AWS_REGION
aws logs tail /aws/lambda/travel-planner-proxy --follow --region $AWS_REGION
```

### Common Issues

1. **DSQL Connection Failed**
   - Verify IAM role has `dsql:GenerateDbConnectAdminAuthToken` permission
   - Check DSQL endpoint is correct
   - Ensure Lambda is in same region as DSQL cluster

2. **Knowledge Base Not Found**
   - Verify KB_ID environment variable
   - Check IAM permissions for Bedrock access

3. **DynamoDB Access Denied**
   - Run `update_orchestrator_permissions.sh` to add DynamoDB permissions
   - Verify table name in environment variables

### Backup and Recovery

1. **DSQL**: Automatic backups enabled by default
2. **DynamoDB**: Enable point-in-time recovery
3. **Lambda code**: Store in version control
4. **Knowledge Base**: Backup source documents in S3
