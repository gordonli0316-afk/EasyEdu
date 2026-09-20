"""Offline demo backend for EasyEdu.

A deployed copy of EasyEdu may not have a GPU or an API key available. In that
case the three-agent loop would fail and the reviewer would just see an error.
This module keeps the product usable by answering from the question's own
reference answer with a small rule-based evaluator, so the workflow (evaluate ->
peer follow-up / tutor feedback) can still be experienced end to end.

It is deliberately *not* presented as an AI model: the web UI labels it clearly
as demo mode, and every response is derived from the bundled textbook answer
rather than being invented.
"""
import os
import re
from typing import Dict, List, Optional

# Words too common to be evidence that the student engaged with the content.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "that", "this",
    "these", "those", "is", "are", "was", "were", "be", "been", "being", "am",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "as", "into",
    "it", "its", "we", "you", "your", "they", "them", "their", "he", "she",
    "his", "her", "not", "no", "yes", "do", "does", "did", "so", "such",
    "there", "here", "when", "where", "which", "who", "whom", "what", "why",
    "how", "all", "any", "both", "each", "more", "most", "other", "some",
    "can", "could", "will", "would", "should", "must", "may", "might", "have",
    "has", "had", "about", "because", "since", "therefore", "also", "very",
    "just", "only", "same", "different", "value", "values", "using", "use",
}

# Phrases that show the student is explaining a mechanism rather than naming it.
_REASONING_MARKERS = (
    "because", "since", "therefore", "thus", "hence", "so that", "which means",
    "due to", "as a result", "this means", "reason", "explains why", "leads to",
    "gives us", "results in", "in order to",
)


def _tokens(text: str) -> set:
    words = re.findall(r"[A-Za-z][A-Za-z\-']{3,}", (text or "").lower())
    tokens = {w for w in words if w not in _STOPWORDS}
    # Formula symbols, logic operators and numbers carry real content in physics
    # and CS answers ("t = v0/g = 1.22 s", "R = G AND NOT E"), so keep them.
    tokens |= set(re.findall(r"\b[A-Z]\b", text or ""))
    tokens |= set(re.findall(r"\b(?:AND|OR|NOT|NAND|NOR|XOR|TCP|UDP|IP|DNA|ATP)\b", text or ""))
    tokens |= set(re.findall(r"\d+(?:\.\d+)?", text or ""))
    return tokens


def _overlap_ratio(student_answer: str, reference_text: str) -> float:
    ref = _tokens(reference_text)
    if not ref:
        return 0.0
    return len(_tokens(student_answer) & ref) / len(ref)


def _has_reasoning(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in _REASONING_MARKERS)


def is_demo_mode() -> bool:
    """True when the deterministic demo backend should be used."""
    forced = os.getenv("EASYEDU_DEMO_MODE", "").strip().lower()
    if forced in ("1", "true", "yes", "on"):
        return True
    if forced in ("0", "false", "no", "off"):
        return False
    return os.getenv("EASYEDU_LLM_BACKEND", "").strip().lower() == "demo"


def evaluate_answer(question: Dict, answer: str) -> Dict:
    """Rule-based stand-in for the router agent's structured judgement.

    Two signals are combined so that long reference explanations do not drown out
    a short but correct student answer:

    * ``essential`` - how much of the *reference answer itself* was stated
    * ``on_topic``  - how much of what the student wrote is relevant at all
    """
    reference = question.get("reference_answer", {}) or {}
    essential_terms = _tokens(str(reference.get("content", "")))
    all_terms = essential_terms | _tokens(str(reference.get("explanation", "")))

    answer_terms = _tokens(answer)
    words = len(re.findall(r"\S+", answer or ""))
    reasoned = _has_reasoning(answer)

    essential = len(answer_terms & essential_terms) / max(len(essential_terms), 1)
    on_topic = len(answer_terms & all_terms) / max(len(answer_terms), 1)

    if words < 12:
        is_right, is_complete = False, False
        reason = "The answer is too short to judge the reasoning behind it."
    elif essential >= 0.5 or (on_topic >= 0.35 and len(answer_terms & all_terms) >= 3):
        is_right = True
        is_complete = reasoned and words >= 35
        reason = (
            "The explanation reaches the correct result and justifies it with the "
            "underlying principle or mechanism."
            if is_complete
            else "The result looks right, but the reasoning behind it is not yet explicit."
        )
    else:
        is_right, is_complete = False, False
        reason = "The answer does not yet cover the key ideas of the reference answer."

    return {
        "is_right": is_right,
        "is_complete": is_complete,
        "reason": reason,
        "next_agent": "teacher" if (not is_right or is_complete) else "student",
    }


def _excerpt(answer: str, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", (answer or "").strip())
    return text[: limit - 1] + "…" if len(text) > limit else text


def peer_follow_up(
    question: Dict, answer: str, evaluation: Dict, turn: int, language: str = "en"
) -> str:
    """A Socratic follow-up from the 'study partner' agent."""
    reference = question.get("reference_answer", {}) or {}
    knowledge_points = question.get("knowledge_points") or []
    first_term = ""
    for term in sorted(_tokens(str(reference.get("explanation", "")))):
        first_term = term
        break
    focus = first_term or "that step"

    if language == "zh":
        templates = [
            "你写到「{excerpt}」。结论我接受，但我自己未必能复现。你实际依赖的是哪一条原理或公式？为什么它在这个情境下成立？",
            "等一下——为什么 {focus} 必须是那样？如果前提不成立，结论会在哪一步垮掉？",
            "能把它和「{kp}」连起来吗？你的解释里我还没看到这一环。",
        ]
    else:
        templates = [
            "You wrote: “{excerpt}”. I'll accept the result, but I'm not sure I could reproduce it. "
            "Which principle or equation are you actually relying on, and why is it valid in this situation?",
            "Hold on — why does {focus} have to be true? If that assumption failed, at which step would the conclusion break down?",
            "Could you connect this to “{kp}”? I don't see where that fits into your explanation yet.",
        ]

    kp_title = ""
    if knowledge_points:
        kp_title = str(knowledge_points[0]).replace("_", " ")
    template = templates[turn % len(templates)]
    return template.format(excerpt=_excerpt(answer), focus=focus, kp=kp_title or "the key idea")


def _knowledge_lines(knowledge_points: List[str], loader) -> List[str]:
    lines: List[str] = []
    if loader is None:
        return lines
    for kp_id in knowledge_points or []:
        info = loader.get_knowledge_point(kp_id)
        if info and info.get("summry"):
            lines.append(f"**{info.get('title', kp_id)}** — {info['summry']}")
    return lines


def tutor_feedback(
    question: Dict,
    answer: str,
    evaluation: Dict,
    loader=None,
    language: str = "en",
) -> str:
    """Tutor-style feedback assembled from the reference answer and knowledge points."""
    reference = question.get("reference_answer", {}) or {}
    ref_content = str(reference.get("content", "")).strip()
    ref_explanation = str(reference.get("explanation", "")).strip()
    knowledge_lines = _knowledge_lines(question.get("knowledge_points", []), loader)

    if language == "zh":
        if evaluation.get("is_right"):
            verdict = "✅ **结论正确。**"
        else:
            verdict = "🔍 **这里还有一处关键缺口。**"
        parts = [verdict, "", f"**参考答案：** {ref_content}"]
        if ref_explanation:
            parts += ["", f"**为什么：** {ref_explanation}"]
        if knowledge_lines:
            parts += ["", "**相关知识点**"] + [f"- {line}" for line in knowledge_lines]
        parts += ["", "**下一步：** 合上答案，把上面这段推理用自己的话再讲一遍；讲不顺的地方就是还没真正掌握的地方。"]
        return "\n".join(parts)

    if evaluation.get("is_right"):
        verdict = "✅ **Your conclusion is correct.**"
    else:
        verdict = "🔍 **There is a key gap in your explanation.**"

    parts = [verdict, "", f"**Reference answer:** {ref_content}"]
    if ref_explanation:
        parts += ["", f"**Why this is the answer:** {ref_explanation}"]
    if knowledge_lines:
        parts += ["", "**Related knowledge points**"] + [f"- {line}" for line in knowledge_lines]
    parts += [
        "",
        "**Next step:** close the answer and explain the reasoning above again in your own words. "
        "Anywhere you stall is the part that is not yet secure.",
    ]
    return "\n".join(parts)

def human_turn_count(messages) -> int:
    """How many times the student has written something in this session."""
    return sum(1 for m in (messages or []) if getattr(m, "type", "") == "human")


def last_human_text(messages) -> str:
    """Text of the most recent human turn (empty string when there is none)."""
    for message in reversed(list(messages or [])):
        if getattr(message, "type", "") == "human":
            return str(getattr(message, "content", ""))
    return ""


def fallback_notice(language: str = "en") -> str:
    """One honest line shown only when a live model call failed mid-conversation.

    Demo mode that was known from the start is announced once by the page banner, so
    this is purely to avoid implying that a reference-based reply came from the model.
    """
    if language == "zh":
        return "_AI 模型暂时不可用，下面的反馈来自 EasyEdu 内置的参考答案。_\n\n"
    return "_The AI model is unavailable right now, so this reply comes from EasyEdu's built-in reference answers._\n\n"
