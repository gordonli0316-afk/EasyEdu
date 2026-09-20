from fastapi import APIRouter, HTTPException
from typing import Optional
from web.services.qa_service import get_qa_service

router = APIRouter()
qa_service = get_qa_service()

# 注意：这条必须放在 /knowledge/{knowledge_id} 之前，否则会被当成 knowledge_id="cards"
@router.get("/knowledge/cards", tags=["knowledge"])
async def get_knowledge_cards(subject: Optional[str] = None, limit: int = 60):
    """知识点卡片（用于抽认卡页面），直接读题库，无需上传文件。"""
    try:
        loader = qa_service.get_qa_system().index_system
        cards = []
        for kp_id, kp in loader.knowledge_index.items():
            if subject and kp.get("subject") != subject:
                continue
            cards.append({
                "id": kp_id,
                "title": kp.get("title", ""),
                "summary": kp.get("summry", ""),
                "subject": kp.get("subject", ""),
                "course": kp.get("course", ""),
            })
            if len(cards) >= max(1, min(limit, 500)):
                break
        return {"cards": cards, "count": len(cards)}
    except HTTPException:
        # 不要把 404 之类的正常错误重新包成 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/chapters", tags=["knowledge"])
async def get_chapter_knowledge_points():
    """获取所有章节的知识点"""
    try:
        knowledge_points = qa_service.chapter_knowledge_points()
        return knowledge_points
    except HTTPException:
        # 不要把 404 之类的正常错误重新包成 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/{knowledge_id}", tags=["knowledge"])
async def get_knowledge_summary(knowledge_id: str):
    """获取指定知识点的概要"""
    try:
        summary = qa_service.knowledge_points_summary_by_knowledge_id(knowledge_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"知识点未找到: {knowledge_id}")
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # 不要把 404 之类的正常错误重新包成 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/{knowledge_id}/title", tags=["knowledge"])
async def get_knowledge_title(knowledge_id: str):
    """获取指定知识点的标题"""
    try:
        title = qa_service.get_knowledge_title(knowledge_id)
        if not title:
            raise HTTPException(status_code=404, detail=f"知识点标题未找到: {knowledge_id}")
        return {"id": knowledge_id, "title": title}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # 不要把 404 之类的正常错误重新包成 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/details/all", tags=["knowledge"])
async def get_all_knowledge_details():
    """获取所有知识点的详细信息（ID和标题）"""
    try:
        details = qa_service.get_all_knowledge_details()
        return details
    except HTTPException:
        # 不要把 404 之类的正常错误重新包成 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 