# src/agents/agents/teacher.py
import os
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.types import Command

from ..base import State
from ..models import get_llm, stream_or_chat
from data.courses_loader import CoursesDataLoader

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "prompts")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
COURSES_DIR = os.path.join(ROOT_DIR, "data", "courses")
COURSES_INDICES_PATH = os.path.join(COURSES_DIR, "courses_indices.pkl")

# 题库加载一次后缓存，避免每次回答都重读
_KP_LOADER: CoursesDataLoader | None = None


def _get_loader() -> CoursesDataLoader:
    global _KP_LOADER
    if _KP_LOADER is None:
        if os.path.exists(COURSES_INDICES_PATH):
            _KP_LOADER = CoursesDataLoader.load_indices(COURSES_INDICES_PATH)
        else:
            _KP_LOADER = CoursesDataLoader()
            _KP_LOADER.load_all_subjects()
    return _KP_LOADER


async def knowledge_summry_search(knowledge_points: list) -> str:
    """从 AP/IB 题库取知识点摘要（Python 侧查好，不靠模型发工具调用）。"""
    try:
        loader = _get_loader()
        knowledge_summry = []
        for kp in knowledge_points:
            kp_info = loader.get_knowledge_point(kp)
            if kp_info:
                # 注意：字段名 "summry" 是历史拼写错误（应为 summary），数据与代码都依赖它，
                # 改动需同时迁移题库数据，故暂保留。见 docs/DATA.md。
                knowledge_summry.append({
                    "knowledge_point": kp_info.get("title", ""),
                    "summry": kp_info.get("summry", ""),
                })
        if knowledge_summry:
            return "\n".join([f"{kp['knowledge_point']}: {kp['summry']}" for kp in knowledge_summry])
        return "No matching knowledge points found."
    except Exception as e:
        return str(e)


class TeacherAgent:
    """教师：先把知识点查好塞进提示词，再让模型回答（不靠模型自己发工具调用）。"""

    def __init__(self, model_type: str = "local_vllm"):
        self.model_type = model_type

    async def __call__(self, state: State, config) -> Command[Literal["__end__"]]:
        try:
            curr_question = state.question[0]
            evaluation = state.evaluation

            prompt_path = os.path.join(PROMPTS_DIR, "teacher_agent_prompt.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()

            knowledge_points = curr_question.get("knowledge_points", [])
            knowledge_context = ""
            if knowledge_points:
                knowledge_context = await knowledge_summry_search(knowledge_points)

            language = getattr(state, "language", "en")
            if language == "zh":
                lang_instruction = "你必须完全用中文回复，包括所有解释、提问和总结。"
            else:
                lang_instruction = "You must respond entirely in English."

            system_text = prompt_template.format(
                title=curr_question["title"],
                content=curr_question["content"],
                answer=curr_question["reference_answer"]["content"],
                knowledge_points=knowledge_points,
                explanation=curr_question["reference_answer"]["explanation"],
                is_right=evaluation.get("is_right"),
                is_complete=evaluation.get("is_complete"),
                reason=evaluation.get("reason", ""),
                knowledge_context=knowledge_context or "N/A",
                language_instruction=lang_instruction,
            )

            messages = [SystemMessage(content=system_text)]
            messages.extend(state.messages)

            client = get_llm(model_type=self.model_type)
            content = await stream_or_chat(client, messages, "teacher_agent")

            return Command(
                update={"messages": AIMessage(content=content)},
                goto="__end__",
            )

        except Exception as e:
            return Command(
                update={"log": str(e), "messages": AIMessage(content=f"Sorry, an error occurred: {e}")},
                goto="__end__",
            )
