#!/usr/bin/env python3
"""
WO-RESTRUCTURE-001 STEP 5: 코드 참조 업데이트
STATUS_DIRS → 직접 contents/ 스캔 방식으로 변경
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 2026-02-13: 플랫 구조 적용 완료 - 참조용
# 업데이트 대상 패턴
OLD_PATTERNS = [
    (r'STATUS_DIRS\s*=\s*\[.*?"1_cover_only".*?\]', '# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거'),
    (r'"1_cover_only"', '"DEPRECATED"'),
    (r'"2_body_ready"', '"DEPRECATED"'),
    (r'"3_approved"', '"DEPRECATED"'),
    (r'"4_posted"', '"DEPRECATED"'),
    (r'/blog/', '/02_Blog/'),
    (r'/insta/', '/01_Insta&Thread/'),
    (r'/captions/', '# 2026-02-13: captions/ 제거 - 각 플랫폼 폴더 내'),
    (r'/0_Clean', '/00_Clean'),
    (r'/ blog /', '/ 02_Blog /'),
    (r'/ insta /', '/ 01_Insta&Thread /'),
]


def analyze_scripts():
    """스크립트 참조 분석"""
    results = {
        "status_dirs": [],
        "blog_ref": [],
        "insta_ref": [],
        "captions_ref": [],
        "clean_ref": [],
    }

    for script in SCRIPTS_DIR.glob("*.py"):
        # WO- 스크립트는 제외 (마이그레이션 도구)
        if script.name.startswith("wo_"):
            continue

        content = script.read_text(encoding="utf-8")

        if "STATUS_DIRS" in content or "1_cover_only" in content:
            results["status_dirs"].append(script.name)
        if "/blog/" in content.lower() or '"blog"' in content.lower():
            results["blog_ref"].append(script.name)
        if "/insta/" in content.lower() or '"insta"' in content.lower():
            results["insta_ref"].append(script.name)
        if "/captions/" in content.lower() or '"captions"' in content.lower():
            results["captions_ref"].append(script.name)
        if "/0_clean/" in content.lower() or '"0_clean"' in content.lower():
            results["clean_ref"].append(script.name)

    return results


def main():
    print("━━━━━ STEP 5: 코드 참조 분석 ━━━━━")

    results = analyze_scripts()

    print(f"\n[분석 결과]")
    print(f"  STATUS_DIRS 참조: {len(results['status_dirs'])}개 스크립트")
    print(f"  /blog/ 참조: {len(results['blog_ref'])}개 스크립트")
    print(f"  /insta/ 참조: {len(results['insta_ref'])}개 스크립트")
    print(f"  /captions/ 참조: {len(results['captions_ref'])}개 스크립트")
    print(f"  /0_clean/ 참조: {len(results['clean_ref'])}개 스크립트")

    # 영향받는 파일 목록
    all_affected = set()
    for key, files in results.items():
        all_affected.update(files)

    print(f"\n[영향받는 스크립트] ({len(all_affected)}개)")
    for f in sorted(all_affected):
        print(f"  - {f}")

    # 주요 스크립트 상세 분석
    print(f"\n[주요 스크립트 상세]")
    key_scripts = [
        "batch_produce_v2.py",
        "batch_infographic.py",
        "generate_captions.py",
        "cloudinary_uploader.py",
        "notion_sync.py",
    ]

    for script_name in key_scripts:
        script_path = SCRIPTS_DIR / script_name
        if script_path.exists():
            content = script_path.read_text(encoding="utf-8")

            # STATUS_DIRS 라인 찾기
            status_match = re.search(r'STATUS_DIRS\s*=\s*\[.*?\]', content)
            if status_match:
                print(f"  {script_name}:")
                print(f"    현재: {status_match.group()[:60]}...")
                print(f"    변경: STATUS_DIRS = []  # Flat structure")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("코드 참조 분석 완료")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("\n⚠️ 주의: 자동 업데이트 미실행")
    print("  → 각 스크립트 수동 검토 권장")
    print("  → 새 경로 매핑:")
    print("    blog/ → 02_Blog/")
    print("    insta/ → 01_Insta&Thread/")
    print("    captions/ → (각 플랫폼 폴더 내)")
    print("    0_Clean/ → 00_Clean/")
    print("    STATUS_DIRS → contents/ 직접 스캔")

    return results


if __name__ == "__main__":
    main()
