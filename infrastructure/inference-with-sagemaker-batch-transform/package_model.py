#!/usr/bin/env python

"""
This script packages the ModernBERT model artifacts for SageMaker.
It creates a model.tar.gz file containing all necessary model files.
"""

import os
import tarfile
import shutil
import argparse
from dotenv import load_dotenv

def package_model(model_dir, output_path):
    """
    Package model artifacts into a tar.gz file for SageMaker
    
    Args:
        model_dir: Directory containing model files
        output_path: Path for the output tar.gz file
    """
    print(f"Packaging model from {model_dir}")
    
    # Create a temporary directory
    tmp_dir = "tmp_model"
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Copy model files to the temp directory
    for file in os.listdir(model_dir):
        source = os.path.join(model_dir, file)
        destination = os.path.join(tmp_dir, file)
        if os.path.isfile(source):
            shutil.copy2(source, destination)
            print(f"Copied {file}")
    
    # Create the tar.gz file
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(tmp_dir, arcname=".")
    
    # Clean up
    shutil.rmtree(tmp_dir)
    
    print(f"Model packaged successfully to {output_path}")

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Package ModernBERT model for SageMaker")
    parser.add_argument(
        "--model-dir", 
        type=str, 
        default=os.environ.get("MODEL_DIR", "./modernbert_dispute_classifier/final"),
        help="Directory containing model files"
    )
    parser.add_argument(
        "--output-path", 
        type=str, 
        default="model.tar.gz",
        help="Path for the output tar.gz file"
    )
    
    args = parser.parse_args()
    package_model(args.model_dir, args.output_path) 