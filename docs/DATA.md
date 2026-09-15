# 数据

讲清楚数据长什么样，以及 AP/IB 的内容该怎么放。

## 数据从哪来

原始教材 PDF 放在 `textbooks/` 下（`AP/`、`IB/`、`reference/`，清单见 `textbooks/README.md`）。这些 PDF 只是原料，应用不会直接读它们——得先经过生成管线，把它们变成结构化的 JSON。

## 格式长这样

每门学科由三类 JSON 组成，可以直接参考能跑的样例 `data/ds_data/`。

章节 `chapters.json`：

```json
{
  "id": "01",
  "title": "章节标题",
  "parent_id": "",
  "order": 1,
  "description": "章节概述...",
  "knowledge_points": ["kc0111", "kc0112"],
  "sub_chapters": []
}
```

题目 `questions/<chapter>.json`（一个数组）：

```json
{
  "id": "q011002",
  "title": "题目短标题",
  "content": "题干，选择题把选项写进来\nA. ...\nB. ...",
  "difficulty": 1,
  "type": "concept",
  "knowledge_points": ["kc0111"],
  "related_questions": [{ "id": "q...", "relation_type": "similar" }],
  "reference_answer": {
    "content": "A",
    "key_points": ["要点1", "要点2"],
    "explanation": "答案解析..."
  },
  "chapter": "01"
}
```

知识点 `knowledgepoints/<chapter>.json`（一个数组）：

```json
{
  "id": "kc0111",
  "title": "知识点名称",
  "chapter_id": "c01",
  "description": "知识点详细说明...",
  "summry": "教师智能体读的就是这个字段"
}
```

两个历史遗留的坑，写数据时注意：教师智能体读的字段名是 `summry`（拼错了，但代码依赖它，懒得动）；旧样例里 `order`/`difficulty` 有时被填成字符串 `"integer"` 占位，真实数据要填数字。

## 怎么生成

`scripts/ingest_textbooks.py` 干的就是这件事：PDF 抽文本 → 切块 → 调我们自己的模型把每块变成「题目+知识点」→ 存成上面的 JSON。

因为第二步要调模型读教材出题，所以**得在模型服务起着的机器上跑**（见 `MODEL_SERVING.md`）。本地 Mac 既没 PDF 库也没模型，跑不了。

```bash
export EASYEDU_LLM_BACKEND=local_vllm
export EASYEDU_LLM_BASE_URL=http://127.0.0.1:8000/v1

# 全量，每本书最多 10 块、每块 3 题
python scripts/ingest_textbooks.py --course all --max-chunks 10 --questions-per-chunk 3

# 只做 AP、多切几块、覆盖重建
python scripts/ingest_textbooks.py --course AP --max-chunks 20 --overwrite
```

跑完会在 `data/courses/<AP|IB>/<subject>/` 下生成那三类文件，外加一个 `manifest.json` 记录每本书出了多少题。还能调 `--max-pages`（读多少页）、`--chunk-chars`（每块多大）、`--skip-front`（跳过前面几页前言）。

## 目录怎么分

按 课程 → 学科 分，每个学科下还是那三件套：

```
data/courses/
├── AP/
│   ├── statistics/
│   ├── physics/
│   └── cs_principles/
└── IB/
    ├── math_aa_hl/
    └── computer_science/
```

ID 建议带上前缀，方便去重和跨学科引用：章节 `ap_stat_c01`、题目 `ap_stat_q0001`、知识点 `ap_stat_kc0001`。

## 索引

应用是通过 `.pkl` 索引读数据的（见 `ARCHITECTURE.md`），所以**改完数据要重建索引**，不然读到的是旧缓存。抽取和建索引的可复用代码在 `data/ds_data/data_processing/`（`pdf_extractor.py`、`index_builder.py`）。

## 双语

教材是英文的，产品要做中英双语。题干和解析建议保留英文原文，需要的话再加中文辅助字段（比如 `content_zh`、`explanation_zh`），前端按用户语言挑着显示。这只是个数据约定，具体还要 ingestion 和前端配合落地。
