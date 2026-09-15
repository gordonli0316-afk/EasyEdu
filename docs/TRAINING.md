# 训练（4090 QLoRA）

在一张 RTX 4090 上用 4-bit QLoRA 微调，不需要 DeepSpeed 那一套。

## 第一步：造训练数据

```bash
python scripts/build_sft_data.py
# 生成 data/rlhf_data/sft/train.jsonl 和 val.jsonl
```

数据格式是 `input`（一串对话消息）配 `output`（assistant 的回复），细节在 `src/models/rlhf/sft/data_preprocess.py`。

脚本会优先读 `data/courses` 里真实的 AP/IB 题库（`ingest_textbooks.py` 生成的），没有就回退到 `data/ds_data`。用的是混合策略：既让模型学三个智能体的教学行为，也顺带吸收学科内容（带解析的接地数据），这样准确率更稳。

## 第二步：训练

```bash
export EASYEDU_MODEL_PATH=/root/autodl-tmp/models/Qwen2.5-7B-Instruct
bash src/models/rlhf/sft/train.sh
```

想看所有参数就 `python -m src.models.rlhf.sft.train --help`。常用的几个环境变量：`EASYEDU_MODEL_PATH`（基座）、`EASYEDU_SFT_TRAIN`/`EASYEDU_SFT_VAL`（数据路径）、`EASYEDU_SFT_OUTPUT`（输出目录）。默认 LoRA r=16、梯度累积 16、max_source 1536，target modules 按 Qwen 配好了。

**大概要多久**：3 轮、几千条样本，4090 上 1.5~3 小时。第一次想快点验证流程，把 `--num_train_epochs` 改成 1，半小时到一小时就能跑完。

## 第三步：把训练好的权重用起来

合并 LoRA 或直接指向输出目录，然后起服务：

```bash
export EASYEDU_MODEL_PATH=/path/to/output/checkpoint
export EASYEDU_LLM_MODEL=EasyEdu-7B-Feynman
./scripts/serve_model_vllm.sh
```

具体见 [`MODEL_SERVING.md`](MODEL_SERVING.md)。

## 依赖（GPU 机器上）

```bash
pip install torch transformers peft bitsandbytes accelerate
# 要起推理服务再加 vllm
```

## 为什么要自己训

微调出来的模型能替掉按量付费的 API，边际成本压下来，同时也是一份能跟机构谈合作的、属于自己的资产。
