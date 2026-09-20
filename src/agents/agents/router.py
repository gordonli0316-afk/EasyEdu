# src/agents/agents/router.py
import os
from typing import Literal, Optional

from langchain_core.messages import SystemMessage
from langgraph.types import Command
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from ..base import State
from ..demo import evaluate_answer, last_human_text
from ..llm.health import active_mode, mark_unavailable
from ..models import get_llm

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "prompts")


class EvaluationSchema(BaseModel):
    is_right: Optional[bool] = Field(None, description="Whether the explanation is correct")
    is_complete: Optional[bool] = Field(None, description="Whether the explanation is complete")
    reason: str = Field(..., description="Evaluation rationale")
    next_agent: Literal["teacher", "student"] = Field(..., description="Next agent to route to")


class Evaluation(TypedDict):
    is_right: Optional[bool]
    is_complete: Optional[bool]
    reason: str
    next_agent: Literal["teacher", "student"]


class RouterAgent:
    """路由：让模型直接吐 JSON，我们自己解析校验，不依赖 function calling。"""

    def __init__(self, model_type: str = "local_vllm"):
        self.model_type = model_type

    async def __call__(self, state: State, config) -> Command[Literal["teacher_agent", "student_agent"]]:
        try:
            curr_question = state.question[0]
        except Exception:
            return Command(
                update={"evaluation": {
                    "is_right": False, "is_complete": False,
                    "reason": "No question is loaded for this session.",
                    "next_agent": "teacher",
                }},
                goto="teacher_agent",
            )

        # 优先走真实模型；不可用时退回规则评估，保证网页流程不断
        live_failed = False
        if active_mode() == "live":
            try:
                return await self._route_with_model(state, curr_question)
            except Exception:
                # Never surface provider details; demote so the next request is fast.
                mark_unavailable("model request failed")
                live_failed = True

        router_result: Evaluation = evaluate_answer(curr_question, last_human_text(state.messages))
        if live_failed:
            # Carry the fact downstream: the node that writes the reply must say that
            # it came from the built-in reference answers, not from the model.
            router_result["used_fallback"] = True
        goto = "teacher_agent" if router_result["next_agent"] == "teacher" else "student_agent"
        return Command(update={"evaluation": router_result}, goto=goto)

    async def _route_with_model(self, state: State, curr_question: dict) -> Command:
        prompt_path = os.path.join(PROMPTS_DIR, "router_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_text = f.read()

        system_text = system_text.format(
            title=curr_question["title"],
            content=curr_question["content"],
            answer=curr_question["reference_answer"]["content"],
            explanation=curr_question["reference_answer"]["explanation"],
        )

        messages = [SystemMessage(content=system_text)]
        messages.extend(state.messages)

        client = get_llm(model_type=self.model_type)
        # 路由是"对/错/完整性"的结构化判断，用低温度让评估和 JSON 输出更稳定
        result = await client.chat_json(messages, EvaluationSchema, temperature=0.2)

        router_result: Evaluation = {
            "is_right": result.is_right,
            "is_complete": result.is_complete,
            "reason": result.reason,
            "next_agent": result.next_agent,
        }
        goto = "teacher_agent" if router_result["next_agent"] == "teacher" else "student_agent"
        return Command(update={"evaluation": router_result}, goto=goto)
