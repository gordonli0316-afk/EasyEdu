"""
视频推荐API端点
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.services.video_recommender import VideoRecommender
from web.services.qa_service import QAService

router = APIRouter()
video_recommender = VideoRecommender()
qa_service = QAService()


@router.get("/questions/{question_id}/videos", tags=["videos"])
async def get_recommended_videos(question_id: str, limit: int = 5):
    """
    获取题目推荐视频
    
    Args:
        question_id: 题目ID
        limit: 返回数量限制
    """
    try:
        qa_system = qa_service.get_qa_system()
        question = qa_system.get_question_detail(question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail=f"题目未找到: {question_id}")
        
        videos = video_recommender.recommend_videos_for_question(question, limit=limit)
        return {
            "question_id": question_id,
            "videos": videos,
            "count": len(videos)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/search", tags=["videos"])
async def search_videos(keyword: str, subject: Optional[str] = None, limit: int = 10):
    """
    搜索视频
    
    Args:
        keyword: 搜索关键词
        subject: 科目筛选（可选）
        limit: 返回数量限制
    """
    try:
        videos = video_recommender.search_videos(keyword, subject=subject, limit=limit)
        return {
            "keyword": keyword,
            "videos": videos,
            "count": len(videos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/subjects/{subject}", tags=["videos"])
async def get_videos_by_subject(subject: str):
    """
    获取指定科目的所有视频
    
    Args:
        subject: 科目代码
    """
    try:
        videos = video_recommender.get_videos_by_subject(subject)
        return {
            "subject": subject,
            "videos": videos,
            "count": len(videos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos", tags=["videos"])
async def add_video(video: Dict):
    """
    添加视频到资源库
    
    Args:
        video: 视频信息字典
    """
    try:
        success = video_recommender.add_video(video)
        if success:
            return {"message": "视频添加成功", "video_id": video.get("id")}
        else:
            raise HTTPException(status_code=400, detail="视频添加失败，可能是ID已存在或缺少必需字段")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/subjects", tags=["videos"])
async def get_video_subjects():
    """获取所有有视频的科目列表"""
    try:
        subjects = video_recommender.get_all_subjects()
        return {"subjects": subjects, "count": len(subjects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
