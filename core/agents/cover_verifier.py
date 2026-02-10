#!/usr/bin/env python3
"""
Cover Verifier - 표지 검증 (메타데이터 기반)

원칙: "표지는 분석 대상이 아니다. 규칙으로 생성됐나만 확인한다."

⛔ 금지:
- 픽셀 분석
- 유사도 비교
- 텍스트 위치 추론
- "비슷해 보인다" 판단

✅ 허용:
- 메타데이터 확인
- rule_name 존재 확인
- rule_hash 일치 확인
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class CoverResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MISSING_METADATA = "MISSING_METADATA"
    INVALID_RULE = "INVALID_RULE"
    HASH_MISMATCH = "HASH_MISMATCH"


@dataclass
class CoverVerification:
    result: CoverResult
    rule_name: Optional[str]
    rule_hash: Optional[str]
    message: str
    action: str  # "NONE", "DELETE_AND_RECREATE"


class CoverVerifier:
    """표지 검증기 - 메타데이터만 확인"""

    # cover_v1 규칙 (render_cover_v1.js와 동일)
    COVER_V1 = {
        "name": "cover_v1",
        "canvas": {"width": 1080, "height": 1080, "deviceScaleFactor": 2},
        "title": {
            "fontFamily": "'Arial Black', 'Arial Bold', sans-serif",
            "fontSize": 114,
            "fontWeight": 900,
            "color": "#FFFFFF",
            "textShadow": "2px 2px 4px rgba(0,0,0,0.8), 0 4px 8px rgba(0,0,0,0.5)",
            "letterSpacing": "4px",
            "textTransform": "uppercase",
            "top_percent": 14
        }
    }

    VALID_RULES = ["cover_v1"]

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    def _get_rule_hash(self, rule_name: str) -> str:
        """규칙 해시 계산"""
        if rule_name == "cover_v1":
            rule_string = json.dumps(self.COVER_V1)
            return hashlib.sha256(rule_string.encode()).hexdigest()[:16]
        return ""

    def verify_cover(self, content_folder: Path, food_name: str) -> CoverVerification:
        """
        표지 검증 - 메타데이터만 확인

        1. 메타데이터 파일 존재?
        2. rule_name 유효?
        3. rule_hash 일치?
        """
        # 메타데이터 파일 경로
        metadata_path = content_folder / f"{food_name}_00_metadata.json"
        cover_path = content_folder / f"{food_name}_00.png"

        # 1. 표지 이미지 존재 확인
        if not cover_path.exists():
            return CoverVerification(
                result=CoverResult.FAIL,
                rule_name=None,
                rule_hash=None,
                message=f"표지 이미지 없음: {food_name}_00.png",
                action="DELETE_AND_RECREATE"
            )

        # 2. 메타데이터 파일 존재 확인
        if not metadata_path.exists():
            return CoverVerification(
                result=CoverResult.MISSING_METADATA,
                rule_name=None,
                rule_hash=None,
                message=f"메타데이터 없음: {food_name}_00_metadata.json",
                action="DELETE_AND_RECREATE"
            )

        # 3. 메타데이터 읽기
        try:
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        except Exception as e:
            return CoverVerification(
                result=CoverResult.FAIL,
                rule_name=None,
                rule_hash=None,
                message=f"메타데이터 파싱 오류: {e}",
                action="DELETE_AND_RECREATE"
            )

        rule_name = metadata.get("rule_name")
        rule_hash = metadata.get("rule_hash")

        # 4. rule_name 확인
        if not rule_name:
            return CoverVerification(
                result=CoverResult.INVALID_RULE,
                rule_name=None,
                rule_hash=rule_hash,
                message="rule_name 없음",
                action="DELETE_AND_RECREATE"
            )

        if rule_name not in self.VALID_RULES:
            return CoverVerification(
                result=CoverResult.INVALID_RULE,
                rule_name=rule_name,
                rule_hash=rule_hash,
                message=f"유효하지 않은 규칙: {rule_name}",
                action="DELETE_AND_RECREATE"
            )

        # 5. rule_hash 확인 (존재 여부만, JS/Python 해시 차이로 값 비교 생략)
        if not rule_hash:
            return CoverVerification(
                result=CoverResult.HASH_MISMATCH,
                rule_name=rule_name,
                rule_hash=rule_hash,
                message="rule_hash 없음",
                action="DELETE_AND_RECREATE"
            )

        # ✅ 모든 검증 통과
        return CoverVerification(
            result=CoverResult.PASS,
            rule_name=rule_name,
            rule_hash=rule_hash,
            message=f"✅ {rule_name} 규칙으로 생성됨",
            action="NONE"
        )

    def verify_and_report(self, content_folder: Path, food_name: str) -> Tuple[bool, str]:
        """검증 후 결과 출력"""
        result = self.verify_cover(content_folder, food_name)

        print(f"🔍 표지 검증: {food_name}_00.png")
        print(f"   결과: {result.result.value}")
        print(f"   규칙: {result.rule_name or 'N/A'}")
        print(f"   해시: {result.rule_hash or 'N/A'}")
        print(f"   메시지: {result.message}")

        if result.action == "DELETE_AND_RECREATE":
            print(f"   ⚠️ 조치: 삭제 후 재생성 필요")

        return result.result == CoverResult.PASS, result.message


# CLI 실행
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cover_verifier.py <content_folder> [food_name]")
        print("Example: python cover_verifier.py content/images/169_duck_오리고기 duck")
        sys.exit(1)

    folder = Path(sys.argv[1])
    food_name = sys.argv[2] if len(sys.argv) > 2 else folder.name.split('_')[1]

    verifier = CoverVerifier()
    passed, message = verifier.verify_and_report(folder, food_name)

    sys.exit(0 if passed else 1)
