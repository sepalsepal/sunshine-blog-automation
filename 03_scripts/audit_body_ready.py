#!/usr/bin/env python3
"""
WO-2026-0205-003: body_ready 전수조사
SHA256 해시 비교로 커버/바디 이미지 동일성 감사

검사 항목:
  1. cover(_00) ≠ body1(_01) — 커버와 바디1 동일 여부
  2. cover(_00) ≠ body2(_02) — 커버와 바디2 동일 여부
  3. body1(_01) ≠ body2(_02) — 바디1과 바디2 동일 여부
  4. archive 폴더 내 bg 원본과 렌더링 후 비교
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
BODY_READY_DIR = PROJECT_ROOT / "contents" / "2_body_ready"
REPORT_PATH = PROJECT_ROOT / "config" / "data" / "wo_2026_0205_003_audit.json"


def sha256_file(filepath: Path) -> str:
    """파일의 SHA256 해시 계산"""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_folder(folder: Path) -> dict:
    """단일 폴더 감사"""
    folder_name = folder.name
    # food_id 추출 (예: 064_chocolate_초콜릿 → chocolate)
    parts = folder_name.split("_", 2)
    if len(parts) >= 2:
        food_id = parts[1]
    else:
        food_id = folder_name

    result = {
        "folder": folder_name,
        "food_id": food_id,
        "slides_found": [],
        "hashes": {},
        "bg_hashes": {},
        "checks": {},
        "issues": [],
        "status": "PASS",
    }

    # 슬라이드 파일 찾기 (다양한 네이밍 패턴 지원)
    slide_files = {}
    for suffix in ["_00.png", "_01.png", "_02.png", "_03.png"]:
        # 패턴: {food_id}{suffix} 또는 {any_prefix}{suffix}
        candidates = list(folder.glob(f"*{suffix}"))
        if candidates:
            slide_num = suffix.replace("_", "").replace(".png", "")
            slide_files[slide_num] = candidates[0]

    # 메타데이터 확인
    meta_path = folder / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                result["metadata"] = json.load(f)
        except Exception:
            result["metadata"] = None

    # 해시 계산
    for slide_num, filepath in sorted(slide_files.items()):
        result["slides_found"].append(f"_{slide_num}.png")
        result["hashes"][f"slide_{slide_num}"] = {
            "file": filepath.name,
            "sha256": sha256_file(filepath),
            "size_kb": os.path.getsize(filepath) // 1024,
        }

    # archive 폴더 bg 원본 해시
    archive_dir = folder / "archive"
    if archive_dir.exists():
        for bg_file in sorted(archive_dir.glob("*_bg.png")):
            bg_key = bg_file.stem  # e.g., chocolate_00_bg
            result["bg_hashes"][bg_key] = {
                "file": bg_file.name,
                "sha256": sha256_file(bg_file),
                "size_kb": os.path.getsize(bg_file) // 1024,
            }

    # === 검증 ===
    h = result["hashes"]

    # Check 1: cover(_00) vs body1(_01)
    if "slide_00" in h and "slide_01" in h:
        same = h["slide_00"]["sha256"] == h["slide_01"]["sha256"]
        result["checks"]["cover_vs_body1"] = {
            "same_hash": same,
            "result": "FAIL" if same else "PASS",
        }
        if same:
            result["issues"].append("cover(_00) == body1(_01): 동일 이미지")
            result["status"] = "FAIL"

    # Check 2: cover(_00) vs body2(_02)
    if "slide_00" in h and "slide_02" in h:
        same = h["slide_00"]["sha256"] == h["slide_02"]["sha256"]
        result["checks"]["cover_vs_body2"] = {
            "same_hash": same,
            "result": "FAIL" if same else "PASS",
        }
        if same:
            result["issues"].append("cover(_00) == body2(_02): 동일 이미지")
            result["status"] = "FAIL"

    # Check 3: body1(_01) vs body2(_02)
    if "slide_01" in h and "slide_02" in h:
        same = h["slide_01"]["sha256"] == h["slide_02"]["sha256"]
        result["checks"]["body1_vs_body2"] = {
            "same_hash": same,
            "result": "FAIL" if same else "PASS",
        }
        if same:
            result["issues"].append("body1(_01) == body2(_02): 동일 이미지")
            result["status"] = "FAIL"

    # Check 4: bg 원본 동일성 (archive 폴더)
    bg_h = result["bg_hashes"]
    bg_sha_values = [v["sha256"] for v in bg_h.values()]
    if len(bg_sha_values) >= 2:
        unique_bgs = len(set(bg_sha_values))
        total_bgs = len(bg_sha_values)
        if unique_bgs < total_bgs:
            result["checks"]["bg_uniqueness"] = {
                "unique": unique_bgs,
                "total": total_bgs,
                "result": "FAIL",
            }
            result["issues"].append(
                f"bg 원본 {total_bgs}개 중 고유 {unique_bgs}개: 동일 소스 사용"
            )
            # bg 동일은 이미 expected이므로 status는 유지
        else:
            result["checks"]["bg_uniqueness"] = {
                "unique": unique_bgs,
                "total": total_bgs,
                "result": "PASS",
            }

    # Check 5: 슬라이드 누락
    expected = {"_00.png", "_01.png", "_02.png", "_03.png"}
    found = set(result["slides_found"])
    missing = expected - found
    if missing:
        result["issues"].append(f"슬라이드 누락: {sorted(missing)}")
        result["status"] = "WARN" if result["status"] == "PASS" else result["status"]

    return result


def main():
    print("=" * 70)
    print("WO-2026-0205-003: body_ready 전수조사")
    print(f"대상 폴더: {BODY_READY_DIR}")
    print("=" * 70)

    if not BODY_READY_DIR.exists():
        print(f"[ERROR] 폴더 없음: {BODY_READY_DIR}")
        sys.exit(1)

    folders = sorted(
        [d for d in BODY_READY_DIR.iterdir() if d.is_dir()],
        key=lambda x: x.name,
    )

    print(f"\n감사 대상: {len(folders)}개 폴더\n")

    results = []
    pass_count = 0
    fail_count = 0
    warn_count = 0

    for folder in folders:
        print(f"[감사] {folder.name} ... ", end="", flush=True)
        r = audit_folder(folder)
        results.append(r)

        if r["status"] == "PASS":
            print(f"PASS ({len(r['slides_found'])}장)")
            pass_count += 1
        elif r["status"] == "FAIL":
            print(f"FAIL - {'; '.join(r['issues'])}")
            fail_count += 1
        else:
            print(f"WARN - {'; '.join(r['issues'])}")
            warn_count += 1

    # === 요약 보고서 ===
    print(f"\n{'=' * 70}")
    print("감사 결과 요약")
    print(f"{'=' * 70}")
    print(f"전체: {len(results)}건")
    print(f"  PASS: {pass_count}건")
    print(f"  FAIL: {fail_count}건")
    print(f"  WARN: {warn_count}건")

    if fail_count > 0:
        print(f"\n{'─' * 70}")
        print("FAIL 상세:")
        print(f"{'─' * 70}")
        for r in results:
            if r["status"] == "FAIL":
                print(f"\n  [{r['folder']}]")
                for issue in r["issues"]:
                    print(f"    - {issue}")
                # 해시 비교 상세
                for check_name, check in r["checks"].items():
                    if check.get("result") == "FAIL" and "same_hash" in check:
                        print(f"    - {check_name}: 해시 동일")

    if warn_count > 0:
        print(f"\n{'─' * 70}")
        print("WARN 상세:")
        print(f"{'─' * 70}")
        for r in results:
            if r["status"] == "WARN":
                print(f"\n  [{r['folder']}]")
                for issue in r["issues"]:
                    print(f"    - {issue}")

    # bg 원본 동일성 통계
    bg_fail_count = 0
    for r in results:
        bg_check = r["checks"].get("bg_uniqueness", {})
        if bg_check.get("result") == "FAIL":
            bg_fail_count += 1

    if bg_fail_count > 0:
        print(f"\n{'─' * 70}")
        print(f"bg 원본 동일 소스 사용: {bg_fail_count}건 (archive/ 내 bg 파일 해시 비교)")
        print(f"{'─' * 70}")
        for r in results:
            bg_check = r["checks"].get("bg_uniqueness", {})
            if bg_check.get("result") == "FAIL":
                unique = bg_check["unique"]
                total = bg_check["total"]
                print(f"  [{r['folder']}] bg {total}개 중 고유 {unique}개")
                # 상세 해시
                for bg_name, bg_info in r["bg_hashes"].items():
                    print(f"    {bg_info['file']}: {bg_info['sha256'][:16]}...")

    # JSON 보고서 저장
    report = {
        "work_order": "WO-2026-0205-003",
        "title": "body_ready 전수조사 (SHA256 해시 비교)",
        "executed_at": datetime.now().isoformat(),
        "target_dir": str(BODY_READY_DIR),
        "total_folders": len(results),
        "summary": {
            "PASS": pass_count,
            "FAIL": fail_count,
            "WARN": warn_count,
            "bg_same_source": bg_fail_count,
        },
        "results": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n보고서 저장: {REPORT_PATH}")
    print(f"\n{'=' * 70}")

    if fail_count > 0:
        print(f"결론: {fail_count}건 FAIL — 렌더링 후 이미지가 동일한 경우 없음 확인 필요")
    else:
        print("결론: 렌더링 후 이미지 해시는 모두 상이함")
        if bg_fail_count > 0:
            print(f"  단, bg 원본(렌더링 전 소스)이 동일한 폴더 {bg_fail_count}건 존재")
            print("  → 렌더링으로 텍스트가 다르므로 해시는 다르지만, 배경 이미지가 동일")

    return fail_count


if __name__ == "__main__":
    sys.exit(main())
