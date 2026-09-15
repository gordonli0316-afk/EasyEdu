# src/agents/workflow.py
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from .base import State
from .agents.router import RouterAgent
from .agents.student import StudentAgent
from .agents.teacher import TeacherAgent


def create_workflow(
    router_model_type: str = "local_vllm",
    teacher_model_type: str = "local_vllm",
    student_model_type: str = "local_vllm",
):
    """搭好 LangGraph 工作流。这里只管编排，模型调用都走自有的 LLM 客户端。

    三个 *_model_type 分别指定 router/teacher/student 用哪个模型后端。
    """
    workflow = StateGraph(State)

    router_agent = RouterAgent(model_type=router_model_type)
    student_agent = StudentAgent(model_type=student_model_type)
    teacher_agent = TeacherAgent(model_type=teacher_model_type)

    workflow.add_node("router_agent", router_agent)
    workflow.add_node("student_agent", student_agent)
    workflow.add_node("teacher_agent", teacher_agent)

    workflow.add_edge(START, "router_agent")
    workflow.add_edge("student_agent", "__end__")

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
