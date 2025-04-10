#!/bin/bash

# Exit on error
set -e

# Get environment variables from .env file
if [ -f ../.env ]; then
    export $(grep -v '^#' ../.env | xargs)
fi

# Set up variables
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY=${ECR_REPOSITORY_NAME:-"dispute-classifier"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
DOCKERFILE_PATH="."

# Full image name
FULLNAME="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"

# Check if ECR repository exists, create if it doesn't
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${REGION} || aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${REGION}

# Get ECR login
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Build Docker image using standard Docker build (no buildx)
echo "Building Docker image for linux/amd64 platform..."
docker build --platform=linux/amd64 -t ${ECR_REPOSITORY} ${DOCKERFILE_PATH}

# Tag Docker image
docker tag ${ECR_REPOSITORY} ${FULLNAME}

# Push Docker image to ECR
echo "Pushing Docker image to ECR..."
docker push ${FULLNAME}

echo "Successfully built and pushed image: ${FULLNAME}"
echo "To use this image with the batch transform, update your environment variables with:"
echo "export CONTAINER_IMAGE=${FULLNAME}" 