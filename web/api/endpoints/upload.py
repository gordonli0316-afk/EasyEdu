"""
文件上传API端点
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Optional
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.services.file_upload_service import FileUploadService
from web.models.schemas import UploadedFileInfo, QuestionInfo

router = APIRouter()

# 初始化文件上传服务
upload_service = FileUploadService(upload_dir="data/uploads")

# 简单的内存存储（生产环境应使用数据库）
file_storage = {}


@router.post("/upload/file", response_model=UploadedFileInfo, tags=["upload"])
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    上传文件（PDF或图片）
    
    支持的文件类型：
    - PDF: .pdf
    - 图片: .jpg, .jpeg, .png, .bmp, .gif
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 保存文件
        file_info = await upload_service.save_uploaded_file(content, file.filename)
        
        # 存储文件信息
        file_storage[file_info["id"]] = file_info
        
        # 异步处理文件（提取文本和题目）
        if background_tasks:
            background_tasks.add_task(process_file_async, file_info["id"])
        else:
            # 如果没有background_tasks，同步处理（不推荐）
            await process_file_async(file_info["id"])
        
        return file_info
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


async def process_file_async(file_id: str):
    """异步处理文件：提取文本和题目"""
    if file_id not in file_storage:
        return
    
    file_info = file_storage[file_id]
    file_info["processing_status"] = "processing"
    
    try:
        # 提取文本
        text = await upload_service.extract_text_from_file(file_info)
        file_info["extracted_text"] = text
        
        if not text or len(text.strip()) < 10:
            file_info["processing_status"] = "failed"
            file_info["error_message"] = "未能从文件中提取到有效文本"
            return
        
        # 提取题目
        subject = await upload_service._detect_subject(text)
        questions = await upload_service.extract_questions_from_text(text, subject)
        
        # 保存题目（这里应该保存到数据库，暂时只存储ID）
        question_ids = []
        for q in questions:
            # TODO: 保存题目到数据库
            # question_id = save_question_to_database(q)
            question_id = q.get("id", f"q_{file_id}_{len(question_ids)}")
            question_ids.append(question_id)
        
        file_info["questions"] = question_ids
        file_info["processed"] = True
        file_info["processing_status"] = "completed"
        
    except Exception as e:
        file_info["processing_status"] = "failed"
        file_info["error_message"] = str(e)
        print(f"处理文件失败 {file_id}: {e}")


@router.get("/upload/files", response_model=List[UploadedFileInfo], tags=["upload"])
async def get_uploaded_files():
    """获取所有上传的文件列表"""
    return list(file_storage.values())


@router.get("/upload/{file_id}", response_model=UploadedFileInfo, tags=["upload"])
async def get_file_info(file_id: str):
    """获取文件信息和处理状态"""
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail=f"文件未找到: {file_id}")
    return file_storage[file_id]


@router.get("/upload/{file_id}/status", tags=["upload"])
async def get_file_status(file_id: str):
    """获取文件处理状态"""
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail=f"文件未找到: {file_id}")
    
    file_info = file_storage[file_id]
    return {
        "file_id": file_id,
        "status": file_info.get("processing_status", "unknown"),
        "processed": file_info.get("processed", False),
        "questions_count": len(file_info.get("questions", [])),
        "error_message": file_info.get("error_message")
    }


@router.get("/upload/{file_id}/questions", response_model=List[QuestionInfo], tags=["upload"])
async def get_extracted_questions(file_id: str):
    """获取从文件中提取的题目"""
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail=f"文件未找到: {file_id}")
    
    file_info = file_storage[file_id]
    if not file_info.get("processed"):
        raise HTTPException(status_code=400, detail="文件尚未处理完成")
    
    # TODO: 从数据库获取题目详情
    # questions = get_questions_by_ids(file_info["questions"])
    # return questions
    
    return []  # 暂时返回空列表


@router.delete("/upload/{file_id}", tags=["upload"])
async def delete_file(file_id: str):
    """删除上传的文件"""
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail=f"文件未找到: {file_id}")
    
    file_info = file_storage[file_id]
    
    # 删除文件
    try:
        file_path = file_info.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"删除文件失败: {e}")
    
    # 从存储中删除
    del file_storage[file_id]
    
    return {"message": "文件已删除", "file_id": file_id}

