#!/usr/bin/env python3
"""
Cloudinary Backup Script
백업 대상 파일들을 _backup/2026-02-13/ 폴더로 이동
"""

import requests
import json
from datetime import datetime

CLOUD_NAME = "ddzbnrfei"
API_KEY = "873749328429167"
API_SECRET = "EQ_ZtHiD-IEX8pzqKsxlVPndk4E"
BASE_URL = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}"
AUTH = (API_KEY, API_SECRET)

BACKUP_DATE = "2026-02-13"
BACKUP_PREFIX = f"_backup/{BACKUP_DATE}"

def get_all_resources():
    """모든 이미지 리소스 조회"""
    resp = requests.get(f"{BASE_URL}/resources/image", params={"max_results": 500}, auth=AUTH)
    return resp.json().get("resources", [])

def identify_backup_targets(resources):
    """백업 대상 파일 식별"""
    backup_targets = []

    # 1. 미발행 폴더 (without _published suffix)
    unpublished_folders = [
        "011_strawberry", "012_mango", "013_orange",
        "014_pear", "015_kiwi", "016_papaya", "017_peach"
    ]

    # 2. Legacy folders
    legacy_prefixes = ["dog_food/", "sunshinedogfood/"]

    for r in resources:
        public_id = r["public_id"]
        folder = public_id.rsplit("/", 1)[0] if "/" in public_id else ""
        filename = public_id.rsplit("/", 1)[-1]

        # Check unpublished folders
        if folder in unpublished_folders:
            backup_targets.append({
                "public_id": public_id,
                "bytes": r.get("bytes", 0),
                "category": "unpublished",
                "backup_folder": f"{BACKUP_PREFIX}/{folder}",
                "new_public_id": f"{BACKUP_PREFIX}/{folder}/{filename}"
            })

        # Check legacy folders
        elif public_id.startswith("dog_food/"):
            subfolder = folder.replace("dog_food/", "")
            backup_targets.append({
                "public_id": public_id,
                "bytes": r.get("bytes", 0),
                "category": "legacy_dog_food",
                "backup_folder": f"{BACKUP_PREFIX}/dog_food/{subfolder}",
                "new_public_id": f"{BACKUP_PREFIX}/dog_food/{subfolder}/{filename}"
            })

        elif public_id.startswith("sunshinedogfood/"):
            subfolder = folder.replace("sunshinedogfood/", "")
            backup_targets.append({
                "public_id": public_id,
                "bytes": r.get("bytes", 0),
                "category": "legacy_sunshinedogfood",
                "backup_folder": f"{BACKUP_PREFIX}/sunshinedogfood/{subfolder}",
                "new_public_id": f"{BACKUP_PREFIX}/sunshinedogfood/{subfolder}/{filename}"
            })

        # Check threads folder
        elif folder.startswith("threads/"):
            subfolder = folder.replace("threads/", "")
            backup_targets.append({
                "public_id": public_id,
                "bytes": r.get("bytes", 0),
                "category": "threads_duplicate",
                "backup_folder": f"{BACKUP_PREFIX}/threads/{subfolder}",
                "new_public_id": f"{BACKUP_PREFIX}/threads/{subfolder}/{filename}"
            })

    return backup_targets

def rename_resource(from_public_id, to_public_id):
    """Cloudinary rename API를 사용하여 파일 이동"""
    url = f"{BASE_URL}/image/rename"
    data = {
        "from_public_id": from_public_id,
        "to_public_id": to_public_id
    }
    resp = requests.post(url, data=data, auth=AUTH)
    return resp.status_code == 200, resp.json()

def main():
    print("=" * 60)
    print("Cloudinary Backup Script")
    print("=" * 60)

    # 1. Get all resources
    print("\n[1/4] 리소스 조회 중...")
    resources = get_all_resources()
    print(f"  총 리소스: {len(resources)}개")

    # 2. Identify backup targets
    print("\n[2/4] 백업 대상 식별 중...")
    targets = identify_backup_targets(resources)
    print(f"  백업 대상: {len(targets)}개")

    total_bytes = sum(t["bytes"] for t in targets)
    print(f"  총 용량: {total_bytes / 1024 / 1024:.2f}MB")

    # Category breakdown
    categories = {}
    for t in targets:
        cat = t["category"]
        if cat not in categories:
            categories[cat] = {"count": 0, "bytes": 0}
        categories[cat]["count"] += 1
        categories[cat]["bytes"] += t["bytes"]

    print("\n  카테고리별:")
    for cat, data in sorted(categories.items()):
        print(f"    - {cat}: {data['count']}개 ({data['bytes']/1024/1024:.2f}MB)")

    # 3. Execute backup (rename operations)
    print("\n[3/4] 백업 실행 중...")
    backup_log = {
        "backup_date": BACKUP_DATE,
        "total_files": len(targets),
        "total_size_mb": round(total_bytes / 1024 / 1024, 2),
        "files": []
    }

    success_count = 0
    fail_count = 0

    for i, t in enumerate(targets, 1):
        from_id = t["public_id"]
        to_id = t["new_public_id"]

        success, result = rename_resource(from_id, to_id)

        if success:
            success_count += 1
            backup_log["files"].append({
                "original_path": from_id,
                "backup_path": to_id,
                "size_mb": round(t["bytes"] / 1024 / 1024, 2),
                "status": "success"
            })
            print(f"  [{i}/{len(targets)}] ✓ {from_id}")
        else:
            fail_count += 1
            error_msg = result.get("error", {}).get("message", "Unknown error")
            backup_log["files"].append({
                "original_path": from_id,
                "backup_path": to_id,
                "size_mb": round(t["bytes"] / 1024 / 1024, 2),
                "status": "failed",
                "error": error_msg
            })
            print(f"  [{i}/{len(targets)}] ✗ {from_id} - {error_msg}")

    # 4. Save backup log
    print("\n[4/4] 로그 저장 중...")
    backup_log["success_count"] = success_count
    backup_log["fail_count"] = fail_count

    log_path = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/config/logs/cloudinary_backup_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(backup_log, f, indent=2, ensure_ascii=False)
    print(f"  로그 저장: {log_path}")

    # Summary
    print("\n" + "=" * 60)
    print("백업 완료 보고")
    print("=" * 60)
    print(f"이동 완료: {success_count}개 / {len(targets)}개")
    print(f"실패: {fail_count}개")
    print(f"백업 용량: {total_bytes / 1024 / 1024:.2f}MB")
    print(f"백업 위치: {BACKUP_PREFIX}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
