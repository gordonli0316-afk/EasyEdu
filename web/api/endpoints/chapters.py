from fastapi import APIRouter, HTTPException
from typing import Optional
from web.services.qa_service import QAService

router = APIRouter()
qa_service = QAService()

@router.get("/chapters", tags=["chapters"])
async def get_chapters(subject: Optional[str] = None):
    """
    获取所有章节
    
    Args:
        subject: 科目筛选（可选）：math, physics, chemistry, biology, english, chinese
    """
    try:
        qa_system = qa_service.get_qa_system()
        chapters = qa_system.get_chapters(subject=subject)
        return chapters
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AP/IB 题库 slug -> 友好展示名
SUBJECT_NAMES = {
    "ap_cs_principles_hare_4th": "AP Computer Science Principles",
    "ap_physics_5_steps_to_a_5_2023": "AP Physics",
    "ap_statistics_the_practice_of_statistics": "AP Statistics",
    "ib_biology_hodder": "IB Biology",
    "ib_computer_science_hodder": "IB Computer Science",
    "ib_math_aa_hl_analysis_and_approaches": "IB Math AA HL",
    # 兼容旧高中数据
    "math": "数学", "physics": "物理", "chemistry": "化学",
    "biology": "生物", "english": "英语", "chinese": "语文",
    "data_structure": "数据结构",
}

# 用于美化未知 slug 的关键词
_UPPER_TOKENS = {"ap", "ib", "hl", "sl", "cs", "aa", "ai"}


def _prettify_subject(slug: str) -> str:
    """把未知 slug 变成大致可读的名字，如 ib_xx_yy -> IB Xx Yy。"""
    words = slug.replace("-", "_").split("_")
    out = []
    for w in words:
        if not w:
            continue
        out.append(w.upper() if w.lower() in _UPPER_TOKENS else w.capitalize())
    return " ".join(out) or slug


@router.get("/subjects", tags=["chapters"])
async def get_subjects():
    """获取所有科目列表（带友好展示名）"""
    try:
        qa_system = qa_service.get_qa_system()
        if hasattr(qa_system, 'get_all_subjects'):
            subjects = qa_system.get_all_subjects()
        else:
            subjects = []

        result = []
        for sub_id in subjects:
            result.append({
                "id": sub_id,
                "name": SUBJECT_NAMES.get(sub_id) or _prettify_subject(sub_id),
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 