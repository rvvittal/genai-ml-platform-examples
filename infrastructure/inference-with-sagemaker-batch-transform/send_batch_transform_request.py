#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Send Batch Transform Request

This script sends a message to an SQS queue to trigger a batch transform job.

Usage:
    python send_batch_transform_request.py [options]

Options:
    --queue-url TEXT                 SQS queue URL to send the message to [default: from .env]
    --input-path TEXT                S3 path to the input data [default: from .env]
    --output-path TEXT               S3 path for the output data [default: from .env]
    --instance-type TEXT             Instance type for the batch transform job [default: from .env]
    --instance-count INTEGER         Number of instances for the batch transform job [default: from .env]
    --help                           Show this message and exit.
"""

import os
import json
import logging
import argparse
import boto3
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
    parser = argparse.ArgumentParser(description='Send Batch Transform Request')
    
    parser.add_argument('--queue-url', type=str,
                        default=os.environ.get('SQS_QUEUE_URL'),
                        help='SQS queue URL to send the message to')
    parser.add_argument('--input-path', type=str,
                        default=f"s3://{os.environ.get('S3_BUCKET_NAME', '')}/{os.environ.get('S3_INPUT_PATH', '')}",
                        help='S3 path to the input data')
    parser.add_argument('--output-path', type=str,
                        default=f"s3://{os.environ.get('S3_BUCKET_NAME', '')}/{os.environ.get('S3_OUTPUT_PATH', '')}",
                        help='S3 path for the output data')
    parser.add_argument('--instance-type', type=str,
                        default=os.environ.get('SAGEMAKER_INSTANCE_TYPE', 'ml.g4dn.xlarge'),
                        help='Instance type for the batch transform job')
    parser.add_argument('--instance-count', type=int,
                        default=int(os.environ.get('SAGEMAKER_INSTANCE_COUNT', '1')),
                        help='Number of instances for the batch transform job')
    
    return parser.parse_args()

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

def send_sqs_message(queue_url, message_body):
    """
    Send a message to an SQS queue.
    
    Args:
        queue_url (str): URL of the SQS queue
        message_body (dict): Message body to send
        
    Returns:
        dict: Response from SQS
    """
    # Create SQS client
    sqs_client = boto3.client('sqs')
    
    try:
        # Send message to SQS queue
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
        
        logger.info(f"Message sent to SQS queue: {response['MessageId']}")
        return response
    
    except ClientError as e:
        logger.error(f"Error sending message to SQS queue: {str(e)}")
        raise

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Validate required arguments
    missing_args = []
    
    if not args.queue_url:
        missing_args.append("SQS queue URL (--queue-url or SQS_QUEUE_URL in .env)")
    
    if not args.input_path:
        missing_args.append("Input path (--input-path or S3_BUCKET_NAME and S3_INPUT_PATH in .env)")
    
    if missing_args:
        logger.error("Missing required arguments:")
        for arg in missing_args:
            logger.error(f"  - {arg}")
        logger.error("Please provide these arguments via command line or .env file")
        return
    
    # Validate the input path
    valid, message = validate_s3_path(args.input_path)
    if not valid:
        logger.error(message)
        return
    
    # Create message body
    message_body = {
        'input_path': args.input_path,
        'instance_type': args.instance_type,
        'instance_count': args.instance_count
    }
    
    # Add output path if provided
    if args.output_path:
        message_body['output_path'] = args.output_path
    
    # Log configuration
    logger.info("Sending batch transform request with the following configuration:")
    logger.info(f"  Queue URL: {args.queue_url}")
    logger.info(f"  Input Path: {args.input_path}")
    logger.info(f"  Output Path: {args.output_path if args.output_path else 'Not specified (will use default)'}")
    logger.info(f"  Instance Type: {args.instance_type}")
    logger.info(f"  Instance Count: {args.instance_count}")
    
    # Send message to SQS queue
    try:
        response = send_sqs_message(args.queue_url, message_body)
        logger.info(f"Successfully sent message to SQS queue: {response}")
        logger.info(f"Request details: {json.dumps(message_body, indent=2)}")
    
    except Exception as e:
        logger.error(f"Error sending message to SQS queue: {str(e)}")

if __name__ == '__main__':
    main() 