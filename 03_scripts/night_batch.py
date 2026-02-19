#!/usr/bin/env python3
"""
night_batch.py - WO-NIGHT-001 야간 배치 처리
커버 레디 → 게시 준비 자동화

사용법:
  python3 scripts/night_batch.py --test         # 1개 테스트
  python3 scripts/night_batch.py --start 0 --end 10  # 범위 지정
  python3 scripts/night_batch.py --all          # 전체 실행
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# 기존 스크립트 임포트
try:
    from scripts.infographic_generator import (
        generate_nutrition_info,
        generate_do_dont,
        generate_dosage_table,
        generate_precautions,
        generate_cooking_method,
    )
    INFOGRAPHIC_AVAILABLE = True
except ImportError:
    INFOGRAPHIC_AVAILABLE = False
    print("⚠️ infographic_generator 임포트 실패")

# 터미널 색상
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

# 경로
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_FILE = PROJECT_ROOT / "config" / "food_data.json"
TARGETS_FILE = PROJECT_ROOT / "config" / "night_batch_targets.json"
LOG_DIR = PROJECT_ROOT / "logs" / "night_batch"

# 안전도 설정
SAFETY_CONFIG = {
    "SAFE": {"emoji": "🟢", "tone": "긍정적"},
    "CAUTION": {"emoji": "🟡", "tone": "신중"},
    "DANGER": {"emoji": "🔴", "tone": "경고"},
    "FORBIDDEN": {"emoji": "⛔", "tone": "금지"},
}

# 결과 추적
class BatchResult:
    def __init__(self):
        self.caption_success = 0
        self.caption_fail = 0
        self.caption_retry = 0
        self.image_success = 0
        self.image_fail = 0
        self.image_retry = 0
        self.cover_success = 0
        self.cover_fail = 0
        self.errors = []
        self.start_time = datetime.now()


def load_food_data() -> Dict:
    """음식 데이터 로드"""
    if not FOOD_DATA_FILE.exists():
        return {}
    with open(FOOD_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_targets() -> List[Dict]:
    """배치 대상 로드"""
    if not TARGETS_FILE.exists():
        print(f"{Colors.RED}❌ 대상 파일 없음: {TARGETS_FILE}{Colors.RESET}")
        print("   먼저 콘텐츠 스캔을 실행하세요.")
        return []

    with open(TARGETS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # UNKNOWN 제외
    valid = [f for f in data['folders'] if f['safety'] != 'UNKNOWN']
    return valid


def get_food_info(folder_name: str, food_data: Dict) -> Optional[Dict]:
    """폴더명에서 음식 정보 찾기"""
    for fid, info in food_data.items():
        name = info.get('name', '')
        eng = info.get('english_name', '')
        if name in folder_name or eng in folder_name.lower():
            return info
    return None


def ensure_folder_structure(content_path: Path):
    """출력 폴더 구조 생성"""
    # 2026-02-13: 플랫 구조
    (content_path / "00_Clean").mkdir(exist_ok=True)
    (content_path / "01_Insta&Thread").mkdir(exist_ok=True)
    (content_path / "02_Blog").mkdir(exist_ok=True)


def generate_captions(content_path: Path, food_info: Dict, safety: str) -> Tuple[bool, str]:
    """캡션 3종 생성 (인스타, 블로그, 쓰레드)"""
    food_name = food_info.get('name', content_path.name)
    # 2026-02-13: 플랫 구조 - 캡션은 각 플랫폼 폴더에 저장
    insta_dir = content_path / "01_Insta&Thread"
    blog_dir = content_path / "02_Blog"
    insta_dir.mkdir(exist_ok=True)
    blog_dir.mkdir(exist_ok=True)

    try:
        # 인스타 캡션 (01_Insta&Thread 폴더에 저장)
        insta_caption = generate_instagram_caption(food_name, food_info, safety)
        (insta_dir / "instagram_caption.txt").write_text(insta_caption, encoding='utf-8')

        # 블로그 캡션 (02_Blog 폴더에 저장)
        blog_caption = generate_blog_caption(food_name, food_info, safety)
        (blog_dir / "blog_caption.txt").write_text(blog_caption, encoding='utf-8')

        # 쓰레드 캡션 (01_Insta&Thread 폴더에 저장)
        thread_caption = generate_thread_caption(food_name, food_info, safety)
        (insta_dir / "threads_caption.txt").write_text(thread_caption, encoding='utf-8')

        return True, "캡션 3종 생성 완료"
    except Exception as e:
        return False, str(e)


def generate_instagram_caption(food_name: str, food_info: Dict, safety: str) -> str:
    """인스타그램 캡션 생성 (파스타 스타일)"""
    config = SAFETY_CONFIG.get(safety, SAFETY_CONFIG["SAFE"])
    dosages = food_info.get('dosages', {})

    # 급여량 문구 생성
    dosage_text = ""
    for size, info in dosages.items():
        weight = info.get('weight', '')
        amount = info.get('amount', '')
        desc = info.get('desc', '')
        dosage_text += f"{size} ({weight}) — {amount} ({desc})\n"

    # 안전도별 답변
    if safety == "SAFE":
        answer = f"네, {food_name}은(는) 강아지에게 급여 가능해요! 🎉"
    elif safety == "CAUTION":
        answer = f"주의해서 급여하세요! {food_name}은(는) 조건부로 급여 가능해요."
    elif safety == "DANGER":
        answer = f"위험해요! {food_name}은(는) 강아지에게 급여하지 마세요. 🚨"
    else:  # FORBIDDEN
        answer = f"절대 금지! {food_name}은(는) 강아지에게 치명적이에요. ⛔"

    # 팁 생성
    do_items = food_info.get('do_items', ['소량씩 급여하세요', '신선한 것만 급여하세요', '처음 급여 시 반응을 확인하세요'])
    tips = "\n".join([f"• {item}" for item in do_items[:3]])

    caption = f"""🐕 강아지 {food_name}, 줘도 되나요?

{answer}

📏 체중별 급여량

{dosage_text}
✅ 급여 팁
{tips}

우리 햇살이도 {food_name} 좋아하는데, 처음 줄 땐 아주 조금만 줬어요.

처음 주실 땐 조금만! 반응 보고 늘려주세요.

#강아지{food_name} #강아지간식 #반려견음식 #강아지먹어도되나요 #펫푸드 #반려견간식 #햇살이네음식연구소

⚠️ 이 콘텐츠는 AI의 도움을 받아 작성되었습니다.
"""
    return caption


def generate_blog_caption(food_name: str, food_info: Dict, safety: str) -> str:
    """블로그 캡션 생성"""
    config = SAFETY_CONFIG.get(safety, SAFETY_CONFIG["SAFE"])
    dosages = food_info.get('dosages', {})
    nutrients = food_info.get('nutrients', [])

    # 영양 정보
    nutrient_text = ""
    for n in nutrients[:4]:
        nutrient_text += f"- {n.get('name', '')}: {n.get('value', '')}{n.get('unit', '')} ({n.get('benefit', '')})\n"

    # 급여량 문구
    dosage_text = ""
    for size, info in dosages.items():
        dosage_text += f"- {size} ({info.get('weight', '')}): {info.get('amount', '')} - {info.get('desc', '')}\n"

    caption = f"""[이미지 1번: 표지]

안녕하세요, 11살 골든리트리버 햇살이 엄마예요.

오늘은 많은 분들이 궁금해하시는 '{food_name}' 급여에 대해 이야기해볼게요.
우리 햇살이도 {food_name}을(를) 정말 좋아하는데요, 처음 줬을 때 반응이 아직도 기억나요!

[이미지 2번: 음식 사진]


## 강아지 {food_name}, 먹어도 되나요?

{config['emoji']} 결론부터 말씀드리면, {safety} 등급이에요.

{food_name}에는 다양한 영양소가 들어있어요:
{nutrient_text}

[이미지 3번: 영양성분 인포그래픽]


## 어떻게 급여하면 좋을까요?

{food_name}을(를) 급여할 때는 몇 가지 주의사항이 있어요.

[이미지 4번: 급여방법 인포그래픽]


## 체중별 급여량

우리 아이 체중에 맞는 적정량을 확인해주세요:

{dosage_text}

[이미지 5번: 급여량 인포그래픽]


## 주의사항

안전하게 급여하기 위해 꼭 확인해주세요!

[이미지 6번: 주의사항 인포그래픽]


## 간단 레시피

햇살이가 좋아하는 방법으로 준비해봤어요.

[이미지 7번: 조리방법 인포그래픽]


## 마무리

{food_name} 급여, 어렵지 않죠?
우리 아이들 건강하게 간식 주는 게 보호자로서 가장 큰 기쁨인 것 같아요.

궁금한 점 있으시면 댓글로 남겨주세요! 💛

[이미지 8번: 햇살이 사진]


---
참고 자료: AAFCO, 미국수의학협회, 펫 영양학 연구 자료

⚠️ 이 콘텐츠는 AI의 도움을 받아 작성되었습니다. 정확한 급여는 수의사와 상담하세요.
"""
    return caption


def generate_thread_caption(food_name: str, food_info: Dict, safety: str) -> str:
    """쓰레드 캡션 생성"""
    config = SAFETY_CONFIG.get(safety, SAFETY_CONFIG["SAFE"])
    dosages = food_info.get('dosages', {})

    # 안전도별 답변
    if safety == "SAFE":
        answer = f"네! 급여 가능해요 ✅"
    elif safety == "CAUTION":
        answer = f"조건부로 가능해요 ⚠️"
    elif safety == "DANGER":
        answer = f"급여하지 마세요 🚨"
    else:
        answer = f"절대 금지! ⛔"

    # 급여량 (소형/대형만)
    small = dosages.get('소형견', {}).get('amount', '소량')
    large = dosages.get('대형견', {}).get('amount', '적정량')

    caption = f"""🐕 강아지 {food_name} 줘도 되나요?

{answer}

📏 급여량
소형견: {small}
대형견: {large}

처음엔 아주 조금만!
반응 보고 늘려주세요 💛

#강아지{food_name} #반려견간식

⚠️ AI 도움 작성
"""
    return caption


def generate_infographics(content_path: Path, food_info: Dict, safety: str) -> Tuple[bool, str]:
    """인포그래픽 5장 생성 (블로그 3~7번)"""
    if not INFOGRAPHIC_AVAILABLE:
        return False, "infographic_generator 사용 불가"

    # 2026-02-13: 플랫 구조 - blog → 02_Blog
    blog_dir = content_path / "02_Blog"
    blog_dir.mkdir(exist_ok=True)

    food_name = food_info.get('name', content_path.name)

    try:
        # 3번: 영양성분
        generate_nutrition_info(
            food_name,
            food_info.get('nutrients', []),
            safety,  # safety_str
            food_info.get('nutrition_footnote', ''),  # footnote
            str(blog_dir / "blog_03_nutrition.png")  # output_path
        )

        # 4번: DO/DON'T
        generate_do_dont(
            food_name,
            food_info.get('do_items', []),
            food_info.get('dont_items', []),
            safety,  # safety_str
            str(blog_dir / "blog_04_dodont.png")  # output_path
        )

        # 5번: 급여량
        generate_dosage_table(
            food_info.get('dosages', {}),  # dosages
            food_info.get('dosage_warning', []),  # warning_text
            food_info.get('dosage_footnote', ''),  # footnote
            safety,  # safety_str
            str(blog_dir / "blog_05_dosage.png")  # output_path
        )

        # 6번: 주의사항
        generate_precautions(
            food_name,
            food_info.get('precautions', []),  # items
            food_info.get('precaution_emergency', ''),  # emergency_note
            safety,  # safety_str
            str(blog_dir / "blog_06_precautions.png")  # output_path
        )

        # 7번: 조리방법
        generate_cooking_method(
            food_name,
            food_info.get('cooking_steps', []),  # steps
            food_info.get('cooking_tip', ''),  # tip
            safety,  # safety_str
            str(blog_dir / "blog_07_cooking.png")  # output_path
        )

        return True, "인포그래픽 5장 생성 완료"
    except Exception as e:
        return False, str(e)


def validate_content(content_path: Path, food_info: Dict, safety: str) -> Tuple[bool, List[str]]:
    """콘텐츠 검수"""
    errors = []
    # 2026-02-13: 플랫 구조
    insta_dir = content_path / "01_Insta&Thread"
    blog_dir = content_path / "02_Blog"

    # 캡션 검수 - 2026-02-13: 플랫 구조
    required_captions = [
        (insta_dir / "instagram_caption.txt", "instagram_caption.txt"),
        (blog_dir / "blog_caption.txt", "blog_caption.txt"),
        (insta_dir / "threads_caption.txt", "threads_caption.txt")
    ]
    for cap_path, cap_name in required_captions:
        if not cap_path.exists():
            errors.append(f"캡션 누락: {cap_name}")
        else:
            content = cap_path.read_text(encoding='utf-8')
            # 안전도 톤 검수
            if safety == "FORBIDDEN" and "급여 가능" in content:
                errors.append(f"톤 불일치: {cap_name} - FORBIDDEN인데 긍정적 톤")
            if safety == "SAFE" and "절대 금지" in content:
                errors.append(f"톤 불일치: {cap_name} - SAFE인데 경고 톤")

    # 인포그래픽 검수
    required_images = ["blog_03_nutrition.png", "blog_04_dodont.png",
                       "blog_05_dosage.png", "blog_06_precautions.png",
                       "blog_07_cooking.png"]
    for img in required_images:
        img_path = blog_dir / img
        if not img_path.exists():
            errors.append(f"이미지 누락: {img}")

    return len(errors) == 0, errors


def print_status(current: int, total: int, content_name: str, status: str,
                 results: BatchResult):
    """터미널 상태 표시"""
    print("\033[2J\033[H")  # 화면 클리어

    print("━" * 60)
    print(f"{Colors.BOLD}🌙 야간 작업 진행 현황{Colors.RESET}")
    print("━" * 60)
    print()

    # 진행바
    progress = int((current / total) * 40)
    bar = "█" * progress + "░" * (40 - progress)
    print(f"[{bar}] {current}/{total}")
    print()

    # 현재 작업
    print(f"📌 현재: {content_name} - {status}")
    print()

    # 통계
    print(f"✅ 캡션: {results.caption_success}건 완료 / {results.caption_fail}건 실패")
    print(f"🖼️ 이미지: {results.image_success}건 완료 / {results.image_fail}건 실패")
    print(f"📝 표지: {results.cover_success}건 완료 / {results.cover_fail}건 실패")

    if results.errors:
        print()
        print(f"{Colors.RED}❌ 최근 오류:{Colors.RESET}")
        for err in results.errors[-3:]:
            print(f"   {err}")

    print()
    print("━" * 60)


def process_content(folder_info: Dict, food_data: Dict, results: BatchResult) -> bool:
    """단일 콘텐츠 처리"""
    folder_name = folder_info['name']
    safety = folder_info['safety']

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    content_path = None
    # for status_dir in ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]:
    #     check_path = CONTENTS_DIR / status_dir / folder_name
    #     if check_path.exists():
    #         content_path = check_path
    #         break
    check_path = CONTENTS_DIR / folder_name
    if check_path.exists():
        content_path = check_path

    if not content_path:
        results.errors.append(f"폴더 없음: {folder_name}")
        return False

    # 음식 정보 가져오기
    food_info = get_food_info(folder_name, food_data)
    if not food_info:
        # 기본 템플릿 사용
        food_info = create_default_food_info(folder_name, safety)

    # 폴더 구조 생성
    ensure_folder_structure(content_path)

    # 1. 캡션 생성
    success, msg = generate_captions(content_path, food_info, safety)
    if success:
        results.caption_success += 1
    else:
        results.caption_fail += 1
        results.errors.append(f"{folder_name}: 캡션 - {msg}")

    # 2. 인포그래픽 생성
    success, msg = generate_infographics(content_path, food_info, safety)
    if success:
        results.image_success += 1
    else:
        results.image_fail += 1
        results.errors.append(f"{folder_name}: 이미지 - {msg}")

    # 3. 검수
    passed, errors = validate_content(content_path, food_info, safety)
    if not passed:
        # 재작업 시도
        for error in errors:
            results.errors.append(f"{folder_name}: 검수 - {error}")

        # 캡션 재생성 시도
        if any("캡션" in e for e in errors):
            results.caption_retry += 1
            success, _ = generate_captions(content_path, food_info, safety)

        # 이미지 재생성 시도
        if any("이미지" in e for e in errors):
            results.image_retry += 1
            success, _ = generate_infographics(content_path, food_info, safety)

        # 재검수
        passed, _ = validate_content(content_path, food_info, safety)

    # 상태 파일 저장
    status_file = content_path / "status.json"
    status_data = {
        "processed_at": datetime.now().isoformat(),
        "safety": safety,
        "validation_passed": passed,
        "captions": ["instagram", "blog", "threads"],
        "images": ["blog_03", "blog_04", "blog_05", "blog_06", "blog_07"]
    }
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

    return passed


def create_default_food_info(folder_name: str, safety: str) -> Dict:
    """기본 음식 정보 생성"""
    # 폴더명에서 음식명 추출 (예: 033_baguette -> baguette)
    parts = folder_name.split('_', 1)
    food_name = parts[1] if len(parts) > 1 else folder_name
    food_name = food_name.replace('_', ' ').title()

    return {
        "name": food_name,
        "english_name": parts[1] if len(parts) > 1 else folder_name,
        "safety": safety,
        "nutrients": [
            {"name": "주요 영양소", "benefit": "건강 효능", "value": "100", "unit": "mg"},
            {"name": "비타민", "benefit": "면역력 강화", "value": "10", "unit": "mg"},
            {"name": "미네랄", "benefit": "건강 유지", "value": "5", "unit": "mg"},
            {"name": "식이섬유", "benefit": "소화 건강", "value": "2", "unit": "g"},
        ],
        "dosages": {
            "소형견": {"weight": "5kg 이하", "amount": "10~20g", "desc": "소량"},
            "중형견": {"weight": "5~15kg", "amount": "20~40g", "desc": "적정량"},
            "대형견": {"weight": "15~30kg", "amount": "40~60g", "desc": "적정량"},
            "초대형견": {"weight": "30kg 이상", "amount": "60~80g", "desc": "적정량"},
        },
        "do_items": ["깨끗이 씻어서 급여", "작게 잘라서 급여", "소량씩 급여", "신선한 것만 급여", "반응 확인 후 급여"],
        "dont_items": ["과다 급여 금지", "양념된 것 급여 금지", "상한 것 급여 금지", "가공품 급여 금지", "매일 급여 금지"],
        "precautions": [
            {"title": "적정량 준수", "desc": "하루 칼로리의 10% 이내"},
            {"title": "처음 급여 시 주의", "desc": "소량부터 시작"},
            {"title": "알러지 확인", "desc": "24시간 관찰"},
            {"title": "신선도 확인", "desc": "상한 것 급여 금지"},
        ],
        "cooking_steps": [
            {"title": "세척", "desc": "깨끗이 씻기"},
            {"title": "손질", "desc": "먹을 수 없는 부분 제거"},
            {"title": "자르기", "desc": "먹기 좋은 크기로"},
            {"title": "조리", "desc": "필요시 익혀서"},
            {"title": "식히기", "desc": "적당히 식힌 후 급여"},
        ],
        "nutrition_footnote": "개체별 차이가 있으므로 반응을 보며 조절하세요",
        "dosage_warning": ["하루 칼로리의 10% 이내로 급여해주세요"],
        "dosage_footnote": "개체별 차이가 있으므로 반응을 보며 조절하세요",
        "precaution_emergency": "이상 증상 시 수의사 상담",
        "cooking_tip": "신선한 재료로 간단하게 준비"
    }


def save_report(results: BatchResult, output_path: Path):
    """완료 보고서 저장"""
    elapsed = datetime.now() - results.start_time
    hours = elapsed.total_seconds() / 3600

    report = f"""[WO-NIGHT-001 완료 보고]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| 항목 | 완료 | 실패 | 재작업 |
|------|------|------|--------|
| 캡션 | {results.caption_success}건 | {results.caption_fail}건 | {results.caption_retry}건 |
| 블로그 이미지 | {results.image_success}건 | {results.image_fail}건 | {results.image_retry}건 |
| 표지 | {results.cover_success}건 | {results.cover_fail}건 | 0건 |
| CTA 이미지 | 0건 | 0건 | 0건 |

총 소요 시간: {hours:.1f}시간
생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
    if results.errors:
        report += "실패 목록:\n"
        for err in results.errors:
            report += f"  - {err}\n"

    report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)


def main():
    parser = argparse.ArgumentParser(description="WO-NIGHT-001 야간 배치 처리")
    parser.add_argument("--test", action="store_true", help="1개 테스트 실행")
    parser.add_argument("--start", type=int, default=0, help="시작 인덱스")
    parser.add_argument("--end", type=int, default=None, help="종료 인덱스")
    parser.add_argument("--all", action="store_true", help="전체 실행")
    parser.add_argument("--dry-run", action="store_true", help="실제 생성 없이 확인만")
    args = parser.parse_args()

    # 로그 디렉토리 생성
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 대상 로드
    targets = load_targets()
    if not targets:
        print("처리할 대상이 없습니다.")
        return

    print(f"📊 처리 대상: {len(targets)}개 (UNKNOWN 제외)")

    # 범위 설정
    if args.test:
        targets = targets[:1]
        print("🧪 테스트 모드: 1개만 처리")
    elif args.end:
        targets = targets[args.start:args.end]
        print(f"📍 범위: {args.start} ~ {args.end}")
    elif not args.all:
        print("전체 실행하려면 --all 옵션을 사용하세요.")
        print("테스트: --test")
        print("범위 지정: --start N --end M")
        return

    if args.dry_run:
        print("\n🔍 Dry-run 모드 - 실제 생성 없음")
        for t in targets:
            print(f"  - {t['name']} ({t['safety']})")
        return

    # 음식 데이터 로드
    food_data = load_food_data()

    # 배치 처리
    results = BatchResult()
    total = len(targets)

    for i, target in enumerate(targets):
        print_status(i + 1, total, target['name'], "처리 중...", results)

        success = process_content(target, food_data, results)

        status = "✅ 완료" if success else "❌ 실패"
        print_status(i + 1, total, target['name'], status, results)

        time.sleep(0.5)  # 속도 조절

    # 보고서 저장
    report_path = LOG_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    save_report(results, report_path)

    print(f"\n📄 보고서 저장: {report_path}")


if __name__ == "__main__":
    main()
