#!/usr/bin/env python3
"""
🔍 키워드 파서 (업무 10번)

사용자 입력에서 의도 추출
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    """파싱된 명령 데이터"""
    intent: Optional[str]          # SYNC, STATUS, APPROVE, REJECT, HELP, etc.
    food_id: Optional[str] = None  # 영문 food_id (e.g., "banana")
    food_kr: Optional[str] = None  # 한글 음식명 (e.g., "바나나")
    raw_text: str = ""             # 원본 텍스트
    confidence: float = 0.0        # 신뢰도 (0.0~1.0)


INTENT_KEYWORDS = {
    "SYNC": ["동기화", "싱크", "sync", "연동", "맞춰"],
    "STATUS": ["상태", "확인", "뭐야", "어때", "현황", "status"],
    "APPROVE": ["승인", "ok", "ㅇㅋ", "ㄱㄱ", "게시", "올려"],
    "REJECT": ["반려", "취소", "삭제", "안돼", "ㄴㄴ", "reject"],
    "HELP": ["도움", "명령어", "help", "뭐", "어떻게"],
    "CREATE": ["생성", "만들어", "create", "시작", "제작"],
    "LIST": ["목록", "리스트", "list", "전체", "보여"],
    "COVER": ["표지", "커버", "cover", "썸네일"],
    "BODY": ["본문", "body", "내용", "이미지"],
}

ENTITY_PATTERNS = {
    "food_id": r'\b([a-z_]{3,20})\b',  # 영문 음식명
    "food_kr": r'([가-힣]{2,10})',      # 한글 음식명
    "number": r'(\d{1,3})',             # 번호
}


def parse_intent(text: str) -> Optional[str]:
    """
    텍스트에서 의도 추출

    Returns:
        의도 문자열 (SYNC, STATUS, APPROVE, etc.) 또는 None
    """
    text_lower = text.lower()

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return intent

    return None


def extract_entities(text: str) -> dict:
    """
    텍스트에서 엔티티 추출

    Returns:
        {"food_id": "banana", "food_kr": "바나나", "number": "027"}
    """
    entities = {}

    for entity_type, pattern in ENTITY_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            entities[entity_type] = matches[0]

    return entities


def parse_command(text: str) -> ParsedCommand:
    """
    전체 명령어 파싱

    Returns:
        ParsedCommand 객체
    """
    intent = parse_intent(text)
    entities = extract_entities(text)

    # 신뢰도 계산
    confidence = 0.8 if intent else 0.0

    # food_id 추출 (영문 우선)
    food_id = entities.get("food_id")

    # 한글이면 영문으로 변환 시도
    food_kr = entities.get("food_kr")
    if food_kr and not food_id:
        from utils.entity_mapper import extract_food_id
        food_id = extract_food_id(food_kr)

    return ParsedCommand(
        intent=intent,
        food_id=food_id,
        food_kr=food_kr,
        raw_text=text,
        confidence=confidence
    )


# 테스트
if __name__ == "__main__":
    test_cases = [
        "바나나 상태 확인해줘",
        "027번 승인 ㅇㅋ",
        "동기화 해",
        "spinach 목록 보여줘",
        "도움말",
    ]

    for text in test_cases:
        intent, entities = parse_command(text)
        print(f"입력: {text}")
        print(f"  의도: {intent}")
        print(f"  엔티티: {entities}")
        print()
