FROM python:3.8-slim-buster

# Update the package list and install basic dependencies
RUN apt-get update && apt-get install -y \
    make \
    awscli \
    git \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app/ml/code

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY requirements-training.txt .

RUN pip install -r requirements-training.txt

COPY README.md .
COPY MANIFEST.in .
COPY setup.sh .
COPY setup_mfsq.py .
COPY setup_openclip.py .
COPY src src

RUN chmod +x setup.sh
RUN ./setup.sh

COPY weighted_training weighted_training

# Set the final working directory to where the main script is located
WORKDIR /app/ml/code/weighted_training

ENV PYTHONPATH "/app/ml/code"

# Set the entrypoint to the main training script
ENTRYPOINT ["python", "docker_main.py"]
