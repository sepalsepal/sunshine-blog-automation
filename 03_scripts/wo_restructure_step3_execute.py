#!/usr/bin/env python3
"""
WO-RESTRUCTURE-001 STEP 3: 구조 재구성 실행
165개 폴더 순차 처리
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"


def get_food_name(folder_name):
    """폴더명에서 음식명 추출"""
    match = re.match(r'^\d{3}_(.+)$', folder_name)
    return match.group(1) if match else None


def restructure_folder(folder_path, food_data):
    """단일 폴더 구조 재구성"""
    food = get_food_name(folder_path.name)
    if not food:
        return None

    num = int(re.match(r'^(\d{3})_', folder_path.name).group(1))
    fd = food_data.get(str(num), {})
    safety = fd.get("safety", "SAFE")

    stats = {
        "common_moved": 0,
        "common_deleted": 0,
        "captions_moved": 0,
        "clean_renamed": 0,
        "clean_skipped": 0,
        "thread_deleted": False,
        "thread_files_moved": 0
    }

    # [3-A] Thread/ 처리
    thread_dir = folder_path / "Thread"
    if thread_dir.exists():
        # Thread 내 파일을 01_Insta&Thread로 이동 준비
        thread_files = [f for f in thread_dir.iterdir() if f.is_file()]
        for tf in thread_files:
            # 나중에 01_Insta&Thread 생성 후 이동
            stats["thread_files_moved"] += 1

    # [3-B] 공통 이미지 루트 이동
    blog_dir = folder_path / "Blog"
    insta_dir = folder_path / "Insta"

    common_patterns = [
        ("Common_01_Cover", f"{food}_Common_01_Cover.png"),
        ("Common_02_Food", f"{food}_Common_02_Food.png"),
        ("Common_08_Cta", f"{food}_Common_08_Cta.png"),
    ]

    for pattern, target_name in common_patterns:
        # Blog에서 찾기
        if blog_dir.exists():
            matches = [f for f in blog_dir.iterdir() if pattern in f.name and f.suffix == ".png"]
            if matches:
                src = matches[0]
                dst = folder_path / target_name
                if not dst.exists():
                    shutil.move(str(src), str(dst))
                    stats["common_moved"] += 1

        # Insta에서 중복 삭제
        if insta_dir.exists():
            matches = [f for f in insta_dir.iterdir() if pattern in f.name and f.suffix == ".png"]
            for m in matches:
                m.unlink()
                stats["common_deleted"] += 1

    # [3-C] 캡션 이동 준비 (폴더 생성 후 이동)
    captions_dir = folder_path / "Captions"
    caption_moves = []
    if captions_dir.exists():
        for cap in captions_dir.iterdir():
            if cap.is_file():
                if "Insta" in cap.name or "Thread" in cap.name:
                    caption_moves.append((cap, "01_Insta&Thread"))
                elif "Blog" in cap.name:
                    caption_moves.append((cap, "02_Blog"))

    # [3-D] Insta 전용 이미지 (Dog) 이동 준비
    insta_dog_files = []
    if insta_dir.exists():
        insta_dog_files = [f for f in insta_dir.iterdir() if "Insta_03_Dog" in f.name or "03_Dog" in f.name]

    # [3-E] 폴더명 변경 + 파일 이동

    # 1. 먼저 01_Insta&Thread 생성 (Insta 리네이밍)
    new_insta_dir = folder_path / "01_Insta&Thread"
    if insta_dir.exists():
        # Insta의 남은 파일들을 새 폴더로 이동
        new_insta_dir.mkdir(exist_ok=True)
        for f in insta_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(new_insta_dir / f.name))
        # 빈 Insta 폴더 삭제
        if not list(insta_dir.iterdir()):
            insta_dir.rmdir()
    else:
        new_insta_dir.mkdir(exist_ok=True)

    # Thread 파일 이동
    if thread_dir.exists():
        for tf in thread_dir.iterdir():
            if tf.is_file():
                shutil.move(str(tf), str(new_insta_dir / tf.name))
        # Thread 폴더 삭제
        if not list(thread_dir.iterdir()):
            thread_dir.rmdir()
            stats["thread_deleted"] = True

    # 2. 02_Blog 생성 (Blog 리네이밍)
    new_blog_dir = folder_path / "02_Blog"
    if blog_dir.exists():
        new_blog_dir.mkdir(exist_ok=True)
        for f in blog_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(new_blog_dir / f.name))
        # 빈 Blog 폴더 삭제
        if not list(blog_dir.iterdir()):
            blog_dir.rmdir()
    else:
        new_blog_dir.mkdir(exist_ok=True)

    # 3. 캡션 이동
    for cap, target_dir in caption_moves:
        if cap.exists():
            target_path = folder_path / target_dir
            target_path.mkdir(exist_ok=True)
            shutil.move(str(cap), str(target_path / cap.name))
            stats["captions_moved"] += 1

    # Captions 폴더 삭제
    if captions_dir.exists() and not list(captions_dir.iterdir()):
        captions_dir.rmdir()

    # 4. 0_Clean → 00_Clean
    old_clean = folder_path / "0_Clean"
    new_clean = folder_path / "00_Clean"
    if old_clean.exists():
        old_clean.rename(new_clean)

    # [3-F] 00_Clean 파일 리네이밍
    if new_clean.exists():
        clean_files = [f for f in new_clean.iterdir() if f.is_file() and f.suffix == ".png"]
        for cf in clean_files:
            old_name = cf.name.lower()
            new_name = None

            # 리네이밍 규칙
            if "cover" in old_name or cf.name.startswith("hf_"):
                # 첫 번째 hf_ 파일은 Cover로 간주
                if not (new_clean / f"{food}_Cover_Clean.png").exists():
                    new_name = f"{food}_Cover_Clean.png"
            elif "food" in old_name:
                new_name = f"{food}_Food_Clean.png"
            elif "cta" in old_name:
                new_name = f"{food}_Cta_Clean.png"

            if new_name and new_name != cf.name:
                new_path = new_clean / new_name
                if not new_path.exists():
                    cf.rename(new_path)
                    stats["clean_renamed"] += 1
                else:
                    stats["clean_skipped"] += 1
            else:
                stats["clean_skipped"] += 1

    return stats


def main():
    print("━━━━━ STEP 3: 구조 재구성 ━━━━━")

    # food_data 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    # 폴더 목록
    folders = sorted([f for f in CONTENTS_DIR.iterdir() if f.is_dir() and re.match(r'^\d{3}_', f.name)])
    total = len(folders)

    totals = {
        "common_moved": 0,
        "common_deleted": 0,
        "captions_moved": 0,
        "clean_renamed": 0,
        "clean_skipped": 0,
        "thread_deleted": 0,
        "thread_files_moved": 0
    }

    for i, folder in enumerate(folders, 1):
        stats = restructure_folder(folder, food_data)
        if stats:
            for k, v in stats.items():
                if k == "thread_deleted":
                    if v:
                        totals[k] += 1
                else:
                    totals[k] += v

        # 진행률 표시 (매 20개마다)
        if i % 20 == 0 or i == total:
            print(f"[{i:03d}/{total}] 처리 완료...")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"재구성 완료: {total}/{total}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n[집계]")
    print(f"  공통 이미지 루트 이동: {totals['common_moved']}건")
    print(f"  공통 이미지 중복 삭제: {totals['common_deleted']}건")
    print(f"  캡션 플랫폼 이동: {totals['captions_moved']}건")
    print(f"  00_Clean 리네이밍: {totals['clean_renamed']}건 (SKIP {totals['clean_skipped']}건)")
    print(f"  Thread 폴더 삭제: {totals['thread_deleted']}건")
    print(f"  Thread 파일 이동: {totals['thread_files_moved']}건")

    return totals


if __name__ == "__main__":
    main()
