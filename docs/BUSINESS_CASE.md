# EasyEdu — 商业思路 / Business case

Product: EasyEdu · Track: IAIO "AI for Business"

## 卖给谁

主要是做 IB/AP 的培训机构、国际学校，还有那些帮学生备考的留学辅导机构。再往外一点，是想做 AI 辅导但不想从零搭的 edtech 平台——我们可以给他们一套能贴牌的方案。

这些机构有个共同点：学生多、老师贵、而且很在意自己的教学数据和题库。

## 痛点

通用聊天机器人能答题，但学生“看懂了答案”不等于“真的学会了”。机构真正缺的是能规模化的“讲题式”练习——以前这只能靠老师一对一盯着。

如果直接接商业大模型 API，又有三个绕不开的问题：按 token 付费，用得越多越贵；学生数据要发到第三方云上；几乎没法按自己的课程深度定制。

## 我们的做法

EasyEdu 把费曼学习法做成了一个闭环：学生讲题 → Router 判断讲得怎么样 → 要么 Student 追问、要么 Teacher 纠错或总结。

关键是模型是我们自己的。在一张 4090 上用 QLoRA 微调，再用 vLLM 自己部署（见 [`MODEL_SERVING.md`](MODEL_SERVING.md)、[`TRAINING.md`](TRAINING.md)）。题库也是自己的——把机构买了版权的 IB/AP 教材喂给 [`ingest_textbooks.py`](../scripts/ingest_textbooks.py)，自动生成结构化题库。反馈是中英双语的，照顾国际课程里中英混合的课堂。

## 为什么这套对机构更划算

| | 接商业 API 的辅导 | EasyEdu |
|---|---|---|
| 成本 | 按 token，随人数涨 | 固定一张卡，API 只做兜底 |
| 数据 | 在第三方云 | 留在机构自己手里 |
| 教学方式 | 一问一答 | 讲题式 + 多智能体 |
| 课程内容 | 通用 | 用机构自己的 AP/IB 教材定制 |

## 比赛 demo 怎么演

选课程和题目 → 学生在对话框里讲解 → （可选）把 Router 判断的 JSON 亮出来给评委看决策过程 → Student/Teacher 用中英双语回应。最后强调一句：这整套跑在我们自己的模型端点上（`EASYEDU_LLM_BACKEND=local_vllm`），不依赖任何外部 API。

## 落地节奏

先拿一门 AP（比如 Statistics）加一门 IB（Math AA HL）做试点。卖给机构的是一个打包：软件 + 模型权重 + 针对他们自己教材的题库生成。效果就看几个数：学生有没有把一次讲解走完、讲解的深度（Router 的 `is_complete`）、以及帮老师省了多少时间。
