import os
import logging
from typing import Optional

from src.knowledge_qa_system import KnowledgeQASystem
from src.agents.llm.env import get_default_model_backend
from src.agents.llm.health import active_mode, mode_reason

logger = logging.getLogger(__name__)

# 题库索引 + LangGraph 工作流只建一次：每个 endpoint 模块各自 new 一个
# QAService 会重复加载整个题库（9 份副本），在小型容器上非常浪费。
_shared_service: Optional["QAService"] = None


def get_qa_service() -> "QAService":
    """进程内共享的 QAService 单例。"""
    global _shared_service
    if _shared_service is None:
        _shared_service = QAService()
    return _shared_service


def _model_backend() -> str:
    return os.getenv("EASYEDU_LLM_BACKEND", get_default_model_backend())


class QAService:
    """问答服务，封装 KnowledgeQASystem 功能"""

    def __init__(
        self,
        router_model_type: Optional[str] = None,
        teacher_model_type: Optional[str] = None,
        student_model_type: Optional[str] = None,
    ):
        backend = _model_backend()
        self.qa_system = KnowledgeQASystem(
            use_high_school_data=True,
            router_model_type=router_model_type or backend,
            teacher_model_type=teacher_model_type or backend,
            student_model_type=student_model_type or backend,
        )

    @property
    def mode(self) -> str:
        """ "demo" when answering without a model, otherwise "live"."""
        return active_mode()

    @property
    def mode_reason(self) -> str:
        """Short, non-technical reason for the current mode (never contains secrets)."""
        return mode_reason()

    @property
    def source(self) -> str:
        """Which question bank is loaded: "generated" or "sample"."""
        root = str(getattr(self.qa_system.index_system, "source_dir", "") or "")
        return "sample" if "seed_courses" in root else "generated"

    def get_chapters(self, subject: Optional[str] = None):
        return self.qa_system.get_chapters(subject=subject)

    def get_qa_system(self):
        return self.qa_system

    def get_questions_by_chapter(self, chapter_id):
        return self.qa_system.get_questions_by_chapter(chapter_id)

    def get_question_detail(self, question_id):
        return self.qa_system.get_question_detail(question_id)

    def create_session(self, question_id, language="en"):
        return self.qa_system.create_session(question_id, language=language)

    async def process_answer(self, session_id, answer):
        logger.info(f"QAService.process_answer - session_id: {session_id}")
        try:
            async for chunk, node in self.qa_system.process_answer(session_id, answer):
                yield chunk, node
        except Exception as e:
            # Log the detail server-side only; the visitor gets a plain message.
            logger.exception("process_answer failed: %s", type(e).__name__)
            yield "Something went wrong while reviewing your answer. Please send it again.", "system"

    def get_session_info(self, session_id):
        return self.qa_system.get_session_info(session_id)

    def get_related_knowledge_points(self, question_id):
        return self.qa_system.get_related_knowledge_points(question_id)

    def get_similar_questions(self, question_id):
        return self.qa_system.get_similar_questions(question_id)

    def delete_session(self, session_id):
        return self.qa_system.delete_session(session_id)

    def chapter_knowledge_points(self):
        return self.qa_system.chapter_knowledge_points()

    def knowledge_points_summary_by_knowledge_id(self, knowledge_id):
        return self.qa_system.knowledge_points_summary_by_knowledge_id(knowledge_id)

    def get_knowledge_title(self, knowledge_id):
        try:
            return self.qa_system.get_knowledge_name_by_knowledge_id(knowledge_id)
        except Exception as e:
            logger.error(f"get_knowledge_title error: {e}")
            return ""

    def get_all_knowledge_details(self):
        try:
            result = {}
            all_chapter_knowledge_points = self.chapter_knowledge_points()
            for chapter_id, knowledge_ids in all_chapter_knowledge_points.items():
                for knowledge_id in knowledge_ids:
                    if knowledge_id not in result:
                        title = self.get_knowledge_title(knowledge_id)
                        result[knowledge_id] = {"id": knowledge_id, "title": title}
            return result
        except Exception as e:
            logger.error(f"get_all_knowledge_details error: {e}")
            return {}
