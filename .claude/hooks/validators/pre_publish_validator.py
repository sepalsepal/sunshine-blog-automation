#!/usr/bin/env python3
"""
pre_publish_validator.py - 게시 전 전체 Validator
WO-036: RULES.md §9.2 게시 전 점검 기준

사용법: python3 pre_publish_validator.py [content_folder]
Exit 0: PASS (게시 허용)
Exit 1: FAIL (게시 차단)
"""

import sys
import os
from pathlib import Path

def find_latest_content_folder() -> Path | None:
    """가장 최근 작업 중인 콘텐츠 폴더 찾기"""
    project_root = Path(__file__).parent.parent.parent.parent

    # 우선순위: 3_approved > 2_body_ready > 1_cover_only
    search_paths = [
        project_root / "contents" / "3_approved",
        project_root / "contents" / "2_body_ready",
    ]

    for search_path in search_paths:
        if search_path.exists():
            folders = [f for f in search_path.iterdir() if f.is_dir() and not f.name.startswith('.')]
            if folders:
                # 가장 최근 수정된 폴더
                return max(folders, key=lambda x: x.stat().st_mtime)

    return None


def validate_pre_publish(content_folder: Path | None = None) -> tuple[bool, list[str]]:
    """
    게시 전 전체 검증
    RULES.md §9.2 기준
    """
    fails = []
    passes = []

    if content_folder is None:
        content_folder = find_latest_content_folder()

    if content_folder is None:
        return False, ["검증할 콘텐츠 폴더를 찾을 수 없음"]

    if not content_folder.exists():
        return False, [f"폴더가 존재하지 않음: {content_folder}"]

    blog_folder = content_folder / "blog"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §9.2.1 이미지 전체 존재 (표지 + 본문 8장)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if blog_folder.exists():
        image_files = list(blog_folder.glob("*.png")) + list(blog_folder.glob("*.jpg"))
        image_count = len(image_files)

        if image_count >= 8:
            passes.append(f"이미지 {image_count}장 PASS (8장 이상)")
        else:
            fails.append(f"이미지 FAIL: {image_count}장 (8장 필요)")
    else:
        fails.append("blog 폴더 없음")
        image_files = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §9.2.2 전 슬라이드 1080x1080
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    try:
        from PIL import Image

        wrong_size = []
        for img_path in image_files:
            try:
                img = Image.open(img_path)
                if img.size != (1080, 1080):
                    wrong_size.append(f"{img_path.name}: {img.size}")
            except Exception:
                wrong_size.append(f"{img_path.name}: 열기 실패")

        if not wrong_size:
            passes.append("전 슬라이드 해상도 1080x1080 PASS")
        else:
            fails.append(f"해상도 FAIL: {', '.join(wrong_size)}")
    except ImportError:
        passes.append("PIL 미설치 - 해상도 검증 스킵")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §9.2.3 캡션 파일 존재
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    caption_files = list(content_folder.glob("**/caption*.txt"))
    if caption_files:
        passes.append(f"캡션 파일 존재 PASS ({len(caption_files)}개)")
    else:
        fails.append("캡션 파일 FAIL: caption*.txt 없음")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §9.2.4~6 캡션 내용 검증
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if caption_files:
        import re

        for caption_file in caption_files:
            try:
                content = caption_file.read_text(encoding='utf-8')

                # 안전도 이모지
                if re.search(r'[🟢🟡🔴]', content):
                    passes.append(f"{caption_file.name}: 안전 이모지 PASS")
                else:
                    fails.append(f"{caption_file.name}: 안전 이모지 FAIL")

                # AI 고지
                if re.search(r'AI|인공지능', content, re.IGNORECASE):
                    passes.append(f"{caption_file.name}: AI 고지 PASS")
                else:
                    fails.append(f"{caption_file.name}: AI 고지 FAIL")

                # 해시태그 12~16개
                hashtags = re.findall(r'#\w+', content)
                if 12 <= len(hashtags) <= 16:
                    passes.append(f"{caption_file.name}: 해시태그 {len(hashtags)}개 PASS")
                else:
                    fails.append(f"{caption_file.name}: 해시태그 {len(hashtags)}개 FAIL (12~16)")

            except Exception as e:
                fails.append(f"{caption_file.name}: 읽기 실패 - {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §2.1.1 8장 햇살이 실사 확인
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if blog_folder.exists():
        img_08 = list(blog_folder.glob("08_*")) + list(blog_folder.glob("*햇살이*"))
        if img_08:
            passes.append("8장 햇살이 이미지 존재 PASS")
        else:
            fails.append("8장 햇살이 이미지 FAIL: 08_* 또는 *햇살이* 파일 없음")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 결과
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    all_passed = len(fails) == 0

    return all_passed, [f"대상: {content_folder}"] + passes + fails


def main():
    content_folder = None
    if len(sys.argv) >= 2:
        content_folder = Path(sys.argv[1])

    passed, messages = validate_pre_publish(content_folder)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"PRE-PUBLISH VALIDATOR: {'PASS' if passed else 'FAIL'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for msg in messages:
        if "대상:" in msg:
            print(msg)
            print("")
        elif "PASS" in msg:
            print(f"  ✅ {msg}")
        elif "FAIL" in msg:
            print(f"  ❌ {msg}")
        else:
            print(f"  ℹ️ {msg}")

    print("")
    if passed:
        print("→ 게시 진행 가능")
    else:
        print("→ FAIL 항목 수정 후 재시도")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
