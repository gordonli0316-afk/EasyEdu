# EasyEdu

一个让学生"给 AI 讲题"的辅导系统，主要面向 IB / AP 国际课程。

大部分 AI 辅导都是学生提问、AI 给答案。EasyEdu 反过来：你来讲，AI 当那个不停追问的老师。能把一道题讲明白，才算是真的学会了——这也是费曼学习法的出发点。

## 它是怎么工作的

学生讲完一道题，后面有三个智能体接力，根据这次讲解的情况决定下一步：

- **Router** 先判断：讲得对不对，透不透。
- 讲对了但还停在表面，就交给 **Student**——一个爱追问的"同学"，继续问"那为什么"。
- 讲错了，或者已经讲完整了，交给 **Teacher** 来纠错或者收尾总结。

工作流用 LangGraph 编排。模型这一层是自己写的调用客户端（`src/agents/llm/`），默认连本地用 vLLM 部署的模型，也可以切到商业 API 兜底。把模型放在自己手里，主要是为了成本可控、数据不外流，以及能照着具体课程去调。

题库不是手写的，是把教材 PDF 喂给 `scripts/ingest_textbooks.py` 自动生成的——抽文本、切块、让模型产出结构化的题目和知识点。

## 跑起来（AutoDL 4090）

```bash
cd /root/autodl-tmp
source /etc/network_turbo
git clone https://github.com/gordonli0316-afk/EasyEdu.git
cd EasyEdu
bash scripts/setup_autodl.sh        # 装依赖 + 下 Qwen2.5-7B
```

开两个终端，一个跑模型，一个跑网页：

```bash
# 终端 A：起模型
export EASYEDU_MODEL_PATH=/root/autodl-tmp/models/Qwen2.5-7B-Instruct
./scripts/serve_model_vllm.sh

# 终端 B：起网页
export EASYEDU_LLM_BACKEND=local_vllm
export EASYEDU_LLM_BASE_URL=http://127.0.0.1:8000/v1
export EASYEDU_WEB_PORT=6006
bash run_web.sh
```

网页跑在 6006 端口，配合 AutoDL 的「自定义服务」就能在浏览器里打开，具体见 [`docs/AUTODL.md`](docs/AUTODL.md)。

生成题库、做训练（单卡显存吃紧，训练前记得先把 vLLM 停掉）：

```bash
python scripts/ingest_textbooks.py --course all --max-chunks 10   # 需要模型在线
python scripts/build_sft_data.py
bash src/models/rlhf/sft/train.sh
```

## 目录

```
src/         智能体、模型调用层(agents/llm)、QA 系统、训练代码
web/         FastAPI 网页应用
scripts/     部署 / 数据 / 训练脚本
data/        运行时数据（courses=AP/IB 题库，rlhf_data=训练集）
textbooks/   AP/IB 教材 PDF（题库来源，文件太大没进 git）
config/      路径和模型配置
docs/        文档
```

更细的目录说明在 [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md)。

## 文档

- [`docs/AUTODL.md`](docs/AUTODL.md) — 在 AutoDL 上把它跑起来
- [`docs/MODEL_SERVING.md`](docs/MODEL_SERVING.md) — vLLM 部署
- [`docs/TRAINING.md`](docs/TRAINING.md) — 4090 上的 QLoRA 训练
- [`docs/DATA.md`](docs/DATA.md) — 数据格式和生成管线
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 架构和数据流

## 技术栈

FastAPI、LangGraph、自己写的 LLM 客户端（httpx + OpenAI 兼容协议）、vLLM、QLoRA（PEFT + bitsandbytes）、pdfplumber / PyMuPDF，前端是原生 HTML/CSS/JS。

## 作者

作者：[gordonli0316-afk](https://github.com/gordonli0316-afk)。内容基础全部由本人完成，后续老师帮忙微调并给出建议。

## 开源许可证

项目代码采用 [MIT License](LICENSE) 开源。第三方依赖、模型权重和教材等资源遵循各自的许可条款。
