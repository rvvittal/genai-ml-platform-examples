#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lambda Batch Transform Handler

This Lambda function is triggered by SQS messages and starts a SageMaker batch transform job.
It replaces the need for a constantly running SQS listener process.

The Lambda function expects the following environment variables:
- MODEL_PATH: S3 path to the model.tar.gz file
- CONTAINER_IMAGE: Container image URI for the batch transform job
- ROLE_ARN: SageMaker execution role ARN
- MODEL_NAME: Name for the SageMaker model (default: modernbert-dispute-classifier)
- TRANSFORM_JOB_PREFIX: Prefix for batch transform job names (default: dispute-classifier-job)
- DEFAULT_INSTANCE_TYPE: Default instance type for the batch transform job (default: ml.g4dn.xlarge)
- DEFAULT_INSTANCE_COUNT: Default number of instances for the batch transform job (default: 1)
- DEFAULT_OUTPUT_PREFIX: Default S3 prefix for output files (default: output/)
"""

import os
import json
import uuid
import logging
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
MODEL_PATH = os.environ.get('MODEL_PATH')
CONTAINER_IMAGE = os.environ.get('CONTAINER_IMAGE')
ROLE_ARN = os.environ.get('ROLE_ARN')
MODEL_NAME = os.environ.get('MODEL_NAME', 'modernbert-dispute-classifier')
TRANSFORM_JOB_PREFIX = os.environ.get('TRANSFORM_JOB_PREFIX', 'dispute-classifier-job')
DEFAULT_INSTANCE_TYPE = os.environ.get('DEFAULT_INSTANCE_TYPE', 'ml.g4dn.xlarge')
DEFAULT_INSTANCE_COUNT = int(os.environ.get('DEFAULT_INSTANCE_COUNT', '1'))
DEFAULT_OUTPUT_PREFIX = os.environ.get('DEFAULT_OUTPUT_PREFIX', 'output/')

def validate_s3_path(s3_path):
    """Validate that an S3 path exists and is accessible."""
    if not s3_path.startswith('s3://'):
        return False, f"Invalid S3 path format: {s3_path}. Must start with 's3://'"
    
    # Extract bucket and key
    path_parts = s3_path[5:].split('/', 1)
    if len(path_parts) < 2:
        return False, f"Invalid S3 path format: {s3_path}. Must include bucket and key"
    
    bucket = path_parts[0]
    prefix = path_parts[1]
    
    # Check if bucket exists and is accessible
    s3_client = boto3.client('s3')
    try:
        # List objects to check if prefix exists
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=1
        )
        
        # Check if the prefix exists (has at least one object)
        if 'Contents' not in response:
            return False, f"S3 prefix does not exist or is empty: {s3_path}"
        
        return True, s3_path
    except ClientError as e:
        return False, f"Error accessing S3 path {s3_path}: {str(e)}"

def create_sagemaker_model(model_name, model_path, container_image, role_arn):
    """
    Create a SageMaker model using the specified model artifacts and container.
    
    Args:
        model_name (str): Name for the SageMaker model
        model_path (str): S3 path to the model artifacts
        container_image (str): URI of the container image
        role_arn (str): SageMaker execution role ARN
        
    Returns:
        str: The name of the created model
    """
    logger.info(f"Creating SageMaker model: {model_name}")
    
    # Ensure model_path is a proper S3 URI
    if not model_path.startswith('s3://'):
        raise ValueError(f"Model path must be an S3 URI, got: {model_path}")
    
    # Create SageMaker client
    sagemaker_client = boto3.client('sagemaker')
    
    try:
        # Check if model already exists
        try:
            sagemaker_client.describe_model(ModelName=model_name)
            logger.info(f"Model {model_name} already exists, using existing model")
            return model_name
        except ClientError as e:
            if e.response['Error']['Code'] != 'ValidationException':
                raise
            # Model doesn't exist, create it
            logger.info(f"Model {model_name} doesn't exist, creating new model")
        
        # Create the model
        sagemaker_client.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': container_image,
                'ModelDataUrl': model_path,
                'Environment': {
                    'SAGEMAKER_BATCH': 'true'
                }
            },
            ExecutionRoleArn=role_arn
        )
        
        logger.info(f"Successfully created model: {model_name}")
        return model_name
    
    except ClientError as e:
        logger.error(f"Error creating SageMaker model: {str(e)}")
        raise

def create_batch_transform_job(model_name, input_path, output_path, transform_job_name, instance_type, instance_count):
    """
    Create a SageMaker batch transform job.
    
    Args:
        model_name (str): Name of the SageMaker model to use
        input_path (str): S3 path to the input data
        output_path (str): S3 path for the output data
        transform_job_name (str): Name for the transform job
        instance_type (str): Instance type for the transform job
        instance_count (int): Number of instances for the transform job
        
    Returns:
        str: The name of the created transform job
    """
    logger.info(f"Creating batch transform job: {transform_job_name}")
    
    # Ensure input_path is a proper S3 URI
    if not input_path.startswith('s3://'):
        raise ValueError(f"Input path must be an S3 URI, got: {input_path}")
    
    # Ensure output_path is a proper S3 URI
    if not output_path.startswith('s3://'):
        raise ValueError(f"Output path must be an S3 URI, got: {output_path}")
    
    # Create SageMaker client
    sagemaker_client = boto3.client('sagemaker')
    
    try:
        # Create the transform job
        response = sagemaker_client.create_transform_job(
            TransformJobName=transform_job_name,
            ModelName=model_name,
            TransformInput={
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': input_path
                    }
                },
                'ContentType': 'text/plain',
                'SplitType': 'Line'
            },
            TransformOutput={
                'S3OutputPath': output_path,
                'Accept': 'application/json',
                'AssembleWith': 'Line'
            },
            TransformResources={
                'InstanceType': instance_type,
                'InstanceCount': instance_count
            },
            BatchStrategy='MultiRecord',
            MaxPayloadInMB=6
        )
        
        logger.info(f"Successfully created transform job: {transform_job_name}")
        return transform_job_name
    
    except ClientError as e:
        logger.error(f"Error creating batch transform job: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Lambda function handler.
    
    Args:
        event (dict): The event dict containing the SQS message
        context (LambdaContext): The Lambda context object
        
    Returns:
        dict: Response containing the status and details of the batch transform job
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Validate required environment variables
    missing_env_vars = []
    if not MODEL_PATH:
        missing_env_vars.append("MODEL_PATH")
    if not CONTAINER_IMAGE:
        missing_env_vars.append("CONTAINER_IMAGE")
    if not ROLE_ARN:
        missing_env_vars.append("ROLE_ARN")
    
    if missing_env_vars:
        error_message = f"Missing required environment variables: {', '.join(missing_env_vars)}"
        logger.error(error_message)
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error_message})
        }
    
    # Process each SQS message
    responses = []
    for record in event['Records']:
        try:
            # Parse the message body
            message_body = json.loads(record['body'])
            logger.info(f"Processing message: {message_body}")
            
            # Extract the input path from the message
            if 'input_path' not in message_body:
                error_message = "Message does not contain 'input_path' field"
                logger.error(error_message)
                responses.append({
                    'status': 'error',
                    'message': error_message,
                    'messageId': record['messageId']
                })
                continue
            
            input_path = message_body['input_path']
            
            # Validate the input path
            valid, message = validate_s3_path(input_path)
            if not valid:
                logger.error(message)
                responses.append({
                    'status': 'error',
                    'message': message,
                    'messageId': record['messageId']
                })
                continue
            
            # Extract optional parameters from the message
            # If output_path is not provided, construct one using the input bucket and DEFAULT_OUTPUT_PREFIX
            if 'output_path' in message_body:
                output_path = message_body['output_path']
            else:
                # Extract bucket from input_path
                bucket = input_path.split('/')[2]
                output_path = f"s3://{bucket}/{DEFAULT_OUTPUT_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}/"
            
            instance_type = message_body.get('instance_type', DEFAULT_INSTANCE_TYPE)
            instance_count = message_body.get('instance_count', DEFAULT_INSTANCE_COUNT)
            
            # Generate a unique transform job name
            transform_job_name = f"{TRANSFORM_JOB_PREFIX}-{uuid.uuid4().hex[:8]}"
            
            # Create or use existing SageMaker model
            model_name = MODEL_NAME
            create_sagemaker_model(
                model_name=model_name,
                model_path=MODEL_PATH,
                container_image=CONTAINER_IMAGE,
                role_arn=ROLE_ARN
            )
            
            # Create batch transform job
            create_batch_transform_job(
                model_name=model_name,
                input_path=input_path,
                output_path=output_path,
                transform_job_name=transform_job_name,
                instance_type=instance_type,
                instance_count=instance_count
            )
            
            # Add job details to the response
            responses.append({
                'status': 'success',
                'transform_job_name': transform_job_name,
                'input_path': input_path,
                'output_path': output_path,
                'instance_type': instance_type,
                'instance_count': instance_count,
                'messageId': record['messageId']
            })
            
            logger.info(f"Successfully processed message and created transform job: {transform_job_name}")
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            responses.append({
                'status': 'error',
                'message': str(e),
                'messageId': record['messageId']
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"Processed {len(event['Records'])} messages",
            'results': responses
        })
    } 