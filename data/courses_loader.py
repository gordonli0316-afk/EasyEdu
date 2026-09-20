"""
AP/IB 题库加载器。

读 ingest_textbooks.py 生成的 data/courses/<AP|IB>/<书>/ 结构：
    chapters.json
    questions/ch01.json ...
    knowledgepoints/ch01.json ...（或 all_knowledgepoints.json）

data/courses 为空时（例如刚 clone 下来还没跑过 ingest 脚本），自动改用仓库自带的
示例题库 data/seed_courses，保证网页开箱可用。

出题脚本给每本书的章节都编了 01~10，跨书会撞 ID，所以这里统一把章节 ID
改写成 "<course>_<书>_<原ID>" 这种全局唯一的形式，题目里的 chapter 字段也
跟着改。对外提供的方法跟原来的高中数据加载器一致，上层（KnowledgeQASystem、
网页）不用改。
"""
import hashlib
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional

# 正式题库（由 scripts/ingest_textbooks.py 生成，不进 git）
DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "courses"
# 随仓库发布的示例题库：当正式题库为空时自动兜底，保证网页开箱可用
SEED_DATA_DIR = Path(__file__).resolve().parent / "seed_courses"


class CoursesDataLoader:
    """读 data/courses 下的 AP/IB 题库；为空时回退到 data/seed_courses。"""

    def __init__(self, data_dir: str = None, seed_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.seed_dir = Path(seed_dir) if seed_dir else SEED_DATA_DIR
        self.source_dir: Optional[Path] = None

        # 每本书是一个 "subject"（用书的 slug 当 id）
        self.subjects: List[str] = []

        self.knowledge_index: Dict[str, dict] = {}
        self.knowledge_question_index: Dict[str, List[str]] = {}
        self.question_index: Dict[str, dict] = {}
        self.chapter_index: Dict[str, dict] = {}
        self.subject_chapters: Dict[str, List[dict]] = {}

    def data_fingerprint(self) -> str:
        """题库文件的轻量指纹，用于判断 pickle 缓存是否过期。"""
        digest = hashlib.sha256()
        for root in (self.data_dir, self.seed_dir):
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.json")):
                stat = path.stat()
                digest.update(f"{path}:{stat.st_size}:{int(stat.st_mtime)}".encode("utf-8"))
        return digest.hexdigest()[:16]

    # ------------------------------------------------------------------ #
    # 加载
    # ------------------------------------------------------------------ #
    def load_all_subjects(self):
        print("开始加载 AP/IB 题库...")
        self._load_tree(self.data_dir)

        # 正式题库为空（例如刚 clone 下来还没有跑过 ingest 脚本）时，用内置示例题库兜底
        if not self.chapter_index and self.seed_dir.exists():
            print(f"ℹ️  {self.data_dir} 中没有题库，改用内置示例题库 {self.seed_dir}")
            self._load_tree(self.seed_dir)

        print(f"\n✅ AP/IB 题库加载完成")
        print(f"   - 数据源: {self.source_dir}")
        print(f"   - 科目(书)数: {len(self.subjects)}")
        print(f"   - 章节数: {len(self.chapter_index)}")
        print(f"   - 题目数: {len(self.question_index)}")
        print(f"   - 知识点数: {len(self.knowledge_index)}")

    def _load_tree(self, root: Path) -> int:
        order = 0
        if not root.exists():
            return order
        for course_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            course = course_dir.name  # AP / IB
            if course.lower() not in ("ap", "ib"):
                continue
            for subject_dir in sorted(p for p in course_dir.iterdir() if p.is_dir()):
                slug = subject_dir.name
                prefix = f"{course.lower()}_{slug}"
                order = self._load_book(course, slug, subject_dir, prefix, order)
        if order and self.source_dir is None:
            self.source_dir = root
        return order

    def _load_book(self, course: str, slug: str, book_dir: Path, prefix: str, order: int) -> int:
        chapters_file = book_dir / "chapters.json"
        if not chapters_file.exists():
            return order

        if slug not in self.subjects:
            self.subjects.append(slug)

        # 章节：把原始 ID 改写成全局唯一
        chapters = json.loads(chapters_file.read_text(encoding="utf-8"))
        book_chapters = []
        for ch in chapters:
            orig_id = str(ch.get("id", ""))
            new_id = f"{prefix}_{orig_id}"
            ch["id"] = new_id
            ch["subject"] = slug
            ch["course"] = course
            order += 1
            ch["order"] = order
            self.chapter_index[new_id] = ch
            book_chapters.append(ch)
        self.subject_chapters[slug] = book_chapters

        # 知识点（优先合并文件）
        kp_dir = book_dir / "knowledgepoints"
        if kp_dir.exists():
            kp_files = list(kp_dir.glob("all_knowledgepoints.json")) or sorted(kp_dir.glob("*.json"))
            for kp_file in kp_files:
                for kp in json.loads(kp_file.read_text(encoding="utf-8")):
                    kp["subject"] = slug
                    kp["course"] = course
                    self.knowledge_index[kp["id"]] = kp
                    self.knowledge_question_index.setdefault(kp["id"], [])

        # 题目：chapter 字段跟着章节 ID 改写
        q_dir = book_dir / "questions"
        if q_dir.exists():
            for q_file in sorted(q_dir.glob("*.json")):
                for q in json.loads(q_file.read_text(encoding="utf-8")):
                    q["subject"] = slug
                    q["course"] = course
                    if "chapter" in q and q["chapter"] is not None:
                        q["chapter"] = f"{prefix}_{q['chapter']}"
                    self.question_index[q["id"]] = q
                    for kp_id in q.get("knowledge_points", []):
                        self.knowledge_question_index.setdefault(kp_id, [])
                        if q["id"] not in self.knowledge_question_index[kp_id]:
                            self.knowledge_question_index[kp_id].append(q["id"])
        return order

    # ------------------------------------------------------------------ #
    # 查询（与旧加载器同名，供上层调用）
    # ------------------------------------------------------------------ #
    def get_chapters_by_subject(self, subject_id: str) -> List[Dict]:
        return self.subject_chapters.get(subject_id, [])

    def get_all_chapters(self) -> List[Dict]:
        return list(self.chapter_index.values())

    def get_questions_by_chapter(self, chapter_id: str) -> List[Dict]:
        return [q for q in self.question_index.values() if q.get("chapter") == chapter_id]

    def get_questions_by_subject(self, subject_id: str) -> List[Dict]:
        return [q for q in self.question_index.values() if q.get("subject") == subject_id]

    def get_question(self, question_id: str) -> Optional[Dict]:
        return self.question_index.get(question_id)

    def get_knowledge_point(self, knowledge_id: str) -> Optional[Dict]:
        return self.knowledge_index.get(knowledge_id)

    def get_questions_by_knowledge(self, knowledge_id: str) -> List[Dict]:
        return [
            self.question_index[q_id]
            for q_id in self.knowledge_question_index.get(knowledge_id, [])
            if q_id in self.question_index
        ]

    # ------------------------------------------------------------------ #
    # 索引缓存
    # ------------------------------------------------------------------ #
    def save_indices(self, filepath: str):
        with open(filepath, "wb") as f:
            pickle.dump({
                "fingerprint": self.data_fingerprint(),
                "source_dir": str(self.source_dir) if self.source_dir else "",
                "subjects": self.subjects,
                "knowledge_index": self.knowledge_index,
                "knowledge_question_index": self.knowledge_question_index,
                "question_index": self.question_index,
                "chapter_index": self.chapter_index,
                "subject_chapters": self.subject_chapters,
            }, f)

    @classmethod
    def load_indices(cls, filepath: str):
        """读缓存；题库文件变了或缓存来自不同数据源时返回 None，让调用方重新读 JSON。"""
        try:
            with open(filepath, "rb") as f:
                data = pickle.load(f)
        except Exception as e:
            print(f"⚠️  题库缓存不可读（{e}），将重新读取题库")
            return None

        loader = cls()
        if data.get("fingerprint") != loader.data_fingerprint():
            print("⚠️  题库文件已变化，忽略过期缓存")
            return None

        loader.subjects = data.get("subjects", [])
        loader.knowledge_index = data.get("knowledge_index", {})
        loader.knowledge_question_index = data.get("knowledge_question_index", {})
        loader.question_index = data.get("question_index", {})
        loader.chapter_index = data.get("chapter_index", {})
        loader.subject_chapters = data.get("subject_chapters", {})
        source = data.get("source_dir") or ""
        loader.source_dir = Path(source) if source else None
        print(f"✅ AP/IB 题库索引已从 {filepath} 加载")
        return loader


if __name__ == "__main__":
    loader = CoursesDataLoader()
    loader.load_all_subjects()
