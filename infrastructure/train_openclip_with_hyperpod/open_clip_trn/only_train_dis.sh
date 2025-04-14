#!/bin/bash
CACHE_DIR=/home/ubuntu/compiler_cache


export LD_LIBRARY_PATH=/opt/amazon/efa/lib:/opt/amazon/openmpi/lib:$LD_LIBRARY_PATH

export FI_EFA_USE_DEVICE_RDMA=1 # use for p4de
export FI_PROVIDER=efa
export NCCL_PROTO=simple
export NCCL_ALGO=Tree
export FI_EFA_FORK_SAFE=1
export FI_LOG_LEVEL=1
export RDMAV_FORK_SAFE=1
export FI_EFA_ENABLE_SHM_TRANSFER=1
export NCCL_DEBUG=INFO


rm -r ./logs/

NODEID=$SLURM_NODEID
NTASKS=$SLURM_NTASKS
MASTER_ADDR=(`scontrol show hostnames \$SLURM_JOB_NODELIST | head -n 1`)
MASTER_PORT=$(expr 10000 + $(echo -n $SLURM_JOBID | tail -c 4))

export PROCESSES_PER_NODE=32

export DISTRIBUTED_ARGS="--nproc_per_node $PROCESSES_PER_NODE \
                         --nnodes $NTASKS \
                         --node_rank $NODEID \
                         --master_addr $MASTER_ADDR \
                         --master_port $MASTER_PORT \
                         "
echo $DISTRIBUTED_ARGS

MALLOC_ARENA_MAX=64 NEURON_NUM_RECENT_MODELS_TO_KEEP=4 \
NEURON_RT_ASYNC_EXEC_MAX_INFLIGHT_REQUESTS=3 \
XLA_USE_BF16=1 \
NEURON_CC_FLAGS="--model-type=transformer --cache_dir=$CACHE_DIR --enable-saturate-infinity" \
 torchrun $DISTRIBUTED_ARGS weighted_training/main.py \
--train-data Marqo/marqo-ge-sample \
--warmup 10000 \
--epochs 100 \
--lr 1e-5 \
--precision fp32 \
--workers 0 \
--model ViT-B-16 \
--pretrained laion2b_s34b_b88k \
--batch-size 32 \
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
