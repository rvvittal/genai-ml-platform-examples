#!/bin/bash

DISTRIBUTED_ARGS="--nproc_per_node 32 --nnodes 1 --node_rank 0"
echo $DISTRIBUTED_ARGS
rm -r ./logs/

# Train CLIP using a cached compiled model graph.
MALLOC_ARENA_MAX=64 NEURON_NUM_RECENT_MODELS_TO_KEEP=4 NEURON_RT_ASYNC_EXEC_MAX_INFLIGHT_REQUESTS=3 XLA_USE_BF16=1 NEURON_CC_FLAGS="--model-type=transformer --cache_dir=./compiler_cache --enable-saturate-infinity" torchrun $DISTRIBUTED_ARGS weighted_training/main.py \
    --train-data Marqo/marqo-ge-sample \
    --warmup 10000 \
    --epochs 100 \
    --lr 1e-5 \
    --precision fp32 \
    --workers 0 \
    --model ViT-B-16 \
    --pretrained laion2b_s34b_b88k \
    --batch-size 64 \
    --wd 0.001 \
    --name "VITB16" \
    --dataset-type hf \
    --hf-split-key google_shopping \
    --hf-img-key image \
    --hf-caption-key title \
    --save-frequency 1 \
    --save-most-recent \
    --log-every-n-steps 10 \
    --grad-checkpointing --local-loss --gather-with-grad \
    --logit-scale 100
