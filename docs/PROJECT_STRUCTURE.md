# 项目结构

每个目录/文件是干嘛的、动它会不会影响运行，方便快速定位。

## 顶层

| 路径 | 说明 |
|------|------|
| `src/` | 核心代码：智能体、自有模型层、QA 系统、服务、训练 |
| `web/` | FastAPI 网页应用（API、模板、静态资源） |
| `scripts/` | 部署/数据/训练脚本（serve、ingest、build_sft、setup_autodl） |
| `data/` | 运行时数据和产物 |
| `textbooks/` | AP/IB 教材 PDF（数据来源，太大没进 git） |
| `config/` | 路径常量和配置 |
| `docs/` | 文档 |
| `requirements.txt` / `run_web.sh` | 依赖 / 启动脚本 |

## `src/`

| 路径 | 说明 |
|------|------|
| `knowledge_qa_system.py` | 主类 `KnowledgeQASystem`：加载索引 + 建工作流 + 管会话，Web 层都从这里访问 |
| `agents/workflow.py` | LangGraph 工作流（router → student/teacher） |
| `agents/agents/{router,student,teacher}.py` | 三个智能体节点 |
| `agents/llm/` | **自有模型调用层**：`client.py`（httpx 直连 OpenAI 兼容端点）、`config.py`（env 配置）、`json_utils.py`（结构化输出解析）、`env.py` |
| `agents/models.py` | 模型工厂，默认返回连本地 vLLM 的客户端 |
| `agents/base.py` / `session_manager.py` | 状态定义 / 会话管理 |
| `agents/prompts/*.txt` | 三个智能体的系统提示词，已是 AP/IB 双语版 |
| `services/` | 上传OCR、出题、导出、抽认卡、视频推荐（OCR/导出依赖是可选的，没装会优雅降级） |
| `database/schema.py` | 数据模型定义 |
| `models/rlhf/sft/` | QLoRA 训练代码（见 `docs/TRAINING.md`） |
| `.env` | 密钥，已 gitignore，别提交 |

训练目录 `models/rlhf/sft/`：`train.py` 是单卡 QLoRA 主流程（HF Trainer + 4-bit + LoRA，没有 DeepSpeed），`train.sh` 是启动脚本（相对路径、默认 Qwen2.5-7B），`data_preprocess.py` 处理对话模板，`arguments.py` 是参数定义。

## `web/`

| 路径 | 说明 |
|------|------|
| `main.py` | FastAPI 入口，注册路由和页面 |
| `core/config.py` | Web 层配置（数据目录当前指向 `data/ds_data`） |
| `services/qa_service.py` | 封装 `KnowledgeQASystem`，给各 API 调用 |
| `api/endpoints/*.py` | REST 接口：chapters / questions / sessions / knowledge / upload / tags / videos / flashcards |
| `templates/*.html` `static/` | 页面和前端资源 |

## `data/`

| 路径 | 说明 |
|------|------|
| `courses/AP`, `courses/IB` | AP/IB 题库的目标位置，由 `ingest_textbooks.py` 生成 |
| `ds_data/` | 旧的数据结构题库，但**目前唯一能跑的 demo 数据**。含真实题目 + `ds_indices.pkl` + `data_processing/`（抽取、建索引的可复用代码，`knowledge_qa_system` 会 import 它的 `index_builder`） |
| `hs_indices.pkl` | 索引缓存，启动时加载 |
| `high_school_data/` | 旧的高中方向，题目全空，只占位 |
| `high_school_data_loader.py` | 高中数据加载器，被主类 import，暂时删不得 |
| `rlhf_data/sft/` | 训练集（`build_sft_data.py` 生成） |
| `samples/` `uploads/` `exports/` | 测试样图 / 上传落地 / 导出产物 |

## `config/`

`paths.py` 是全局路径常量（默认还指向 `ds_data`），`db_config.yaml` 是数据库配置，`model_config.yaml` 是模型服务的默认值。

## `docs/`

`AUTODL.md`（怎么在 AutoDL 跑）、`MODEL_SERVING.md`（部署）、`TRAINING.md`（训练）、`DATA.md`（数据）、`ARCHITECTURE.md`（架构）、`BUSINESS_CASE.md`（商业）、本文件。推理服务脚本在 `scripts/serve_model_vllm.sh`。
