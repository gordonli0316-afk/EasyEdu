# 架构

## 分层

```
┌───────────────────────────────────────────────┐
│  前端 (web/templates + web/static)             │  浏览题目 / 对话 / 抽认卡
├───────────────────────────────────────────────┤
│  FastAPI 后端 (web/main.py + web/api)          │  REST API / 会话 / 上传
├───────────────────────────────────────────────┤
│  核心 (src/)                                    │
│   ├─ KnowledgeQASystem   数据索引 + 题目查询    │
│   ├─ 多智能体 (LangGraph) router/student/teacher│
│   └─ 服务层  上传OCR / 出题 / 导出 / 抽认卡      │
├───────────────────────────────────────────────┤
│  数据层   JSON 题库/知识点 + Pickle 索引         │
└───────────────────────────────────────────────┘
```

## 智能体怎么流转

```
学生回答 ──▶ Router 评估
                ├─ 对但不够深 ──▶ Student 追问 ──┐
                ├─ 错         ──▶ Teacher 纠错 ──┤──▶ 继续 / 换题
                └─ 对且完整   ──▶ Teacher 总结 ──┘
```

图的定义在 `src/agents/workflow.py`，每个节点在 `src/agents/agents/*.py`，提示词在 `src/agents/prompts/*.txt`（已经是 AP/IB 双语版）。模型调用统一走 `src/agents/llm/`，默认连自部署的 vLLM。

一个值得说的设计：Router 的判断没有依赖模型的 function calling，而是让它直接吐 JSON，我们自己解析+校验，解析失败就重试一次。Teacher 也不靠模型自己发起工具调用——相关知识点是 Python 先查好、直接塞进提示词的。这样换成自部署的小模型也稳。

## 索引

题库是一堆 JSON，每次遍历太慢，所以第一次启动时建一个内存索引落盘成 `.pkl`，之后直接加载，秒级启动。

```
第一次：读 JSON → 建索引 → 存 .pkl
之后：  直接 load .pkl
```

索引结构见 `data/ds_data/data_processing/index_builder.py`：`chapter_index` / `question_index` / `knowledge_index` / `knowledge_question_index`。改了数据记得重建，不然读到旧的。

## 从教材到题库

```
textbooks/*.pdf
   │  pdfplumber / PyMuPDF 抽文本
   ▼
切块 ──▶ 调自有模型生成 题目+知识点(JSON) ──▶ data/courses/{AP,IB}/...
                                                  │
                                                  ▼  建索引(.pkl) ──▶ 上线
```

这条管线已经实现，就是 `scripts/ingest_textbooks.py`，细节在 `DATA.md`。
