#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check Batch Transform Status

This script checks the status of SageMaker batch transform jobs.

Usage:
    python check_batch_transform_status.py [options]

Options:
    --job-name TEXT                  Name of the batch transform job to check
    --list-jobs BOOLEAN              List all batch transform jobs [default: False]
    --max-results INTEGER            Maximum number of jobs to list [default: 10]
    --help                           Show this message and exit.
"""

import os
import json
import logging
import argparse
import boto3
from datetime import datetime
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
    parser = argparse.ArgumentParser(description='Check Batch Transform Status')
    
    parser.add_argument('--job-name', type=str,
                        help='Name of the batch transform job to check')
    parser.add_argument('--list-jobs', action='store_true',
                        help='List all batch transform jobs')
    parser.add_argument('--max-results', type=int, default=10,
                        help='Maximum number of jobs to list')
    
    return parser.parse_args()

def get_transform_job_status(job_name):
    """
    Get the status of a SageMaker batch transform job.
    
    Args:
        job_name (str): Name of the batch transform job
        
    Returns:
        dict: Details of the batch transform job
    """
    # Create SageMaker client
    sagemaker_client = boto3.client('sagemaker')
    
    try:
        # Get transform job details
        response = sagemaker_client.describe_transform_job(
            TransformJobName=job_name
        )
        
        return response
    
    except ClientError as e:
        logger.error(f"Error getting transform job status: {str(e)}")
        raise

def list_transform_jobs(max_results=10):
    """
    List SageMaker batch transform jobs.
    
    Args:
        max_results (int): Maximum number of jobs to list
        
    Returns:
        list: List of batch transform jobs
    """
    # Create SageMaker client
    sagemaker_client = boto3.client('sagemaker')
    
    try:
        # List transform jobs
        response = sagemaker_client.list_transform_jobs(
            MaxResults=max_results,
            SortBy='CreationTime',
            SortOrder='Descending'
        )
        
        return response['TransformJobSummaries']
    
    except ClientError as e:
        logger.error(f"Error listing transform jobs: {str(e)}")
        raise

def format_job_status(job_details):
    """
    Format the status of a batch transform job for display.
    
    Args:
        job_details (dict): Details of the batch transform job
        
    Returns:
        str: Formatted status string
    """
    # Extract relevant details
    job_name = job_details['TransformJobName']
    job_status = job_details['TransformJobStatus']
    model_name = job_details['ModelName']
    creation_time = job_details['CreationTime']
    
    # Format creation time
    creation_time_str = creation_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Get additional details based on status
    status_details = ""
    if job_status == 'Completed':
        end_time = job_details.get('TransformEndTime')
        if end_time:
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
            duration = end_time - creation_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            status_details = f"Completed at: {end_time_str}, Duration: {duration_str}"
    elif job_status == 'Failed':
        failure_reason = job_details.get('FailureReason', 'Unknown')
        status_details = f"Failure reason: {failure_reason}"
    elif job_status == 'InProgress':
        status_details = "Job is still running..."
    
    # Format input and output details
    input_details = job_details['TransformInput']
    output_details = job_details['TransformOutput']
    
    input_path = input_details['DataSource']['S3DataSource']['S3Uri']
    output_path = output_details['S3OutputPath']
    
    # Format resources
    resources = job_details['TransformResources']
    instance_type = resources['InstanceType']
    instance_count = resources['InstanceCount']
    
    # Build the formatted status string
    status_str = f"""
Job Name: {job_name}
Status: {job_status}
{status_details}

Model: {model_name}
Created: {creation_time_str}

Resources:
  Instance Type: {instance_type}
  Instance Count: {instance_count}

Paths:
  Input: {input_path}
  Output: {output_path}
"""
    
    return status_str

def format_job_summary(job_summary):
    """
    Format the summary of a batch transform job for display.
    
    Args:
        job_summary (dict): Summary of the batch transform job
        
    Returns:
        str: Formatted summary string
    """
    # Extract relevant details
    job_name = job_summary['TransformJobName']
    job_status = job_summary['TransformJobStatus']
    model_name = job_summary['ModelName']
    creation_time = job_summary['CreationTime']
    
    # Format creation time
    creation_time_str = creation_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Get additional details based on status
    status_details = ""
    if job_status == 'Completed':
        end_time = job_summary.get('TransformEndTime')
        if end_time:
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
            duration = end_time - creation_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            status_details = f"Completed at: {end_time_str}, Duration: {duration_str}"
    elif job_status == 'Failed':
        status_details = "Job failed"
    elif job_status == 'InProgress':
        status_details = "Job is still running..."
    
    # Build the formatted summary string
    summary_str = f"{job_name:<40} | {job_status:<12} | {model_name:<30} | {creation_time_str} | {status_details}"
    
    return summary_str

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Check if job name is provided or list jobs is specified
    if args.job_name:
        try:
            # Get job status
            job_details = get_transform_job_status(args.job_name)
            
            # Format and print job status
            status_str = format_job_status(job_details)
            print(status_str)
            
        except Exception as e:
            logger.error(f"Error checking transform job status: {str(e)}")
    
    elif args.list_jobs:
        try:
            # List jobs
            job_summaries = list_transform_jobs(args.max_results)
            
            # Print header
            print(f"{'Job Name':<40} | {'Status':<12} | {'Model Name':<30} | {'Creation Time':<19} | {'Details'}")
            print("-" * 120)
            
            # Format and print job summaries
            for job_summary in job_summaries:
                summary_str = format_job_summary(job_summary)
                print(summary_str)
            
            # Print footer
            print("\nTo check a specific job, run:")
            print("python check_batch_transform_status.py --job-name <job-name>")
            
        except Exception as e:
            logger.error(f"Error listing transform jobs: {str(e)}")
    
    else:
        print("Please provide a job name or use --list-jobs to list all jobs")
        print("For help, run: python check_batch_transform_status.py --help")

if __name__ == '__main__':
    main() 