from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from web.api.endpoints import (
    chapters, questions, sessions, knowledge, upload,
    tags, videos, flashcards, questions_extended
)

app = FastAPI(
    title="EasyEdu API",
    description="IB/AP Feynman tutoring API — interactive explain-back learning platform",
    version="3.0.0",
)

# 配置静态文件
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="web/templates")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/problems")
async def problems_page(request: Request):
    return templates.TemplateResponse(request, "problems.html")

@app.get("/knowledge")
async def knowledge_page(request: Request):
    return templates.TemplateResponse(request, "knowledge.html")

@app.get("/chat/{question_id}")
async def chat_view(request: Request, question_id: str):
    return templates.TemplateResponse(request, "chat.html", {"question_id": question_id})

@app.get("/upload")
async def upload_page(request: Request):
    """文件上传页面"""
    return templates.TemplateResponse(request, "upload.html")

@app.get("/flashcards")
async def flashcards_page(request: Request):
    """抽认卡学习页面"""
    return templates.TemplateResponse(request, "flashcards.html")