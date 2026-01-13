# Streamline Your ML Migration Journey: Getting Started with SageMigrator

Moving machine learning workloads from EC2 instances to Amazon SageMaker can feel like navigating a complex maze. Between analyzing code compatibility, generating infrastructure templates, and ensuring pre-production readiness, the migration process often becomes a bottleneck that delays your ML initiatives. What if there was a way to automate this entire journey with just a few commands?

Enter **SageMigrator** – an intelligent CLI tool that transforms the daunting task of EC2-to-SageMaker migration into a streamlined, automated workflow. In this guide, we'll walk you through everything you need to know to get started with SageMigrator and successfully migrate your first ML project.

## Introduction: Solving the Migration Challenge

### The Problem with Manual Migration

Organizations running machine learning workloads on EC2 instances face several challenges when migrating to SageMaker:

- **Code Compatibility Issues**: Existing training scripts often require significant modifications to work with SageMaker's managed environment
- **Infrastructure Complexity**: Setting up proper IAM roles, S3 buckets, and networking configurations manually is error-prone and time-consuming  
- **MLOps Integration**: Creating end-to-end pipelines with preprocessing, training, evaluation, and model registration requires deep SageMaker expertise
- **Production Readiness**: Ensuring security best practices, cost optimization, and monitoring configurations meet enterprise standards

### How SageMigrator Addresses These Challenges

SageMigrator is designed to eliminate these pain points through intelligent automation:

🔍 **Automated Code Analysis**: Scans your existing ML code to identify compatibility issues, dependencies, and migration requirements

🏗️ **Infrastructure Generation**: Creates pre-production-ready CloudFormation templates with proper IAM roles, S3 buckets, and security configurations

🚀 **Complete MLOps Pipelines**: Generates end-to-end SageMaker pipelines with preprocessing, training, evaluation, and conditional model registration

✅ **Production Validation**: Includes comprehensive testing suites and security validation to ensure enterprise readiness

🎯 **Cost Optimization**: Implements best practices like spot instances and compute-optimized instance types to minimize costs

## Getting Started: Installation and Setup

### Prerequisites

Before installing SageMigrator, ensure you have the following prerequisites:

**System Requirements:**
- Python 3.8 or higher
- AWS CLI configured with appropriate permissions
- Virtual environment (recommended)

**AWS Permissions:**
Your AWS credentials need the following permissions:
- SageMaker full access
- S3 bucket creation and management  
- IAM role creation and management
- CloudFormation stack operations
- CloudWatch logs access

### Installation Steps

**1. Clone the Repository**
```bash
git clone <repository-url>
cd genai-ml-platform-examples/migration
```

**2. Create and Activate Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Install SageMigrator in Development Mode**
```bash
pip install -e .
```

**5. Verify Installation**
```bash
python -m sagemigrator --help
```

You should see the SageMigrator CLI help menu with available commands.

**6. Configure AWS Credentials**
```bash
aws configure
# OR set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Understanding the Core Commands

SageMigrator follows a simple three-step workflow:

#### 1. **migrate** - Analyze and Generate Artifacts
The `migrate` command is your starting point. It analyzes your existing ML code and generates all necessary SageMaker-compatible artifacts.

```bash
python -m sagemigrator migrate <source-directory> -o <output-directory>
```

**Key Features:**
- Analyzes code for SageMaker compatibility issues
- Generates training scripts, pipelines, and infrastructure code
- Creates comprehensive testing suites
- Supports both PyTorch and SKLearn processors
- Includes validation and documentation

**Options:**
- `--processor-type`: Choose between `pytorch` or `sklearn` (default: `sklearn`)
- `--interactive`: Enable interactive mode with confirmations
- `--dry-run`: Preview what would be generated without creating files
- `--skip-validation`: Skip validation of generated artifacts

#### 2. **deploy** - Create AWS Infrastructure
The `deploy` command creates the necessary AWS infrastructure using CloudFormation.

```bash
python -m sagemigrator deploy <artifacts-directory>
```

**What Gets Deployed:**
- IAM execution role with appropriate permissions
- S3 bucket for storing training data, models, and artifacts
- SageMaker Studio Domain (optional)
- CloudWatch log groups for monitoring
- Model Package Group for model registry

**Options:**
- `--region`: Specify AWS region (default: `us-east-1`)
- `--interactive`: Interactive deployment with confirmations
- `--dry-run`: Show deployment plan without creating resources
- `--stack-name`: Custom CloudFormation stack name

#### 3. **execute** - Run Your Pipeline
The `execute` command runs your generated SageMaker training pipeline.

```bash
python -m sagemigrator execute <pipeline-file>
```

**Features:**
- Automatically retrieves execution roles and S3 buckets from deployed infrastructure
- Supports environment variable configuration
- Provides real-time output capture
- Includes timeout management

**Options:**
- `--working-dir`: Specify working directory for execution
- `--env-vars`: Set environment variables (format: `KEY=VALUE`)
- `--timeout`: Set timeout in seconds (default: 3600)
- `--capture-output`: Display real-time pipeline output

## Example Migration Walkthrough: EC2-MNIST to SageMaker

Let's walk through a complete migration example using the provided EC2-MNIST project. This example demonstrates how to migrate a simple PyTorch MNIST training script from EC2 to a full SageMaker MLOps pipeline.

### Step 1: Examine the Source Project

First, let's look at our source EC2 project structure:

```
ec2-mnist/
├── main.py           # PyTorch MNIST training script
├── requirements.txt  # Python dependencies
└── README.md        # Basic usage instructions
```

The `main.py` file contains a standard PyTorch training script that:
- Downloads the MNIST dataset
- Defines a simple CNN model
- Trains the model on CPU or GPU
- Saves the trained model locally

### Step 2: Analyze and Migrate

Run the migration command to analyze the source code and generate SageMaker artifacts:

```bash
python -m sagemigrator migrate ./ec2-mnist -o ./sagemaker-mnist --processor-type sklearn
```

**What Happens During Migration:**

🔍 **Analysis Phase**: SageMigrator scans the source code and identifies:
- PyTorch framework usage
- MNIST dataset dependencies  
- GPU/CPU compatibility requirements
- Package dependencies and versions

📦 **Artifact Generation**: Creates a complete SageMaker project structure:

```
sagemaker-mnist/
├── training/
│   ├── train.py              # SageMaker-compatible training script
│   ├── pipeline.py           # Complete MLOps pipeline
│   ├── preprocessing.py      # Data preprocessing script
│   ├── evaluation.py         # Model evaluation script (sklearn processor)
│   └── deploy_pipeline.py    # Pipeline deployment script
├── infrastructure/
│   └── cloudformation/
│       └── main.yaml         # CloudFormation template
├── tests/                    # Generated test suites
└── documentation/            # Migration documentation
```

**Expected Output:**
```
✅ Analysis completed
✅ Artifact generation completed
📁 Artifacts saved to: ./sagemaker-mnist
📊 Analysis report: analysis_report.json
✅ Validation report: validation_report.json

Next steps:
1. Review generated artifacts
2. Run: sagemigrator deploy ./sagemaker-mnist
3. Execute: sagemigrator execute ./sagemaker-mnist/training/pipeline.py
```

### Step 3: Deploy Infrastructure

Deploy the AWS infrastructure using the generated CloudFormation template:

```bash
python -m sagemigrator deploy ./sagemaker-mnist --region us-east-1
```

**Deployment Process:**

🏗️ **Infrastructure Creation**: SageMigrator creates:
- IAM execution role: `sagemigrator-project-SageMaker-ExecutionRole-dev`
- S3 bucket: `sagemigrator-project-sagemaker-bucket-{account-id}-us-east-1`
- CloudWatch log group: `/aws/sagemaker/sagemigrator-project-dev`
- Model package group for model registry

**Expected Output:**
```
✅ Deployment Completed Successfully!

🏗️  Stack Name: sagemigrator-project-dev
🌍 Region: us-east-1
📊 Resources Created: 8
🔑 ExecutionRoleArn: arn:aws:iam::123456789012:role/sagemigrator-project-SageMaker-ExecutionRole-dev
🪣 S3BucketName: sagemigrator-project-sagemaker-bucket-123456789012-us-east-1

Next steps:
1. Execute SageMaker pipeline: sagemigrator execute ./sagemaker-mnist/training/pipeline.py
2. Monitor CloudWatch logs
3. Check AWS console for resources
```

### Step 4: Execute the Pipeline

Run your newly created SageMaker pipeline:

```bash
python -m sagemigrator execute ./sagemaker-mnist/training/pipeline.py --capture-output
```

**Pipeline Execution:**

🚀 **Automated MLOps Workflow**: The generated pipeline includes:

1. **Data Preprocessing Step**: 
   - Downloads and preprocesses MNIST dataset
   - Converts data to SageMaker-compatible format
   - Stores processed data in S3

2. **Training Step**:
   - Uses compute-optimized instances (`ml.c5.xlarge`)
   - Trains PyTorch CNN model with SageMaker managed infrastructure
   - Saves model artifacts to S3

3. **Evaluation Step**:
   - Evaluates model performance using sklearn processor
   - Generates comprehensive metrics (accuracy, precision, recall, F1-score)
   - Creates evaluation report

4. **Conditional Registration**:
   - Automatically registers model in SageMaker Model Registry if accuracy > 85%
   - Tags model with performance metrics and metadata

**Expected Output:**
```
🚀 Executing SageMaker pipeline: pipeline.py
✅ Using execution role from CloudFormation stack: arn:aws:iam::123456789012:role/...
✅ Using S3 bucket from CloudFormation stack: sagemigrator-project-sagemaker-bucket-...
✅ Pipeline 'sagemigrator-pipeline' deployed successfully!
✅ Pipeline execution started: arn:aws:sagemaker:us-east-1:123456789012:pipeline/...

🚀 Pipeline deployed and executed!
📊 Monitor execution: https://console.aws.amazon.com/sagemaker/home#/pipelines
```


## Conclusion: Accelerate Your ML Migration Journey

SageMigrator transforms what used to be a weeks-long manual migration process into a streamlined workflow that takes just minutes to complete. By automating code analysis, infrastructure generation, and MLOps pipeline creation, SageMigrator enables your team to:

- **Reduce Migration Time**: From weeks to hours with automated artifact generation
- **Ensure Best Practices**: Built-in security, cost optimization, and monitoring configurations
- **Minimize Errors**: Comprehensive validation and testing suites catch issues early
- **Scale Efficiently**: Production-ready infrastructure that grows with your needs

The MNIST example we walked through demonstrates SageMigrator's power with a simple use case, but the tool scales to handle complex, multi-model ML workloads with the same ease and reliability.

### Ready to Get Started?

**Take Action Today:**

1. **Clone the repository** and follow the installation steps above
2. **Try the MNIST example** to see SageMigrator in action
3. **Migrate your first real project** using your existing EC2 ML workloads
4. **Join the community** and share your migration success stories

The future of ML infrastructure is automated, scalable, and cloud-native. With SageMigrator, that future is available today. Don't let migration complexity hold back your ML initiatives – start your SageMaker journey now and unlock the full potential of AWS's managed ML platform.

**Get started with SageMigrator today and transform your ML migration experience from complex to effortless.**

---

*Ready to migrate your ML workloads? Visit our [GitHub repository](https://github.com/aws-samples/genai-ml-platform-examples) to download SageMigrator and start your migration journey today.*