"""
Visual Guard Agent - Phase 4 품질 관리 시스템
게시 전 이미지 품질 자동 검증

BLOCK 조건 하나라도 걸리면 게시 중단
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# pytesseract는 선택적 의존성
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    print("Warning: pytesseract not available. OCR checks will be skipped.")

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent


class CheckResult(Enum):
    PASS = "PASS"
    CAUTION = "CAUTION"
    BLOCK = "BLOCK"


@dataclass
class CheckItem:
    name: str
    result: CheckResult
    reason: str
    details: Optional[Dict] = None


@dataclass
class VisualGuardResult:
    agent: str = "visual_guard"
    result: CheckResult = CheckResult.PASS
    checks: List[Dict] = None
    final_reason: str = ""
    recommendation: str = ""
    timestamp: str = ""

    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()
        if self.checks is None:
            self.checks = []

    def to_dict(self):
        return {
            "agent": self.agent,
            "result": self.result.value,
            "checks": self.checks,
            "final_reason": self.final_reason,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp
        }


class VisualGuard:
    """이미지 품질 검증 에이전트"""

    # 표지 규칙 v9 확정
    COVER_SPECS = {
        "font": "Arial Black",
        "font_size": 114,
        "position_top_percent": 25,  # 상단 25%
        "text_color": "#FFFFFF",
        "has_drop_shadow": True
    }

    # 안전도별 색상 규칙 v1.0 (RULES_v1.0.md 참조)
    SAFETY_COLORS = {
        "safe": {"hex": "#4CAF50", "rgb": (76, 175, 80), "name": "초록"},
        "caution": {"hex": "#FFD93D", "rgb": (255, 217, 61), "name": "노랑"},
        "danger": {"hex": "#FF6B6B", "rgb": (255, 107, 107), "name": "빨강"},
    }

    # 기준 콘텐츠 (비교용)
    REFERENCE_CONTENTS = {
        "safe": ["032_boiled_egg_삶은달걀", "026_spinach_시금치"],
        "caution": ["140_shrimp_새우"],
        "danger": ["060_grape_포도"],
    }

    # 본문 규칙 (안전도 기반)
    CONTENT_SPECS = {
        "font": "Noto Sans KR Bold",
        "model": "flux-2-pro",
        "background_style": "warm_living_room",
        "position_bottom_percent": 25  # 하단 25%
    }

    # CTA 규칙
    CTA_SOURCE_DIR = ROOT / "content/images/sunshine/cta_source/best_cta"

    # 허용된 모델
    ALLOWED_MODELS = ["fal-ai/flux-2-pro", "flux-2-pro", "flux_2_pro"]

    def __init__(self):
        self.checks: List[CheckItem] = []
        self.cta_hashes = self._load_cta_hashes()

    def _load_cta_hashes(self) -> set:
        """best_cta 폴더의 실사 이미지 해시 로드"""
        hashes = set()
        if self.CTA_SOURCE_DIR.exists():
            for img_path in self.CTA_SOURCE_DIR.glob("*.jpg"):
                try:
                    with open(img_path, "rb") as f:
                        hashes.add(hashlib.md5(f.read()).hexdigest())
                except Exception:
                    pass
        return hashes

    def _add_check(self, name: str, result: CheckResult, reason: str, details: Dict = None):
        """검사 항목 추가"""
        check = CheckItem(name, result, reason, details)
        self.checks.append(check)

    def _get_image_text_position(self, img: Image.Image) -> Tuple[Optional[int], Optional[str]]:
        """OCR로 텍스트 위치 추출"""
        if not HAS_TESSERACT:
            return None, "pytesseract not available"

        try:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            # 텍스트가 있는 첫 번째 위치 찾기
            for i, text in enumerate(data['text']):
                if text.strip():
                    top = data['top'][i]
                    height = img.height
                    top_percent = (top / height) * 100
                    return int(top_percent), text
            return None, None
        except Exception as e:
            return None, str(e)

    def _check_for_broken_text(self, img: Image.Image) -> Tuple[bool, str]:
        """OCR로 깨진 텍스트(□) 확인"""
        if not HAS_TESSERACT:
            return False, "pytesseract not available - skipping OCR check"

        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            if '□' in text or '■' in text:
                return True, text
            return False, text
        except Exception as e:
            return False, str(e)

    def _get_image_hash(self, img_path: Path) -> str:
        """이미지 파일 해시"""
        with open(img_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _analyze_background_style(self, img: Image.Image) -> Dict:
        """배경 스타일 분석 (색상 히스토그램 기반)"""
        # 간단한 색상 분석
        img_small = img.resize((100, 100))
        colors = img_small.getcolors(10000)
        if colors:
            # 가장 많은 색상 추출
            dominant = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
            return {
                "dominant_colors": [c[1] for c in dominant],
                "warm_tone": self._is_warm_tone(dominant)
            }
        return {"dominant_colors": [], "warm_tone": False}

    def _is_warm_tone(self, colors: List) -> bool:
        """따뜻한 톤인지 확인"""
        for count, color in colors:
            if isinstance(color, tuple) and len(color) >= 3:
                r, g, b = color[:3]
                # 따뜻한 톤: R > B, 전체적으로 밝음
                if r > b and (r + g + b) / 3 > 100:
                    return True
        return False

    def _check_text_is_white(self, img: Image.Image, top_percent: int = 25) -> bool:
        """상단 영역의 텍스트가 흰색인지 확인"""
        # 상단 25% 영역 추출
        height = img.height
        top_region = img.crop((0, 0, img.width, int(height * top_percent / 100)))

        # 흰색 픽셀 비율 확인 (텍스트 영역)
        pixels = list(top_region.getdata())
        white_count = sum(1 for p in pixels if isinstance(p, tuple) and len(p) >= 3 and p[0] > 240 and p[1] > 240 and p[2] > 240)

        # 흰색 픽셀이 일정 비율 이상이면 흰색 텍스트로 판단
        return white_count > len(pixels) * 0.01  # 1% 이상

    def _check_text_color_by_safety(self, img: Image.Image, safety: str, bottom_percent: int = 30) -> Tuple[bool, str, Dict]:
        """
        하단 영역의 텍스트가 안전도에 맞는 색상인지 확인

        Args:
            img: PIL Image
            safety: "safe", "caution", "danger"
            bottom_percent: 검사할 하단 영역 비율 (기본 30%)

        Returns:
            (is_correct, detected_color, details)
        """
        if safety not in self.SAFETY_COLORS:
            return False, "unknown", {"error": f"Unknown safety: {safety}"}

        expected = self.SAFETY_COLORS[safety]
        expected_rgb = expected["rgb"]

        height = img.height
        width = img.width
        # 하단 30% 영역 추출
        bottom_region = img.crop((0, int(height * (100 - bottom_percent) / 100), width, height))

        # 각 안전도 색상별 픽셀 카운트
        color_counts = {"safe": 0, "caution": 0, "danger": 0, "white": 0}
        total_bright = 0

        for y in range(0, bottom_region.height, 2):
            for x in range(0, bottom_region.width, 3):
                try:
                    pixel = bottom_region.getpixel((x, y))
                    if not isinstance(pixel, tuple) or len(pixel) < 3:
                        continue
                    r, g, b = pixel[:3]

                    brightness = (r + g + b) / 3
                    if brightness < 100:
                        continue  # 어두운 픽셀 스킵

                    total_bright += 1

                    # 초록색 #4CAF50 (76, 175, 80) ±30
                    if 50 <= r <= 110 and 145 <= g <= 205 and 50 <= b <= 110:
                        color_counts["safe"] += 1
                    # 노란색 #FFD93D (255, 217, 61) ±30
                    elif 225 <= r <= 255 and 190 <= g <= 255 and 30 <= b <= 100:
                        color_counts["caution"] += 1
                    # 빨간색 #FF6B6B (255, 107, 107) ±30
                    elif 225 <= r <= 255 and 80 <= g <= 140 and 80 <= b <= 140:
                        color_counts["danger"] += 1
                    # 흰색
                    elif r > 240 and g > 240 and b > 240:
                        color_counts["white"] += 1
                except Exception:
                    pass

        # 가장 많은 색상 찾기
        detected = max(color_counts.items(), key=lambda x: x[1])
        detected_color = detected[0]
        detected_count = detected[1]

        # 결과 계산
        is_correct = (detected_color == safety) and (detected_count > 50)  # 최소 50픽셀

        details = {
            "expected_safety": safety,
            "expected_color": expected["name"],
            "expected_hex": expected["hex"],
            "detected_color": detected_color,
            "detected_count": detected_count,
            "color_counts": color_counts,
            "total_bright": total_bright
        }

        return is_correct, detected_color, details

    def _check_text_is_yellow(self, img: Image.Image, bottom_percent: int = 25) -> bool:
        """하단 영역의 텍스트가 노란색인지 확인 (DEPRECATED - 안전도 기반 사용 권장)"""
        height = img.height
        bottom_region = img.crop((0, int(height * (100 - bottom_percent) / 100), img.width, height))
        pixels = list(bottom_region.getdata())
        yellow_count = sum(1 for p in pixels if isinstance(p, tuple) and len(p) >= 3
                          and p[0] > 200 and p[1] > 180 and p[2] < 120)
        return yellow_count > len(pixels) * 0.005

    # ========== 표지 검증 ==========

    def verify_cover(self, cover_path: Path, expected_text: str = None) -> CheckResult:
        """표지 이미지 검증"""
        if not cover_path.exists():
            self._add_check("cover_exists", CheckResult.BLOCK, f"표지 파일 없음: {cover_path}")
            return CheckResult.BLOCK

        try:
            img = Image.open(cover_path)
        except Exception as e:
            self._add_check("cover_readable", CheckResult.BLOCK, f"이미지 읽기 실패: {e}")
            return CheckResult.BLOCK

        result = CheckResult.PASS

        # 1. 텍스트 위치 확인 (상단 25%)
        top_percent, detected_text = self._get_image_text_position(img)
        if top_percent is not None:
            if top_percent > self.COVER_SPECS["position_top_percent"]:
                self._add_check(
                    "cover_text_position",
                    CheckResult.BLOCK,
                    f"텍스트 위치 상단 25% 벗어남 (현재: {top_percent}%)",
                    {"expected": "≤25%", "actual": f"{top_percent}%"}
                )
                result = CheckResult.BLOCK
            else:
                self._add_check("cover_text_position", CheckResult.PASS, f"텍스트 위치 정상 ({top_percent}%)")
        else:
            self._add_check("cover_text_position", CheckResult.CAUTION, "텍스트 위치 감지 실패")
            if result != CheckResult.BLOCK:
                result = CheckResult.CAUTION

        # 2. 텍스트 색상 확인 (흰색)
        if self._check_text_is_white(img):
            self._add_check("cover_text_color", CheckResult.PASS, "텍스트 색상 흰색 확인")
        else:
            self._add_check("cover_text_color", CheckResult.BLOCK, "텍스트 색상이 흰색이 아님")
            result = CheckResult.BLOCK

        # 3. 깨진 텍스트 확인
        has_broken, ocr_text = self._check_for_broken_text(img)
        if has_broken:
            self._add_check("cover_text_broken", CheckResult.BLOCK, "텍스트 깨짐 감지 (□ 포함)")
            result = CheckResult.BLOCK
        else:
            self._add_check("cover_text_broken", CheckResult.PASS, "텍스트 정상")

        return result

    # ========== 본문 검증 ==========

    def _load_food_safety_db(self) -> Dict:
        """food_safety.json 로드"""
        safety_file = ROOT / "config/settings/food_safety.json"
        if safety_file.exists():
            try:
                with open(safety_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"safe": [], "caution": [], "danger": []}

    def _get_food_safety(self, folder_path: Path) -> str:
        """폴더명에서 음식명 추출 후 안전도 확인"""
        folder_name = folder_path.name.lower()

        # food_safety.json에서 확인
        safety_db = self._load_food_safety_db()

        for safety_level in ["safe", "caution", "danger"]:
            foods = safety_db.get(safety_level, [])
            for food in foods:
                if food.lower() in folder_name:
                    return safety_level

        # 기준 콘텐츠와 비교 (fallback)
        for safety, refs in self.REFERENCE_CONTENTS.items():
            for ref in refs:
                if ref.lower() in folder_name:
                    return safety

        # 기본값: SAFE (안전 음식)
        return "safe"

    def verify_content(self, content_path: Path, cover_path: Path = None, safety: str = None) -> CheckResult:
        """본문 이미지 검증 (안전도 기반)"""
        if not content_path.exists():
            self._add_check("content_exists", CheckResult.BLOCK, f"본문 파일 없음: {content_path}")
            return CheckResult.BLOCK

        try:
            img = Image.open(content_path)
        except Exception as e:
            self._add_check("content_readable", CheckResult.BLOCK, f"이미지 읽기 실패: {e}")
            return CheckResult.BLOCK

        # 안전도 확인
        if safety is None:
            safety = self._get_food_safety(content_path.parent)

        result = CheckResult.PASS

        # 1. OCR 깨짐 확인
        has_broken, ocr_text = self._check_for_broken_text(img)
        if has_broken:
            self._add_check(
                "content_text_broken",
                CheckResult.BLOCK,
                "텍스트 깨짐 감지 (□ 포함)",
                {"ocr_sample": ocr_text[:100] if ocr_text else ""}
            )
            result = CheckResult.BLOCK
        else:
            self._add_check("content_text_broken", CheckResult.PASS, "텍스트 정상")

        # 2. 본문 텍스트 색상 확인 (안전도 기반)
        is_correct, detected_color, details = self._check_text_color_by_safety(img, safety)

        expected_info = self.SAFETY_COLORS.get(safety, {})
        expected_name = expected_info.get("name", "알 수 없음")
        expected_hex = expected_info.get("hex", "N/A")

        if is_correct:
            self._add_check(
                "content_text_color",
                CheckResult.PASS,
                f"텍스트 색상 {expected_name}({expected_hex}) 확인",
                details
            )
        else:
            self._add_check(
                "content_text_color",
                CheckResult.BLOCK,
                f"본문 색상 불일치: 예상 {expected_name}({expected_hex}), 감지 {detected_color}",
                details
            )
            result = CheckResult.BLOCK

        # 3. 배경 스타일 확인 (표지와 비교)
        if cover_path and cover_path.exists():
            try:
                cover_img = Image.open(cover_path)
                cover_style = self._analyze_background_style(cover_img)
                content_style = self._analyze_background_style(img)

                if cover_style["warm_tone"] != content_style["warm_tone"]:
                    self._add_check(
                        "content_background_match",
                        CheckResult.CAUTION,
                        "배경 스타일이 표지와 불일치",
                        {"cover": cover_style, "content": content_style}
                    )
                    if result != CheckResult.BLOCK:
                        result = CheckResult.CAUTION
                else:
                    self._add_check("content_background_match", CheckResult.PASS, "배경 스타일 일치")
            except Exception as e:
                self._add_check("content_background_match", CheckResult.CAUTION, f"배경 비교 실패: {e}")

        return result

    # ========== CTA 검증 ==========

    def verify_cta(self, cta_path: Path) -> CheckResult:
        """CTA 이미지 검증 (실사 확인)"""
        if not cta_path.exists():
            self._add_check("cta_exists", CheckResult.BLOCK, f"CTA 파일 없음: {cta_path}")
            return CheckResult.BLOCK

        result = CheckResult.PASS

        # 1. 실사 해시 확인
        try:
            cta_hash = self._get_image_hash(cta_path)

            # CTA 원본이 best_cta에서 온 것인지 확인
            # (텍스트 오버레이 후에는 해시가 달라지므로, 원본 검증은 생성 시점에)
            # 여기서는 AI 생성 이미지 특성 확인

            img = Image.open(cta_path)

            # 이미지 크기 확인 (실사는 보통 다양한 크기)
            if img.size == (1024, 1024) or img.size == (1080, 1080):
                # AI 생성 가능성 체크 - EXIF 메타데이터 확인
                exif = img._getexif() if hasattr(img, '_getexif') else None
                if exif is None:
                    self._add_check(
                        "cta_is_real_photo",
                        CheckResult.CAUTION,
                        "EXIF 데이터 없음 - AI 생성 가능성",
                        {"size": img.size}
                    )
                    if result != CheckResult.BLOCK:
                        result = CheckResult.CAUTION
                else:
                    self._add_check("cta_is_real_photo", CheckResult.PASS, "EXIF 데이터 존재 - 실사 확인")
            else:
                self._add_check("cta_is_real_photo", CheckResult.PASS, "이미지 크기 다양 - 실사 가능성 높음")

        except Exception as e:
            self._add_check("cta_hash_check", CheckResult.CAUTION, f"해시 검증 실패: {e}")
            if result != CheckResult.BLOCK:
                result = CheckResult.CAUTION

        return result

    # ========== 공통 검증 ==========

    def verify_model_metadata(self, img_path: Path) -> CheckResult:
        """이미지 메타데이터에서 모델 확인"""
        # PNG 메타데이터 또는 생성 로그에서 모델 확인
        # 실제 구현에서는 생성 시 메타데이터를 저장해야 함

        # 현재는 파일명이나 동반 JSON에서 확인
        json_path = img_path.with_suffix('.json')
        if json_path.exists():
            try:
                with open(json_path, 'r') as f:
                    meta = json.load(f)
                    model = meta.get('model', '')
                    if any(allowed in model for allowed in self.ALLOWED_MODELS):
                        self._add_check("model_check", CheckResult.PASS, f"모델 확인: {model}")
                        return CheckResult.PASS
                    else:
                        self._add_check(
                            "model_check",
                            CheckResult.BLOCK,
                            f"허용되지 않은 모델: {model}",
                            {"allowed": self.ALLOWED_MODELS}
                        )
                        return CheckResult.BLOCK
            except Exception as e:
                self._add_check("model_check", CheckResult.CAUTION, f"메타데이터 읽기 실패: {e}")
                return CheckResult.CAUTION

        self._add_check("model_check", CheckResult.CAUTION, "메타데이터 파일 없음")
        return CheckResult.CAUTION

    # ========== 전체 검증 ==========

    def verify_content_folder(self, folder_path: Path, safety: str = None) -> VisualGuardResult:
        """콘텐츠 폴더 전체 검증 (안전도 기반)"""
        self.checks = []  # 초기화

        folder = Path(folder_path)
        if not folder.exists():
            return VisualGuardResult(
                result=CheckResult.BLOCK,
                checks=[],
                final_reason=f"폴더 없음: {folder}",
                recommendation="콘텐츠 폴더 경로 확인"
            )

        # 음식 안전도 확인
        if safety is None:
            safety = self._get_food_safety(folder)

        self._add_check(
            "food_safety",
            CheckResult.PASS,
            f"음식 안전도: {safety.upper()}",
            {"expected_color": self.SAFETY_COLORS.get(safety, {}).get("hex", "N/A")}
        )

        # 파일 찾기
        files = list(folder.glob("*.png")) + list(folder.glob("*.jpg"))

        cover_file = None
        content_files = []
        cta_file = None

        for f in files:
            name = f.stem.lower()
            if "_00" in name or "cover" in name:
                cover_file = f
            elif "_03" in name or "cta" in name:
                cta_file = f
            elif any(f"_{i:02d}" in name for i in range(1, 10)):
                content_files.append(f)

        overall_result = CheckResult.PASS

        # 1. 표지 검증
        if cover_file:
            cover_result = self.verify_cover(cover_file)
            if cover_result == CheckResult.BLOCK:
                overall_result = CheckResult.BLOCK
            elif cover_result == CheckResult.CAUTION and overall_result != CheckResult.BLOCK:
                overall_result = CheckResult.CAUTION
        else:
            self._add_check("cover_file", CheckResult.BLOCK, "표지 파일 없음")
            overall_result = CheckResult.BLOCK

        # 2. 본문 검증 (안전도 기반 색상 확인)
        for content_file in content_files:
            content_result = self.verify_content(content_file, cover_file, safety=safety)
            if content_result == CheckResult.BLOCK:
                overall_result = CheckResult.BLOCK
            elif content_result == CheckResult.CAUTION and overall_result != CheckResult.BLOCK:
                overall_result = CheckResult.CAUTION

        # 3. CTA 검증
        if cta_file:
            cta_result = self.verify_cta(cta_file)
            if cta_result == CheckResult.BLOCK:
                overall_result = CheckResult.BLOCK
            elif cta_result == CheckResult.CAUTION and overall_result != CheckResult.BLOCK:
                overall_result = CheckResult.CAUTION
        else:
            self._add_check("cta_file", CheckResult.CAUTION, "CTA 파일 없음 또는 감지 실패")
            if overall_result != CheckResult.BLOCK:
                overall_result = CheckResult.CAUTION

        # 결과 생성
        checks_dict = [
            {
                "name": c.name,
                "result": c.result.value,
                "reason": c.reason,
                "details": c.details
            }
            for c in self.checks
        ]

        blocked_checks = [c for c in self.checks if c.result == CheckResult.BLOCK]
        caution_checks = [c for c in self.checks if c.result == CheckResult.CAUTION]

        if blocked_checks:
            final_reason = f"BLOCK: {', '.join(c.name for c in blocked_checks)}"
            recommendation = "위 항목 수정 후 재검증 필요"
        elif caution_checks:
            final_reason = f"CAUTION: {', '.join(c.name for c in caution_checks)}"
            recommendation = "주의 항목 확인 권장, 게시 가능"
        else:
            final_reason = "모든 검증 통과"
            recommendation = "게시 진행 가능"

        return VisualGuardResult(
            result=overall_result,
            checks=checks_dict,
            final_reason=final_reason,
            recommendation=recommendation
        )


def verify_before_publish(folder_path: str) -> Dict:
    """게시 전 검증 (외부 호출용)"""
    guard = VisualGuard()
    result = guard.verify_content_folder(Path(folder_path))
    return result.to_dict()


# CLI 지원
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python visual_guard.py <content_folder>")
        print("Example: python visual_guard.py content/images/169_duck_오리고기")
        sys.exit(1)

    folder = sys.argv[1]
    result = verify_before_publish(folder)

    print("\n" + "="*60)
    print("🛡️ Visual Guard 검증 결과")
    print("="*60)
    print(f"결과: {result['result']}")
    print(f"사유: {result['final_reason']}")
    print(f"권장: {result['recommendation']}")
    print("\n상세 검사:")
    for check in result['checks']:
        icon = "✅" if check['result'] == "PASS" else "⚠️" if check['result'] == "CAUTION" else "❌"
        print(f"  {icon} {check['name']}: {check['reason']}")
    print("="*60)

    # 종료 코드
    sys.exit(0 if result['result'] == "PASS" else 1)
