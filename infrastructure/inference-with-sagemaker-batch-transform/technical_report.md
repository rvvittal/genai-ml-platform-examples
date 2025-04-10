# Technical Report: ModernBERT Dispute Classifier for SageMaker Batch Transform

## Executive Summary

This technical report provides a comprehensive overview of the ModernBERT Dispute Classifier project, a system designed to deploy a fine-tuned ModernBERT model for legal dispute classification using Amazon SageMaker's batch transform capabilities. The system processes text documents from Amazon S3, classifies them into dispute categories, and saves the results back to S3.

The project implements two deployment approaches:
1. **Manual Batch Transform**: Direct invocation of SageMaker batch transform jobs with both standard and optimized processing options
2. **Automatic Batch Transform**: A serverless architecture using AWS Lambda and SQS for automated, event-driven processing

This report details the system architecture, code implementation, and operational considerations for both approaches.

## System Architecture

### High-Level Architecture

The system consists of several interconnected components:

1. **Model Preparation**:
   - Fine-tuned ModernBERT model packaged for SageMaker deployment
   - Custom container with inference code for model serving

2. **Deployment Options**:
   - **Manual Batch Transform**: Direct invocation of SageMaker batch transform jobs
     - Standard (CPU-based) processing
     - Optimized (GPU-accelerated) processing
   - **Automatic Batch Transform**: Serverless architecture
     - SQS queue for receiving batch transform requests
     - Lambda function for processing queue messages
     - CloudFormation stack for infrastructure deployment

3. **Monitoring and Management**:
   - Job status checking
   - CloudWatch integration for logging and monitoring

### Serverless Architecture Diagram

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

## Code Walkthrough

### 1. Custom Container Implementation

The custom container is the core of the inference system, responsible for loading the model and processing inference requests.

#### 1.1 Container Structure

```
custom_container/
├── Dockerfile                      # Container definition
├── build_and_push.sh               # Script to build and push container to ECR
├── app.py                          # Flask application for inference server
├── requirements.txt                # Python dependencies for the container
└── src/                            # Source code for inference
    ├── inference.py                # Model loading and inference logic
    └── __init__.py                 # Package initialization
```

#### 1.2 Dockerfile Analysis

The Dockerfile uses a multi-stage build approach:
- First stage (`builder`): Installs dependencies including PyTorch with CUDA support
- Second stage: Creates a lightweight runtime image with only necessary components
- Sets environment variables for SageMaker batch transform
- Creates SageMaker-compatible entry points (`serve` and `train`)

Key optimizations:
- Uses Python 3.11 for improved performance
- Configures PyTorch for reduced overhead
- Disables PyTorch inductor to avoid C compiler dependency
- Minimizes image size by removing unnecessary files

#### 1.3 Flask Application (app.py)

The Flask application implements the SageMaker inference server protocol:

```python
# Initialize Flask app
app = Flask(__name__)

# Environment variables for batch transform settings
MAX_CONCURRENT_TRANSFORMS = int(os.environ.get('SAGEMAKER_MAX_CONCURRENT_TRANSFORMS', '1'))
BATCH_STRATEGY = os.environ.get('SAGEMAKER_BATCH_STRATEGY', 'MULTI_RECORD')
MAX_PAYLOAD_MB = int(os.environ.get('SAGEMAKER_MAX_PAYLOAD_IN_MB', '6'))

# Load model on startup
model_dict = model_fn(model_dir)

@app.route('/ping', methods=['GET'])
def ping():
    """SageMaker health check endpoint."""
    # Health check implementation

@app.route('/execution-parameters', methods=['GET'])
def execution_parameters():
    """Returns the recommended execution parameters for this model."""
    # Execution parameters implementation

@app.route('/invocations', methods=['POST'])
def invoke():
    """SageMaker invocation endpoint for batch transform."""
    # Inference implementation
```

Key features:
- Implements required SageMaker endpoints: `/ping`, `/execution-parameters`, and `/invocations`
- Loads the model once at startup for efficient inference
- Configurable batch transform parameters via environment variables
- Handles both standard and optimized batch processing

#### 1.4 Inference Implementation (inference.py)

The inference module implements the core model loading and prediction functions:

```python
def model_fn(model_dir, context=None):
    """Load the model and tokenizer from the model directory."""
    # Model loading implementation

def input_fn(request_body, request_content_type):
    """Parse and preprocess the input data."""
    # Input processing implementation

def predict_fn(input_data, model_dict, context=None):
    """Generate predictions for the input data."""
    # Prediction implementation

def output_fn(prediction_output, accept):
    """Format the prediction output according to the accept type."""
    # Output formatting implementation

def batch_predict_fn(data, model_dict):
    """Process a batch of inputs for optimized performance."""
    # Batch prediction implementation
```

Key features:
- Modular design with separate functions for each stage of the inference pipeline
- Optimized batch processing for GPU acceleration
- Handles various input and output formats
- Error handling and logging for production reliability

### 2. Batch Transform Setup

#### 2.1 Standard Batch Transform (setup_batch_transform.py)

The standard batch transform approach processes each document individually:

```python
def setup_batch_transform(model_path, s3_bucket, s3_model_prefix, s3_input_prefix, 
                         s3_output_prefix, container_image, instance_type, 
                         instance_count, role_arn=None):
    """Set up a SageMaker batch transform job."""
    # Implementation details
```

Key features:
- Creates a SageMaker model from the packaged model artifacts
- Configures a batch transform job with standard settings
- Processes each input file separately
- Creates individual output files for each input

#### 2.2 Optimized Batch Transform (setup_optimized_batch_transform.py)

The optimized batch transform approach processes documents in batches for improved performance:

```python
def setup_optimized_batch_transform(model_path, s3_bucket, s3_model_prefix, s3_input_prefix, 
                                   s3_output_prefix, container_image, instance_type, 
                                   instance_count, role_arn=None):
    """Set up an optimized SageMaker batch transform job using our custom batch processing."""
    # Implementation details
```

Key features:
- Creates a manifest file that references all input files
- Uses a custom batch processing approach in the container
- Processes documents in batches for GPU acceleration
- Outputs a single consolidated JSON file with all results
- Significantly faster than standard batch transform

### 3. Serverless Architecture Implementation

#### 3.1 Lambda Function (lambda_batch_transform.py)

The Lambda function is triggered by SQS messages and starts batch transform jobs:

```python
def lambda_handler(event, context):
    """
    Lambda handler function that processes SQS messages and starts batch transform jobs.
    """
    # Extract message from SQS event
    for record in event['Records']:
        message_body = json.loads(record['body'])
        
        # Extract parameters from message
        input_path = message_body.get('input_path')
        output_path = message_body.get('output_path')
        instance_type = message_body.get('instance_type', DEFAULT_INSTANCE_TYPE)
        instance_count = message_body.get('instance_count', DEFAULT_INSTANCE_COUNT)
        
        # Validate input path
        valid, message = validate_s3_path(input_path)
        if not valid:
            logger.error(f"Invalid input path: {message}")
            return {'statusCode': 400, 'body': message}
        
        # Create SageMaker model if it doesn't exist
        create_sagemaker_model(MODEL_NAME, MODEL_PATH, CONTAINER_IMAGE, ROLE_ARN)
        
        # Create batch transform job
        transform_job_name = f"{TRANSFORM_JOB_PREFIX}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        create_batch_transform_job(MODEL_NAME, input_path, output_path, transform_job_name, 
                                  instance_type, instance_count)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Batch transform job started successfully',
                'transformJobName': transform_job_name
            })
        }
```

Key features:
- Processes SQS messages containing batch transform parameters
- Creates or reuses a SageMaker model
- Starts a batch transform job with the specified parameters
- Returns the job name for status tracking

#### 3.2 CloudFormation Template (lambda_batch_transform_template.yaml)

The CloudFormation template defines the serverless infrastructure:

```yaml
Resources:
  # SQS Queue
  BatchTransformQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Ref SQSQueueName
      VisibilityTimeout: 900  # 15 minutes
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt BatchTransformDeadLetterQueue.Arn
        maxReceiveCount: 5

  # Dead Letter Queue
  BatchTransformDeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub "${SQSQueueName}-dlq"

  # Lambda Execution Role
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      # Role configuration with necessary permissions

  # Lambda Function
  BatchTransformLambda:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Ref LambdaFunctionName
      Handler: lambda_batch_transform.lambda_handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Runtime: python3.9
      Timeout: 300  # 5 minutes
      Environment:
        Variables:
          # Environment variables for Lambda function

  # Event Source Mapping
  LambdaSQSEventSourceMapping:
    Type: AWS::Lambda::EventSourceMapping
    Properties:
      BatchSize: 1
      Enabled: true
      EventSourceArn: !GetAtt BatchTransformQueue.Arn
      FunctionName: !Ref BatchTransformLambda
```

Key features:
- Defines an SQS queue for batch transform requests
- Includes a dead-letter queue for failed messages
- Creates a Lambda function with necessary permissions
- Sets up event source mapping between SQS and Lambda
- Configures environment variables for the Lambda function

#### 3.3 Deployment Script (deploy_lambda.py)

The deployment script packages and deploys the Lambda function:

```python
def package_lambda_code(s3_bucket, s3_prefix):
    """Package the Lambda code and upload it to S3."""
    # Implementation details

def update_cloudformation_template(template_path, s3_url):
    """Update the CloudFormation template with the S3 URL of the Lambda code package."""
    # Implementation details

def deploy_cloudformation_stack(stack_name, template_path, parameters):
    """Deploy or update the CloudFormation stack."""
    # Implementation details

def main():
    """Main function to deploy the Lambda function."""
    # Parse arguments
    args = parse_arguments()
    
    # Package Lambda code
    s3_url = package_lambda_code(args.s3_bucket, args.s3_prefix)
    
    # Update CloudFormation template
    updated_template_path = update_cloudformation_template('lambda_batch_transform_template.yaml', s3_url)
    
    # Deploy CloudFormation stack
    deploy_cloudformation_stack(args.stack_name, updated_template_path, {
        'SQSQueueName': args.queue_name,
        'LambdaFunctionName': args.lambda_name,
        'ModelPath': args.model_path,
        'ContainerImage': args.container_image,
        'RoleArn': args.role_arn
    })
```

Key features:
- Packages the Lambda function code into a ZIP file
- Uploads the package to S3 for CloudFormation deployment
- Updates the CloudFormation template with the S3 URL
- Deploys or updates the CloudFormation stack
- Configurable parameters via command-line arguments or environment variables

### 4. Request and Monitoring Tools

#### 4.1 Send Batch Transform Request (send_batch_transform_request.py)

This script sends a message to the SQS queue to trigger a batch transform job:

```python
def send_sqs_message(queue_url, message_body):
    """Send a message to the SQS queue."""
    # Implementation details

def main():
    """Main function to send a batch transform request."""
    # Parse arguments
    args = parse_arguments()
    
    # Validate input path
    valid, message = validate_s3_path(args.input_path)
    if not valid:
        logger.error(f"Invalid input path: {message}")
        sys.exit(1)
    
    # Prepare message body
    message_body = {
        'input_path': args.input_path,
        'output_path': args.output_path,
        'instance_type': args.instance_type,
        'instance_count': args.instance_count
    }
    
    # Send message to SQS queue
    send_sqs_message(args.queue_url, json.dumps(message_body))
```

Key features:
- Sends a message to the SQS queue with batch transform parameters
- Validates the S3 input path before sending
- Configurable parameters via command-line arguments or environment variables
- Simple interface for triggering batch transform jobs

#### 4.2 Check Batch Transform Status (check_batch_transform_status.py)

This script checks the status of batch transform jobs:

```python
def get_transform_job_status(job_name):
    """Get the status of a specific batch transform job."""
    # Implementation details

def list_transform_jobs(max_results=10):
    """List all batch transform jobs, sorted by creation time."""
    # Implementation details

def main():
    """Main function to check batch transform job status."""
    # Parse arguments
    args = parse_arguments()
    
    if args.job_name:
        # Check status of a specific job
        job_details = get_transform_job_status(args.job_name)
        print(format_job_status(job_details))
    elif args.list_jobs:
        # List all jobs
        jobs = list_transform_jobs(args.max_results)
        for job in jobs:
            print(format_job_summary(job))
    else:
        logger.error("Either --job-name or --list-jobs must be specified")
        sys.exit(1)
```

Key features:
- Checks the status of a specific batch transform job
- Lists all batch transform jobs sorted by creation time
- Formats job details for easy reading
- Useful for monitoring both manual and automatic batch transform jobs

## Implementation Details

### Data Flow

1. **Input Preparation**:
   - Text files are uploaded to an S3 bucket
   - Each line in a file represents a document to be classified

2. **Batch Transform Invocation**:
   - **Manual**: Direct invocation of setup scripts
   - **Automatic**: Message sent to SQS queue, triggering Lambda function

3. **Model Inference**:
   - SageMaker downloads the model from S3
   - Custom container loads the model and processes input data
   - Model generates predictions for each document

4. **Result Storage**:
   - Predictions are saved to the specified S3 output location
   - **Standard**: Separate output files for each input
   - **Optimized**: Single consolidated JSON file with all results

### Performance Optimizations

1. **GPU Acceleration**:
   - Custom container configured for GPU inference
   - PyTorch optimizations for reduced overhead
   - Batch processing for efficient GPU utilization

2. **Optimized Batch Transform**:
   - Processes documents in batches rather than individually
   - Reduces overhead from multiple S3 operations and HTTP requests
   - Consolidates results into a single output file

3. **Serverless Architecture**:
   - No need for a long-lived process to poll the SQS queue
   - Automatic scaling with the number of messages
   - Cost-effective as you only pay for Lambda invocations

### Error Handling and Reliability

1. **Input Validation**:
   - S3 path validation before processing
   - Content type checking and appropriate error messages

2. **Dead-Letter Queue**:
   - Failed messages are sent to a dead-letter queue
   - Configurable retry policy (5 attempts by default)

3. **Logging and Monitoring**:
   - Comprehensive logging throughout the system
   - CloudWatch integration for monitoring and alerting
   - Job status checking for tracking progress

## Conclusion

The ModernBERT Dispute Classifier project demonstrates a robust and flexible approach to deploying machine learning models for batch inference. By offering both manual and automatic deployment options, it caters to different use cases and operational requirements.

The optimized batch transform approach significantly improves performance for large datasets, while the serverless architecture provides a scalable and cost-effective solution for production environments. The comprehensive monitoring and error handling ensure reliable operation in real-world scenarios.

This system can serve as a template for deploying other NLP models for batch inference, with minimal modifications required to adapt to different model architectures or classification tasks.

