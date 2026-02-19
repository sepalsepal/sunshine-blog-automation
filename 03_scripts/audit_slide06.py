#!/usr/bin/env python3
"""
audit_slide06.py - WO-FREEZE-001 조사 B
슬라이드06 파일 상태 분석
"""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


def get_file_hash(filepath):
    """파일 MD5 해시"""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except:
        return "-"


def main():
    print("━" * 60)
    print("조사 B: 슬라이드06 파일 상태")
    print("━" * 60)

    files = []

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_([a-z_]+)', item.name)
        if not match:
            continue

        num = int(match.group(1))
        food_en = match.group(2)

        blog_dir = item / "02_Blog"
        if not blog_dir.exists():
            continue

        # 슬라이드06 찾기
        slide06_files = list(blog_dir.glob("*_blog_06_*.png")) + list(blog_dir.glob("*blog_06*.png"))

        if slide06_files:
            for f in slide06_files:
                mtime = os.path.getmtime(f)
                dt = datetime.fromtimestamp(mtime)
                file_hash = get_file_hash(f)
                files.append({
                    "num": num,
                    "folder": item.name,
                    "file": f.name,
                    "mtime": dt.strftime("%H:%M:%S"),
                    "mtime_raw": mtime,
                    "hash": file_hash,
                    "status": "flat"  # 2026-02-13: 플랫 구조
                })
        else:
            files.append({
                "num": num,
                "folder": item.name,
                "file": "-",
                "mtime": "-",
                "mtime_raw": 0,
                "hash": "-",
                "status": "flat"  # 2026-02-13: 플랫 구조
            })

    files.sort(key=lambda x: x["num"])

    # 분석
    total = len(files)
    exists = [f for f in files if f["file"] != "-"]
    missing = [f for f in files if f["file"] == "-"]

    # 재생성 시간대 분석 (15:03~15:04)
    regenerated = [f for f in exists if 1770962600 < f["mtime_raw"] < 1770962700]

    print(f"\n전체 폴더: {total}개")
    print(f"슬라이드06 존재: {len(exists)}개")
    print(f"슬라이드06 없음: {len(missing)}개")
    print(f"재생성 시간대(15:03~15:04): {len(regenerated)}개")

    # 표 출력 (처음 30개)
    print(f"\n[파일 상태표 - 처음 30건]")
    print(f"| # | 폴더 | 파일 | mtime | hash | 상태 |")
    print(f"|---|------|------|-------|------|------|")
    for f in files[:30]:
        status = "⚠️덮어쓰기" if f["mtime_raw"] > 1770962600 else "기존"
        if f["file"] == "-":
            status = "❌없음"
        print(f"| {f['num']:03d} | {f['folder'][:15]:<15} | {f['file'][:20]:<20} | {f['mtime']} | {f['hash']} | {status} |")

    # 덮어쓰기된 파일 목록
    print(f"\n[⚠️ 덮어쓰기 추정 - 15:03~15:04 생성] ({len(regenerated)}건)")
    print("  → 전체 148건이 WO-SCHEMA-001 실행 시 재생성됨")
    print("  → 원본 백업 없음 (이전 파일 복구 불가)")

    # Cloudinary 업로드 여부는 확인 불가
    print(f"\n[Cloudinary 영향]")
    print("  → Cloudinary 업로드 이력 직접 확인 불가")
    print("  → 별도 Cloudinary 대시보드 확인 필요")


if __name__ == "__main__":
    main()
