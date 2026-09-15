"""
视频推荐服务
基于题目知识点推荐相关学习视频
"""

from typing import List, Dict, Optional
import re


class VideoRecommender:
    """视频推荐服务"""
    
    def __init__(self):
        # 视频资源库（可以后续扩展为从数据库或配置文件加载）
        self.video_database = [
            {
                "id": "v001",
                "title": "高中数学：微积分基础",
                "url": "https://www.bilibili.com/video/BV1xx411c7mu",
                "platform": "bilibili",
                "subject": "math",
                "tags": ["微积分", "导数", "积分", "函数"],
                "knowledge_points": ["导数", "积分", "极限"],
                "duration": 1800,  # 秒
                "views": 10000,
                "rating": 4.5,
                "thumbnail": ""
            },
            {
                "id": "v002",
                "title": "高中物理：力学基础",
                "url": "https://www.bilibili.com/video/BV1xx411c7mv",
                "platform": "bilibili",
                "subject": "physics",
                "tags": ["力学", "牛顿定律", "运动学"],
                "knowledge_points": ["牛顿第一定律", "牛顿第二定律", "运动学"],
                "duration": 2400,
                "views": 15000,
                "rating": 4.7,
                "thumbnail": ""
            },
            {
                "id": "v003",
                "title": "高中化学：有机化学基础",
                "url": "https://www.bilibili.com/video/BV1xx411c7mw",
                "platform": "bilibili",
                "subject": "chemistry",
                "tags": ["有机化学", "烷烃", "烯烃", "醇"],
                "knowledge_points": ["烷烃", "烯烃", "醇类"],
                "duration": 2000,
                "views": 12000,
                "rating": 4.6,
                "thumbnail": ""
            },
            # 可以继续添加更多视频...
        ]
    
    def recommend_videos_for_question(
        self, 
        question: Dict, 
        limit: int = 5
    ) -> List[Dict]:
        """
        为题目推荐视频
        
        Args:
            question: 题目字典
            limit: 返回数量限制
            
        Returns:
            推荐视频列表（按匹配度排序）
        """
        subject = question.get("subject", "")
        tags = question.get("tags", [])
        knowledge_points = question.get("knowledge_points", [])
        
        # 匹配视频
        matched_videos = []
        for video in self.video_database:
            score = 0
            
            # 科目匹配（权重最高）
            if video.get("subject") == subject:
                score += 20
            
            # 标签匹配
            video_tags = video.get("tags", [])
            for tag in tags:
                if tag in video_tags:
                    score += 10
            
            # 知识点匹配
            video_knowledge = video.get("knowledge_points", [])
            for kp in knowledge_points:
                if kp in video_knowledge:
                    score += 15
            
            # 视频质量加分
            rating = video.get("rating", 0)
            score += rating * 2
            
            if score > 0:
                matched_videos.append({
                    **video,
                    "match_score": score
                })
        
        # 按分数排序
        matched_videos.sort(key=lambda x: x["match_score"], reverse=True)
        
        return matched_videos[:limit]
    
    def search_videos(
        self, 
        keyword: str, 
        subject: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        搜索视频
        
        Args:
            keyword: 关键词
            subject: 科目筛选（可选）
            limit: 返回数量限制
            
        Returns:
            匹配的视频列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for video in self.video_database:
            # 科目筛选
            if subject and video.get("subject") != subject:
                continue
            
            # 关键词匹配（标题、标签、知识点）
            title = video.get("title", "").lower()
            tags = [tag.lower() for tag in video.get("tags", [])]
            knowledge_points = [kp.lower() for kp in video.get("knowledge_points", [])]
            
            if (keyword_lower in title or 
                any(keyword_lower in tag for tag in tags) or
                any(keyword_lower in kp for kp in knowledge_points)):
                results.append(video)
        
        return results[:limit]
    
    def get_videos_by_subject(self, subject: str) -> List[Dict]:
        """按科目获取视频"""
        return [v for v in self.video_database if v.get("subject") == subject]
    
    def add_video(self, video: Dict) -> bool:
        """
        添加视频到资源库
        
        Args:
            video: 视频信息字典
            
        Returns:
            是否成功
        """
        # 验证必需字段
        required_fields = ["id", "title", "url", "subject"]
        if not all(field in video for field in required_fields):
            return False
        
        # 检查ID是否已存在
        if any(v.get("id") == video["id"] for v in self.video_database):
            return False
        
        self.video_database.append(video)
        return True
    
    def get_all_subjects(self) -> List[str]:
        """获取所有有视频的科目"""
        subjects = set()
        for video in self.video_database:
            subject = video.get("subject")
            if subject:
                subjects.add(subject)
        return sorted(list(subjects))
