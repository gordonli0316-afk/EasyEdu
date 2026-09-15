"""
标签管理API端点
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.knowledge_qa_system import KnowledgeQASystem
from web.services.qa_service import QAService

router = APIRouter()
qa_service = QAService()


@router.get("/tags", tags=["tags"])
async def get_all_tags(subject: Optional[str] = None):
    """
    获取所有标签列表
    
    Args:
        subject: 科目筛选（可选）
    """
    try:
        qa_system = qa_service.get_qa_system()
        tags = qa_system.get_all_tags(subject=subject)
        return {"tags": tags, "count": len(tags)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/{tag}/questions", tags=["tags"])
async def get_questions_by_tag(tag: str, match_all: bool = False):
    """
    获取带特定标签的题目
    
    Args:
        tag: 标签名称
        match_all: 如果为True，题目必须包含所有提供的标签
    """
    try:
        qa_system = qa_service.get_qa_system()
        questions = qa_system.get_questions_by_tags([tag], match_all=match_all)
        return {"questions": questions, "count": len(questions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/questions/{question_id}/tags", tags=["tags"])
async def add_tags_to_question(question_id: str, tags: List[str]):
    """
    为题目添加标签
    
    Args:
        question_id: 题目ID
        tags: 要添加的标签列表
    """
    try:
        qa_system = qa_service.get_qa_system()
        success = qa_system.add_tags_to_question(question_id, tags)
        if success:
            return {"message": "标签添加成功", "question_id": question_id, "tags": tags}
        else:
            raise HTTPException(status_code=404, detail=f"题目未找到: {question_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/questions/{question_id}/tags/{tag}", tags=["tags"])
async def remove_tag_from_question(question_id: str, tag: str):
    """
    从题目中移除标签
    
    Args:
        question_id: 题目ID
        tag: 要移除的标签
    """
    try:
        qa_system = qa_service.get_qa_system()
        success = qa_system.remove_tag_from_question(question_id, tag)
        if success:
            return {"message": "标签移除成功", "question_id": question_id, "tag": tag}
        else:
            raise HTTPException(status_code=404, detail=f"题目或标签未找到")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subjects", tags=["tags"])
async def get_all_subjects():
    """获取所有科目列表"""
    try:
        qa_system = qa_service.get_qa_system()
        subjects = qa_system.get_all_subjects()
        return {"subjects": subjects, "count": len(subjects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subjects/{subject}/questions", tags=["tags"])
async def get_questions_by_subject(subject: str):
    """
    获取指定科目的所有题目
    
    Args:
        subject: 科目代码
    """
    try:
        qa_system = qa_service.get_qa_system()
        questions = qa_system.get_questions_by_subject(subject)
        return {"questions": questions, "count": len(questions), "subject": subject}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
