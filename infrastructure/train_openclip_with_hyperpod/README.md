# OpenCLIP Training on AWS SageMaker HyperPod

This guide provides step-by-step instructions for setting up a SageMaker HyperPod cluster in AWS and configuring it for training OpenCLIP models using AWS Neuron SDK. The setup includes cluster creation, environment configuration, and training initialization.

## Prerequisites

- AWS Account with appropriate permissions
- Access to AWS region us-west-2 (Recommended for trn1 instance availability)
- SSH client

## 1. Cluster Creation

### 1.1 Deploy SageMaker HyperPod Stack

1. Follow the [AWS SageMaker HyperPod Workshop](https://catalog.workshops.aws/sagemaker-hyperpod/en-US) guide
2. During deployment, set "Availability zone id to deploy the primary subnets" to `usw2-az4`
3. Complete the "Deploy SageMaker HyperPod Stack" section

### 1.2 Create Cluster Configuration

1. Navigate to the [Manual Cluster Setup](https://catalog.workshops.aws/sagemaker-hyperpod/en-US/01-cluster/option-b-manual-cluster-setup) section
2. In the "Create Cluster" step, use [this configuration template](https://paste.amazon.com/show/xniwang/1738065357) to generate your `cluster-config.json`
   - This will create a cluster with:
     - 1 control machine
     - 2 trn1.32xlarge instances

### 1.3 Access the Cluster

Follow the SSH instructions in the workshop guide to connect to your cluster.

## 2. Neuron SDK Configuration

### 2.1 Update Neuron Driver (On Each TRN1 Instance)

SSH into each trn1 instance and run:

```bash
sudo apt-get install \
    aws-neuronx-collectives=2.22.26.0-17a033bc8 \
    aws-neuronx-dkms=2.18.12.0 \
    aws-neuronx-oci-hook=2.5.3.0 \
    aws-neuronx-runtime-lib=2.22.14.0-6e27b8d5b \
    aws-neuronx-tools=2.19.0.0
```

### 2.2 Set Up Virtual Environment (On Controller Machine)

Connect to the controller machine and run:

```bash
# Install required packages
sudo apt-get install -y python3.8-venv g++

# Create and activate virtual environment
python3.8 -m venv /fsx/ubuntu/aws_neuron_venv_pytorch
source /fsx/ubuntu/aws_neuron_venv_pytorch/bin/activate

# Configure pip
python -m pip install -U pip
python -m pip config set global.extra-index-url https://pip.repos.neuron.amazonaws.com

# Install primary dependencies
pip install \
    aws-neuronx-runtime-discovery==2.9 \
    neuronx-cc==2.15.141.0+d3cfc8ca \
    neuronx-distributed==0.9.0 \
    neuronx-distributed-training==1.0.0 \
    torch-neuronx==2.1.2.2.3.1 \
    torch==2.1.2 \
    torchvision==0.16.2 

# Install additional dependencies
pip install \
    aws-neuronx-runtime-discovery==2.9 \
    libneuronxla==2.0.4986.0 \
    neuronx-cc==2.15.141.0+d3cfc8ca \
    neuronx-distributed==0.9.0 \
    neuronx-distributed-training==1.0.0 \
    torch-neuronx==2.1.2.2.3.1
```

## 3. Training Setup

### 3.1 Prepare Training Environment

1. Download `open_clip_trn.tar.gz`
2. Extract it to the `/fsx/ubuntu` folder
3. Navigate to the extracted directory

### 3.2 Run Training

1. Activate the virtual environment:
   ```bash
   source /fsx/ubuntu/aws_neuron_venv_pytorch/bin/activate
   ```

2. Initialize the setup:
   ```bash
   ./setup.sh
   sbatch submit-openclip.sh
   ```

3. Modify the training script:
   - Open `submit-openclip.sh`
   - Change `srun only_compile_dis.sh` to `srun only_train_dis.sh`

4. Submit the training job:
   ```bash
   sbatch submit-openclip.sh
   ```

## Notes

- This setup uses Neuron SDK version 2.20.1
- For detailed SDK information, refer to the [Neuron SDK 2.20.1 documentation](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/prev/content.html#neuron-2-20-1-10-25-2024)
- We don't recommend using the latest version of Neuron SDK (2.21.X) because we found it raised errors during compilation of CLIP. 
- All training data and models should be stored in the `/fsx/ubuntu` directory