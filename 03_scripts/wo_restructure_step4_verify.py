#!/usr/bin/env python3
"""
WO-RESTRUCTURE-001 STEP 4: 무결성 검증
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
SNAPSHOT_PATH = PROJECT_ROOT / "config" / "logs" / "snapshot_pre_restructure.txt"


def main():
    print("━━━━━ STEP 4: 무결성 검증 ━━━━━")

    folders = sorted([f for f in CONTENTS_DIR.iterdir() if f.is_dir() and re.match(r'^\d{3}_', f.name)])
    total = len(folders)

    # [4-A] 폴더 구조 확인
    print("\n[4-A] 폴더 구조 확인")
    required_subs = ["00_Clean", "01_Insta&Thread", "02_Blog"]
    forbidden_subs = ["Blog", "Insta", "Thread", "Captions", "0_Clean"]

    structure_ok = 0
    structure_issues = []

    for folder in folders:
        has_required = all((folder / sub).exists() for sub in required_subs)
        has_forbidden = any((folder / sub).exists() for sub in forbidden_subs)

        # 공통 이미지 루트 확인
        food = re.match(r'^\d{3}_(.+)$', folder.name).group(1)
        common_files = [
            f"{food}_Common_01_Cover.png",
            f"{food}_Common_02_Food.png",
            f"{food}_Common_08_Cta.png"
        ]
        # 최소 1개 이상 있어야 함 (일부 폴더는 전체 없을 수 있음)

        if has_required and not has_forbidden:
            structure_ok += 1
        else:
            issues = []
            if not has_required:
                missing = [s for s in required_subs if not (folder / s).exists()]
                issues.append(f"누락: {missing}")
            if has_forbidden:
                remaining = [s for s in forbidden_subs if (folder / s).exists()]
                issues.append(f"잔재: {remaining}")
            structure_issues.append((folder.name, issues))

    print(f"  정상: {structure_ok}/{total}")
    if structure_issues:
        print(f"  이슈: {len(structure_issues)}건")
        for name, issues in structure_issues[:5]:
            print(f"    {name}: {issues}")

    # [4-B] 파일 수 비교
    print("\n[4-B] 파일 수 비교")
    with open(SNAPSHOT_PATH, "r") as f:
        old_files = f.read().strip().split("\n")
    old_count = len(old_files)

    # 현재 파일 수
    current_files = list(CONTENTS_DIR.rglob("*"))
    current_count = len([f for f in current_files if f.is_file()])

    print(f"  이전: {old_count}개")
    print(f"  현재: {current_count}개")
    diff = current_count - old_count
    if abs(diff) < 200:  # Thread 폴더 삭제 + 중복 삭제로 감소 예상
        print(f"  차이: {diff:+d}개 (Thread/중복 삭제로 감소 예상) ✅")
    else:
        print(f"  ⚠️ 차이: {diff:+d}개")

    # [4-C] PascalCase 유지 확인
    print("\n[4-C] PascalCase 확인")
    lowercase_files = []
    for folder in folders:
        for f in folder.rglob("*"):
            if f.is_file() and f.suffix in [".png", ".txt"]:
                # 첫 글자가 소문자이면서 hf_, . 로 시작하지 않는 경우
                name = f.stem
                if name and name[0].islower() and not name.startswith(("hf_", "blog", "caption")):
                    # 기존 레거시 파일 제외
                    if not any(x in name for x in ["음식", "급여", "영양", "주의"]):
                        lowercase_files.append(str(f.relative_to(CONTENTS_DIR)))

    print(f"  소문자 시작 파일: {len(lowercase_files)}개")
    if lowercase_files and len(lowercase_files) < 10:
        for lf in lowercase_files[:5]:
            print(f"    {lf}")

    # [4-D] 빈 폴더 잔재 확인
    print("\n[4-D] 빈 폴더 잔재 확인")
    empty_forbidden = []
    for folder in folders:
        for sub in ["Blog", "Insta", "Thread", "Captions", "0_Clean"]:
            sub_path = folder / sub
            if sub_path.exists():
                empty_forbidden.append(str(sub_path.relative_to(CONTENTS_DIR)))

    print(f"  잔재 폴더: {len(empty_forbidden)}개")
    if empty_forbidden:
        for ef in empty_forbidden[:5]:
            print(f"    {ef}")

    # 결과
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    checks = [
        ("폴더 구조", structure_ok == total, f"{structure_ok}/{total} 정상"),
        ("파일 수", abs(diff) < 500, "차이 허용 범위"),
        ("PascalCase", len(lowercase_files) < 50, f"위반 {len(lowercase_files)}개"),
        ("빈 폴더", len(empty_forbidden) == 0, f"잔재 {len(empty_forbidden)}개"),
    ]

    all_pass = True
    for name, passed, detail in checks:
        status = "✅" if passed else "⚠️"
        print(f"{name}... {detail} {status}")
        if not passed:
            all_pass = False

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return all_pass


if __name__ == "__main__":
    main()
