#!/usr/bin/env python3
"""
일괄 경로 업데이트 스크립트
WO-RESOLVE-001-B: 45개 스크립트 레거시 경로 → 신규 경로
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 업데이트 대상 스크립트 (45개)
TARGET_SCRIPTS = [
    "audit_asset_matrix.py",
    "audit_captions.py",
    "audit_number_system.py",
    "audit_slide06.py",
    "batch_caption_all.py",
    "batch_runner.py",
    "blog_image_qc.py",
    "caption_recovery.py",
    "caption_safety_validator.py",
    "cleanup_blog_insta_images.py",
    "cleanup_content_folders.py",
    "cloudinary_download.py",
    "cloudinary_uploader.py",
    "content_status_manager.py",
    "cover_batch_001.py",
    "cover_hotfix_001.py",
    "cover_pipeline.py",
    "cover_test_001.py",
    "create_pd_review_folder.py",
    "download_missing_033_040.py",
    "extract_food_data.py",
    "fix_forbidden_captions.py",
    "forbidden_infographic_generator.py",
    "generate_blog_caption.py",
    "generate_thread_captions.py",
    "instagram_api_recovery.py",
    "move_clean_images.py",
    "night_batch.py",
    "notion_check.py",
    "regenerate_slide06.py",
    "reorganize_contents.py",
    "reorganize_from_cloudinary.py",
    "sync_folder_to_notion.py",
    "sync_hook.py",
    "sync_instagram_to_local.py",
    "sync_loop.py",
    "test_rename.py",
    "wo040_backup_system.py",
    "wo_rename_fix_fooddata.py",
    "wo_rename_step1_mapping.py",
    "wo_rename_step2_dryrun.py",
    "wo_rename_step3_snapshot.py",
    "wo_rename_step4_flatmerge.py",
    "wo_restructure_step2_dryrun.py",
    "wo_restructure_step5_update_refs.py",
]

# 경로 변환 매핑
PATH_REPLACEMENTS = [
    # STATUS_DIRS 패턴
    (r'STATUS_DIRS\s*=\s*\[.*?"1_cover_only".*?\]', '# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거\n# contents/ 직접 스캔'),
    (r'"1_cover_only"', '"# REMOVED: flat structure"'),
    (r'"2_body_ready"', '"# REMOVED: flat structure"'),
    (r'"3_approved"', '"# REMOVED: flat structure"'),
    (r'"4_posted"', '"# REMOVED: flat structure"'),

    # 폴더 경로
    (r'/ "blog"', '/ "02_Blog"'),
    (r'/ "insta"', '/ "01_Insta&Thread"'),
    (r'/ "thread"', '/ "01_Insta&Thread"'),
    (r'/ "captions"', '/ "01_Insta&Thread"'),
    (r'/ "0_clean"', '/ "00_Clean"'),
    (r'/ "0_Clean"', '/ "00_Clean"'),
    (r'"blog"', '"02_Blog"'),
    (r'"insta"', '"01_Insta&Thread"'),
    (r'"thread"', '"01_Insta&Thread"'),
    (r'"captions"', '"# REMOVED: use platform folders"'),
    (r'"0_clean"', '"00_Clean"'),
    (r'"0_Clean"', '"00_Clean"'),

    # 파일명 (소문자 → PascalCase)
    (r'_common_01_cover\.png', '_Common_01_Cover.png'),
    (r'_common_02_food\.png', '_Common_02_Food.png'),
    (r'_common_08_cta\.png', '_Common_08_Cta.png'),
    (r'_blog_03_nutrition\.png', '_Blog_03_Nutrition.png'),
    (r'_blog_04_feeding\.png', '_Blog_04_Feeding.png'),
    (r'_blog_05_amount\.png', '_Blog_05_Amount.png'),
    (r'_blog_06_caution\.png', '_Blog_06_Caution.png'),
    (r'_blog_07_cooking\.png', '_Blog_07_Cooking.png'),
    (r'_insta_03_dog\.png', '_Insta_03_Dog.png'),

    # 캡션 파일명
    (r'instagram_caption\.txt', '# PascalCase: {Food}_{Safety}_Insta_Caption.txt'),
    (r'threads_caption\.txt', '# PascalCase: {Food}_{Safety}_Threads_Caption.txt'),
    (r'blog_caption\.txt', '# PascalCase: {Food}_{Safety}_Blog_Caption.txt'),
    (r'"caption\.txt"', '"# PascalCase caption file"'),
]

def update_script(script_path: Path) -> dict:
    """단일 스크립트 업데이트"""
    result = {"file": script_path.name, "changes": 0, "lines": []}

    try:
        content = script_path.read_text(encoding="utf-8")
        original = content

        for pattern, replacement in PATH_REPLACEMENTS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                result["changes"] += len(matches)
                result["lines"].append(f"{pattern[:30]}... → {len(matches)}건")
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        if content != original:
            script_path.write_text(content, encoding="utf-8")

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    print("━" * 60)
    print("스크립트 경로 일괄 업데이트")
    print("━" * 60)

    total_changes = 0
    results = []

    for i, script_name in enumerate(TARGET_SCRIPTS, 1):
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            print(f"[{i:02d}/45] {script_name} ❌ (파일 없음)")
            continue

        result = update_script(script_path)
        results.append(result)

        if result["changes"] > 0:
            print(f"[{i:02d}/45] {script_name} ({result['changes']}줄 수정) ✅")
            total_changes += result["changes"]
        else:
            print(f"[{i:02d}/45] {script_name} (변경 없음)")

    print("━" * 60)
    print(f"완료: {len(results)}/45 스크립트")
    print(f"총 수정: {total_changes}건")
    print("━" * 60)

    return results


if __name__ == "__main__":
    main()
