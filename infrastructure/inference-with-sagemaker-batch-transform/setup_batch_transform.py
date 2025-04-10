#!/usr/bin/env python

"""
This script sets up a SageMaker batch transform job for the ModernBERT model.
It uploads the model to S3, creates a SageMaker model, and sets up a batch transform job.
"""

import os
import boto3
import sagemaker
from sagemaker import get_execution_role
from dotenv import load_dotenv
import time
import argparse

def setup_batch_transform(model_path, s3_bucket, s3_model_prefix, s3_input_prefix, s3_output_prefix, 
                          container_image, instance_type, instance_count, role_arn=None):
    """
    Set up a SageMaker batch transform job
    
    Args:
        model_path: Path to the model.tar.gz file
        s3_bucket: S3 bucket name
        s3_model_prefix: S3 prefix for the model
        s3_input_prefix: S3 prefix for the input data
        s3_output_prefix: S3 prefix for the output data
        container_image: ECR image URI
        instance_type: Instance type for the transform job
        instance_count: Number of instances for the transform job
        role_arn: SageMaker execution role ARN (if None, will try to get from environment)
    
    Returns:
        The transform job name
    """
    # Initialize clients
    session = boto3.Session()
    sm_client = session.client('sagemaker')
    s3_client = session.client('s3')
    
    # Initialize SageMaker session
    sagemaker_session = sagemaker.Session(boto_session=session)
    
    # Get IAM role
    if role_arn:
        # Use provided role ARN
        role = role_arn
        print(f"Using provided role ARN: {role}")
    else:
        # Try to get role from SageMaker environment (works in notebook instances)
        try:
            role = get_execution_role()
            print(f"Using SageMaker execution role: {role}")
        except ValueError as e:
            # If running locally and no role provided, raise a more helpful error
            raise ValueError(
                "No SageMaker execution role found. When running locally, you must provide a "
                "role_arn parameter or set SAGEMAKER_ROLE_ARN in your .env file. "
                f"Original error: {str(e)}"
            )
    
    # Upload model to S3
    print(f"Uploading model to s3://{s3_bucket}/{s3_model_prefix}")
    s3_model_path = f"s3://{s3_bucket}/{s3_model_prefix}"
    s3_client.upload_file(model_path, s3_bucket, s3_model_prefix)
    
    # Create a unique model name
    model_name = f"modernbert-dispute-classifier-{int(time.time())}"
    print(f"Creating SageMaker model: {model_name}")
    
    # Create SageMaker model
    sm_client.create_model(
        ModelName=model_name,
        PrimaryContainer={
            'Image': container_image,
            'ModelDataUrl': s3_model_path,
        },
        ExecutionRoleArn=role
    )
    
    # Create a unique transform job name
    transform_job_name = f"modernbert-transform-{int(time.time())}"
    print(f"Creating batch transform job: {transform_job_name}")
    
    # Set up transform input
    transform_input = {
        "DataSource": {
            "S3DataSource": {
                "S3DataType": "S3Prefix", 
                "S3Uri": f"s3://{s3_bucket}/{s3_input_prefix}"
            }
        },
        "ContentType": "text/plain",
        "SplitType": "Line"
    }
    
    # Set up transform output
    transform_output = {
        "S3OutputPath": f"s3://{s3_bucket}/{s3_output_prefix}",
        "Accept": "application/json",
        "AssembleWith": "Line"
    }
    
    # Set up transform resources
    transform_resources = {
        "InstanceType": instance_type,
        "InstanceCount": instance_count
    }
    
    # Create the transform job
    sm_client.create_transform_job(
        TransformJobName=transform_job_name,
        ModelName=model_name,
        TransformInput=transform_input,
        TransformOutput=transform_output,
        TransformResources=transform_resources,
        BatchStrategy="MultiRecord",
        MaxPayloadInMB=6
    )
    
    print(f"Batch transform job {transform_job_name} created successfully")
    return transform_job_name

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Set up SageMaker batch transform job")
    parser.add_argument(
        "--model-path", 
        type=str, 
        default="model.tar.gz",
        help="Path to the model.tar.gz file"
    )
    parser.add_argument(
        "--s3-bucket", 
        type=str, 
        default=os.environ.get("S3_BUCKET_NAME"),
        help="S3 bucket name"
    )
    parser.add_argument(
        "--s3-model-prefix", 
        type=str, 
        default=os.environ.get("S3_MODEL_PATH"),
        help="S3 prefix for the model"
    )
    parser.add_argument(
        "--s3-input-prefix", 
        type=str, 
        default=os.environ.get("S3_INPUT_PATH"),
        help="S3 prefix for the input data"
    )
    parser.add_argument(
        "--s3-output-prefix", 
        type=str, 
        default=os.environ.get("S3_OUTPUT_PATH"),
        help="S3 prefix for the output data"
    )
    parser.add_argument(
        "--container-image", 
        type=str, 
        default=os.environ.get("CONTAINER_IMAGE"),
        help="ECR image URI"
    )
    parser.add_argument(
        "--instance-type", 
        type=str, 
        default=os.environ.get("SAGEMAKER_INSTANCE_TYPE", "ml.g4dn.xlarge"),
        help="Instance type for the transform job"
    )
    parser.add_argument(
        "--instance-count", 
        type=int, 
        default=int(os.environ.get("SAGEMAKER_INSTANCE_COUNT", "1")),
        help="Number of instances for the transform job"
    )
    parser.add_argument(
        "--role-arn", 
        type=str, 
        default=os.environ.get("SAGEMAKER_ROLE_ARN"),
        help="SageMaker execution role ARN (required when running locally)"
    )
    
    args = parser.parse_args()
    
    setup_batch_transform(
        args.model_path,
        args.s3_bucket,
        args.s3_model_prefix,
        args.s3_input_prefix,
        args.s3_output_prefix,
        args.container_image,
        args.instance_type,
        args.instance_count,
        args.role_arn
    ) 