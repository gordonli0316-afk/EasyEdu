"""
题目扩展功能API端点
包括题目生成、导出等功能
"""

from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.services.question_generator import QuestionGenerator
from src.services.question_exporter import QuestionExporter
from web.services.qa_service import QAService

router = APIRouter()
question_generator = QuestionGenerator()
question_exporter = QuestionExporter()
qa_service = QAService()


class GenerateQuestionRequest(BaseModel):
    """生成题目请求模型"""
    question_id: str = Field(..., description="原始题目ID")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="目标难度（可选）")
    variations: int = Field(1, ge=1, le=10, description="生成数量")


class GenerateByTopicRequest(BaseModel):
    """按主题生成题目请求模型"""
    topic: str = Field(..., description="主题/知识点")
    subject: str = Field(..., description="科目")
    difficulty: int = Field(3, ge=1, le=5, description="难度级别")
    count: int = Field(5, ge=1, le=20, description="生成数量")
    question_type: Optional[str] = Field(None, description="题目类型（可选）")


@router.post("/questions/generate", tags=["questions_extended"])
async def generate_similar_questions(request: GenerateQuestionRequest):
    """
    生成相似题目
    
    Args:
        request: 生成请求
    """
    try:
        qa_system = qa_service.get_qa_system()
        original_question = qa_system.get_question_detail(request.question_id)
        
        if not original_question:
            raise HTTPException(status_code=404, detail=f"题目未找到: {request.question_id}")
        
        generated_questions = await question_generator.generate_similar_question(
            original_question,
            difficulty=request.difficulty,
            variations=request.variations
        )
        
        return {
            "original_question_id": request.question_id,
            "generated_questions": generated_questions,
            "count": len(generated_questions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/questions/generate-by-topic", tags=["questions_extended"])
async def generate_questions_by_topic(request: GenerateByTopicRequest):
    """
    根据主题生成题目
    
    Args:
        request: 生成请求
    """
    try:
        generated_questions = await question_generator.generate_questions_by_topic(
            topic=request.topic,
            subject=request.subject,
            difficulty=request.difficulty,
            count=request.count,
            question_type=request.question_type
        )
        
        return {
            "topic": request.topic,
            "subject": request.subject,
            "generated_questions": generated_questions,
            "count": len(generated_questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/export/formats", tags=["questions_extended"])
async def get_export_formats():
    """获取支持的导出格式"""
    formats = [
        {
            "id": "json",
            "name": "JSON",
            "description": "JSON格式，便于程序处理",
            "available": True
        },
        {
            "id": "txt",
            "name": "文本",
            "description": "纯文本格式",
            "available": True
        },
        {
            "id": "markdown",
            "name": "Markdown",
            "description": "Markdown格式，便于阅读",
            "available": True
        },
        {
            "id": "word",
            "name": "Word文档",
            "description": "Microsoft Word格式 (.docx)",
            "available": question_exporter.__class__.__module__ and "docx" in str(question_exporter.__class__.__module__)
        },
        {
            "id": "excel",
            "name": "Excel表格",
            "description": "Microsoft Excel格式 (.xlsx)",
            "available": question_exporter.__class__.__module__ and "openpyxl" in str(question_exporter.__class__.__module__)
        },
        {
            "id": "pdf",
            "name": "PDF文档",
            "description": "PDF格式，便于打印和分享",
            "available": question_exporter.__class__.__module__ and "reportlab" in str(question_exporter.__class__.__module__)
        }
    ]
    
    # 检查实际可用性
    try:
        from src.services.question_exporter import DOCX_AVAILABLE, EXCEL_AVAILABLE, PDF_AVAILABLE
        for fmt in formats:
            if fmt["id"] == "word":
                fmt["available"] = DOCX_AVAILABLE
            elif fmt["id"] == "excel":
                fmt["available"] = EXCEL_AVAILABLE
            elif fmt["id"] == "pdf":
                fmt["available"] = PDF_AVAILABLE
    except:
        pass
    
    return {"formats": formats}


@router.post("/questions/export", tags=["questions_extended"])
async def export_questions(
    question_ids: Optional[List[str]] = None,
    format: str = "json",
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """
    导出题目
    
    Args:
        question_ids: 题目ID列表（如果为空，则根据subject和tags筛选）
        format: 导出格式 (json, txt, markdown, word, excel, pdf)
        subject: 科目筛选（可选）
        tags: 标签筛选（可选）
    """
    try:
        qa_system = qa_service.get_qa_system()
        
        # 获取题目
        if question_ids:
            questions = []
            for qid in question_ids:
                q = qa_system.get_question_detail(qid)
                if q:
                    questions.append(q)
        else:
            # 根据条件筛选
            if hasattr(qa_system, 'get_questions_by_subject_and_tags'):
                questions = qa_system.get_questions_by_subject_and_tags(
                    subject=subject,
                    tags=tags
                )
                # 获取完整题目详情
                full_questions = []
                for q in questions:
                    detail = qa_system.get_question_detail(q["id"])
                    if detail:
                        full_questions.append(detail)
                questions = full_questions
            else:
                # 兼容旧版本
                questions = []
        
        if not questions:
            raise HTTPException(status_code=404, detail="未找到符合条件的题目")
        
        # 根据格式导出
        if format == "json":
            filepath = question_exporter.export_to_json(questions)
            return {"filepath": filepath, "format": "json", "count": len(questions)}
        
        elif format == "txt":
            filepath = question_exporter.export_to_txt(questions)
            return {"filepath": filepath, "format": "txt", "count": len(questions)}
        
        elif format == "markdown":
            filepath = question_exporter.export_to_markdown(questions)
            return {"filepath": filepath, "format": "markdown", "count": len(questions)}
        
        elif format == "word":
            try:
                filepath = question_exporter.export_to_word(questions)
                return {"filepath": filepath, "format": "word", "count": len(questions)}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        elif format == "excel":
            try:
                filepath = question_exporter.export_to_excel(questions)
                return {"filepath": filepath, "format": "excel", "count": len(questions)}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        elif format == "pdf":
            try:
                filepath = question_exporter.export_to_pdf(questions)
                return {"filepath": filepath, "format": "pdf", "count": len(questions)}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/export/{filepath:path}", tags=["questions_extended"])
async def download_exported_file(filepath: str):
    """
    下载导出的文件
    
    Args:
        filepath: 文件路径（相对于导出目录）
    """
    from fastapi.responses import FileResponse
    import os
    
    full_path = question_exporter.output_dir / filepath
    if not full_path.exists() or not str(full_path).startswith(str(question_exporter.output_dir)):
        raise HTTPException(status_code=404, detail="文件未找到")
    
    return FileResponse(
        path=str(full_path),
        filename=os.path.basename(filepath),
        media_type='application/octet-stream'
    )
