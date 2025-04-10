#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Deploy Lambda Function for SageMaker Batch Transform

This script packages and deploys the Lambda function for SageMaker batch transform jobs
using the CloudFormation template.

Usage:
    python deploy_lambda.py [options]

Options:
    --stack-name TEXT                Name of the CloudFormation stack [default: from .env or batch-transform-lambda-stack]
    --s3-bucket TEXT                 S3 bucket to store the Lambda code package [default: from .env]
    --s3-prefix TEXT                 S3 prefix for the Lambda code package [default: from .env or lambda-code]
    --model-path TEXT                S3 path to the model.tar.gz file [default: from .env]
    --container-image TEXT           Container image URI for the batch transform job [default: from .env]
    --role-arn TEXT                  SageMaker execution role ARN [default: from .env]
    --queue-name TEXT                Name of the SQS queue [default: from .env or batch-transform-queue]
    --lambda-name TEXT               Name of the Lambda function [default: from .env or batch-transform-lambda]
    --help                           Show this message and exit.
"""

import os
import sys
import argparse
import logging
import boto3
import tempfile
import zipfile
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Deploy Lambda Function for SageMaker Batch Transform')
    
    parser.add_argument('--stack-name', type=str,
                        default=os.environ.get('LAMBDA_STACK_NAME', 'batch-transform-lambda-stack'),
                        help='Name of the CloudFormation stack')
    parser.add_argument('--s3-bucket', type=str,
                        default=os.environ.get('S3_BUCKET_NAME'),
                        help='S3 bucket to store the Lambda code package')
    parser.add_argument('--s3-prefix', type=str,
                        default=os.environ.get('LAMBDA_CODE_PREFIX', 'lambda-code'),
                        help='S3 prefix for the Lambda code package')
    parser.add_argument('--model-path', type=str,
                        default=f"s3://{os.environ.get('S3_BUCKET_NAME', '')}/{os.environ.get('S3_MODEL_PATH', '')}",
                        help='S3 path to the model.tar.gz file')
    parser.add_argument('--container-image', type=str,
                        default=os.environ.get('CONTAINER_IMAGE'),
                        help='Container image URI for the batch transform job')
    parser.add_argument('--role-arn', type=str,
                        default=os.environ.get('SAGEMAKER_ROLE_ARN'),
                        help='SageMaker execution role ARN')
    parser.add_argument('--queue-name', type=str,
                        default=os.environ.get('SQS_QUEUE_NAME', 'batch-transform-queue'),
                        help='Name of the SQS queue')
    parser.add_argument('--lambda-name', type=str,
                        default=os.environ.get('LAMBDA_FUNCTION_NAME', 'batch-transform-lambda'),
                        help='Name of the Lambda function')
    
    return parser.parse_args()

def package_lambda_code(s3_bucket, s3_prefix):
    """
    Package the Lambda code and upload it to S3.
    
    Args:
        s3_bucket (str): S3 bucket to store the Lambda code package
        s3_prefix (str): S3 prefix for the Lambda code package
        
    Returns:
        str: S3 URL of the Lambda code package
    """
    logger.info("Packaging Lambda code...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a zip file
        zip_path = os.path.join(temp_dir, 'lambda_function.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the Lambda function code
            zipf.write('lambda_batch_transform.py', 'lambda_batch_transform.py')
        
        # Upload the zip file to S3
        s3_client = boto3.client('s3')
        s3_key = f"{s3_prefix}/lambda_function.zip"
        s3_client.upload_file(zip_path, s3_bucket, s3_key)
        
        s3_url = f"s3://{s3_bucket}/{s3_key}"
        logger.info(f"Lambda code package uploaded to {s3_url}")
        
        return s3_url

def update_cloudformation_template(template_path, s3_url):
    """
    Update the CloudFormation template to use the S3 URL for the Lambda code.
    
    Args:
        template_path (str): Path to the CloudFormation template
        s3_url (str): S3 URL of the Lambda code package
        
    Returns:
        str: Path to the updated CloudFormation template
    """
    logger.info("Updating CloudFormation template...")
    
    # Parse the S3 URL
    s3_parts = s3_url[5:].split('/', 1)
    s3_bucket = s3_parts[0]
    s3_key = s3_parts[1]
    
    # Read the template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace the placeholder code with the S3 reference
    template_content = template_content.replace(
        "      Code:\n        ZipFile: |\n          # This is a placeholder. The actual code will be uploaded separately.\n          def lambda_handler(event, context):\n              return {\n                  'statusCode': 200,\n                  'body': 'This is a placeholder. Please upload the actual code.'\n              }",
        f"      Code:\n        S3Bucket: {s3_bucket}\n        S3Key: {s3_key}"
    )
    
    # Write the updated template
    updated_template_path = f"{template_path}.updated"
    with open(updated_template_path, 'w') as f:
        f.write(template_content)
    
    logger.info(f"Updated CloudFormation template saved to {updated_template_path}")
    
    return updated_template_path

def deploy_cloudformation_stack(stack_name, template_path, parameters):
    """
    Deploy the CloudFormation stack.
    
    Args:
        stack_name (str): Name of the CloudFormation stack
        template_path (str): Path to the CloudFormation template
        parameters (list): List of parameter dictionaries
        
    Returns:
        str: Stack ID of the deployed stack
    """
    logger.info(f"Deploying CloudFormation stack {stack_name}...")
    
    # Read the template
    with open(template_path, 'r') as f:
        template_body = f.read()
    
    # Create CloudFormation client
    cf_client = boto3.client('cloudformation')
    
    try:
        # Check if the stack exists
        try:
            cf_client.describe_stacks(StackName=stack_name)
            stack_exists = True
        except ClientError as e:
            if "does not exist" in str(e):
                stack_exists = False
            else:
                raise
        
        # Create or update the stack
        if stack_exists:
            logger.info(f"Stack {stack_name} already exists, updating...")
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
        else:
            logger.info(f"Creating new stack {stack_name}...")
            response = cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
        
        stack_id = response['StackId']
        logger.info(f"Stack {stack_name} deployment initiated with ID: {stack_id}")
        
        # Wait for the stack to be created or updated
        logger.info(f"Waiting for stack {stack_name} to be deployed...")
        waiter = cf_client.get_waiter('stack_create_complete' if not stack_exists else 'stack_update_complete')
        waiter.wait(StackName=stack_name)
        
        logger.info(f"Stack {stack_name} deployed successfully")
        
        # Get the stack outputs
        response = cf_client.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0]['Outputs']
        
        logger.info("Stack outputs:")
        for output in outputs:
            logger.info(f"  {output['OutputKey']}: {output['OutputValue']}")
        
        return stack_id
    
    except ClientError as e:
        logger.error(f"Error deploying CloudFormation stack: {str(e)}")
        raise

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Validate required arguments
    missing_args = []
    
    if not args.s3_bucket:
        missing_args.append("S3 bucket (--s3-bucket or S3_BUCKET_NAME in .env)")
    
    if not args.model_path:
        missing_args.append("Model path (--model-path or S3_BUCKET_NAME and S3_MODEL_PATH in .env)")
    
    if not args.container_image:
        missing_args.append("Container image URI (--container-image or CONTAINER_IMAGE in .env)")
    
    if not args.role_arn:
        missing_args.append("SageMaker execution role ARN (--role-arn or SAGEMAKER_ROLE_ARN in .env)")
    
    if missing_args:
        logger.error("Missing required arguments:")
        for arg in missing_args:
            logger.error(f"  - {arg}")
        logger.error("Please provide these arguments via command line or .env file")
        return
    
    try:
        # Log configuration
        logger.info("Deploying Lambda function with the following configuration:")
        logger.info(f"  Stack Name: {args.stack_name}")
        logger.info(f"  S3 Bucket: {args.s3_bucket}")
        logger.info(f"  S3 Prefix: {args.s3_prefix}")
        logger.info(f"  Model Path: {args.model_path}")
        logger.info(f"  Container Image: {args.container_image}")
        logger.info(f"  Role ARN: {args.role_arn}")
        logger.info(f"  Queue Name: {args.queue_name}")
        logger.info(f"  Lambda Name: {args.lambda_name}")
        
        # Package the Lambda code
        s3_url = package_lambda_code(args.s3_bucket, args.s3_prefix)
        
        # Update the CloudFormation template
        updated_template_path = update_cloudformation_template('lambda_batch_transform_template.yaml', s3_url)
        
        # Prepare the CloudFormation parameters
        parameters = [
            {
                'ParameterKey': 'SQSQueueName',
                'ParameterValue': args.queue_name
            },
            {
                'ParameterKey': 'LambdaFunctionName',
                'ParameterValue': args.lambda_name
            },
            {
                'ParameterKey': 'ModelPath',
                'ParameterValue': args.model_path
            },
            {
                'ParameterKey': 'ContainerImage',
                'ParameterValue': args.container_image
            },
            {
                'ParameterKey': 'RoleArn',
                'ParameterValue': args.role_arn
            }
        ]
        
        # Deploy the CloudFormation stack
        stack_id = deploy_cloudformation_stack(args.stack_name, updated_template_path, parameters)
        
        logger.info(f"Deployment completed successfully with stack ID: {stack_id}")
        
        # Clean up the updated template
        os.remove(updated_template_path)
    
    except Exception as e:
        logger.error(f"Error deploying Lambda function: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 