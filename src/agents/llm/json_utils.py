"""从模型输出里把 JSON 抠出来并校验，给 router 的结构化输出用。"""
import json
import re
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Extract the first JSON object from model output (handles markdown fences)."""
    if not text or not text.strip():
        return None

    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = cleaned[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def parse_and_validate(text: str, model: Type[T]) -> Optional[T]:
    """Parse JSON from text and validate with a Pydantic model."""
    data = extract_json_object(text)
    if data is None:
        return None
    try:
        return model.model_validate(data)
    except ValidationError:
        return None


def validate_dict(data: Dict[str, Any], model: Type[T]) -> Optional[T]:
    try:
        return model.model_validate(data)
    except ValidationError:
        return None
