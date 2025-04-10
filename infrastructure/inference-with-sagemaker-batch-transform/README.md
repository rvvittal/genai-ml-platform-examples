# ModernBERT Dispute Classifier for SageMaker Batch Transform

This project deploys a fine-tuned ModernBERT model for legal dispute classification to Amazon SageMaker using a custom container for batch transform jobs. The system processes text files from S3, classifies them into dispute categories, and saves the results back to S3.

## Table of Contents

- [ModernBERT Dispute Classifier for SageMaker Batch Transform](#modernbert-dispute-classifier-for-sagemaker-batch-transform)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Project Structure](#project-structure)
  - [Complete Workflow](#complete-workflow)
    - [Phase 1: Model Training (SageMaker Notebook Instance)](#phase-1-model-training-sagemaker-notebook-instance)
    - [Phase 2: Model Deployment for Batch Transform](#phase-2-model-deployment-for-batch-transform)
  - [Environment Setup](#environment-setup)
  - [Preparing Data for Inference](#preparing-data-for-inference)
  - [Deployment Steps](#deployment-steps)
    - [1. Package the Model](#1-package-the-model)
    - [2. Build and Push the Docker Container](#2-build-and-push-the-docker-container)
    - [3. Choose a Deployment Option](#3-choose-a-deployment-option)
      - [Option A: Manual Batch Transform](#option-a-manual-batch-transform)
        - [Optimized Batch Transform (GPU-accelerated, Recommended)](#optimized-batch-transform-gpu-accelerated-recommended)
        - [Standard Batch Transform (CPU-based)](#standard-batch-transform-cpu-based)
      - [Option B: Automatic Batch Transform (Lambda/SQS)](#option-b-automatic-batch-transform-lambdasqs)
    - [4. Sending Batch Transform Requests](#4-sending-batch-transform-requests)
      - [For Manual Deployment](#for-manual-deployment)
      - [For Automatic Deployment](#for-automatic-deployment)
    - [5. Checking Batch Transform Job Status](#5-checking-batch-transform-job-status)
  - [Input and Output Format](#input-and-output-format)
    - [Input](#input)
    - [Output](#output)
  - [Lambda-Based Batch Transform Workflow](#lambda-based-batch-transform-workflow)
    - [Workflow Diagram](#workflow-diagram)
    - [Message Format](#message-format)
    - [Monitoring the Lambda Function](#monitoring-the-lambda-function)
  - [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
  - [Cleaning Up](#cleaning-up)
  - [Performance Considerations](#performance-considerations)
    - [Standard vs. Optimized Batch Transform](#standard-vs-optimized-batch-transform)
    - [When to Use Each Approach](#when-to-use-each-approach)
    - [Manual vs. Automatic Deployment](#manual-vs-automatic-deployment)
    - [Optimizing Further](#optimizing-further)
  - [Acknowledgments](#acknowledgments)

## Prerequisites

- AWS account with appropriate permissions
- Amazon SageMaker access
- Docker installed (for local container building)
- Python 3.9+
- AWS CLI configured with appropriate credentials

## Project Structure

```
.
├── custom_container/                    # Docker container files
│   ├── Dockerfile                      # Container definition
│   ├── build_and_push.sh               # Script to build and push container to ECR
│   ├── app.py                          # Flask application for inference server
│   ├── requirements.txt                # Python dependencies for the container
│   └── src/                            # Source code for inference
│       ├── inference.py                # Model loading and inference logic
│       └── __init__.py                 # Package initialization
├── modernbert_dispute_classifier/      # Model files
│   └── final/                          # Fine-tuned model artifacts
│       ├── config.json                 # Model configuration
│       ├── model.safetensors           # Model weights
│       ├── tokenizer.json              # Tokenizer configuration
│       ├── tokenizer_config.json       # Additional tokenizer settings
│       ├── special_tokens_map.json     # Special tokens configuration
│       ├── training_args.bin           # Training arguments
│       └── label_mapping.csv           # Mapping of label IDs to dispute categories
├── modernbert_finetune.ipynb           # Notebook for fine-tuning the model
├── package_model.py                    # Script to package model for SageMaker
├── setup_batch_transform.py            # Script to set up batch transform job
├── setup_optimized_batch_transform.py   # Script to set up optimized batch transform job
├── send_batch_transform_request.py      # Script to send batch transform request to SQS queue
├── check_batch_transform_status.py      # Script to check batch transform job status
├── lambda_batch_transform.py           # Lambda function code for batch transform
├── lambda_batch_transform_template.yaml # CloudFormation template for Lambda deployment
├── deploy_lambda.py                    # Script to deploy Lambda function
├── .env                                # Environment variables
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## Complete Workflow

The complete workflow consists of two main phases:

### Phase 1: Model Training (SageMaker Notebook Instance)

1. Run the `modernbert_finetune.ipynb` notebook in a SageMaker notebook instance to fine-tune the ModernBERT model on your dispute case dataset.
2. The notebook will save the fine-tuned model to the `modernbert_dispute_classifier/final` directory.

### Phase 2: Model Deployment for Batch Transform

After the model is trained and saved, you can proceed with deploying it for batch transform jobs. The remaining steps can be run locally.

## Environment Setup

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Configure your AWS credentials and settings in the `.env` file:

```
# AWS Configuration
AWS_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# SageMaker Configuration
SAGEMAKER_ROLE_ARN=your_sagemaker_role_arn
SAGEMAKER_INSTANCE_TYPE=ml.g4dn.xlarge
SAGEMAKER_INSTANCE_COUNT=1

# S3 Configuration
S3_BUCKET_NAME=your_bucket_name
S3_MODEL_PATH=models/modernbert/model.tar.gz
S3_INPUT_PATH=input/your_input_folder/
S3_OUTPUT_PATH=output/your_output_folder/

# Model Configuration
MODEL_DIR=./modernbert_dispute_classifier/final

# ECR Repository name for custom container
ECR_REPOSITORY_NAME=dispute-classifier

# Container image URI (will be set by build_and_push.sh)
CONTAINER_IMAGE=your_account_id.dkr.ecr.your_region.amazonaws.com/dispute-classifier:latest

# Lambda Configuration
LAMBDA_STACK_NAME=batch-transform-lambda-stack
LAMBDA_FUNCTION_NAME=batch-transform-lambda
LAMBDA_CODE_PREFIX=lambda-code
SQS_QUEUE_NAME=batch-transform-queue
```

## Preparing Data for Inference

Before running inference, you need to prepare your input data and configure the S3 paths:

1. **Create text files**: Each text file should contain the documents you want to classify, with one document per line.

2. **Upload to S3**: Upload these text files to an S3 folder (e.g., `s3://your-bucket-name/input/your-input-folder/`).

3. **Configure S3 paths in .env file**: Update the following variables in your `.env` file:
   ```
   S3_BUCKET_NAME=your-bucket-name
   S3_INPUT_PATH=input/your-input-folder/
   S3_OUTPUT_PATH=output/your-output-folder/
   ```

This process is the same for both deployment options (manual and automatic). In both cases, you're providing the model with the S3 input path where your text files are located. The pipeline will process all files in the specified folder and generate predictions.

For example, if you have files `case1.txt`, `case2.txt`, and `case3.txt` in your input folder, the batch transform job will process each file and save the results to the output folder.

## Deployment Steps

Follow these steps to deploy the model for batch transform:

### 1. Package the Model

Package the ModernBERT model artifacts into a tar.gz file for SageMaker:

```bash
python package_model.py
```

This creates a `model.tar.gz` file containing the model artifacts. You can customize the model directory and output path:

```bash
python package_model.py --model-dir ./modernbert_dispute_classifier/final --output-path model.tar.gz
```

The packaged model will include all necessary files:
- `model.safetensors`: The model weights
- `config.json`: Model configuration
- `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`: Tokenizer files
- `label_mapping.csv`: Mapping of label IDs to dispute categories

### 2. Build and Push the Docker Container

Build the custom Docker container and push it to Amazon ECR:

```bash
cd custom_container
chmod +x build_and_push.sh
./build_and_push.sh
cd ..
```

This script will:
- Build the Docker image for the custom container
- Tag it with your ECR repository name
- Push it to your ECR repository
- Output the full container image URI to use in the next step

After running this script, note the container image URI that is output. You should update the `CONTAINER_IMAGE` variable in your `.env` file with this URI.

### 3. Choose a Deployment Option

This project offers two deployment options:

#### Option A: Manual Batch Transform

Run batch transform jobs manually using one of the following approaches:

##### Optimized Batch Transform (GPU-accelerated, Recommended)

```bash
python setup_optimized_batch_transform.py
```

This approach:
- Processes documents in batches
- Uses GPU acceleration for significantly faster inference
- Chunks up large document payloads for efficient processing
- Outputs a single consolidated JSON file with all results
- Recommended for large datasets where processing speed is critical

##### Standard Batch Transform (CPU-based)

```bash
python setup_batch_transform.py
```

This approach:
- Processes each document one at a time
- Uses CPU for inference
- Creates separate output files for each input
- Good for small datasets or when you need individual processing

You can customize the parameters for either approach:

```bash
python setup_optimized_batch_transform.py \
  --model-path model.tar.gz \
  --s3-bucket your-bucket-name \
  --s3-model-prefix models/modernbert/model.tar.gz \
  --s3-input-prefix input/your-input-folder/ \
  --s3-output-prefix output/your-output-folder/ \
  --container-image your-container-image-uri \
  --instance-type ml.g4dn.xlarge \
  --instance-count 1 \
  --role-arn arn:aws:iam::your-account-id:role/your-sagemaker-role
```

#### Option B: Automatic Batch Transform (Lambda/SQS)

Deploy a serverless solution that automatically triggers batch transform jobs when messages are sent to an SQS queue:

```bash
python deploy_lambda.py
```

This approach:
- Sets up an SQS queue for receiving batch transform requests
- Deploys a Lambda function that is triggered by SQS messages
- Creates all necessary IAM roles and permissions
- Allows you to trigger batch transform jobs by simply sending a message to the queue
- Provides automatic scaling, retry logic, and dead-letter queue for failed messages
- Ideal for production environments where reliability and automation are priorities

The script will read configuration from your `.env` file. Make sure the following variables are set:

```
# Required for Lambda deployment
S3_BUCKET_NAME=your-bucket-name
S3_MODEL_PATH=models/modernbert/model.tar.gz
CONTAINER_IMAGE=your-account-id.dkr.ecr.your-region.amazonaws.com/dispute-classifier:latest
SAGEMAKER_ROLE_ARN=arn:aws:iam::your-account-id:role/your-sagemaker-role

# Optional for Lambda deployment (defaults shown)
LAMBDA_STACK_NAME=batch-transform-lambda-stack
LAMBDA_FUNCTION_NAME=batch-transform-lambda
LAMBDA_CODE_PREFIX=lambda-code
SQS_QUEUE_NAME=batch-transform-queue
```

This script will:
1. Package the Lambda function code and upload it to S3
2. Create or update a CloudFormation stack that includes:
   - An SQS queue for batch transform requests
   - A dead-letter queue for failed messages
   - A Lambda function that processes messages from the queue
   - IAM roles and permissions for the Lambda function

You can also override any of these settings via command-line arguments:

```bash
python deploy_lambda.py \
  --s3-bucket your-bucket-name \
  --stack-name your-stack-name \
  --s3-prefix lambda-code \
  --model-path s3://your-bucket/models/model.tar.gz \
  --container-image your-container-image-uri \
  --role-arn your-sagemaker-role-arn \
  --queue-name your-queue-name \
  --lambda-name your-lambda-name
```

### 4. Sending Batch Transform Requests

#### For Manual Deployment
If you chose the manual deployment option, the batch transform job will start immediately after running the setup script.

#### For Automatic Deployment
If you chose the automatic deployment option, you can send batch transform requests to the SQS queue:

```bash
python send_batch_transform_request.py
```

The script will read configuration from your `.env` file. Make sure the following variables are set:

```
# Required for sending requests
SQS_QUEUE_URL=https://sqs.your-region.amazonaws.com/your-account-id/your-queue-name
S3_BUCKET_NAME=your-bucket-name
S3_INPUT_PATH=input/your-input-folder/

# Optional for sending requests
S3_OUTPUT_PATH=output/your-output-folder/
SAGEMAKER_INSTANCE_TYPE=ml.g4dn.xlarge
SAGEMAKER_INSTANCE_COUNT=1
```

You can also override any of these settings via command-line arguments:

```bash
python send_batch_transform_request.py --queue-url <sqs-queue-url> --input-path s3://your-bucket/input/
```

Required parameters (either from .env or command line):
- `SQS_QUEUE_URL` or `--queue-url`: URL of the SQS queue to send the message to
- `S3_BUCKET_NAME` and `S3_INPUT_PATH` or `--input-path`: S3 path to the input data

Optional parameters:
- `S3_OUTPUT_PATH` or `--output-path`: S3 path for the output data
- `SAGEMAKER_INSTANCE_TYPE` or `--instance-type`: Instance type for the batch transform job
- `SAGEMAKER_INSTANCE_COUNT` or `--instance-count`: Number of instances for the batch transform job

### 5. Checking Batch Transform Job Status

Regardless of which deployment option you chose (manual or automatic), you can check the status of batch transform jobs using:

```bash
python check_batch_transform_status.py --list-jobs
```

This will list all batch transform jobs, sorted by creation time. You can also check the status of a specific job:

```bash
python check_batch_transform_status.py --job-name <job-name>
```

Optional parameters:
- `--max-results`: Maximum number of jobs to list (default: 10)

This is particularly useful for the automatic deployment option, where jobs are triggered asynchronously by SQS messages.

## Input and Output Format

### Input

The batch transform job expects text files in the S3 input location. Each line in the file should contain a text document to be classified. See the [Preparing Data for Inference](#preparing-data-for-inference) section for details on how to prepare and upload your input files.

This input format is the same for both deployment options (manual and automatic). The pipeline will process all text files found in the S3 input path specified in your `.env` file or provided as a command-line argument.

### Output

The output will be saved to the S3 output location in JSON format with the following structure:

```json
{
  "predictions": {
    "predicted_class": "Contract Dispute",
    "top_predictions": [
      {
        "class": "Contract Dispute",
        "score": 0.85
      },
      {
        "class": "Employment Dispute",
        "score": 0.10
      },
      {
        "class": "Intellectual Property Dispute",
        "score": 0.05
      }
    ]
  }
}
```

## Lambda-Based Batch Transform Workflow

This project uses a serverless approach with AWS Lambda to trigger batch transform jobs. This approach has several advantages:

1. No need to run a long-lived process to poll the SQS queue
2. More cost-effective as you only pay for the Lambda invocations
3. Automatically scales with the number of messages in the queue
4. Built-in retry mechanism with dead-letter queue support

### Workflow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Client   │────▶│  SQS Queue  │────▶│    Lambda   │────▶│  SageMaker  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                                                           │
       │                                                           │
       │                                                           ▼
       │                                                    ┌─────────────┐
       └───────────────────────────────────────────────────▶│  S3 Output  │
                                                            └─────────────┘
```

1. Client sends a message to the SQS queue with the input path
2. Lambda function is triggered by the SQS message
3. Lambda function creates a SageMaker batch transform job
4. SageMaker processes the input data and saves the results to S3
5. Client can check the job status and access the output data

### Message Format

The SQS message format for batch transform requests is:

```json
{
  "input_path": "s3://your-bucket/input/",
  "output_path": "s3://your-bucket/output/",
  "instance_type": "ml.g4dn.xlarge",
  "instance_count": 1
}
```

Only the `input_path` field is required. The other fields are optional and will use default values if not specified.

### Monitoring the Lambda Function

You can monitor the Lambda function in the AWS Management Console:

1. Go to the Lambda console and select your function
2. View the CloudWatch logs for detailed execution logs
3. Check the CloudWatch metrics for invocation counts, errors, and duration

## Monitoring and Troubleshooting

- Monitor the batch transform job in the SageMaker console
- Check CloudWatch logs for any errors
- Verify the output in the specified S3 output location

Common issues and solutions:

1. **Container build fails**: Ensure Docker is installed and running, and that you have permissions to push to ECR
2. **Model loading fails**: Check that the model artifacts are correctly packaged in the tar.gz file
3. **Batch transform job fails**: Check the CloudWatch logs for the specific error message
4. **Role error when running locally**: Make sure you've provided a valid SageMaker execution role ARN with the `--role-arn` parameter or in the `.env` file

## Cleaning Up

To avoid incurring unnecessary charges, delete the following resources when you're done:

1. SageMaker model
2. ECR repository
3. S3 objects (model artifacts, input, and output data)
4. CloudFormation stack (if using the Lambda approach)

You can delete the SageMaker model programmatically:

```python
import boto3
sm_client = boto3.client('sagemaker')
sm_client.delete_model(ModelName='your-model-name')
```

To delete the ECR repository:

```bash
aws ecr delete-repository --repository-name dispute-classifier --force
```

To delete S3 objects:

```bash
aws s3 rm s3://your-bucket-name/models/modernbert/ --recursive
aws s3 rm s3://your-bucket-name/input/your-input-folder/ --recursive
aws s3 rm s3://your-bucket-name/output/your-output-folder/ --recursive
```

To delete the CloudFormation stack (if using the Lambda approach):

```bash
aws cloudformation delete-stack --stack-name batch-transform-lambda-stack
```

## Performance Considerations

### Standard vs. Optimized Batch Transform

The project offers two approaches for batch processing:

1. **Optimized Batch Transform** (`setup_optimized_batch_transform.py`):
   - Processes documents in batches
   - Uses GPU acceleration for significantly faster inference
   - Chunks up large document payloads for efficient processing
   - Reduces overhead by minimizing S3 operations and HTTP requests
   - Outputs a single consolidated JSON file with all results
   - Recommended for large datasets where processing speed is critical

2. **Standard Batch Transform** (`setup_batch_transform.py`):
   - Processes each document one at a time
   - Uses CPU for inference
   - Higher overhead due to multiple S3 operations and HTTP requests
   - Creates separate output files for each input
   - Good for small datasets or when you need individual processing

### When to Use Each Approach

- Use **Optimized Batch Transform** when:
  - You need to process many files at once
  - Processing speed is critical
  - You prefer a single consolidated output file
  - You have access to GPU instances

- Use **Standard Batch Transform** when:
  - You need to process files incrementally
  - Your input files are very large (>100MB each)
  - You need separate output files for each input
  - GPU instances are not available or cost-prohibitive

### Manual vs. Automatic Deployment

- Use **Manual Deployment** when:
  - You need to run batch transform jobs on an ad-hoc basis
  - You want full control over the batch transform job parameters
  - You're in a development or testing environment

- Use **Automatic Deployment (Lambda/SQS)** when:
  - You need to trigger batch transform jobs programmatically
  - You want a serverless architecture with automatic scaling
  - You need built-in retry logic and error handling
  - You're in a production environment where reliability is critical

### Optimizing Further

For even better performance:
- Use a more powerful instance type (e.g., ml.g5.xlarge)
- Increase batch size in `batch_predict_fn` if you have more GPU memory
- Consider using multiple instances with `--instance-count` > 1 for very large datasets

## Acknowledgments

- [ModernBERT](https://huggingface.co/answerdotai/ModernBERT-base) by Answer.ai
- [Amazon SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
