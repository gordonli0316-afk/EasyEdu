"""EasyEdu web application entry point.

Run locally:      bash run_web.sh
Run in production: uvicorn web.main:app --host 0.0.0.0 --port $PORT
"""
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.api.endpoints import (
    chapters, questions, sessions, knowledge, upload,
    tags, videos, flashcards, questions_extended
)
from src.agents.llm.config import get_llm_config
from web.services.qa_service import get_qa_service

# 用绝对路径，这样从任何工作目录启动都能找到静态文件和模板
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

app = FastAPI(
    title="EasyEdu API",
    description="IB/AP Feynman tutoring API — interactive explain-back learning platform",
    version="3.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 同源部署不需要 CORS；只有在用 EASYEDU_CORS_ORIGINS 明确列出前端域名时才开启。
_cors_origins = [o.strip() for o in os.getenv("EASYEDU_CORS_ORIGINS", "").split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

# 注册路由
app.include_router(chapters.router, prefix="/api", tags=["chapters"])
app.include_router(questions.router, prefix="/api", tags=["questions"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(knowledge.router, prefix="/api", tags=["knowledge"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(tags.router, prefix="/api", tags=["tags"])
app.include_router(videos.router, prefix="/api", tags=["videos"])
app.include_router(flashcards.router, prefix="/api", tags=["flashcards"])
app.include_router(questions_extended.router, prefix="/api", tags=["questions_extended"])


def _public_backend() -> str:
    """Backend name only — never a key, URL credential or model secret."""
    try:
        return get_llm_config().backend
    except Exception:
        return "unknown"


@app.get("/healthz", include_in_schema=False)
async def healthz():
    """Liveness probe for the hosting platform (must stay cheap)."""
    return JSONResponse({"status": "ok"})


@app.get("/api/status", tags=["meta"])
async def api_status():
    """What the running instance is actually serving.

    The frontend uses this to tell the visitor whether responses come from a real
    model or from the bundled offline demo, and which question bank is loaded.
    """
    service = get_qa_service()
    qa_system = service.get_qa_system()
    loader = qa_system.index_system
    return {
        "status": "ok",
        "mode": service.mode,
        # Non-technical and secret-free: lets an operator confirm from outside which
        # provider is in use and why the app is (or is not) in demo mode.
        "mode_reason": service.mode_reason,
        "model_backend": _public_backend(),
        "question_source": service.source,
        "subjects": loader.subjects,
        "counts": {
            "chapters": len(loader.chapter_index),
            "questions": len(loader.question_index),
            "knowledge_points": len(loader.knowledge_index),
        },
    }


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/problems", include_in_schema=False)
async def problems_page(request: Request):
    return templates.TemplateResponse(request, "problems.html")


@app.get("/knowledge", include_in_schema=False)
async def knowledge_page(request: Request):
    return templates.TemplateResponse(request, "knowledge.html")


@app.get("/chat/{question_id}", include_in_schema=False)
async def chat_view(request: Request, question_id: str):
    # 未知题目不要渲染一个空壳页面，直接把访客送回题目列表
    if get_qa_service().get_question_detail(question_id) is None:
        return RedirectResponse("/problems", status_code=302)
    return templates.TemplateResponse(request, "chat.html", {"question_id": question_id})


@app.get("/flashcards", include_in_schema=False)
async def flashcards_page(request: Request):
    return templates.TemplateResponse(request, "flashcards.html")


@app.get("/demo", include_in_schema=False)
async def demo_question():
    """One-click entry point for a first-time visitor: open a real question."""
    loader = get_qa_service().get_qa_system().index_system
    for chapter in loader.get_all_chapters():
        questions = loader.get_questions_by_chapter(chapter["id"])
        if questions:
            return RedirectResponse(f"/chat/{questions[0]['id']}", status_code=307)
    return RedirectResponse("/problems", status_code=307)
