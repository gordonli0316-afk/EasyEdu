#!/usr/bin/env python3
"""
造 SFT 训练数据（jsonl）。

优先读 data/courses 里真实的 AP/IB 题库（ingest_textbooks.py 生成的），
没有就回退到 data/ds_data。

混合策略，准确率优先——每道题既生成"教学行为"样本（router 判断、teacher
纠错/总结、student 追问），也生成"学科内容"样本（带解析的接地回答），让模型
既学会怎么教，也吸收点学科知识、少胡编。teacher 样本会把知识点上下文放进
输入里，这样模型学到的是"用给定的资料回答"，跟运行时 teacher 的做法一致。
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSES_DIR = ROOT / "data" / "courses"
DS_QUESTIONS_DIR = ROOT / "data" / "ds_data" / "questions"
OUT_DIR = ROOT / "data" / "rlhf_data" / "sft"

SYSTEM_ROUTER = (
    "You are the Router Agent in EasyEdu IB/AP Feynman tutoring. "
    "Output ONLY JSON with is_right, is_complete, reason, next_agent."
)
SYSTEM_TEACHER = (
    "You are the Teacher Agent in EasyEdu. Guide the student bilingually (EN+CN), "
    "Feynman style — hints before full answers, grounded in the provided context."
)
SYSTEM_STUDENT = (
    "You are the Student Agent in EasyEdu. Ask one deep Socratic question as a peer learner."
)


def _load_question_files() -> tuple[list[dict], str]:
    """Prefer real AP/IB course questions; fall back to ds_data."""
    course_questions = []
    if COURSES_DIR.exists():
        for qfile in COURSES_DIR.glob("*/*/questions/*.json"):
            try:
                course_questions.extend(json.loads(qfile.read_text(encoding="utf-8")))
            except Exception:
                continue
    if course_questions:
        return course_questions, "data/courses (AP/IB)"

    ds = []
    if DS_QUESTIONS_DIR.exists():
        for qfile in sorted(DS_QUESTIONS_DIR.glob("*.json")):
            try:
                ds.extend(json.loads(qfile.read_text(encoding="utf-8")))
            except Exception:
                continue
    return ds, "data/ds_data (fallback)"


def _ref(q: dict) -> dict:
    return q.get("reference_answer", {}) or {}


def _wrong_option(answer: str) -> str:
    answer = (answer or "").strip().upper()
    for opt in ["A", "B", "C", "D"]:
        if opt != answer:
            return opt
    return "B"


def _kp_context(q: dict) -> str:
    """Grounding text: explanation + key points (stands in for retrieved KP summary)."""
    ref = _ref(q)
    parts = []
    if ref.get("explanation"):
        parts.append(f"Reference explanation: {ref['explanation']}")
    if ref.get("key_points"):
        parts.append("Key points: " + "; ".join(ref["key_points"]))
    return "\n".join(parts) or "N/A"


def sample(system: str, user: str, assistant: str) -> dict:
    return {
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "output": {"role": "assistant", "content": assistant},
    }


def build_samples(q: dict) -> list[dict]:
    out = []
    content = q.get("content", "")
    title = q.get("title", "")
    ref = _ref(q)
    answer = ref.get("content", "")
    explanation = ref.get("explanation", "")
    ctx = _kp_context(q)
    is_mcq = isinstance(answer, str) and len(answer.strip()) == 1 and answer.strip().upper() in "ABCD"

    base = f"Problem: {title}\n{content}"

    # 1. Router — correct MCQ answer only → guide to explain (student)
    if is_mcq:
        out.append(sample(
            SYSTEM_ROUTER,
            f"{base}\n\nStudent says: {answer}",
            json.dumps({"is_right": True, "is_complete": False,
                        "reason": "Correct MCQ answer; needs Feynman explanation",
                        "next_agent": "student"}, ensure_ascii=False),
        ))
        # 2. Router — wrong answer → teacher
        out.append(sample(
            SYSTEM_ROUTER,
            f"{base}\n\nStudent says: {_wrong_option(answer)}",
            json.dumps({"is_right": False, "is_complete": False,
                        "reason": "Incorrect answer; needs correction",
                        "next_agent": "teacher"}, ensure_ascii=False),
        ))

    # 3. Router — full correct explanation → teacher (summarize)
    if explanation:
        out.append(sample(
            SYSTEM_ROUTER,
            f"{base}\n\nStudent explanation: {explanation}",
            json.dumps({"is_right": True, "is_complete": True,
                        "reason": "Explanation is correct and complete",
                        "next_agent": "teacher"}, ensure_ascii=False),
        ))

    # 4. Teacher — summary/affirm, grounded in context
    if explanation:
        out.append(sample(
            SYSTEM_TEACHER,
            f"{base}\n\nContext:\n{ctx}\n\nStudent gave a correct, complete explanation. Affirm and summarize.",
            f"Excellent — you've nailed it. **Key takeaway**: {explanation} "
            f"（核心：{title}）One step further: where else could this idea apply?",
        ))
        # 5. Teacher — correction via hint (no full answer dump)
        out.append(sample(
            SYSTEM_TEACHER,
            f"{base}\n\nContext:\n{ctx}\n\nStudent's explanation has an error. Guide with a hint, do not give the full answer.",
            "Good attempt, but check one step: which assumption breaks here? "
            "Try re-deriving from the definition. （想想哪一步的前提不成立？）",
        ))

    # 6. Student — Socratic probe
    out.append(sample(
        SYSTEM_STUDENT,
        f"{base}\n\nStudent gave a mostly correct but shallow answer.",
        "That's a good start — but **why** does that hold here? Can you connect it to "
        "another concept or give a real example? （为什么成立？能联系别的知识点吗？）",
    ))

    # 7. Domain content adaptation — direct concept explanation
    if explanation:
        out.append(sample(
            SYSTEM_TEACHER,
            f"Explain the core idea behind: {title}\n{content}",
            f"{explanation}",
        ))

    return out


def main():
    questions, source = _load_question_files()
    if not questions:
        print("No questions found; writing tiny placeholder.")
        questions = [{
            "title": "Sample", "content": "What is 2+2?",
            "reference_answer": {"content": "4", "explanation": "Basic addition."},
        }]

    samples = []
    for q in questions:
        samples.extend(build_samples(q))

    random.shuffle(samples)
    split = max(1, int(len(samples) * 0.9))
    train, val = samples[:split], samples[split:]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "train.jsonl", "w", encoding="utf-8") as f:
        for row in train:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(OUT_DIR / "val.jsonl", "w", encoding="utf-8") as f:
        for row in val:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Source: {source}")
    print(f"Questions: {len(questions)} -> {len(samples)} samples")
    print(f"Wrote {len(train)} train + {len(val)} val to {OUT_DIR}")


if __name__ == "__main__":
    main()
