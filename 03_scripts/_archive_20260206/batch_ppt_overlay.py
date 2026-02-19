#!/usr/bin/env python3
"""
배치 PPT 템플릿 텍스트 오버레이
- render_with_ppt_template.py의 함수 활용
- 10개 콘텐츠 일괄 처리

담당: 김과장
검수: 김감독
"""

import json
import shutil
from pathlib import Path

# 기존 스크립트 임포트
import sys
sys.path.insert(0, str(Path(__file__).parent))
from render_with_ppt_template import create_slide_with_template

ROOT = Path(__file__).parent.parent.parent
CONTENT_DIR = ROOT / "content" / "images"
SETTINGS_DIR = ROOT / "config" / "settings"


def get_text_settings(food_name: str) -> list:
    """텍스트 설정 파일 로드"""
    patterns = [
        f"{food_name}_text.json",
        f"{food_name.replace('_', '')}_text.json",
    ]

    for pattern in patterns:
        path = SETTINGS_DIR / pattern
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


def process_folder(folder_path: Path) -> dict:
    """폴더 내 본문 이미지에 PPT 템플릿으로 텍스트 오버레이"""
    folder_name = folder_path.name

    # 폴더명에서 영문명 추출 (예: 024_beef_소고기 → beef)
    parts = folder_name.split('_')
    if len(parts) >= 2:
        food_name = parts[1]
    else:
        food_name = folder_name

    print(f"\n📁 {folder_name}")

    # 텍스트 설정 로드
    text_settings = get_text_settings(food_name)
    if not text_settings:
        print(f"  ⚠️ 텍스트 설정 없음: {food_name}_text.json")
        return {'success': 0, 'failed': 0, 'skipped': 1}

    results = {'success': 0, 'failed': 0, 'skipped': 0}

    # 01, 02, 03 슬라이드 처리 (커버 00은 제외)
    for slide_data in text_settings:
        slide_num = slide_data.get('slide', 0)
        if slide_num == 0:  # 커버는 스킵
            continue

        slide_type = slide_data.get('type', 'content_bottom')
        title = slide_data.get('title', '')
        subtitle = slide_data.get('subtitle', '')

        # 입력 파일 찾기
        input_patterns = [
            folder_path / f"{food_name}_{slide_num:02d}.png",
            folder_path / f"{food_name}_0{slide_num}.png",
        ]

        input_path = None
        for pattern in input_patterns:
            if pattern.exists():
                input_path = pattern
                break

        if not input_path:
            print(f"  ⏭️ 슬라이드 {slide_num} 이미지 없음")
            results['skipped'] += 1
            continue

        # 원본 백업 (최초 1회만)
        bg_path = folder_path / f"{food_name}_{slide_num:02d}_bg.png"
        if not bg_path.exists():
            shutil.copy(input_path, bg_path)
            print(f"  💾 배경 백업: {bg_path.name}")

        print(f"  📝 슬라이드 {slide_num}: {title}")

        # PPT 템플릿으로 텍스트 오버레이
        try:
            success = create_slide_with_template(
                bg_image_path=str(bg_path),
                title=title,
                subtitle=subtitle,
                slide_type=slide_type,
                output_path=str(input_path)
            )

            if success:
                results['success'] += 1
                print(f"     ✅ 완료")
            else:
                results['failed'] += 1
                print(f"     ❌ 실패")
        except Exception as e:
            print(f"     ❌ 오류: {e}")
            results['failed'] += 1

    return results


def main():
    """메인 실행"""
    print("=" * 60)
    print("🎨 김과장입니다. PPT 템플릿 배치 텍스트 오버레이")
    print("   (render_with_ppt_template.py 함수 활용)")
    print("=" * 60)

    # 대상 폴더 목록
    target_folders = [
        "024_beef_소고기",
        "026_kale_케일",
        "030_poached_egg_수란",
        "044_burdock_우엉",
        "054_salmon_연어",
        "074_yangnyeom_chicken_양념치킨",
        "089_samgyeopsal_삼겹살",
        "094_icecream_아이스크림",
        "107_budweiser_버드와이저",
        "117_kitkat_킷캣",
    ]

    total_success = 0
    total_failed = 0
    total_skipped = 0

    for folder_name in target_folders:
        folder_path = CONTENT_DIR / folder_name
        if folder_path.exists():
            results = process_folder(folder_path)
            total_success += results['success']
            total_failed += results['failed']
            total_skipped += results['skipped']

    print("\n" + "=" * 60)
    print("📊 최종 결과")
    print("=" * 60)
    print(f"✅ 성공: {total_success}장")
    print(f"❌ 실패: {total_failed}장")
    print(f"⏭️ 스킵: {total_skipped}장")
    print("=" * 60)
    print("\n🎬 김감독님, 검수 부탁드립니다.")


if __name__ == '__main__':
    main()
