# Deploying EasyEdu as a public website

This document is the short version: how to get from this repository to a link you can
send to someone who has never installed anything.

There are only two things a reviewer needs:

1. a URL that works,
2. a working tutor response.

EasyEdu needs **no environment variables at all** to be useful, because it starts in
**demo mode**: replies are assembled from the bundled reference answers with a
rule-based evaluator, and the full three-agent flow (evaluate → peer follow-up →
tutor feedback) runs exactly as it does with a model attached. The UI labels this
clearly. Connect a model later if you want free-form AI answers (see step 4).

---

## Option A — Render (recommended, free tier available)

Render runs Python web services with HTTPS and a public `*.onrender.com` domain, and
this repo already contains a `render.yaml` blueprint, so there is nothing to configure.

1. Push this repository to GitHub.
2. Create an account at <https://render.com> and connect your GitHub account.
3. In the dashboard: **New +** → **Blueprint**.
4. Select the repository. Render reads `render.yaml`, creates the service and starts
   the first build automatically.
5. Wait for the build (2–4 minutes). The service page shows your URL, e.g.
   `https://easyedu.onrender.com`. Open it — that link is what you share.

**Free-plan behaviour you should know:** the instance sleeps after ~15 minutes with no
visitors. The first visit afterwards takes 30–60 seconds to wake up; subsequent pages
are instant. If that matters for a live review, upgrade the service to the cheapest
paid instance type (it stays awake), or open the URL yourself a minute before the
review so it is already warm.

To keep the app awake for free, point a scheduled request at `https://<your-url>/healthz`
every 10 minutes (any free uptime pinger works).

## Option B — Docker, anywhere (Railway, Fly.io, a VPS, Render Docker)

The `Dockerfile` is production-ready: it installs only the runtime requirements, runs
as a non-root user, reads `$PORT`, has a `HEALTHCHECK` and serves on `0.0.0.0`.

```bash
docker build -t easyedu .
docker run -p 8000:8000 easyedu          # http://127.0.0.1:8000
docker run -p 8080:8080 -e PORT=8080 easyedu
```

On any host that detects a `Dockerfile`, no further configuration is needed.
Start command if you need to enter it manually:

```bash
uvicorn web.main:app --host 0.0.0.0 --port $PORT --workers 1
```

Do **not** increase `--workers` on the free tiers: sessions live in the process
memory of a single worker, so a second worker would not see sessions created by the
first one.

## Option C — Local run (for development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash run_web.sh          # http://127.0.0.1:8000
```

`run_web.sh` honours `$PORT` first, then `$EASYEDU_WEB_PORT`, then defaults to 8000.

---

## 3. Verify a deployment

```bash
curl https://<your-url>/healthz        # {"status":"ok"}
curl https://<your-url>/api/status     # mode, question-bank source and counts
```

`/api/status` is the honest summary of what the running instance is doing:

```json
{"status":"ok","mode":"demo","question_source":"sample",
 "subjects":["ap_physics","ap_statistics","ib_biology","ib_computer_science"],
 "counts":{"chapters":8,"questions":23,"knowledge_points":23}}
```

- `mode: "demo"` → no AI model connected; answers come from the bundled bank.
- `mode: "live"` → a model is connected.
- `question_source: "sample"` → the bundled sample bank in `data/seed_courses/`.
- `question_source: "generated"` → your own bank in `data/courses/`.

## 4. Connecting a real model (optional)

All model traffic goes through the backend; **no API key is ever sent to the
browser**. Set these in the host's environment-variable panel (never in git):

| Variable | Value |
| --- | --- |
| `EASYEDU_LLM_BACKEND` | `deepseek` or `tongyi` |
| `DEEPSEEK_API_KEY` | your key (when using `deepseek`) |
| `TONGYI_API_KEY` | your key (when using `tongyi`) |

Notes:

- The key stays server-side; the frontend only ever talks to `/api/...` on the same origin.
- `EASYEDU_LLM_BACKEND=demo` forces demo mode; leaving it unset makes the app probe
  the configured endpoint once at startup and fall back to demo mode automatically if
  nothing answers, so the site never breaks for a visitor.
- To serve your own fine-tuned model, run it behind an OpenAI-compatible endpoint
  (vLLM) and set `EASYEDU_LLM_BACKEND=local_vllm` plus `EASYEDU_LLM_BASE_URL`.

## 5. Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| First page load takes ~1 minute | Free instance was asleep. Expected; see the note above. |
| Pages load but there are no questions | `data/courses/` and `data/seed_courses/` are both missing or empty. Check `/api/status` → `counts.questions`. |
| `/api/status` shows `mode: live` but answers error | The model endpoint rejected the key (wrong key, no credit, wrong base URL). Set `EASYEDU_LLM_BACKEND=demo` to recover instantly. |
| Build fails installing dependencies | The host is using an old Python. `render.yaml` pins 3.11.9; other hosts need Python 3.10+. |
| Answers reset between requests | Expected: sessions are in-memory and single-worker, and free hosts restart containers. |
