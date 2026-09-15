"""
文件上传和处理服务
支持PDF和图片上传，OCR文本提取，以及使用LLM从文本中提取题目
"""

import os
import uuid
import json
import asyncio
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

# PDF 提取器：懒加载，避免在没有 PyMuPDF/PaddleOCR 的机器上（如本地 Mac）import 失败
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from data.ds_data.data_processing.pdf_extractor import PDFExtractor
    PDF_EXTRACTOR_AVAILABLE = True
except Exception:
    PDFExtractor = None
    PDF_EXTRACTOR_AVAILABLE = False
    print("警告: PDFExtractor 不可用（缺少 PyMuPDF/pdfplumber 等依赖），PDF 提取功能将不可用")

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("警告: PaddleOCR未安装，图片OCR功能将不可用")

try:
    from langchain_openai import ChatOpenAI
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("警告: LangChain未安装，题目提取功能将不可用")


class FileUploadService:
    """文件上传和处理服务"""
    
    def __init__(self, upload_dir: str = "data/uploads", use_ocr: bool = True):
        """
        初始化文件上传服务
        
        Args:
            upload_dir: 文件上传存储目录
            use_ocr: 是否使用OCR（需要PaddleOCR）
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.use_ocr = use_ocr and PADDLEOCR_AVAILABLE
        
        # 初始化OCR（如果需要）
        if self.use_ocr:
            try:
                self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            except Exception as e:
                print(f"OCR初始化失败: {e}")
                self.use_ocr = False
        
        # 初始化LLM（用于题目提取）
        self.llm = None
        if LLM_AVAILABLE:
            try:
                api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
                base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
                model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
                
                if api_key:
                    self.llm = ChatOpenAI(
                        model=model,
                        base_url=base_url,
                        api_key=api_key,
                        temperature=0.3
                    )
            except Exception as e:
                print(f"LLM初始化失败: {e}")
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> Dict:
        """
        保存上传的文件
        
        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            
        Returns:
            文件信息字典
        """
        file_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix.lower()
        
        # 确定文件类型
        if file_ext == '.pdf':
            file_type = 'pdf'
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            file_type = 'image'
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}。支持的类型: .pdf, .jpg, .jpeg, .png, .bmp, .gif")
        
        # 验证文件大小（限制100MB）
        max_size = 100 * 1024 * 1024  # 100MB
        if len(file_content) > max_size:
            raise ValueError(f"文件大小超过限制（最大100MB）")
        
        # 保存文件
        file_path = self.upload_dir / f"{file_id}{file_ext}"
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return {
            "id": file_id,
            "filename": filename,
            "file_type": file_type,
            "file_path": str(file_path),
            "upload_time": datetime.now(),
            "file_size": len(file_content),
            "processed": False,
            "processing_status": "pending"
        }
    
    async def extract_text_from_file(self, file_info: Dict) -> str:
        """
        从文件中提取文本
        
        Args:
            file_info: 文件信息字典
            
        Returns:
            提取的文本内容
        """
        file_path = file_info["file_path"]
        file_type = file_info["file_type"]
        
        if file_type == "pdf":
            if not PDF_EXTRACTOR_AVAILABLE:
                raise RuntimeError(
                    "PDF 提取依赖未安装（PyMuPDF/pdfplumber）。请在带这些依赖的环境运行，或安装后重试。"
                )
            # 使用PDFExtractor
            output_dir = self.upload_dir / file_info["id"]
            output_dir.mkdir(exist_ok=True)
            
            # 尝试判断是否为扫描版PDF
            is_scanned = await self._is_scanned_pdf(file_path)
            
            extractor = PDFExtractor(
                file_path,
                str(output_dir),
                is_scanned=is_scanned,
                lang='ch'
            )
            
            # 提取文本
            extractor.extract_text()
            
            # 读取提取的文本
            text_files = sorted((output_dir / "text").glob("*.txt"))
            all_text = ""
            for text_file in text_files:
                try:
                    with open(text_file, 'r', encoding='utf-8') as f:
                        all_text += f.read() + "\n"
                except Exception as e:
                    print(f"读取文本文件失败 {text_file}: {e}")
            
            return all_text.strip()
        
        elif file_type == "image":
            # 使用OCR识别图片
            if not self.use_ocr:
                raise ValueError("OCR功能不可用，无法处理图片文件")
            
            result = self.ocr.ocr(file_path)
            text = ""
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text += line[1][0] + "\n"
            return text.strip()
        
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    async def _is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        简单判断PDF是否为扫描版
        可以通过尝试提取文本来判断
        """
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) > 0:
                    text = pdf.pages[0].extract_text()
                    # 如果提取的文本很少，可能是扫描版
                    return text is None or len(text.strip()) < 50
        except:
            pass
        return True  # 默认当作扫描版处理
    
    async def extract_questions_from_text(
        self, 
        text: str, 
        subject: Optional[str] = None
    ) -> List[Dict]:
        """
        从文本中提取题目（使用LLM）
        
        Args:
            text: 提取的文本内容
            subject: 科目（可选，如果不提供会尝试自动识别）
            
        Returns:
            提取的题目列表
        """
        if not self.llm:
            raise ValueError("LLM未初始化，无法提取题目。请设置DEEPSEEK_API_KEY或OPENAI_API_KEY环境变量")
        
        # 如果文本太长，分段处理
        max_chunk_size = 5000  # 每次处理5000字符
        all_questions = []
        
        # 分段处理
        for i in range(0, len(text), max_chunk_size):
            chunk = text[i:i + max_chunk_size]
            questions = await self._extract_questions_from_chunk(chunk, subject)
            all_questions.extend(questions)
        
        return all_questions
    
    async def _extract_questions_from_chunk(
        self, 
        text_chunk: str, 
        subject: Optional[str] = None
    ) -> List[Dict]:
        """从文本块中提取题目"""
        
        # 如果没有指定科目，尝试自动识别
        if not subject:
            subject = await self._detect_subject(text_chunk)
        
        prompt = f"""你是一个题目提取专家。请从以下文本中识别并提取所有题目。

要求：
1. 识别题目的类型（选择题choice、填空题fill、解答题essay、计算题calculation）
2. 提取题目的完整内容，包括题目、选项（如果有）、答案
3. 识别题目所属的科目和知识点
4. 为题目添加合适的标签（如：微积分、力学、有机化学等）
5. 评估题目难度（1-5，1最简单，5最难）

文本内容：
{text_chunk[:4000]}  # 限制长度避免超出token限制

请以JSON格式返回，格式如下：
{{
    "questions": [
        {{
            "title": "题目标题（简短描述）",
            "content": "题目完整内容",
            "type": "choice/fill/essay/calculation",
            "options": {{"A": "选项A", "B": "选项B", ...}},  # 如果是选择题
            "answer": "答案",
            "explanation": "解析（可选）",
            "tags": ["标签1", "标签2"],
            "difficulty": 3,
            "subject": "{subject or 'unknown'}",
            "knowledge_points": ["知识点1", "知识点2"]
        }}
    ]
}}

只返回JSON，不要其他文字。如果文本中没有题目，返回 {{"questions": []}}。
"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            # 尝试提取JSON（可能包含markdown代码块）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            questions = result.get("questions", [])
            
            # 为每个题目添加ID和默认值
            for q in questions:
                q.setdefault("id", f"q_{uuid.uuid4().hex[:8]}")
                q.setdefault("source", "upload")
                q.setdefault("grade", "")
                if "reference_answer" not in q:
                    q["reference_answer"] = {
                        "content": q.get("answer", ""),
                        "explanation": q.get("explanation", ""),
                        "key_points": []
                    }
            
            return questions
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"响应内容: {content[:500]}")
            return []
        except Exception as e:
            print(f"题目提取失败: {e}")
            return []
    
    async def _detect_subject(self, text: str) -> str:
        """
        自动识别文本所属科目
        
        Returns:
            科目代码 (math, physics, chemistry, biology, english, chinese)
        """
        if not self.llm:
            return "unknown"
        
        prompt = f"""请判断以下文本内容最可能属于哪个高中科目。

科目选项：
- math: 数学
- physics: 物理
- chemistry: 化学
- biology: 生物
- english: 英语
- chinese: 语文

文本内容（前500字）：
{text[:500]}

只返回科目代码（如：math），不要其他文字。"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            subject = response.content.strip().lower()
            
            # 验证科目代码
            valid_subjects = ["math", "physics", "chemistry", "biology", "english", "chinese"]
            if subject in valid_subjects:
                return subject
        except:
            pass
        
        return "unknown"

