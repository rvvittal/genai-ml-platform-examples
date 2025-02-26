#!/bin/bash

# Exit on any error
set -e

# Configuration variables
PROJECT_NAME="arm-docker-build"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO_NAME="llama-cpp-python"
IMAGE_TAG="latest"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUILDSPEC_FILE="buildspec.yml"
S3_BUCKET="${AWS_ACCOUNT_ID}-codebuild-source"
CODEBUILD_ROLE_NAME="codebuild-${PROJECT_NAME}-service-role"

# Function to wait for CodeBuild project to be ready
wait_for_codebuild_project() {
    echo "Waiting for CodeBuild project to be ready..."
    while true; do
        if aws codebuild batch-get-projects --names "${PROJECT_NAME}" --region "${AWS_REGION}" | grep -q "\"name\": \"${PROJECT_NAME}\""; then
            echo "CodeBuild project is ready"
            break
        fi
        echo "Still waiting for CodeBuild project..."
        sleep 10
    done
}

# Function to check if project exists
check_project_exists() {
    aws codebuild batch-get-projects --names "${PROJECT_NAME}" --region "${AWS_REGION}" | grep -q "\"name\": \"${PROJECT_NAME}\"" || return 1
}

# Create CodeBuild project
create_codebuild_project() {
    echo "Creating CodeBuild project..."
    
    aws codebuild create-project \
        --name "${PROJECT_NAME}" \
        --description "Docker build project for ARM64 architecture" \
        --source "{
            \"type\": \"S3\",
            \"location\": \"${S3_BUCKET}/source.zip\"
        }" \
        --artifacts "{
            \"type\": \"NO_ARTIFACTS\"
        }" \
        --environment "{
            \"type\": \"ARM_CONTAINER\",
            \"image\": \"aws/codebuild/amazonlinux2-aarch64-standard:2.0\",
            \"computeType\": \"BUILD_GENERAL1_LARGE\",
            \"privilegedMode\": true,
            \"environmentVariables\": [
                {
                    \"name\": \"AWS_DEFAULT_REGION\",
                    \"value\": \"${AWS_REGION}\",
                    \"type\": \"PLAINTEXT\"
                },
                {
                    \"name\": \"AWS_ACCOUNT_ID\",
                    \"value\": \"${AWS_ACCOUNT_ID}\",
                    \"type\": \"PLAINTEXT\"
                },
                {
                    \"name\": \"ECR_REPO_NAME\",
                    \"value\": \"${ECR_REPO_NAME}\",
                    \"type\": \"PLAINTEXT\"
                }
            ]
        }" \
        --service-role "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${CODEBUILD_ROLE_NAME}" \
        --region "${AWS_REGION}"

    # Wait for project to be ready
    wait_for_codebuild_project
}

# Create IAM role for CodeBuild
create_codebuild_role() {
    echo "Creating IAM role for CodeBuild..."
    
    # Create trust policy
    cat << EOF > trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create policy document
    cat << EOF > policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Resource": [
                "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/aws/codebuild/${PROJECT_NAME}",
                "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/aws/codebuild/${PROJECT_NAME}:*"
            ],
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ]
        },
        {
            "Effect": "Allow",
            "Resource": [
                "arn:aws:s3:::${S3_BUCKET}/*"
            ],
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:GetBucketAcl",
                "s3:GetBucketLocation"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:BatchCheckLayerAvailability",
                "ecr:CompleteLayerUpload",
                "ecr:GetAuthorizationToken",
                "ecr:InitiateLayerUpload",
                "ecr:PutImage",
                "ecr:UploadLayerPart",
                "ecr:BatchGetImage",
                "ecr:GetDownloadUrlForLayer"
            ],
            "Resource": "*"
        }
    ]
}
EOF

    # Create IAM role
    aws iam create-role \
        --role-name ${CODEBUILD_ROLE_NAME} \
        --assume-role-policy-document file://trust-policy.json

    # Create IAM policy
    aws iam put-role-policy \
        --role-name ${CODEBUILD_ROLE_NAME} \
        --policy-name codebuild-policy \
        --policy-document file://policy.json

    # Clean up policy files
    rm trust-policy.json policy.json

    # Wait for role to be available
    echo "Waiting for IAM role to be available..."
    sleep 20
}

# Check and create S3 bucket
if ! aws s3api head-bucket --bucket "${S3_BUCKET}" 2>/dev/null; then
    echo "Creating S3 bucket: ${S3_BUCKET}"
    if [ "${AWS_REGION}" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "${S3_BUCKET}" \
            --region "${AWS_REGION}"
    else
        aws s3api create-bucket \
            --bucket "${S3_BUCKET}" \
            --region "${AWS_REGION}" \
            --create-bucket-configuration LocationConstraint="${AWS_REGION}"
    fi

    # Configure bucket
    aws s3api put-bucket-versioning \
        --bucket "${S3_BUCKET}" \
        --versioning-configuration Status=Enabled

    aws s3api put-bucket-encryption \
        --bucket "${S3_BUCKET}" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
fi

# Check if role exists
if aws iam get-role --role-name "${CODEBUILD_ROLE_NAME}" 2>/dev/null; then
    echo "Role ${CODEBUILD_ROLE_NAME} exists. Deleting..."
    
    # First detach all policies from the role
    for policy_arn in $(aws iam list-attached-role-policies --role-name "${CODEBUILD_ROLE_NAME}" --query 'AttachedPolicies[*].PolicyArn' --output text); do
        echo "Detaching policy: ${policy_arn}"
        aws iam detach-role-policy \
            --role-name "${CODEBUILD_ROLE_NAME}" \
            --policy-arn "${policy_arn}"
    done

    # Delete any inline policies
    for policy_name in $(aws iam list-role-policies --role-name "${CODEBUILD_ROLE_NAME}" --query 'PolicyNames[*]' --output text); do
        echo "Deleting inline policy: ${policy_name}"
        aws iam delete-role-policy \
            --role-name "${CODEBUILD_ROLE_NAME}" \
            --policy-name "${policy_name}"
    done

    # Delete the role
    aws iam delete-role --role-name "${CODEBUILD_ROLE_NAME}"
    
    # Wait a bit for deletion to propagate
    echo "Waiting for role deletion to propagate..."
    sleep 10
fi

# Create new role
echo "Creating new role: ${CODEBUILD_ROLE_NAME}"
create_codebuild_role

# Verify the role was created
if aws iam get-role --role-name "${CODEBUILD_ROLE_NAME}" &>/dev/null; then
    echo "Role ${CODEBUILD_ROLE_NAME} successfully created"
else
    echo "Failed to create role ${CODEBUILD_ROLE_NAME}"
    exit 1
fi

# Check and create CodeBuild project
if ! check_project_exists; then
    create_codebuild_project
fi

# Delete buildspec.yml if it exists and create new one
if [ -f "$BUILDSPEC_FILE" ]; then
    echo "Removing existing buildspec file..."
    rm -f "$BUILDSPEC_FILE"
fi

# Create new buildspec.yml
if [ ! -f "$BUILDSPEC_FILE" ]; then
    echo "Creating new buildspec file..."
    cat << EOF > "$BUILDSPEC_FILE"
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region \$AWS_DEFAULT_REGION | docker login --username AWS --password-stdin \$AWS_ACCOUNT_ID.dkr.ecr.\$AWS_DEFAULT_REGION.amazonaws.com
      - aws ecr get-login-password --region \$AWS_DEFAULT_REGION | docker login --username AWS --password-stdin 763104351884.dkr.ecr.\$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=\$AWS_ACCOUNT_ID.dkr.ecr.\$AWS_DEFAULT_REGION.amazonaws.com/\$ECR_REPO_NAME
      - COMMIT_HASH=\$(echo \$CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=\${COMMIT_HASH:=latest}
  build:
    commands:
      - echo Build started on \`date\`
      - echo Building the Docker image...
      - docker build -t \$REPOSITORY_URI:latest .
      - docker tag \$REPOSITORY_URI:latest \$REPOSITORY_URI:\$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on \`date\`
      - echo Pushing the Docker images...
      - docker push \$REPOSITORY_URI:latest
      - docker push \$REPOSITORY_URI:\$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '{"ImageURI":"%s"}' \$REPOSITORY_URI:\$IMAGE_TAG > imageDefinitions.json
artifacts:
  files:
    - imageDefinitions.json
EOF
fi

# Create ECR repository if needed
if aws ecr describe-repositories --repository-names "${{ECR_REPO_NAME}" &>/dev/null; then
    echo "Repository ${{ECR_REPO_NAME} already exists"
else
# if ! aws ecr describe-repositories --repository-names "${ECR_REPO_NAME}" --region "${AWS_REGION}" &> /dev/null; then
    echo "Creating ECR repository..."
    aws ecr create-repository \
        --repository-name "${ECR_REPO_NAME}" \
        --region "${AWS_REGION}"
fi

echo "Creating source package..."
zip -r source.zip . -x "*.git*" -x "*.cache*" -x "*code*" -x "*.ipynb*" -x "*.tar.gz*"

echo "Uploading source to S3..."
aws s3 cp source.zip "s3://${S3_BUCKET}/source.zip"

# Wait a moment for S3 upload to complete
sleep 5

# Start build with retry logic
echo "Starting CodeBuild job..."
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if BUILD_ID=$(aws codebuild start-build \
        --project-name "${PROJECT_NAME}" \
        --region "${AWS_REGION}" \
        --query 'build.id' \
        --output text 2>/dev/null); then
        echo "Build started with ID: ${BUILD_ID}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "Failed to start build, retrying in 10 seconds..."
            sleep 10
        else
            echo "Failed to start build after ${MAX_RETRIES} attempts"
            exit 1
        fi
    fi
done

# Monitor build progress
while true; do
    BUILD_STATUS=$(aws codebuild batch-get-builds \
        --ids "${BUILD_ID}" \
        --region "${AWS_REGION}" \
        --query 'builds[0].buildStatus' \
        --output text 2>/dev/null)
    
    echo "Build status: ${BUILD_STATUS}"
    
    if [ "${BUILD_STATUS}" = "SUCCEEDED" ]; then
        echo "Build completed successfully!"
        break
    elif [ "${BUILD_STATUS}" = "FAILED" ] || [ "${BUILD_STATUS}" = "STOPPED" ]; then
        echo "Build failed or was stopped."
        exit 1
    fi
    
    sleep 30
done

echo "Docker image built and pushed to ECR successfully!"
