"""
题目生成服务
基于现有题目生成相似题目，或根据主题生成新题目
"""

import os
import json
import uuid
from typing import Dict, List, Optional

try:
    from langchain_openai import ChatOpenAI
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("警告: LangChain未安装，题目生成功能将不可用")


class QuestionGenerator:
    """题目生成服务"""
    
    def __init__(self):
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
                        temperature=0.7  # 稍高温度以增加创造性
                    )
            except Exception as e:
                print(f"LLM初始化失败: {e}")
    
    async def generate_similar_question(
        self, 
        original_question: Dict,
        difficulty: Optional[int] = None,
        variations: int = 1
    ) -> List[Dict]:
        """
        生成相似题目
        
        Args:
            original_question: 原始题目字典
            difficulty: 目标难度（如果为None，使用原题目难度）
            variations: 生成题目数量
            
        Returns:
            生成的题目列表
        """
        if not self.llm:
            raise ValueError("LLM未初始化，无法生成题目")
        
        target_difficulty = difficulty or original_question.get("difficulty", 3)
        
        prompt = f"""基于以下题目，生成{variations}道相似但不同的新题目。

原题目：
标题：{original_question.get('title', '')}
内容：{original_question.get('content', '')}
类型：{original_question.get('type', 'choice')}
难度：{original_question.get('difficulty', 3)}
科目：{original_question.get('subject', '')}
标签：{', '.join(original_question.get('tags', []))}
答案：{original_question.get('reference_answer', {}).get('content', '')}

要求：
1. 保持相同的知识点和难度级别（目标难度：{target_difficulty}）
2. 改变具体数值、场景或表述方式
3. 确保题目逻辑正确，答案准确
4. 如果是选择题，生成完整的选项（至少4个选项）
5. 提供详细的解析
6. 保持相同的科目和标签

请以JSON格式返回，格式如下：
{{
    "questions": [
        {{
            "title": "题目标题",
            "content": "题目完整内容",
            "type": "{original_question.get('type', 'choice')}",
            "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
            "answer": "答案",
            "explanation": "详细解析",
            "difficulty": {target_difficulty},
            "tags": {json.dumps(original_question.get('tags', []))},
            "subject": "{original_question.get('subject', '')}",
            "knowledge_points": {json.dumps(original_question.get('knowledge_points', []))}
        }}
    ]
}}

只返回JSON，不要其他文字。"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            # 提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            questions = result.get("questions", [])
            
            # 为每个题目添加ID和默认值
            for q in questions:
                q.setdefault("id", f"q_gen_{uuid.uuid4().hex[:8]}")
                q.setdefault("source", "generate")
                q.setdefault("grade", original_question.get("grade", ""))
                if "reference_answer" not in q:
                    q["reference_answer"] = {
                        "content": q.get("answer", ""),
                        "explanation": q.get("explanation", ""),
                        "key_points": []
                    }
            
            return questions
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return []
        except Exception as e:
            print(f"题目生成失败: {e}")
            return []
    
    async def generate_questions_by_topic(
        self,
        topic: str,
        subject: str,
        difficulty: int = 3,
        count: int = 5,
        question_type: Optional[str] = None
    ) -> List[Dict]:
        """
        根据主题生成题目
        
        Args:
            topic: 主题/知识点
            subject: 科目
            difficulty: 难度级别（1-5）
            count: 生成数量
            question_type: 题目类型（可选）
            
        Returns:
            生成的题目列表
        """
        if not self.llm:
            raise ValueError("LLM未初始化，无法生成题目")
        
        type_instruction = ""
        if question_type:
            type_instruction = f"题目类型：{question_type}。"
        
        prompt = f"""请生成{count}道关于"{topic}"的{subject}题目。

要求：
1. 难度级别：{difficulty}（1最简单，5最难）
2. {type_instruction}题目类型多样化（选择题、填空题、解答题）
3. 每道题都要有完整的答案和详细解析
4. 题目要符合高中教学大纲
5. 确保题目逻辑正确，答案准确

请以JSON格式返回，格式如下：
{{
    "questions": [
        {{
            "title": "题目标题",
            "content": "题目完整内容",
            "type": "choice/fill/essay/calculation",
            "options": {{"A": "...", "B": "...", ...}},  # 如果是选择题
            "answer": "答案",
            "explanation": "详细解析",
            "difficulty": {difficulty},
            "tags": ["{topic}"],
            "subject": "{subject}",
            "knowledge_points": ["{topic}"]
        }}
    ]
}}

只返回JSON，不要其他文字。"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            # 提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            questions = result.get("questions", [])
            
            # 为每个题目添加ID和默认值
            for q in questions:
                q.setdefault("id", f"q_topic_{uuid.uuid4().hex[:8]}")
                q.setdefault("source", "generate")
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
            return []
        except Exception as e:
            print(f"题目生成失败: {e}")
            return []
