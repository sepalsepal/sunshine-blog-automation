#!/usr/bin/env python3
"""
김감독 품질 검수 스크립트
v9.1 규칙 기반 자동 검수
"""

import os
import re
from pathlib import Path
from PIL import Image

BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine")
CONTENT_DIR = BASE_DIR / "content/images"

# 검수 기준
EXPECTED_SIZE = (1080, 1080)
REQUIRED_AI_DISCLAIMER = ["AI로 생성되었습니다", "AI 생성 이미지"]

# DANGER 음식 목록
DANGER_FOODS = [
    'onion', 'garlic', 'grape', 'raisin', 'chocolate',
    'budweiser', 'cass_beer', 'soju', 'fanta', 'coca_cola',
    'sprite', 'milkis', 'starbucks_coffee', 'perrier'
]

# 알코올/카페인 금지 음식
STRICTLY_FORBIDDEN = ['budweiser', 'cass_beer', 'soju', 'starbucks_coffee']

def check_image(image_path):
    """이미지 품질 검사"""
    issues = []

    if not image_path.exists():
        return ["이미지 파일 없음"]

    try:
        img = Image.open(image_path)
        if img.size != EXPECTED_SIZE:
            issues.append(f"크기 오류: {img.size} (기대: {EXPECTED_SIZE})")
    except Exception as e:
        issues.append(f"이미지 로드 실패: {e}")

    return issues

def check_caption(caption_path, is_danger):
    """캡션 품질 검사"""
    issues = []

    if not caption_path.exists():
        return ["캡션 파일 없음"]

    content = caption_path.read_text(encoding='utf-8')

    # AI 표기 확인
    has_ai_disclaimer = any(d in content for d in REQUIRED_AI_DISCLAIMER)
    if not has_ai_disclaimer:
        issues.append("AI 표기 누락")

    # DANGER 표기 확인
    if is_danger:
        if "🚫" not in content and "❌" not in content:
            issues.append("DANGER 표기 누락 (🚫 또는 ❌ 필요)")
    else:
        if "🚫" in content:
            issues.append("안전 음식인데 금지 표기됨")

    return issues

def review_content(folder_path):
    """단일 콘텐츠 검수"""
    folder_name = folder_path.name

    # 폴더명에서 정보 추출
    match = re.match(r'(\d+)_([a-z_]+)_(.+?)(?:_published)?$', folder_name)
    if not match:
        return {"folder": folder_name, "status": "스킵", "issues": ["폴더명 형식 오류"]}

    num, english, korean = match.groups()

    # DANGER 여부 확인
    is_danger = any(d in english for d in DANGER_FOODS)
    is_strictly_forbidden = any(d in english for d in STRICTLY_FORBIDDEN)

    issues = []

    # 커버 이미지 검사
    cover_files = list(folder_path.glob(f"{english}_00.png")) + list(folder_path.glob(f"*_00*.png"))
    if cover_files:
        issues.extend(check_image(cover_files[0]))
    else:
        issues.append("커버 이미지 없음")

    # 캡션 검사
    caption_insta = folder_path / "caption_instagram.txt"
    caption_threads = folder_path / "caption_threads.txt"

    issues.extend([f"[인스타] {i}" for i in check_caption(caption_insta, is_danger)])
    issues.extend([f"[쓰레드] {i}" for i in check_caption(caption_threads, is_danger)])

    # 특별 경고 (이슈로 카운트하지 않음)
    warnings = []
    if is_strictly_forbidden:
        warnings.append("⚠️ 알코올/카페인 - 특별 주의 필요")

    status = "PASS" if not issues else "FAIL"

    return {
        "folder": folder_name,
        "english": english,
        "korean": korean,
        "is_danger": is_danger,
        "status": status,
        "issues": issues
    }

def main():
    print("=" * 70)
    print("🎬 김감독입니다. 품질 검수를 시작합니다.")
    print("=" * 70)

    # 새로 생성된 콘텐츠 폴더만 검수 (시스템 폴더 제외)
    SKIP_FOLDERS = {'000_cover', 'archive', 'reference', 'sunshine', 'temp', '.DS_Store'}
    content_folders = []
    for folder in sorted(CONTENT_DIR.iterdir()):
        if folder.is_dir() and folder.name not in SKIP_FOLDERS:
            if 'published' not in folder.name:
                content_folders.append(folder)

    print(f"\n📁 검수 대상: {len(content_folders)}개 콘텐츠")

    passed = []
    failed = []

    for folder in content_folders:
        result = review_content(folder)
        if result["status"] == "PASS":
            passed.append(result)
        else:
            failed.append(result)

    # 결과 출력
    print("\n" + "=" * 70)
    print("📊 검수 결과")
    print("=" * 70)
    print(f"  ✅ PASS: {len(passed)}개")
    print(f"  ❌ FAIL: {len(failed)}개")

    if failed:
        print(f"\n❌ 실패 항목 ({len(failed)}개):")
        for result in failed[:30]:  # 처음 30개만 출력
            print(f"\n  📁 {result['folder']}")
            for issue in result['issues']:
                print(f"      - {issue}")
        if len(failed) > 30:
            print(f"\n  ... 외 {len(failed) - 30}개")

    # DANGER 음식 목록
    danger_contents = [r for r in passed + failed if r.get('is_danger')]
    if danger_contents:
        print(f"\n⚠️ DANGER 음식 ({len(danger_contents)}개):")
        for r in danger_contents[:20]:
            status = "✅" if r['status'] == 'PASS' else "❌"
            print(f"    {status} {r['korean']} ({r['english']})")

    print("\n" + "=" * 70)
    print("🎬 김감독 검수 완료")
    print("=" * 70)

    return passed, failed

if __name__ == "__main__":
    main()
