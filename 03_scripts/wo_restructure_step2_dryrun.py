#!/usr/bin/env python3
"""
WO-RESTRUCTURE-001 STEP 2: Dry-Run
5개 폴더로 구조 변경 시뮬레이션 (실제 변경 없음)
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"


def get_food_name(folder_name):
    """폴더명에서 음식명 추출 (001_Apple → Apple)"""
    match = re.match(r'^\d{3}_(.+)$', folder_name)
    return match.group(1) if match else None


def simulate_folder(folder_path):
    """단일 폴더 구조 변경 시뮬레이션"""
    food = get_food_name(folder_path.name)
    if not food:
        return None

    result = {
        "folder": folder_path.name,
        "food": food,
        "actions": [],
        "conflicts": [],
        "thread_files": []
    }

    # 1. Thread/ 처리 확인
    thread_dir = folder_path / "Thread"
    if thread_dir.exists():
        thread_files = list(thread_dir.iterdir())
        if thread_files:
            result["thread_files"] = [f.name for f in thread_files if f.is_file()]
            result["actions"].append(f"Thread/ 처리: {len(result['thread_files'])}개 파일 → 01_Insta&Thread/")
        else:
            result["actions"].append("Thread/ 처리: 파일 없음, 삭제")
    else:
        result["actions"].append("Thread/ 처리: 폴더 없음, SKIP")

    # 2. 공통 이미지 루트 이동 확인
    blog_dir = folder_path / "Blog"
    common_files = [f"{food}_Common_01_Cover.png", f"{food}_Common_02_Food.png", f"{food}_Common_08_Cta.png"]

    for cf in common_files:
        blog_file = blog_dir / cf if blog_dir.exists() else None
        root_file = folder_path / cf

        if blog_file and blog_file.exists():
            if root_file.exists():
                result["conflicts"].append(f"충돌: {cf} 루트에 이미 존재")
            else:
                result["actions"].append(f"Blog/{cf} → ./{cf}")
        else:
            # 패턴 매칭으로 찾기
            if blog_dir.exists():
                matches = list(blog_dir.glob(f"*Common_0{cf[-6]}*"))
                if matches:
                    result["actions"].append(f"Blog/{matches[0].name} → ./{cf}")
                else:
                    result["actions"].append(f"Blog/{cf} 없음 SKIP")

    # 3. Insta 공통 이미지 삭제 확인
    insta_dir = folder_path / "Insta"
    if insta_dir.exists():
        for cf in common_files:
            insta_file = insta_dir / cf
            if insta_file.exists():
                result["actions"].append(f"Insta/{cf} 삭제 (루트에 원본)")

    # 4. 캡션 이동 확인
    captions_dir = folder_path / "Captions"
    if captions_dir.exists():
        for cap in captions_dir.iterdir():
            if cap.is_file():
                if "Insta" in cap.name or "Thread" in cap.name:
                    result["actions"].append(f"Captions/{cap.name} → 01_Insta&Thread/")
                elif "Blog" in cap.name:
                    result["actions"].append(f"Captions/{cap.name} → 02_Blog/")
        result["actions"].append("Captions/ 폴더 삭제")

    # 5. 폴더명 변경 확인
    if (folder_path / "0_Clean").exists():
        result["actions"].append("0_Clean/ → 00_Clean/")
    if (folder_path / "Insta").exists():
        result["actions"].append("Insta/ → 01_Insta&Thread/")
    if (folder_path / "Blog").exists():
        result["actions"].append("Blog/ → 02_Blog/")

    # 6. 00_Clean 리네이밍 확인
    clean_dir = folder_path / "0_Clean"
    if clean_dir.exists():
        clean_files = [f for f in clean_dir.iterdir() if f.is_file() and f.suffix == ".png"]
        result["actions"].append(f"00_Clean 리네이밍: {len(clean_files)}개 파일")

    return result


def main():
    print("━━━━━ STEP 2: Dry-Run ━━━━━")

    # 5개 폴더 선택 (다양한 번호대)
    test_nums = [1, 34, 66, 120, 158]
    test_folders = []

    for item in sorted(CONTENTS_DIR.iterdir()):
        if item.is_dir():
            match = re.match(r'^(\d{3})_', item.name)
            if match and int(match.group(1)) in test_nums:
                test_folders.append(item)

    if len(test_folders) < 5:
        # 부족하면 처음 5개로 대체
        test_folders = [f for f in sorted(CONTENTS_DIR.iterdir()) if f.is_dir() and re.match(r'^\d{3}_', f.name)][:5]

    all_pass = True
    for i, folder in enumerate(test_folders, 1):
        result = simulate_folder(folder)
        if not result:
            continue

        print(f"[{i}/5] {result['folder']}")

        for action in result["actions"]:
            print(f"  ├─ {action} ✅")

        if result["conflicts"]:
            for conflict in result["conflicts"]:
                print(f"  ├─ ⚠️ {conflict}")
            all_pass = False

        if result["thread_files"]:
            print(f"  ├─ Thread 파일: {result['thread_files']}")

        conflict_msg = "없음" if not result["conflicts"] else f"{len(result['conflicts'])}건"
        print(f"  └─ 충돌: {conflict_msg}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if all_pass:
        print("Dry-Run 통과 ✅")
    else:
        print("⚠️ 충돌 발견 - 확인 필요")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return all_pass


if __name__ == "__main__":
    main()
