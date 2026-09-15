# courses/ — AP/IB 结构化题库（新方向）

应用运行时读取的 **AP/IB 题库目标位置**，当前为空脚手架。
数据格式与组织方式见 [`docs/DATA.md`](../../docs/DATA.md)。

```
courses/
├── AP/   # ap 各学科：每科一个 {chapters.json, questions/, knowledgepoints/}
└── IB/   # ib 各学科：同上
```

由 `scripts/ingest_textbooks.py` 从 `textbooks/` 生成（需模型服务在线，见 `docs/DATA.md` 第 3 节）。
在 AP/IB 数据生成并接入 loader 前，可运行的 demo 仍使用 `data/ds_data/`（旧数据结构数据）。
