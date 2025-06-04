# Travel Planner Backend

A serverless travel planning API built on AWS Lambda, providing intelligent trip planning through specialized AI agents.

### Components

- **API Gateway**: REST API endpoints for client applications
- **Proxy Lambda**: Request validation and orchestrator invocation
- **Orchestrator Lambda**: Coordinates specialist agents to build travel plans
- **Specialist Agents**:
  - Flight Specialist: Searches and recommends flights
  - Hotel Specialist: Finds accommodations matching preferences
  - Activities Curator: Discovers experiences and attractions
  - Destination Expert: Provides insights via Bedrock Knowledge Base
  - Budget Analyst: Tracks and optimizes travel expenses
  - Itinerary Builder: Creates day-by-day travel plans
- **DynamoDB**: Stores travel plans and planning state
- **Amazon DSQL**: Travel data (cities, flights, hotels, activities)
- **Bedrock Knowledge Base**: Destination information and recommendations

### Prerequisites

- AWS CLI v2 configured with credentials
- Python 3.12
- PostgreSQL client (`psql`)
- Node.js

###  Setup

### Step 1: Create DSQL Database

1. **Create DSQL Cluster** (AWS Console or CLI):
   ```bash
   # Create a single or multi-region cluster named "travel-planner-dsql" in your preferred region
   ```

2. **Set environment variables**:
   ```bash
   
   export DSQL_ENDPOINT=your-cluster-endpoint.dsql.region.on.aws
   export AWS_REGION=us-west-2
   export DSQL_DATABASE=postgres
   export DSQL_USER=admin
   ```

3. **Setup database schema and seed data**:
   ```bash
   cd data-setup/dsql
   ./setup_dsql.sh fresh
   ```

   This will:
   - Create a Python virtual environment (if needed)
   - Install all required dependencies
   - Apply the schema (cities, hotels, activities, flight_routes, etc.)
   - Seed with sample data
   
   Note: The script automatically manages a virtual environment in `backend/venv/`

### Step 2: Create Bedrock Knowledge Base

1. Navigate to Amazon Bedrock → Knowledge bases
2. Click "Create knowledge base with vector store"
3. Configure:
   - Name: `travel-planner-kb`
   - Select `Amazon S3` as your data source
   - Select an empty S3 bucket or folder
   - Select Amazon Bedrock default parser
   - Set Chunking Strategy to `No Chunking`
   - Embeddings model: `Titan Embeddings V2`
   - Vector database: `OpenSearch Serverless`
   - Select `Create`

4. **Prepare and upload documents**:
   ```bash
   cd data-setup/knowledge_base
   python3 create_kb_documents.py
   # This creates JSON documents in kb_data/
   ```

5. Upload the generated documents to your S3 folder and sync with Knowledge Base

6. Note the Knowledge Base ID (e.g., `TMLXOGDYXH`)

### Step 3: Deploy Backend Infrastructure

#### Option A: Automated Deployment (Recommended)

Run the complete deployment script that handles all steps:

```bash
cd travel-planner/backend

# Set required environment variables
export KB_ID=your-knowledge-base-id
export DSQL_ENDPOINT=your-cluster.dsql.region.on.aws
export AWS_REGION=us-west-2

# Run complete deployment
./scripts/deploy_all.sh
```

This script will:
1. Create DynamoDB table for plan storage
2. Package Lambda dependencies
3. Deploy orchestrator Lambda function
4. Deploy proxy Lambda function
5. Update IAM permissions
6. Setup API Gateway with all endpoints
7. Configure environment variables

#### Option B: Manual Step-by-Step Deployment

If you prefer to run each step manually:

1. **Create DynamoDB Table**:
   ```bash
   aws dynamodb create-table \
     --table-name travel-planner-plans \
     --attribute-definitions \
       AttributeName=plan_id,AttributeType=S \
     --key-schema \
       AttributeName=plan_id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --region $AWS_REGION
   ```

2. **Package dependencies**:
   ```bash
   cd travel-planner/backend
   ./scripts/package.sh
   ```

3. **Deploy orchestrator Lambda**:
   ```bash
   # Ensure DSQL_ENDPOINT is set (required)
   export DSQL_ENDPOINT=your-cluster.dsql.region.on.aws
   ./scripts/deploy.sh
   ```

4. **Deploy proxy Lambda**:
   ```bash
   ./scripts/deploy_proxy.sh
   ```

5. **Update permissions**:
   ```bash
   ./scripts/update_orchestrator_permissions.sh
   ```

6. **Setup API Gateway**:
   ```bash
   ./scripts/setup_api_gateway.sh
   ```

7. **Configure environment variables**:
   ```bash
   # For orchestrator Lambda
   aws lambda update-function-configuration \
     --function-name travel-planner-orchestrator \
     --environment Variables="{
       KB_ID=$KB_ID,
       KB_REGION=$AWS_REGION,
       DSQL_ENDPOINT=$DSQL_ENDPOINT,
       DSQL_DATABASE=$DSQL_DATABASE,
       DSQL_USER=$DSQL_USER,
       PLANS_TABLE_NAME=travel-planner-plans
     }" \
     --region $AWS_REGION

   # For proxy Lambda
   aws lambda update-function-configuration \
     --function-name travel-planner-proxy \
     --environment Variables="{
       ORCHESTRATOR_FUNCTION_NAME=travel-planner-orchestrator
     }" \
     --region $AWS_REGION
   ```

## 📂 Project Structure

```
backend/
├── lambda/                     # Lambda function code
│   ├── handler.py             # Main orchestrator handler
│   ├── orchestrator_wrapper.py # DynamoDB integration wrapper
│   ├── proxy_handler.py       # API proxy handler
│   ├── tools/                 # Agent tool implementations
│   └── utils/                 # Shared utilities
├── data-setup/                # Database setup
│   └── dsql/                  # DSQL schema and seeding
│       ├── schemas/           # Database schemas
│       └── data/              # Seed data scripts
├── scripts/                   # Deployment scripts
│   ├── deploy_all.sh         # Complete deployment
│   ├── package.sh            # Package Lambda code
│   └── setup_api_gateway.sh  # Configure API Gateway
├── packaging/                 # Build artifacts
└── requirements-lambda.txt    # Lambda dependencies
```

## 🔧 Configuration

### Environment Variables

**Orchestrator Lambda:**
- `KB_ID`: Bedrock Knowledge Base ID
- `KB_REGION`: AWS region for Knowledge Base
- `DSQL_ENDPOINT`: DSQL cluster endpoint
- `DSQL_DATABASE`: Database name (default: postgres)
- `DSQL_USER`: Database user (default: admin)
- `PLANS_TABLE_NAME`: DynamoDB table name

**Proxy Lambda:**
- `ORCHESTRATOR_FUNCTION_NAME`: Name of orchestrator Lambda

## 📡 API Endpoints

### Start Planning
```bash
POST /api/planning/start
{
  "user_goal": "I want to visit Paris for 5 days",
  "user_id": "user-123"
}
```

### Continue Planning
```bash
POST /api/planning/continue
{
  "plan_id": "plan-xyz",
  "user_input": "I prefer boutique hotels"
}
```

### Get Plan Status
```bash
GET /api/planning/{plan_id}/status
```

### Finalize Plan
```bash
POST /api/planning/{plan_id}/finalize
```

## 📝 API Response Examples

### Successful Planning Start
```json
{
  "statusCode": 200,
  "body": {
    "plan_id": "plan-123",
    "status": "in_progress",
    "message": "Planning started"
  }
}
```

### Plan Status
```json
{
  "statusCode": 200,
  "body": {
    "plan_id": "plan-123",
    "status": "completed",
    "plan": {
      "flights": [...],
      "hotels": [...],
      "activities": [...],
      "total_cost": 2850
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **DSQL Connection Failed**
   - Verify IAM role has `dsql:GenerateDbConnectAdminAuthToken`
   - Check DSQL endpoint is correct
   - Ensure Lambda is in same region

2. **Knowledge Base Not Found**
   - Verify KB_ID environment variable
   - Check IAM permissions for Bedrock

3. **DynamoDB Access Denied**
   - Run `update_orchestrator_permissions.sh`
   - Verify table name in environment variables

## 📚 Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon DSQL Documentation](https://docs.aws.amazon.com/dsql/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)