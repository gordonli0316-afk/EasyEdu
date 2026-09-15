#!/usr/bin/env bash
# EasyEdu QLoRA SFT — single RTX 4090 (relative paths, Qwen2.5-7B)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../../" && pwd)"
cd "$ROOT"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-max_split_size_mb:512}"

LR="${EASYEDU_SFT_LR:-2e-4}"
DATESTR="$(date +%Y%m%d-%H%M%S)"
RUN_NAME="${EASYEDU_SFT_RUN_NAME:-easyedu_feynman}"
OUTPUT_DIR="${EASYEDU_SFT_OUTPUT:-output/${RUN_NAME}-${DATESTR}}"
MODEL_PATH="${EASYEDU_MODEL_PATH:-/root/autodl-tmp/models/Qwen2.5-7B-Instruct}"
TRAIN_FILE="${EASYEDU_SFT_TRAIN:-data/rlhf_data/sft/train.jsonl}"
VAL_FILE="${EASYEDU_SFT_VAL:-data/rlhf_data/sft/val.jsonl}"

mkdir -p "$OUTPUT_DIR"

python -m src.models.rlhf.sft.train \
  --do_train \
  --do_eval \
  --bf16 \
  --train_file "$TRAIN_FILE" \
  --validation_file "$VAL_FILE" \
  --prompt_column input \
  --response_column output \
  --max_source_length 1536 \
  --max_target_length 512 \
  --model_name_or_path "$MODEL_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --per_device_train_batch_size 1 \
  --per_device_eval_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --gradient_checkpointing \
  --learning_rate "$LR" \
  --num_train_epochs 3 \
  --weight_decay 0.01 \
  --warmup_ratio 0.05 \
  --lr_scheduler_type cosine \
  --logging_steps 10 \
  --save_steps 200 \
  --save_total_limit 3 \
  --eval_strategy steps \
  --eval_steps 100 \
  --lora_rank 16 \
  --lora_alpha 32 \
  --lora_dropout 0.05 \
  --target_modules "q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj" \
  2>&1 | tee "${OUTPUT_DIR}/train.log"
