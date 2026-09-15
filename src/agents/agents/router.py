# src/agents/agents/router.py
import os
from typing import Literal, Optional

from langchain_core.messages import SystemMessage
from langgraph.types import Command
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from ..base import State
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

            return Command(
                update={"evaluation": router_result},
                goto=goto,
            )

        except Exception as e:
            return Command(
                update={"log": str(e), "evaluation": {
                    "is_right": False,
                    "is_complete": False,
                    "reason": f"Router error: {e}",
                    "next_agent": "teacher",
                }},
                goto="teacher_agent",
            )
