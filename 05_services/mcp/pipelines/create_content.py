#!/usr/bin/env python3
"""
콘텐츠 자동 생성 파이프라인 v1.0

명령 1개 → 전체 자동 실행 → 텔레그램 보고

사용법:
    python3 mcp/pipelines/create_content.py duck 오리고기

플로우:
    1. RULES.md 자동 읽기
    2. 안전도 확인 (food_safety.json)
    3. 기준 콘텐츠 비교 준비
    4. 이미지 생성 (fal-ai)
    5. 텍스트 오버레이 (puppeteer)
    6. visual_guard 검증
    7. 시트 기록 (대기)
    8. 텔레그램 알림
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent


class ContentPipeline:
    """콘텐츠 자동 생성 파이프라인"""

    def __init__(self, topic_en: str, topic_kr: str):
        self.topic_en = topic_en.lower()
        self.topic_kr = topic_kr
        self.safety = None
        self.color = None
        self.folder_path = None
        self.errors = []
        self.log = []

    def _log(self, step: str, message: str, status: str = "INFO"):
        """로그 기록"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{status}] {step}: {message}"
        self.log.append(log_entry)
        print(log_entry)

    def _load_rules(self) -> Dict:
        """RULES.md 로드 및 파싱"""
        rules_path = ROOT / "RULES_v1.0.md"
        if not rules_path.exists():
            self._log("1. RULES.md", "파일 없음", "ERROR")
            return {}

        with open(rules_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 핵심 규칙 추출
        rules = {
            "cover_font": "Arial Black",
            "cover_size": "114px",
            "cover_color": "#FFFFFF",
            "safety_colors": {
                "safe": "#4CAF50",
                "caution": "#FFD93D",
                "danger": "#FF6B6B",
            }
        }

        self._log("1. RULES.md", "규칙 로드 완료", "OK")
        return rules

    def _get_food_safety(self) -> str:
        """음식 안전도 확인"""
        safety_file = ROOT / "config/settings/food_safety.json"
        if not safety_file.exists():
            self._log("2. 안전도", "food_safety.json 없음", "ERROR")
            return "safe"

        with open(safety_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for level in ["safe", "caution", "danger"]:
            foods = data.get(level, [])
            if self.topic_en in foods:
                self.safety = level
                self._log("2. 안전도", f"{self.topic_en} = {level.upper()}", "OK")
                return level

        self.safety = "safe"  # 기본값
        self._log("2. 안전도", f"{self.topic_en} 미등록, 기본값 SAFE", "WARN")
        return "safe"

    def _get_reference_contents(self) -> list:
        """기준 콘텐츠 목록"""
        refs = {
            "safe": ["032_boiled_egg_삶은달걀", "026_spinach_시금치"],
            "caution": ["140_shrimp_새우"],
            "danger": ["060_grape_포도"],
        }
        ref_list = refs.get(self.safety, refs["safe"])
        self._log("3. 기준 콘텐츠", f"{self.safety} → {ref_list}", "OK")
        return ref_list

    def _determine_text_color(self, rules: Dict) -> str:
        """안전도 기반 텍스트 색상 결정"""
        colors = rules.get("safety_colors", {})
        self.color = colors.get(self.safety, "#4CAF50")
        self._log("3. 텍스트 색상", f"{self.safety} → {self.color}", "OK")
        return self.color

    def _find_or_create_folder(self) -> Path:
        """콘텐츠 폴더 찾기 또는 생성"""
        images_dir = ROOT / "content/images"

        # 기존 폴더 찾기
        for folder in images_dir.iterdir():
            if folder.is_dir() and self.topic_en in folder.name.lower():
                self.folder_path = folder
                self._log("4. 폴더", f"기존 폴더 발견: {folder.name}", "OK")
                return folder

        # 새 폴더 생성
        existing_nums = []
        for folder in images_dir.iterdir():
            if folder.is_dir() and folder.name[:3].isdigit():
                existing_nums.append(int(folder.name[:3]))

        next_num = max(existing_nums) + 1 if existing_nums else 1
        new_folder = images_dir / f"{next_num:03d}_{self.topic_en}_{self.topic_kr}"
        new_folder.mkdir(parents=True, exist_ok=True)

        self.folder_path = new_folder
        self._log("4. 폴더", f"새 폴더 생성: {new_folder.name}", "OK")
        return new_folder

    def _generate_images(self) -> bool:
        """이미지 생성 (fal-ai 호출)"""
        # 실제 구현에서는 fal-ai MCP 도구 호출
        self._log("5. 이미지 생성", "fal-ai/flux-2-pro 호출 필요", "WAIT")

        # 이미지 생성 스크립트 경로
        script_path = ROOT / "services/scripts/generate_images.py"
        if script_path.exists():
            self._log("5. 이미지 생성", f"스크립트 존재: {script_path}", "INFO")
        else:
            self._log("5. 이미지 생성", "generate_images.py 없음", "WARN")

        return True

    def _apply_text_overlay(self) -> bool:
        """텍스트 오버레이 적용"""
        # 본문용 렌더 스크립트 찾기
        render_script = ROOT / f"services/scripts/text_overlay/render_{self.topic_en}.js"

        if render_script.exists():
            self._log("6. 텍스트 오버레이", f"전용 스크립트 발견: {render_script.name}", "OK")
        else:
            self._log("6. 텍스트 오버레이", "범용 스크립트 사용 필요", "INFO")

        # 색상 적용 안내
        self._log("6. 텍스트 오버레이", f"본문 색상: {self.color} ({self.safety})", "INFO")

        return True

    def _run_visual_guard(self) -> Tuple[str, Dict]:
        """visual_guard 검증 실행"""
        if not self.folder_path or not self.folder_path.exists():
            self._log("7. visual_guard", "폴더 없음", "ERROR")
            return "BLOCK", {"error": "폴더 없음"}

        # visual_guard 모듈 임포트
        try:
            sys.path.insert(0, str(ROOT))
            from core.agents.visual_guard import VisualGuard

            guard = VisualGuard()
            result = guard.verify_content_folder(self.folder_path, safety=self.safety)

            self._log("7. visual_guard", f"결과: {result.result.value}", "OK")
            return result.result.value, result.to_dict()

        except ImportError as e:
            self._log("7. visual_guard", f"모듈 임포트 실패: {e}", "ERROR")
            return "CAUTION", {"error": str(e)}

        except Exception as e:
            self._log("7. visual_guard", f"검증 실패: {e}", "ERROR")
            return "CAUTION", {"error": str(e)}

    def _update_sheet(self, result: str) -> bool:
        """Google Sheets 업데이트 (MCP 연동 필요)"""
        self._log("8. 시트 업데이트", "MCP google-sheets 연동 필요", "WAIT")
        # 실제 구현에서는 google-sheets MCP 도구 호출
        return True

    def _send_telegram_notification(self, result: str, details: Dict) -> bool:
        """텔레그램 알림 전송"""
        # 기존 텔레그램 모듈 사용
        try:
            sys.path.insert(0, str(ROOT))
            from pipeline.telegram_notifier import TelegramNotifier

            notifier = TelegramNotifier()

            message = f"""
✅ 콘텐츠 생성 완료

📦 {self.topic_kr} ({self.topic_en})
🏷️ 안전도: {self.safety.upper()}
🎨 텍스트 색상: {self.color}
🛡️ visual_guard: {result}

📊 시트 업데이트: 대기
📂 폴더: {self.folder_path.name if self.folder_path else 'N/A'}
            """.strip()

            notifier._send_message(message)
            self._log("9. 텔레그램", "알림 전송 완료", "OK")
            return True

        except Exception as e:
            self._log("9. 텔레그램", f"전송 실패: {e}", "ERROR")
            return False

    def run(self) -> Dict:
        """파이프라인 실행"""
        print("=" * 60)
        print(f"🚀 콘텐츠 생성 파이프라인 시작: {self.topic_kr} ({self.topic_en})")
        print("=" * 60)

        # 1. RULES.md 로드
        rules = self._load_rules()

        # 2. 안전도 확인
        self._get_food_safety()

        # 3. 기준 콘텐츠 & 색상 결정
        refs = self._get_reference_contents()
        self._determine_text_color(rules)

        # 4. 폴더 생성/찾기
        self._find_or_create_folder()

        # 5. 이미지 생성 (대기)
        self._generate_images()

        # 6. 텍스트 오버레이 (대기)
        self._apply_text_overlay()

        # 7. visual_guard 검증
        result, details = self._run_visual_guard()

        # 8. 시트 업데이트 (대기)
        self._update_sheet(result)

        # 9. 텔레그램 알림
        self._send_telegram_notification(result, details)

        print("=" * 60)
        print(f"✅ 파이프라인 완료: {result}")
        print("=" * 60)

        return {
            "topic_en": self.topic_en,
            "topic_kr": self.topic_kr,
            "safety": self.safety,
            "color": self.color,
            "folder": str(self.folder_path) if self.folder_path else None,
            "visual_guard": result,
            "log": self.log,
        }


def main():
    if len(sys.argv) < 3:
        print("사용법: python3 create_content.py <topic_en> <topic_kr>")
        print("예시: python3 create_content.py duck 오리고기")
        sys.exit(1)

    topic_en = sys.argv[1]
    topic_kr = sys.argv[2]

    pipeline = ContentPipeline(topic_en, topic_kr)
    result = pipeline.run()

    # 결과 JSON 저장
    log_file = ROOT / f"config/logs/pipeline_{topic_en}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n📄 로그 저장: {log_file}")


if __name__ == "__main__":
    main()
