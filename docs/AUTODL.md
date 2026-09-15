# 在 AutoDL 上跑起来

从连上 4090 到把模型、网页、训练都跑通的完整流程。

## 1. 进到 4090 的终端

实例得先是「运行中」。进终端有两个办法：

- **JupyterLab（最省事）**：控制台 → 容器实例 → 你那台的「快捷工具」列点 JupyterLab，新标签页里 File → New → Terminal，就是 4090 上的终端。
- **SSH**：控制台「SSH登录」里复制那条 `ssh -p 端口 root@...`，在自己电脑的终端里跑，提示输密码时把控制台的密码粘进去（输密码时不显示，正常）。

代码和模型都放数据盘，关机不丢：

```bash
cd /root/autodl-tmp
```

## 2. 装环境

```bash
source /etc/network_turbo
git clone https://github.com/gordonli0316-afk/EasyEdu.git
cd EasyEdu
bash scripts/setup_autodl.sh
```

脚本分四步：装网页和智能体依赖 → 装 vLLM（会顺带把 torch 升级到新版，正常）→ 装训练依赖 → 用 ModelScope 把 Qwen2.5-7B 下到 `/root/autodl-tmp/models/`。整个十几二十分钟，看到最后打印 `Done` 就成了。

> 踩过的坑：`network_turbo` 那个代理是给 github/HF 用的，pip 走国内镜像时反而会被它挡住（报 `No matching distribution`）。脚本里已经在装包前把代理关掉了，不用管。

## 3. 一张卡，分时用

24GB 显存装不下「一边服务一边训练」。所以是：要么在跑模型服务，要么在训练，二选一。

跑模型（占住这个终端，监听 8000）：

```bash
export EASYEDU_MODEL_PATH=/root/autodl-tmp/models/Qwen2.5-7B-Instruct
./scripts/serve_model_vllm.sh
```

再开一个终端跑网页：

```bash
cd /root/autodl-tmp/EasyEdu
export EASYEDU_LLM_BACKEND=local_vllm
export EASYEDU_LLM_BASE_URL=http://127.0.0.1:8000/v1
export EASYEDU_WEB_PORT=6006
bash run_web.sh
```

## 4. 在浏览器打开网页

两种方式：

- AutoDL 控制台开「自定义服务」，它固定映射 6006 端口，会给你一个公网地址（所以网页一定要跑在 6006）。
- 或者从自己电脑做端口转发：`ssh -p 端口 -L 6006:127.0.0.1:6006 root@...`，然后本地浏览器开 `http://127.0.0.1:6006`。

## 5. 生成 AP/IB 题库（模型在线时）

教材 PDF 太大没进 git，得先自己传到 `textbooks/AP`、`textbooks/IB`（AutoDL 文件上传或 scp 都行），然后：

```bash
export EASYEDU_LLM_BACKEND=local_vllm
export EASYEDU_LLM_BASE_URL=http://127.0.0.1:8000/v1
python scripts/ingest_textbooks.py --course all --max-chunks 10
```

## 6. 训练自己的模型

训练前先 `Ctrl+C` 把 vLLM 停了，把显存让出来：

```bash
python scripts/build_sft_data.py
bash src/models/rlhf/sft/train.sh
# 结果在 output/easyedu_feynman-<时间戳>/
```

3 轮、几千条样本，4090 上大概 1.5~3 小时。想先快速验证就把轮数改成 1。

## 7. 换上训练好的模型

```bash
export EASYEDU_MODEL_PATH=/root/autodl-tmp/EasyEdu/output/easyedu_feynman-XXXX
export EASYEDU_LLM_MODEL=EasyEdu-7B-Feynman
./scripts/serve_model_vllm.sh
```

## 卡住了看这里

- vLLM 装不上、CUDA 对不上：确认镜像是 PyTorch 2.x + CUDA 12.x，不行就在控制台换镜像。
- 下模型慢：用的是 ModelScope，已经是国内最快的了，15GB 耐心等。
- 网页打不开：自定义服务只认 6006，确认 `EASYEDU_WEB_PORT=6006`。
- 长任务怕断连：用 `screen` 或 `tmux` 开后台，SSH 断了也不影响。
