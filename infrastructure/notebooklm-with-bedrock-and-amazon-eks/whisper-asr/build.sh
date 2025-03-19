#!/bin/bash

# Build Image
echo "Building whisper ASR image.."
docker build -t ray-whisper:latest .
