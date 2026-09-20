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

**Fastest path — one click:**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/gordonli0316-afk/EasyEdu)

Sign in to Render (GitHub login), confirm the blueprint, press **Apply**, and wait for the
build. Render reads `render.yaml` for the runtime, build command, start command, health
check path and environment variables — there are no settings to enter.

**Or from the dashboard:**

1. Create an account at <https://render.com> and connect your GitHub account.
2. **New +** → **Blueprint**.
3. Select `gordonli0316-afk/EasyEdu`. Render reads `render.yaml`, creates the service and
   starts the first build automatically.
4. Wait for the build (2–4 minutes). The service page shows your URL, e.g.
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
browser**. DeepSeek support is already built in — you only need to supply the key.

**On Render:** the blueprint declares the variable, so you just fill in the value.

1. Open your service → **Environment** (Render also prompts for it during Blueprint
   creation if you leave it blank there).
2. Find **`DEEPSEEK_API_KEY`** — already declared by `render.yaml` with `sync: false`,
   so its value is never read from or written to this repository.
3. Paste your key → **Save Changes**. Render redeploys automatically.

That is the only step. `EASYEDU_LLM_BACKEND` does **not** need to be set: EasyEdu
resolves the backend from the environment (see the table below).

| Variable | Value | Required |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | your DeepSeek key | yes, for live answers |
| `DEEPSEEK_MODEL` | defaults to `deepseek-chat` | no |
| `EASYEDU_LLM_BACKEND` | override; normally leave unset | no |
| `TONGYI_API_KEY` | only if you prefer Tongyi/DashScope | no |

Resolution order when `EASYEDU_LLM_BACKEND` is unset:

1. `deepseek` if `DEEPSEEK_API_KEY` is set
2. `tongyi` if `TONGYI_API_KEY` is set
3. `local_vllm` otherwise

Notes:

- The key stays server-side; the frontend only ever talks to `/api/...` on the same origin.
- EasyEdu probes the chosen endpoint once. If it is unreachable, rejects the key, has no
  balance, rate-limits us, or errors mid-request, EasyEdu **automatically** answers from
  its bundled reference material instead. A visitor never sees a provider error, and a
  fallback reply says plainly that it did not come from the model.
- After a runtime failure the process stays in demo mode so the next visitor is not made
  to wait on a provider that is already known to be failing.
- `GET /api/status` reports `mode`, a non-technical `mode_reason`, and `model_backend`,
  so you can confirm from outside which engine is serving.
- To serve your own fine-tuned model, run it behind an OpenAI-compatible endpoint
  (vLLM) and set `EASYEDU_LLM_BACKEND=local_vllm` plus `EASYEDU_LLM_BASE_URL`.

## 5. Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| First page load takes ~1 minute | Free instance was asleep. Expected; see the note above. |
| Pages load but there are no questions | `data/courses/` and `data/seed_courses/` are both missing or empty. Check `/api/status` → `counts.questions`. |
| Answers look like reference explanations, not model prose | Check `/api/status` → `mode` and `mode_reason`. The site is in demo mode because the model is unreachable or the key was rejected; fix the key in the host's environment panel. The site stays fully usable either way. |
| Build fails installing dependencies | The host is using an old Python. `render.yaml` pins 3.11.9; other hosts need Python 3.10+. |
| Answers reset between requests | Expected: sessions are in-memory and single-worker, and free hosts restart containers. |
