#!/usr/bin/env python3
"""
shrimp 콘텐츠 PPT 템플릿 재제작 스크립트

조건:
1. 자동 파이프라인만 사용 (수동 개별 처리 금지)
2. potato/burdock과 동일한 스타일 적용
3. CAUTION 기준 샘플로 지정

담당: 박편집
검수: 김감독
승인: 최부장
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

# 렌더 함수 임포트
from render_with_ppt_template import create_slide_with_template

ROOT = Path(__file__).parent.parent.parent
SHRIMP_DIR = ROOT / "content/images/140_shrimp_새우_published"
ARCHIVE_DIR = SHRIMP_DIR / "archive"
CONFIG_PATH = ROOT / "config/settings/shrimp_text.json"


def backup_current_images():
    """현재 이미지를 archive로 백업"""
    print("=" * 60)
    print("📦 박편집입니다. 기존 이미지 백업 시작합니다.")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ARCHIVE_DIR / f"before_template_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for i in range(4):
        src = SHRIMP_DIR / f"shrimp_0{i}.png"
        if src.exists():
            dst = backup_dir / f"shrimp_0{i}.png"
            shutil.copy(src, dst)
            print(f"   ✅ 백업: {src.name} → {backup_dir.name}/")

    print(f"\n   백업 완료: {backup_dir}")
    return backup_dir


def render_shrimp_content():
    """shrimp 콘텐츠 PPT 템플릿으로 렌더링"""

    print("\n" + "=" * 60)
    print("📝 박편집입니다. shrimp 콘텐츠 PPT 템플릿 작업 시작합니다.")
    print("=" * 60)

    # 텍스트 설정 로드
    with open(CONFIG_PATH, encoding='utf-8') as f:
        text_config = json.load(f)

    print(f"\n📋 텍스트 설정 로드 완료 ({len(text_config)}개 슬라이드)")
    for slide in text_config:
        print(f"   [{slide['slide']}] {slide['type']}: {slide['title']}")

    # 임시 디렉토리에서 작업 (기존 파일 덮어쓰기 방지)
    temp_dir = SHRIMP_DIR / "_temp_render"
    temp_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0

    for slide in text_config:
        slide_num = slide["slide"]
        slide_type = slide["type"]
        title = slide["title"]
        subtitle = slide.get("subtitle", "")

        # 소스 이미지 (현재 shrimp_0X.png)
        src_image = SHRIMP_DIR / f"shrimp_0{slide_num}.png"
        output_path = temp_dir / f"shrimp_0{slide_num}.png"

        if not src_image.exists():
            print(f"\n⚠️ 소스 이미지 없음: {src_image}")
            continue

        print(f"\n📌 Slide {slide_num} [{slide_type}]")
        print(f"   배경: {src_image.name}")
        print(f"   제목: {title}")
        print(f"   부제: {subtitle}")

        success = create_slide_with_template(
            bg_image_path=str(src_image),
            title=title,
            subtitle=subtitle,
            slide_type=slide_type,
            output_path=str(output_path)
        )

        if success:
            success_count += 1
        else:
            print(f"   ❌ 슬라이드 {slide_num} 실패")

    # 성공한 경우 temp에서 메인으로 이동
    if success_count == len(text_config):
        print(f"\n✅ 모든 슬라이드 렌더링 성공 ({success_count}/{len(text_config)})")

        for slide in text_config:
            slide_num = slide["slide"]
            src = temp_dir / f"shrimp_0{slide_num}.png"
            dst = SHRIMP_DIR / f"shrimp_0{slide_num}.png"

            if src.exists():
                shutil.move(str(src), str(dst))
                print(f"   ✅ 적용: {dst.name}")

        # temp 디렉토리 정리
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True
    else:
        print(f"\n❌ 일부 슬라이드 실패 ({success_count}/{len(text_config)})")
        print(f"   임시 파일 유지: {temp_dir}")
        return False


def main():
    """메인 실행"""
    print("=" * 60)
    print("🦐 SHRIMP 콘텐츠 재제작 (PPT 템플릿 파이프라인)")
    print("=" * 60)
    print(f"대상: {SHRIMP_DIR}")
    print(f"설정: {CONFIG_PATH}")
    print("=" * 60)

    # 1. 기존 이미지 백업
    backup_dir = backup_current_images()

    # 2. PPT 템플릿 렌더링
    success = render_shrimp_content()

    # 3. 결과 보고
    print("\n" + "=" * 60)
    if success:
        print("✅ 박편집입니다. shrimp 재제작 완료!")
        print("   김감독님 검수 부탁드립니다.")
    else:
        print("❌ 박편집입니다. 재제작 실패.")
        print(f"   백업 위치: {backup_dir}")
    print("=" * 60)

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
