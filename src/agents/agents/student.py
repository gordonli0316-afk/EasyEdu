# src/agents/agents/student.py
import os

from langchain_core.messages import AIMessage, SystemMessage

from ..base import State
from ..demo import fallback_notice, human_turn_count, last_human_text, peer_follow_up
from ..llm.health import active_mode, mark_unavailable
from ..models import get_llm, stream_or_chat

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "prompts")


class StudentAgent:
    """学生：扮演一个爱追问的同学，用苏格拉底式提问把学生逼深一点。"""

    def __init__(self, model_type: str = "local_vllm"):
        self.model_type = model_type

    async def __call__(self, state: State, config) -> dict:
        curr_question = state.question[0]
        evaluation = state.evaluation
        language = getattr(state, "language", "en")
        answer = last_human_text(state.messages)

        def demo_reply(with_notice: bool) -> dict:
            content = peer_follow_up(
                curr_question,
                answer,
                evaluation,
                turn=max(human_turn_count(state.messages) - 1, 0),
                language=language,
            )
            if with_notice:
                content = fallback_notice(language) + content
            return {"messages": AIMessage(content=content)}

        # The router may already have discovered that the model is unavailable.
        if active_mode() != "live":
            return demo_reply(with_notice=bool(evaluation.get("used_fallback")))

        try:
            content = await self._ask_model(state, curr_question, evaluation, language)
            return {"messages": AIMessage(content=content)}
        except Exception:
            mark_unavailable("model request failed")
            return demo_reply(with_notice=True)

    async def _ask_model(self, state: State, curr_question: dict, evaluation: dict, language: str) -> str:
        prompt_path = os.path.join(PROMPTS_DIR, "student_agent_prompt2.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        if language == "zh":
            lang_instruction = "你必须完全用中文回复，用中文提问。"
        else:
            lang_instruction = "You must respond entirely in English."

        system_text = prompt_template.format(
            title=curr_question["title"],
            content=curr_question["content"],
            answer=curr_question["reference_answer"]["content"],
            explanation=curr_question["reference_answer"]["explanation"],
            is_right=evaluation.get("is_right"),
            is_complete=evaluation.get("is_complete"),
            reason=evaluation.get("reason", ""),
            language_instruction=lang_instruction,
        )

        messages = [SystemMessage(content=system_text)]
        messages.extend(state.messages)

        client = get_llm(model_type=self.model_type)
        return await stream_or_chat(client, messages, "student_agent")
