#!/usr/bin/env python3
"""
🗺️ Entity 매퍼 (업무 11번)

food_safety.json에서 자동 매핑 생성
한글 ↔ 영문 ↔ 폴더명 매핑
"""

import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
FOOD_SAFETY_PATH = PROJECT_ROOT / "config" / "settings" / "food_safety.json"
CONTENTS_DIR = PROJECT_ROOT / "contents"


class EntityMapper:
    def __init__(self):
        self.en_to_kr = {}
        self.kr_to_en = {}
        self.en_to_folder = {}
        self.folder_to_en = {}

        self._load_food_safety()
        self._scan_folders()

    def _load_food_safety(self):
        """food_safety.json에서 매핑 로드"""
        if not FOOD_SAFETY_PATH.exists():
            return

        data = json.loads(FOOD_SAFETY_PATH.read_text())

        # safe, caution, danger 리스트에서 추출
        for safety_level in ["safe", "caution", "danger"]:
            for food_id in data.get(safety_level, []):
                self.en_to_kr[food_id] = food_id  # 기본값 (한글 없으면 영문)

    def _scan_folders(self):
        """contents/ 폴더 스캔하여 매핑 생성"""
        if not CONTENTS_DIR.exists():
            return

        for folder in CONTENTS_DIR.iterdir():
            if not folder.is_dir() or folder.name.startswith("."):
                continue

            parts = folder.name.split("_")
            if len(parts) >= 2:
                # 027_spinach_시금치 형식
                food_en = parts[1]
                food_kr = parts[2] if len(parts) >= 3 else food_en

                self.en_to_folder[food_en] = folder.name
                self.folder_to_en[folder.name] = food_en
                self.en_to_kr[food_en] = food_kr
                self.kr_to_en[food_kr] = food_en

    def get_english(self, text: str) -> Optional[str]:
        """한글 또는 폴더명에서 영문 ID 추출"""
        # 직접 매칭
        if text in self.en_to_folder:
            return text

        # 한글 → 영문
        if text in self.kr_to_en:
            return self.kr_to_en[text]

        # 폴더명 → 영문
        if text in self.folder_to_en:
            return self.folder_to_en[text]

        # 부분 매칭
        text_lower = text.lower()
        for en, kr in self.en_to_kr.items():
            if text_lower in en or text in kr:
                return en

        return None

    def get_korean(self, food_id: str) -> Optional[str]:
        """영문 ID에서 한글명 추출"""
        return self.en_to_kr.get(food_id)

    def get_folder(self, food_id: str) -> Optional[str]:
        """영문 ID에서 폴더명 추출"""
        return self.en_to_folder.get(food_id)

    def find_folder_path(self, query: str) -> Optional[Path]:
        """쿼리에서 폴더 경로 찾기"""
        food_id = self.get_english(query)
        if not food_id:
            return None

        folder_name = self.get_folder(food_id)
        if not folder_name:
            return None

        folder_path = CONTENTS_DIR / folder_name
        if folder_path.exists():
            return folder_path

        return None


# 싱글톤 인스턴스
_mapper = None


def get_mapper() -> EntityMapper:
    global _mapper
    if _mapper is None:
        _mapper = EntityMapper()
    return _mapper


def extract_food_id(text: str) -> Optional[str]:
    """
    텍스트에서 food_id 추출 (한글/영문 자동 처리)

    Args:
        text: 입력 텍스트 (한글 또는 영문)

    Returns:
        영문 food_id 또는 None
    """
    mapper = get_mapper()
    return mapper.get_english(text)


def get_food_display_name(food_id: str) -> str:
    """
    food_id로 표시용 이름 생성 (한글명 우선)

    Args:
        food_id: 영문 food_id

    Returns:
        "한글명 (영문)" 형식 또는 영문만
    """
    mapper = get_mapper()
    kr = mapper.get_korean(food_id)
    if kr and kr != food_id:
        return f"{kr} ({food_id})"
    return food_id


# 테스트
if __name__ == "__main__":
    mapper = get_mapper()

    print("📊 매핑 통계:")
    print(f"  영문→한글: {len(mapper.en_to_kr)}개")
    print(f"  한글→영문: {len(mapper.kr_to_en)}개")
    print(f"  영문→폴더: {len(mapper.en_to_folder)}개")

    print("\n🔍 테스트:")
    tests = ["바나나", "spinach", "시금치", "potato"]
    for query in tests:
        en = mapper.get_english(query)
        kr = mapper.get_korean(en) if en else None
        folder = mapper.get_folder(en) if en else None
        print(f"  {query} → en:{en}, kr:{kr}, folder:{folder}")
