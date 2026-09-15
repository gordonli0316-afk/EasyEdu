"""
EasyEdu 结构化问题数据库模式定义
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class RelatedKnowledgePoint(BaseModel):
    """关联知识点"""
    id: str = Field(..., description="关联知识点ID")
    relation_type: str = Field(..., description="关系类型: prerequisite, related, extension")


class RelatedQuestion(BaseModel):
    """关联问题"""
    id: str = Field(..., description="关联问题ID")
    relation_type: str = Field(..., description="关系类型: extension, application, contrast")


class ReferenceAnswer(BaseModel):
    """参考答案"""
    content: str = Field(..., description="答案内容")
    key_points: List[str] = Field(default_factory=list, description="关键点列表")
    explanation: str = Field(default="", description="详细解释")


class Chapter(BaseModel):
    """章节模型"""
    id: str = Field(..., description="章节唯一标识符")
    title: str = Field(..., description="章节标题")
    parent_id: Optional[str] = Field(None, description="父章节ID（可选）")
    order: int = Field(0, description="排序顺序")
    description: str = Field("", description="章节描述")
    knowledge_points: List[str] = Field(default_factory=list, description="包含的知识点ID列表")
    sub_chapters: List[str] = Field(default_factory=list, description="子章节ID列表")


class KnowledgePoint(BaseModel):
    """知识点模型"""
    id: str = Field(..., description="知识点唯一标识符")
    title: str = Field(..., description="知识点标题")
    chapter_id: str = Field(..., description="所属章节ID")
    description: str = Field("", description="知识点详细描述")
    related_points: List[RelatedKnowledgePoint] = Field(default_factory=list, description="关联知识点")
    questions: List[str] = Field(default_factory=list, description="相关问题ID列表")


class Question(BaseModel):
    """问题模型（扩展版 - 支持高中多科目）"""
    id: str = Field(..., description="问题唯一标识符")
    title: str = Field(..., description="问题标题")
    content: str = Field(..., description="问题内容")
    difficulty: int = Field(1, description="难度等级 (1-5)")
    type: str = Field(..., description="问题类型 (choice, fill, essay, calculation)")
    
    # 新增字段 - 高中教学系统
    subject: str = Field(..., description="科目 (math, physics, chemistry, biology, english, chinese)")
    grade: str = Field(default="", description="年级 (grade1, grade2, grade3)")
    tags: List[str] = Field(default_factory=list, description="标签列表，如：微积分、力学、有机化学等")
    source: str = Field(default="manual", description="来源 (upload, generate, manual)")
    upload_file_id: Optional[str] = Field(None, description="上传文件ID（如果来自文件上传）")
    
    # 原有字段
    knowledge_points: List[str] = Field(default_factory=list, description="相关知识点ID列表")
    related_questions: List[RelatedQuestion] = Field(default_factory=list, description="相关问题（用于扩展）")
    reference_answer: ReferenceAnswer = Field(..., description="参考答案")
    
    # 新增：视频推荐
    video_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="推荐视频列表")
    
    # 新增：选项（用于选择题）
    options: Optional[Dict[str, str]] = Field(None, description="选择题选项，格式：{'A': '选项内容', 'B': '...'}")


class UploadedFile(BaseModel):
    """上传文件模型"""
    id: str = Field(..., description="文件唯一标识符")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型 (pdf, image)")
    file_path: str = Field(..., description="文件存储路径")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")
    file_size: int = Field(..., description="文件大小（字节）")
    processed: bool = Field(default=False, description="是否已处理")
    processing_status: str = Field(default="pending", description="处理状态 (pending, processing, completed, failed)")
    extracted_text: Optional[str] = Field(None, description="提取的文本")
    questions: List[str] = Field(default_factory=list, description="提取的题目ID列表")
    error_message: Optional[str] = Field(None, description="错误信息")


class FlashCard(BaseModel):
    """抽认卡模型（支持间隔重复学习）"""
    id: str = Field(..., description="抽认卡唯一标识符")
    question_id: str = Field(..., description="关联的题目ID")
    front: str = Field(..., description="正面内容（问题）")
    back: str = Field(..., description="背面内容（答案）")
    subject: str = Field(..., description="科目")
    tags: List[str] = Field(default_factory=list, description="标签")
    difficulty: int = Field(1, description="难度")
    
    # 间隔重复算法相关（SM-2算法）
    review_count: int = Field(default=0, description="复习次数")
    ease_factor: float = Field(default=2.5, description="易度因子（SM-2算法）")
    interval: int = Field(default=1, description="复习间隔（天）")
    last_review: Optional[datetime] = Field(None, description="上次复习时间")
    next_review: Optional[datetime] = Field(None, description="下次复习时间")
    quality: int = Field(default=0, description="上次复习质量 (0-5)")


class PomodoroSession(BaseModel):
    """番茄钟会话模型"""
    id: str = Field(..., description="会话唯一标识符")
    user_id: str = Field(default="default", description="用户ID")
    subject: str = Field(..., description="学习科目")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    duration: int = Field(25, description="时长（分钟）")
    completed: bool = Field(default=False, description="是否完成")
    break_time: int = Field(default=5, description="休息时间（分钟）")
    question_ids: List[str] = Field(default_factory=list, description="学习的题目ID列表")
    end_time: Optional[datetime] = Field(None, description="结束时间")


# 数据库模式
class DatabaseSchema:
    """数据库模式定义"""
    
    @staticmethod
    def get_chapter_schema() -> Dict[str, Any]:
        """获取章节集合的模式"""
        return {
            "bsonType": "object",
            "required": ["id", "title"],
            "properties": {
                "id": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "parent_id": {"bsonType": ["string", "null"]},
                "order": {"bsonType": "int"},
                "description": {"bsonType": "string"},
                "knowledge_points": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "sub_chapters": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                }
            }
        }
    
    @staticmethod
    def get_knowledge_point_schema() -> Dict[str, Any]:
        """获取知识点集合的模式"""
        return {
            "bsonType": "object",
            "required": ["id", "title", "chapter_id"],
            "properties": {
                "id": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "chapter_id": {"bsonType": "string"},
                "description": {"bsonType": "string"},
                "related_points": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["id", "relation_type"],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "relation_type": {"bsonType": "string"}
                        }
                    }
                },
                "questions": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                }
            }
        }
    
    @staticmethod
    def get_question_schema() -> Dict[str, Any]:
        """获取问题集合的模式（扩展版）"""
        return {
            "bsonType": "object",
            "required": ["id", "title", "content", "type", "reference_answer", "subject"],
            "properties": {
                "id": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "content": {"bsonType": "string"},
                "difficulty": {"bsonType": "int"},
                "type": {"bsonType": "string"},
                "subject": {"bsonType": "string"},
                "grade": {"bsonType": "string"},
                "tags": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "source": {"bsonType": "string"},
                "upload_file_id": {"bsonType": ["string", "null"]},
                "options": {
                    "bsonType": ["object", "null"],
                    "additionalProperties": {"bsonType": "string"}
                },
                "knowledge_points": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "related_questions": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["id", "relation_type"],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "relation_type": {"bsonType": "string"}
                        }
                    }
                },
                "reference_answer": {
                    "bsonType": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {"bsonType": "string"},
                        "key_points": {
                            "bsonType": "array",
                            "items": {"bsonType": "string"}
                        },
                        "explanation": {"bsonType": "string"}
                    }
                },
                "video_recommendations": {
                    "bsonType": "array",
                    "items": {"bsonType": "object"}
                }
            }
        }
    
    @staticmethod
    def get_uploaded_file_schema() -> Dict[str, Any]:
        """获取上传文件集合的模式"""
        return {
            "bsonType": "object",
            "required": ["id", "filename", "file_type", "file_path", "file_size"],
            "properties": {
                "id": {"bsonType": "string"},
                "filename": {"bsonType": "string"},
                "file_type": {"bsonType": "string"},
                "file_path": {"bsonType": "string"},
                "upload_time": {"bsonType": "date"},
                "file_size": {"bsonType": "int"},
                "processed": {"bsonType": "bool"},
                "processing_status": {"bsonType": "string"},
                "extracted_text": {"bsonType": ["string", "null"]},
                "questions": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "error_message": {"bsonType": ["string", "null"]}
            }
        }
    
    @staticmethod
    def get_flashcard_schema() -> Dict[str, Any]:
        """获取抽认卡集合的模式"""
        return {
            "bsonType": "object",
            "required": ["id", "question_id", "front", "back", "subject"],
            "properties": {
                "id": {"bsonType": "string"},
                "question_id": {"bsonType": "string"},
                "front": {"bsonType": "string"},
                "back": {"bsonType": "string"},
                "subject": {"bsonType": "string"},
                "tags": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "difficulty": {"bsonType": "int"},
                "review_count": {"bsonType": "int"},
                "ease_factor": {"bsonType": "double"},
                "interval": {"bsonType": "int"},
                "last_review": {"bsonType": ["date", "null"]},
                "next_review": {"bsonType": ["date", "null"]},
                "quality": {"bsonType": "int"}
            }
        }
    
    @staticmethod
    def get_pomodoro_session_schema() -> Dict[str, Any]:
        """获取番茄钟会话集合的模式"""
        return {
            "bsonType": "object",
            "required": ["id", "subject", "start_time", "duration"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "subject": {"bsonType": "string"},
                "start_time": {"bsonType": "date"},
                "duration": {"bsonType": "int"},
                "completed": {"bsonType": "bool"},
                "break_time": {"bsonType": "int"},
                "question_ids": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"}
                },
                "end_time": {"bsonType": ["date", "null"]}
            }
        }
