"""
抽认卡API端点
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.services.flashcard_service import FlashCardService
from web.services.qa_service import QAService

router = APIRouter()
flashcard_service = FlashCardService()
qa_service = QAService()

# 简单的内存存储（生产环境应使用数据库）
flashcard_storage = {}


class ReviewRequest(BaseModel):
    """复习请求模型"""
    quality: int = Field(..., ge=0, le=5, description="复习质量 (0-5)")


@router.post("/flashcards", tags=["flashcards"])
async def create_flashcard(question_id: str):
    """
    从题目创建抽认卡
    
    Args:
        question_id: 题目ID
    """
    try:
        qa_system = qa_service.get_qa_system()
        question = qa_system.get_question_detail(question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail=f"题目未找到: {question_id}")
        
        flashcard = flashcard_service.create_flashcard_from_question(question)
        flashcard_storage[flashcard["id"]] = flashcard
        
        return flashcard
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flashcards", tags=["flashcards"])
async def get_flashcards(
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """
    获取抽认卡列表
    
    Args:
        subject: 科目筛选（可选）
        tags: 标签筛选（可选）
    """
    try:
        flashcards = list(flashcard_storage.values())
        
        # 科目筛选
        if subject:
            flashcards = flashcard_service.get_flashcards_by_subject(flashcards, subject)
        
        # 标签筛选
        if tags:
            flashcards = flashcard_service.get_flashcards_by_tags(flashcards, tags)
        
        return {
            "flashcards": flashcards,
            "count": len(flashcards)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flashcards/due", tags=["flashcards"])
async def get_due_flashcards():
    """获取需要复习的抽认卡"""
    try:
        flashcards = list(flashcard_storage.values())
        due_cards = flashcard_service.get_due_flashcards(flashcards)
        return {
            "flashcards": due_cards,
            "count": len(due_cards)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flashcards/{card_id}/review", tags=["flashcards"])
async def review_flashcard(card_id: str, request: ReviewRequest):
    """
    复习抽认卡
    
    Args:
        card_id: 抽认卡ID
        request: 复习请求（包含质量评分）
    """
    try:
        if card_id not in flashcard_storage:
            raise HTTPException(status_code=404, detail=f"抽认卡未找到: {card_id}")
        
        card = flashcard_storage[card_id]
        updated_card = flashcard_service.review_flashcard(card, request.quality)
        flashcard_storage[card_id] = updated_card
        
        return updated_card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flashcards/statistics", tags=["flashcards"])
async def get_flashcard_statistics():
    """获取抽认卡复习统计"""
    try:
        flashcards = list(flashcard_storage.values())
        stats = flashcard_service.get_review_statistics(flashcards)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/flashcards/{card_id}", tags=["flashcards"])
async def delete_flashcard(card_id: str):
    """删除抽认卡"""
    try:
        if card_id not in flashcard_storage:
            raise HTTPException(status_code=404, detail=f"抽认卡未找到: {card_id}")
        
        del flashcard_storage[card_id]
        return {"message": "抽认卡已删除", "card_id": card_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
