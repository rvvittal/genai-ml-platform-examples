#!/bin/bash

# Package Lambda function with layers for deployment
# Based on strands example approach

set -e

echo "🚀 Packaging Travel Planner Lambda with layers..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
LAMBDA_DIR="lambda"
PACKAGING_DIR="packaging"
APP_ZIP="packaging/app.zip"
DEPS_ZIP="packaging/dependencies.zip"

# Clean previous build
echo -e "${YELLOW}Cleaning previous build...${NC}"
rm -rf $PACKAGING_DIR
mkdir -p $PACKAGING_DIR

# Install dependencies with correct platform
echo -e "${YELLOW}Installing dependencies for Lambda...${NC}"
pip install -r requirements-lambda.txt \
    --platform manylinux2014_x86_64 \
    --target $PACKAGING_DIR/_dependencies \
    --python-version 3.12 \
    --implementation cp \
    --only-binary=:all: \
    --upgrade

# Create dependencies layer zip
echo -e "${YELLOW}Creating dependencies layer...${NC}"
cd $PACKAGING_DIR/_dependencies
# Lambda layers expect dependencies in python/ directory
mkdir -p ../python
cp -r * ../python/
cd ../
zip -r dependencies.zip python -q
rm -rf python _dependencies
cd ..

# Create application zip
echo -e "${YELLOW}Creating application package...${NC}"
cd $LAMBDA_DIR
zip -r ../$APP_ZIP . -q
cd ..

# Get package sizes
APP_SIZE=$(du -h $APP_ZIP | cut -f1)
DEPS_SIZE=$(du -h $DEPS_ZIP | cut -f1)

echo -e "${GREEN}✅ Lambda packages created successfully!${NC}"
echo -e "   Application: $APP_ZIP ($APP_SIZE)"
echo -e "   Dependencies: $DEPS_ZIP ($DEPS_SIZE)"
