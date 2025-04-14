#!/bin/bash

rm -r ./compiler_cache

export PATH=/opt/aws/neuron/bin:\$PATH
export PATH=/home/ubuntu/.local/bin:\$PATH
export NCCL_DEBUG=INFO
export FI_EFA_USE_DEVICE_RDMA=1
export FI_PROVIDER=efa
export FI_EFA_FORK_SAFE=1

#rm -r ./compiler_cache

MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -n 1)
MASTER_PORT=$(expr 10000 + $(echo -n $SLURM_JOBID | tail -c 4))

DISTRIBUTED_ARGS="--master_addr \$MASTER_ADDR --master_port \$MASTER_PORT --nproc_per_node 32 --nnodes 2 --node_rank \$SLURM_NODEID"
#DISTRIBUTED_ARGS="--nproc_per_node 32 --nnodes 1 --node_rank 0"
echo $DISTRIBUTED_ARGS
rm -r ./logs/

# Compile process.
MALLOC_ARENA_MAX=64 NEURON_NUM_RECENT_MODELS_TO_KEEP=4 NEURON_RT_ASYNC_EXEC_MAX_INFLIGHT_REQUESTS=3 XLA_USE_BF16=1 NEURON_CC_FLAGS="--model-type=transformer --cache_dir=./compiler_cache --enable-saturate-infinity" neuron_parallel_compile torchrun $DISTRIBUTED_ARGS weighted_training/main.py \
    --train-data Marqo/marqo-ge-sample \
    --warmup 10000 \
    --epochs 200 \
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
    --steps-this-run 10 \
    --logit-scale 100

# Train CLIP using a cached compiled model graph.
MALLOC_ARENA_MAX=64 NEURON_NUM_RECENT_MODELS_TO_KEEP=4 NEURON_RT_ASYNC_EXEC_MAX_INFLIGHT_REQUESTS=3 XLA_USE_BF16=1 NEURON_CC_FLAGS="--model-type=transformer --cache_dir=./compiler_cache --enable-saturate-infinity" torchrun $DISTRIBUTED_ARGS weighted_training/main.py \
    --train-data Marqo/marqo-ge-sample \
    --warmup 10000 \
    --epochs 200 \
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
