FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH="/opt/program:${PATH}" \
    SAGEMAKER_BATCH=true

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    git \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /opt/program

# Copy requirements file
COPY requirements.txt .

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local/lib/python3.11/site-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python3.11/site-packages -name "__pycache__" -delete

# Start the final image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH="/opt/program:${PATH}" \
    SAGEMAKER_BATCH=true \
    TORCH_COMPILE_MODE=reduce-overhead \
    TORCH_INDUCTOR_DISABLE=1

# Install system dependencies in the final image too
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /opt/program

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ src/
COPY app.py .

# Create serve script with proper SageMaker structure
RUN echo '#!/bin/bash\n\
\n\
# Check if required environment variables exist, otherwise set to defaults\n\
export SAGEMAKER_BATCH=${SAGEMAKER_BATCH:-true}\n\
export SAGEMAKER_MAX_PAYLOAD_IN_MB=${SAGEMAKER_MAX_PAYLOAD_IN_MB:-6}\n\
export SAGEMAKER_BATCH_STRATEGY=${SAGEMAKER_BATCH_STRATEGY:-"MULTI_RECORD"}\n\
export SAGEMAKER_MAX_CONCURRENT_TRANSFORMS=${SAGEMAKER_MAX_CONCURRENT_TRANSFORMS:-1}\n\
export TORCH_INDUCTOR_DISABLE=1\n\
\n\
cd /opt/program\n\
\n\
# Log key information\n\
echo "Starting inference server with gunicorn..."\n\
echo "Environment: SAGEMAKER_BATCH=${SAGEMAKER_BATCH}"\n\
echo "Environment: MODEL_DIR=${SM_MODEL_DIR:-/opt/ml/model}"\n\
echo "Environment: TORCH_INDUCTOR_DISABLE=${TORCH_INDUCTOR_DISABLE}"\n\
\n\
# Print PyTorch CUDA information\n\
python -c "import torch; print(f\"PyTorch version: {torch.__version__}\"); print(f\"CUDA available: {torch.cuda.is_available()}\"); print(f\"CUDA device count: {torch.cuda.device_count()}\"); print(f\"CUDA version: {torch.version.cuda}\")"\n\
\n\
# Start gunicorn server\n\
exec gunicorn --bind 0.0.0.0:8080 --timeout 300 --workers 1 app:app\n' > /opt/program/serve && \
    chmod +x /opt/program/serve

# Create train script - required by SageMaker even if unused
RUN echo '#!/bin/bash\n\
echo "Training script - not implemented for this inference-only container"\n\
exit 0\n' > /opt/program/train && \
    chmod +x /opt/program/train

# Make sure all files have correct permissions
RUN chmod -R 755 /opt/program

# The exec form of ENTRYPOINT is required by SageMaker
# SageMaker will append 'serve' to this command, so we point to the directory
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["serve"] 