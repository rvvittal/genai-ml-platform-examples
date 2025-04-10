#!/usr/bin/env python

"""
This script sets up an optimized SageMaker batch transform job for the ModernBERT model.
It uses a manifest-based approach to process all files at once for better performance.
"""

import os
import boto3
import json
import sagemaker
from sagemaker import get_execution_role
from dotenv import load_dotenv
import time
import argparse
import concurrent.futures

def setup_optimized_batch_transform(model_path, s3_bucket, s3_model_prefix, s3_input_prefix, 
                                   s3_output_prefix, container_image, instance_type, 
                                   instance_count, role_arn=None):
    """
    Set up an optimized SageMaker batch transform job using our custom batch processing
    
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
    
    # Normalize S3 input prefix to ensure it doesn't end with a slash
    s3_input_prefix = s3_input_prefix.rstrip('/')
    
    # List all input files in the S3 input prefix
    print(f"Listing input files in s3://{s3_bucket}/{s3_input_prefix}")
    paginator = s3_client.get_paginator('list_objects_v2')
    input_files = []
    
    for page in paginator.paginate(Bucket=s3_bucket, Prefix=s3_input_prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.txt') or obj['Key'].endswith('.csv'):
                    input_files.append(obj['Key'])
    
    print(f"Found {len(input_files)} input files")
    
    if not input_files:
        raise ValueError(f"No input files found in s3://{s3_bucket}/{s3_input_prefix}")
    
    # Function to load a file from S3
    def load_file_content(key):
        try:
            response = s3_client.get_object(Bucket=s3_bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            # Extract filename from the key
            filename = os.path.basename(key)
            return {
                "file_key": key,
                "filename": filename,
                "content": content.strip()  # Don't split by newlines, treat file as one document
            }
        except Exception as e:
            print(f"Error loading file {key}: {str(e)}")
            return {
                "file_key": key,
                "filename": os.path.basename(key),
                "content": "",
                "error": str(e)
            }
    
    # Load all file contents in parallel
    print(f"Loading contents of {len(input_files)} files...")
    start_time = time.time()
    
    # Determine if we need to chunk based on file count
    max_files_per_chunk = 100  # Adjust this based on your average file size
    force_chunking = len(input_files) > max_files_per_chunk
    
    if force_chunking:
        print(f"Large number of files detected ({len(input_files)}), will process in chunks of {max_files_per_chunk}")
    
    all_file_contents = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        all_file_contents = list(executor.map(load_file_content, input_files))
    
    # Filter out any files with errors
    all_file_contents = [f for f in all_file_contents if "error" not in f]
    
    # Create a list of texts with their filenames
    all_texts_with_metadata = []
    for file_content in all_file_contents:
        all_texts_with_metadata.append({
            "text": file_content["content"],
            "filename": file_content["filename"],
            "file_key": file_content["file_key"]
        })
    
    load_time = time.time() - start_time
    print(f"Loaded {len(all_texts_with_metadata)} files in {load_time:.2f} seconds")
    
    # Create a manifest file with all text content and metadata
    manifest_data = {
        "batch_manifest": True,
        "s3_bucket": s3_bucket,
        "all_texts_with_metadata": all_texts_with_metadata,
        "output_key": f"{s3_output_prefix.rstrip('/')}/batch_results.json"
    }
    
    # Upload manifest file to S3 - ensure no double slashes
    manifest_key = f"{s3_input_prefix}/batch_manifest.json"
    
    # Check manifest size
    manifest_json = json.dumps(manifest_data)
    manifest_size_mb = len(manifest_json) / (1024 * 1024)
    print(f"Manifest size: {manifest_size_mb:.2f} MB")
    
    # If manifest is too large or we have too many files, split it into chunks
    max_manifest_size_mb = 5  # Maximum size for a single manifest
    
    if manifest_size_mb > max_manifest_size_mb or force_chunking:
        if manifest_size_mb > max_manifest_size_mb:
            print(f"Manifest is too large ({manifest_size_mb:.2f} MB), splitting into chunks")
        else:
            print(f"Forcing chunking due to large number of files")
        
        # Calculate number of chunks needed
        if force_chunking:
            # Use file count for chunking
            chunk_size = max_files_per_chunk
        else:
            # Use manifest size for chunking
            chunk_size = max(1, int(len(all_texts_with_metadata) / (manifest_size_mb / max_manifest_size_mb)))
            
        num_chunks = (len(all_texts_with_metadata) + chunk_size - 1) // chunk_size
        
        print(f"Splitting {len(all_texts_with_metadata)} texts into {num_chunks} chunks of ~{chunk_size} texts each")
        
        # Create and upload manifest chunks
        manifest_keys = []
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(all_texts_with_metadata))
            
            chunk_manifest_data = {
                "batch_manifest": True,
                "s3_bucket": s3_bucket,
                "all_texts_with_metadata": all_texts_with_metadata[start_idx:end_idx],
                "chunk_index": i,
                "total_chunks": num_chunks,
                "output_key": f"{s3_output_prefix.rstrip('/')}/batch_results_chunk_{i}.json"
            }
            
            chunk_manifest_key = f"{s3_input_prefix}/batch_manifest_chunk_{i}.json"
            s3_client.put_object(
                Body=json.dumps(chunk_manifest_data),
                Bucket=s3_bucket,
                Key=chunk_manifest_key,
                ContentType='application/json'
            )
            
            manifest_keys.append(chunk_manifest_key)
            print(f"Uploaded chunk {i+1}/{num_chunks} to s3://{s3_bucket}/{chunk_manifest_key}")
        
        # Create a master manifest that references all chunks
        master_manifest_data = {
            "batch_manifest": True,
            "is_master_manifest": True,
            "s3_bucket": s3_bucket,
            "manifest_chunks": manifest_keys,
            "total_texts": len(all_texts_with_metadata),
            "output_prefix": f"{s3_output_prefix.rstrip('/')}"
        }
        
        s3_client.put_object(
            Body=json.dumps(master_manifest_data),
            Bucket=s3_bucket,
            Key=manifest_key,
            ContentType='application/json'
        )
        
        print(f"Uploaded master manifest to s3://{s3_bucket}/{manifest_key}")
    else:
        # Upload single manifest
        s3_client.put_object(
            Body=manifest_json,
            Bucket=s3_bucket,
            Key=manifest_key,
            ContentType='application/json'
        )
        
        print(f"Uploaded manifest to s3://{s3_bucket}/{manifest_key}")
    
    # Create a unique transform job name
    transform_job_name = f"modernbert-optimized-transform-{int(time.time())}"
    print(f"Creating optimized batch transform job: {transform_job_name}")
    
    # Set up transform input to only process the manifest file
    transform_input = {
        "DataSource": {
            "S3DataSource": {
                "S3DataType": "S3Prefix", 
                "S3Uri": f"s3://{s3_bucket}/{manifest_key}"
            }
        },
        "ContentType": "application/json",
        "SplitType": "None"  # Process the entire manifest as one record
    }
    
    # Set up transform output
    transform_output = {
        "S3OutputPath": f"s3://{s3_bucket}/{s3_output_prefix.rstrip('/')}",
        "Accept": "application/json",
        "AssembleWith": "None"  # We'll handle the output assembly in our container
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
        BatchStrategy="SingleRecord",  # Process the manifest as a single record
        MaxPayloadInMB=6
    )
    
    print(f"Optimized batch transform job {transform_job_name} created successfully")
    print(f"Results will be available at: s3://{s3_bucket}/{s3_output_prefix.rstrip('/')}/batch_results.json")
    return transform_job_name

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Set up optimized SageMaker batch transform job")
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
    
    setup_optimized_batch_transform(
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