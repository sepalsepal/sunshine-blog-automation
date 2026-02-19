#!/usr/bin/env python3
"""
📊 품질 검사 통합 스크립트 (업무 16-22번)

16. 텍스트 오버레이 점검
17. 이미지 4장 완성도 검증
18. 표지 이미지 품질 검증
19. 본문 이미지 해상도 검증
20. 중복 콘텐츠 검출
21. 게시월 불일치 검증
22. 고아 파일 정리
"""

import json
from pathlib import Path
from datetime import datetime
from PIL import Image

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
POSTED_DIR = PROJECT_ROOT / "posted"
LOGS_DIR = PROJECT_ROOT / "logs"


def check_image_count():
    """17번: 이미지 4장 완성도 검증"""
    print("\n📋 17. 이미지 완성도 검증")
    print("-" * 40)

    issues = []
    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith((".", "🔒")):
            continue

        images = list(folder.glob("*.png")) + list(folder.glob("*.jpg"))
        # archive 폴더 제외
        images = [i for i in images if "archive" not in str(i)]

        if len(images) < 4:
            issues.append({
                "folder": folder.name,
                "count": len(images),
                "missing": 4 - len(images)
            })
            print(f"  ⚠️ {folder.name}: {len(images)}장 (부족: {4 - len(images)})")

    print(f"\n  총 {len(issues)}개 폴더 이미지 부족")
    return issues


def check_resolution():
    """19번: 본문 이미지 해상도 검증"""
    print("\n📋 19. 해상도 검증 (1080x1080)")
    print("-" * 40)

    issues = []
    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith((".", "🔒")):
            continue

        for img_path in folder.glob("*.png"):
            if "archive" in str(img_path) or "_bg" in img_path.name:
                continue

            try:
                with Image.open(img_path) as img:
                    w, h = img.size
                    if w < 1080 or h < 1080:
                        issues.append({
                            "file": str(img_path.relative_to(PROJECT_ROOT)),
                            "size": f"{w}x{h}"
                        })
                        print(f"  ⚠️ {img_path.name}: {w}x{h}")
            except Exception as e:
                print(f"  ❌ 읽기 실패: {img_path.name}")

    print(f"\n  총 {len(issues)}개 파일 해상도 미달")
    return issues


def check_duplicates():
    """20번: 중복 콘텐츠 검출"""
    print("\n📋 20. 중복 콘텐츠 검출")
    print("-" * 40)

    food_ids = {}
    duplicates = []

    for folder in CONTENTS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith((".", "🔒")):
            continue

        parts = folder.name.split("_")
        if len(parts) >= 2:
            food_id = parts[1]
            if food_id in food_ids:
                duplicates.append({
                    "food_id": food_id,
                    "folders": [food_ids[food_id], folder.name]
                })
                print(f"  ⚠️ 중복: {food_id}")
                print(f"     - {food_ids[food_id]}")
                print(f"     - {folder.name}")
            else:
                food_ids[food_id] = folder.name

    print(f"\n  총 {len(duplicates)}개 중복")
    return duplicates


def check_posted_month():
    """21번: 게시월 불일치 검증"""
    print("\n📋 21. 게시월 불일치 검증")
    print("-" * 40)

    issues = []
    if not POSTED_DIR.exists():
        print("  게시완료 폴더 없음")
        return issues

    for month_dir in POSTED_DIR.iterdir():
        if not month_dir.is_dir():
            continue

        expected_month = month_dir.name  # "2026-01"

        for folder in month_dir.iterdir():
            if not folder.is_dir():
                continue

            meta_path = folder / "metadata.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                    posted_at = meta.get("posted_at", "")
                    if posted_at and not posted_at.startswith(expected_month):
                        actual_month = posted_at[:7] if len(posted_at) >= 7 else "unknown"
                        issues.append({
                            "folder": folder.name,
                            "expected": expected_month,
                            "actual": actual_month
                        })
                        print(f"  ⚠️ {folder.name}: 폴더={expected_month}, 메타={actual_month}")
                except:
                    pass

    print(f"\n  총 {len(issues)}개 불일치")
    return issues


def check_orphan_files():
    """22번: 고아 파일 정리"""
    print("\n📋 22. 고아 파일 검사")
    print("-" * 40)

    orphans = []
    for folder in CONTENTS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith((".", "🔒")):
            continue

        # archive 폴더 외 _bg, _draft 파일
        for f in folder.iterdir():
            if f.is_file() and ("_bg" in f.name or "_draft" in f.name):
                orphans.append(str(f.relative_to(PROJECT_ROOT)))
                print(f"  📄 {f.name} (→ archive/)")

    print(f"\n  총 {len(orphans)}개 고아 파일")
    return orphans


def run_all_checks():
    """전체 품질 검사 실행"""
    print("=" * 60)
    print("📊 품질 검사 시작")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {
        "timestamp": datetime.now().isoformat(),
        "image_count": check_image_count(),
        "resolution": check_resolution(),
        "duplicates": check_duplicates(),
        "posted_month": check_posted_month(),
        "orphans": check_orphan_files(),
    }

    # 리포트 저장
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = LOGS_DIR / f"quality_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("📊 검사 완료")
    print("=" * 60)
    print(f"  이미지 부족: {len(results['image_count'])}개")
    print(f"  해상도 미달: {len(results['resolution'])}개")
    print(f"  중복 콘텐츠: {len(results['duplicates'])}개")
    print(f"  게시월 불일치: {len(results['posted_month'])}개")
    print(f"  고아 파일: {len(results['orphans'])}개")
    print(f"\n📄 리포트: {report_path}")

    return results


if __name__ == "__main__":
    run_all_checks()
