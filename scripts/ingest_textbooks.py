#!/usr/bin/env python3
"""
把 AP/IB 教材变成题库。

流程：从 textbooks/<AP|IB>/ 的每个 PDF 抽文本（优先 PyMuPDF，退而求其次
pdfplumber）→ 按字数切块 → 每块调我们自己部署的模型，生成一个知识点和几道
中英双语题目（结构化 JSON）→ 写成标准格式存到 data/courses/<课程>/<学科>/ 下
（chapters.json、questions/、knowledgepoints/）。

要在模型服务起着的机器上跑（见 docs/MODEL_SERVING.md），因为出题这步要调模型：
    export EASYEDU_LLM_BACKEND=local_vllm
    export EASYEDU_LLM_BASE_URL=http://127.0.0.1:8000/v1
    python scripts/ingest_textbooks.py --course all --max-chunks 10

依赖 pdfplumber 或 PyMuPDF，外加一个在线的模型端点。
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEXTBOOKS = ROOT / "textbooks"
COURSES = ROOT / "data" / "courses"


# --------------------------------------------------------------------------- #
# LLM output schema
# --------------------------------------------------------------------------- #
class GenKnowledgePoint(BaseModel):
    title: str
    description: str = Field(..., description="Detailed explanation of the concept")
    summary: str = Field(..., description="Concise summary used by the teacher agent")


class GenQuestion(BaseModel):
    title: str
    content: str = Field(..., description="Question stem; include A/B/C/D options for MCQ")
    type: str = "concept"
    difficulty: int = 3
    answer: str
    key_points: List[str] = Field(default_factory=list)
    explanation: str


class GenSection(BaseModel):
    chapter_title: str
    knowledge_point: GenKnowledgePoint
    questions: List[GenQuestion]


GEN_SYSTEM = (
    "You are a curriculum author for an IB/AP tutoring product. "
    "From a textbook excerpt you create high-quality study material. "
    "Lead with clear English (use correct IB/AP terminology); add a short Chinese "
    "gloss in parentheses where it helps comprehension. "
    "Output ONLY a single JSON object matching the requested schema — no markdown, no commentary."
)

GEN_USER_TEMPLATE = """Course: {course}
Subject: {subject}

Create study material from this textbook excerpt.

Produce JSON with:
- "chapter_title": a concise section title (EN, optional CN gloss)
- "knowledge_point": {{ "title", "description", "summary" }}
- "questions": a list of {n} questions, each {{ "title", "content", "type", "difficulty"(1-5), "answer", "key_points"[], "explanation" }}
  - Mix question types (concept, calculation, application) appropriate for {course} {subject}
  - For multiple-choice, put options A./B./C./D. inside "content" and the letter in "answer"
  - Keep questions grounded in the excerpt; do not invent facts not supported by it

Excerpt:
\"\"\"
{excerpt}
\"\"\"
"""


# --------------------------------------------------------------------------- #
# PDF extraction
# --------------------------------------------------------------------------- #
def extract_pages(pdf_path: Path, max_pages: int) -> List[str]:
    """Return list of page texts. Tries PyMuPDF, then pdfplumber."""
    pages = _extract_pymupdf(pdf_path, max_pages)
    if pages:
        return pages
    return _extract_pdfplumber(pdf_path, max_pages)


def _extract_pymupdf(pdf_path: Path, max_pages: int) -> List[str]:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return []
    pages: List[str] = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            text = page.get_text().strip()
            if text:
                pages.append(text)
        doc.close()
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] PyMuPDF failed on {pdf_path.name}: {e}")
        return []
    return pages


def _extract_pdfplumber(pdf_path: Path, max_pages: int) -> List[str]:
    try:
        import pdfplumber
    except ImportError:
        return []
    pages: List[str] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                text = (page.extract_text() or "").strip()
                if text:
                    pages.append(text)
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] pdfplumber failed on {pdf_path.name}: {e}")
        return []
    return pages


_FRONT_MATTER_PATTERNS = [
    r"about\s+the\s+author",
    r"acknowledgment",
    r"preface",
    r"foreword",
    r"table\s+of\s+contents",
    r"list\s+of\s+(figure|table)",
    r"copyright",
    r"dedication",
    r"committee\s+work",
    r"about\s+college\s+board",
    r"about\s+the\s+college\s+board",
    r"contributor",
    r"reviewer",
    r"location\s+of\s+content",
    r"to\s+the\s+(student|teacher|instructor|reader)",
    r"how\s+to\s+use\s+this\s+book",
    r"supplementary\s+materials",
    r"index\s+of",
    r"glossary",
    r"^references\b",
    r"bibliography",
    r"answer\s+key",
]
_FRONT_MATTER_RE = re.compile(
    "|".join(_FRONT_MATTER_PATTERNS), re.IGNORECASE
)
_MIN_BODY_WORDS = 120  # chunks with fewer words are likely front/back matter


def _is_front_matter(text: str) -> bool:
    """Return True if the chunk looks like front or back matter, not body content."""
    if len(text.split()) < _MIN_BODY_WORDS:
        return True
    # If the first 400 chars are dominated by front-matter keywords, skip
    sample = text[:400]
    return bool(_FRONT_MATTER_RE.search(sample))


def chunk_pages(pages: List[str], chunk_chars: int, skip_front: int) -> List[str]:
    """Group pages into ~chunk_chars text blocks; skip front matter pages and
    any chunk that looks like acknowledgments / author bios / ToC."""
    body = pages[skip_front:] if skip_front < len(pages) else pages
    chunks: List[str] = []
    buf = ""
    for page in body:
        if len(buf) + len(page) > chunk_chars and buf:
            if not _is_front_matter(buf):
                chunks.append(buf)
            buf = page
        else:
            buf += "\n" + page
    if buf.strip() and not _is_front_matter(buf):
        chunks.append(buf)
    return chunks


# --------------------------------------------------------------------------- #
# Per-book skip configuration (pages of front matter to skip)
# Determined by inspecting each PDF's first 40 pages manually.
# --------------------------------------------------------------------------- #
_BOOK_SKIP: dict[str, int] = {
    "ap_cs_principles_hare_4th":               6,
    "ap_physics_5_steps_to_a_5_2023":          24,
    "ap_statistics_the_practice_of_statistics": 25,
    "ib_biology_hodder":                        12,
    "ib_computer_science_hodder":               10,
    # IB Math AA HL is a scanned image PDF — text extraction mostly fails.
    # Skip 30 pages hoping some layers have embedded text; rely on filter.
    "ib_math_aa_hl_analysis_and_approaches":    30,
}


def get_skip_front(pdf_path: Path, default: int) -> int:
    slug = re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_")[:48]
    return _BOOK_SKIP.get(slug, default)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def slug_from_path(pdf_path: Path) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_")
    return name[:48]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- #
# Per-book ingestion
# --------------------------------------------------------------------------- #
async def ingest_book(client, pdf_path: Path, course: str, args) -> dict:
    subject = slug_from_path(pdf_path)
    prefix = f"{course.lower()}_{subject}"
    out_dir = COURSES / course / subject

    if out_dir.exists() and not args.overwrite and (out_dir / "chapters.json").exists():
        print(f"  [skip] {course}/{subject} already exists (use --overwrite)")
        return {"pdf": pdf_path.name, "subject": subject, "status": "skipped"}

    print(f"  extracting text: {pdf_path.name}")
    pages = extract_pages(pdf_path, args.max_pages)
    if not pages:
        print(f"  [warn] no text extracted from {pdf_path.name} (scanned PDF? install OCR)")
        return {"pdf": pdf_path.name, "subject": subject, "status": "no_text"}

    skip = get_skip_front(pdf_path, args.skip_front)
    if skip != args.skip_front:
        print(f"  [info] using book-specific skip_front={skip} for {pdf_path.name}")
    chunks = chunk_pages(pages, args.chunk_chars, skip)[: args.max_chunks]
    print(f"  {len(pages)} pages -> {len(chunks)} chunks (generating with LLM)")

    chapters = []
    all_kps = []
    q_count = 0

    for idx, chunk in enumerate(chunks, 1):
        cid = f"{idx:02d}"
        try:
            section = await client.chat_json(
                [
                    {"role": "system", "content": GEN_SYSTEM},
                    {
                        "role": "user",
                        "content": GEN_USER_TEMPLATE.format(
                            course=course,
                            subject=subject.replace("_", " "),
                            n=args.questions_per_chunk,
                            excerpt=chunk[: args.chunk_chars],
                        ),
                    },
                ],
                GenSection,
                max_tokens=args.gen_max_tokens,
            )
        except Exception as e:  # noqa: BLE001
            print(f"    [warn] chunk {idx} generation failed: {e}")
            continue

        kp_id = f"{prefix}_kc{idx:02d}"
        kp = {
            "id": kp_id,
            "title": section.knowledge_point.title,
            "chapter_id": f"c{idx:02d}",
            "description": section.knowledge_point.description,
            "summry": section.knowledge_point.summary,  # 'summry' kept for code compat
        }
        all_kps.append(kp)

        questions = []
        for qn, q in enumerate(section.questions, 1):
            qid = f"{prefix}_q{idx:02d}{qn:02d}"
            questions.append({
                "id": qid,
                "title": q.title,
                "content": q.content,
                "difficulty": q.difficulty,
                "type": q.type,
                "knowledge_points": [kp_id],
                "related_questions": [],
                "reference_answer": {
                    "content": q.answer,
                    "key_points": q.key_points,
                    "explanation": q.explanation,
                },
                "chapter": cid,
            })
        q_count += len(questions)

        chapters.append({
            "id": cid,
            "title": section.chapter_title,
            "parent_id": "",
            "order": idx,
            "description": section.knowledge_point.summary[:300],
            "knowledge_points": [kp_id],
            "sub_chapters": [],
        })

        write_json(out_dir / "questions" / f"ch{idx:02d}.json", questions)
        write_json(out_dir / "knowledgepoints" / f"ch{idx:02d}.json", [kp])
        print(f"    chunk {idx}/{len(chunks)}: +1 KP, +{len(questions)} questions")

    write_json(out_dir / "chapters.json", chapters)
    write_json(out_dir / "knowledgepoints" / "all_knowledgepoints.json", all_kps)

    return {
        "pdf": pdf_path.name,
        "subject": subject,
        "status": "ok",
        "chapters": len(chapters),
        "knowledge_points": len(all_kps),
        "questions": q_count,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
async def run(args) -> None:
    try:
        from src.agents.llm.client import LLMClient
    except Exception as e:  # noqa: BLE001
        print(f"[error] cannot import LLM client: {e}")
        print("Install deps (pip install -r requirements.txt) and run from project root.")
        sys.exit(1)

    client = LLMClient(model_type=args.model_backend) if args.model_backend else LLMClient()
    print(f"LLM backend: {client.config.backend} | model: {client.config.model} | {client.config.base_url}")

    courses = ["AP", "IB"] if args.course == "all" else [args.course]
    results = []
    for course in courses:
        course_dir = TEXTBOOKS / course
        if not course_dir.exists():
            continue
        for pdf in sorted(course_dir.glob("*.pdf")):
            print(f"\n=== {course} / {pdf.name} ===")
            results.append(await ingest_book(client, pdf, course, args))

    COURSES.mkdir(parents=True, exist_ok=True)
    write_json(COURSES / "manifest.json", results)
    ok = [r for r in results if r.get("status") == "ok"]
    total_q = sum(r.get("questions", 0) for r in ok)
    print(f"\nDone. {len(ok)}/{len(results)} books built, {total_q} questions total.")
    print(f"Manifest: {COURSES / 'manifest.json'}")


def parse_args():
    p = argparse.ArgumentParser(description="Ingest AP/IB textbooks into course bank")
    p.add_argument("--course", choices=["AP", "IB", "all"], default="all")
    p.add_argument("--max-chunks", type=int, default=10, help="Max chunks (sections) per book")
    p.add_argument("--chunk-chars", type=int, default=6000, help="Approx chars per chunk")
    p.add_argument("--questions-per-chunk", type=int, default=3)
    p.add_argument("--gen-max-tokens", type=int, default=2048,
                   help="Max tokens to generate per chunk (keep prompt+gen under the server's --max-model-len)")
    p.add_argument("--max-pages", type=int, default=250, help="Max pages to read per book")
    p.add_argument("--skip-front", type=int, default=8, help="Skip N front-matter pages")
    p.add_argument("--model-backend", default=None, help="Override EASYEDU_LLM_BACKEND")
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
