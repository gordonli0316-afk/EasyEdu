"""
抽认卡服务
实现SM-2间隔重复算法，帮助用户高效复习
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid


class FlashCardService:
    """抽认卡服务，实现SM-2间隔重复算法"""
    
    def create_flashcard_from_question(self, question: Dict) -> Dict:
        """
        从题目创建抽认卡
        
        Args:
            question: 题目字典
            
        Returns:
            抽认卡字典
        """
        return {
            "id": f"fc_{question.get('id', uuid.uuid4().hex[:8])}",
            "question_id": question.get("id", ""),
            "front": self._generate_front(question),
            "back": self._generate_back(question),
            "subject": question.get("subject", ""),
            "tags": question.get("tags", []),
            "difficulty": question.get("difficulty", 3),
            "review_count": 0,
            "ease_factor": 2.5,
            "interval": 1,
            "last_review": None,
            "next_review": datetime.now(),
            "quality": 0
        }
    
    def _generate_front(self, question: Dict) -> str:
        """生成抽认卡正面内容（问题）"""
        content = question.get("content", "")
        title = question.get("title", "")
        
        # 如果是选择题，包含选项
        if question.get("type") == "choice" and question.get("options"):
            options_text = "\n".join([f"{k}. {v}" for k, v in question["options"].items()])
            return f"{title}\n\n{content}\n\n{options_text}"
        
        return f"{title}\n\n{content}"
    
    def _generate_back(self, question: Dict) -> str:
        """生成抽认卡背面内容（答案和解析）"""
        answer = question.get("reference_answer", {})
        answer_content = answer.get("content", "")
        explanation = answer.get("explanation", "")
        key_points = answer.get("key_points", [])
        
        result = f"答案：{answer_content}"
        
        if key_points:
            result += f"\n\n关键点：\n" + "\n".join([f"• {kp}" for kp in key_points])
        
        if explanation:
            result += f"\n\n解析：{explanation}"
        
        return result
    
    def review_flashcard(self, card: Dict, quality: int) -> Dict:
        """
        复习抽认卡并更新间隔（SM-2算法）
        
        Args:
            card: 抽认卡字典
            quality: 复习质量 (0-5)
                0: 完全忘记
                1: 困难，需要提示
                2: 困难，但能回忆起来
                3: 一般
                4: 容易
                5: 非常简单
                
        Returns:
            更新后的抽认卡字典
        """
        if quality < 0 or quality > 5:
            raise ValueError("quality must be between 0 and 5")
        
        # SM-2算法
        if quality < 3:
            # 回答错误，重置
            card["interval"] = 1
            card["ease_factor"] = max(1.3, card["ease_factor"] - 0.2)
        else:
            # 回答正确
            if card["review_count"] == 0:
                card["interval"] = 1
            elif card["review_count"] == 1:
                card["interval"] = 6
            else:
                card["interval"] = int(card["interval"] * card["ease_factor"])
            
            # 更新易度因子
            card["ease_factor"] = card["ease_factor"] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            card["ease_factor"] = max(1.3, card["ease_factor"])
        
        # 更新复习信息
        card["review_count"] += 1
        card["quality"] = quality
        card["last_review"] = datetime.now()
        card["next_review"] = datetime.now() + timedelta(days=card["interval"])
        
        return card
    
    def get_due_flashcards(self, flashcards: List[Dict]) -> List[Dict]:
        """
        获取需要复习的抽认卡
        
        Args:
            flashcards: 抽认卡列表
            
        Returns:
            需要复习的抽认卡列表
        """
        now = datetime.now()
        due_cards = []
        
        for card in flashcards:
            next_review = card.get("next_review")
            if next_review:
                # 如果是datetime对象，直接比较
                if isinstance(next_review, datetime):
                    if next_review <= now:
                        due_cards.append(card)
                # 如果是字符串，需要转换
                elif isinstance(next_review, str):
                    try:
                        next_review_dt = datetime.fromisoformat(next_review.replace('Z', '+00:00'))
                        if next_review_dt <= now:
                            due_cards.append(card)
                    except:
                        # 如果解析失败，当作需要复习
                        due_cards.append(card)
            else:
                # 如果没有下次复习时间，当作新卡片
                due_cards.append(card)
        
        return due_cards
    
    def get_review_statistics(self, flashcards: List[Dict]) -> Dict:
        """
        获取复习统计信息
        
        Args:
            flashcards: 抽认卡列表
            
        Returns:
            统计信息字典
        """
        total = len(flashcards)
        due = len(self.get_due_flashcards(flashcards))
        reviewed = sum(1 for card in flashcards if card.get("review_count", 0) > 0)
        mastered = sum(1 for card in flashcards 
                       if card.get("ease_factor", 0) > 2.5 and card.get("review_count", 0) >= 3)
        
        return {
            "total": total,
            "due": due,
            "reviewed": reviewed,
            "new": total - reviewed,
            "mastered": mastered,
            "mastery_rate": mastered / total if total > 0 else 0
        }
    
    def get_flashcards_by_subject(self, flashcards: List[Dict], subject: str) -> List[Dict]:
        """按科目筛选抽认卡"""
        return [card for card in flashcards if card.get("subject") == subject]
    
    def get_flashcards_by_tags(self, flashcards: List[Dict], tags: List[str]) -> List[Dict]:
        """按标签筛选抽认卡"""
        result = []
        for card in flashcards:
            card_tags = card.get("tags", [])
            if any(tag in card_tags for tag in tags):
                result.append(card)
        return result
