#!/usr/bin/env python3
"""
쓰레드 캡션 AI 표기 추가 스크립트
"""

from pathlib import Path

BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine")
CONTENT_DIR = BASE_DIR / "content/images"

AI_DISCLAIMER = "\n\nℹ️ AI 생성 이미지 포함"
REQUIRED_CHECK = "AI"

def fix_caption(caption_path):
    """캡션에 AI 표기 추가"""
    if not caption_path.exists():
        return False, "파일 없음"

    content = caption_path.read_text(encoding='utf-8')

    # 이미 있으면 스킵
    if REQUIRED_CHECK in content and "생성" in content:
        return False, "이미 포함"

    # AI 표기 추가
    new_content = content.rstrip() + AI_DISCLAIMER
    caption_path.write_text(new_content, encoding='utf-8')

    return True, "추가 완료"

def main():
    print("=" * 60)
    print("🔧 쓰레드 캡션 AI 표기 수정 시작")
    print("=" * 60)

    fixed_count = 0
    skipped_count = 0

    for folder in sorted(CONTENT_DIR.iterdir()):
        if folder.is_dir() and folder.name != '000_cover':
            caption_threads = folder / "caption_threads.txt"
            if caption_threads.exists():
                fixed, status = fix_caption(caption_threads)
                if fixed:
                    fixed_count += 1
                    print(f"  ✅ {folder.name}")
                else:
                    skipped_count += 1

    print("\n" + "=" * 60)
    print(f"✅ 수정 완료: {fixed_count}개")
    print(f"⏭️ 스킵: {skipped_count}개")
    print("=" * 60)

if __name__ == "__main__":
    main()
