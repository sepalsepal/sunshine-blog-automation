#!/usr/bin/env python3
"""
중복 콘텐츠 폴더 탐지 및 정리 스크립트
같은 영문명의 폴더가 여러 개 있는 경우 리포트 생성
"""

import os
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine")
CONTENT_DIR = BASE_DIR / "content/images"

SKIP_FOLDERS = {'000_cover', 'archive', 'reference', 'sunshine', 'temp'}

def analyze_duplicates():
    """중복 폴더 분석"""
    print("=" * 70)
    print("📊 중복 콘텐츠 폴더 분석")
    print("=" * 70)

    # 영문명별 폴더 그룹핑
    food_folders = defaultdict(list)

    for folder in sorted(CONTENT_DIR.iterdir()):
        if not folder.is_dir() or folder.name in SKIP_FOLDERS:
            continue

        # 폴더명에서 영문명 추출
        match = re.match(r'(\d+)_([a-z_]+)', folder.name)
        if match:
            num, english = match.groups()
            english = english.rstrip('_')
            food_folders[english].append({
                'num': int(num),
                'name': folder.name,
                'path': folder,
                'published': 'published' in folder.name
            })

    # 중복 찾기
    duplicates = {k: v for k, v in food_folders.items() if len(v) > 1}

    print(f"\n📁 총 폴더: {sum(len(v) for v in food_folders.values())}개")
    print(f"🔖 고유 음식: {len(food_folders)}개")
    print(f"⚠️ 중복 음식: {len(duplicates)}개")

    if duplicates:
        print("\n" + "=" * 70)
        print("⚠️ 중복 폴더 목록")
        print("=" * 70)

        total_duplicates = 0
        for food, folders in sorted(duplicates.items()):
            total_duplicates += len(folders) - 1
            print(f"\n📌 {food} ({len(folders)}개):")
            for f in sorted(folders, key=lambda x: x['num']):
                status = "📗 게시됨" if f['published'] else "📙 미게시"
                print(f"    {status} {f['name']}")

        print(f"\n📊 정리 가능한 중복 폴더: {total_duplicates}개")

    # 권장 정리 사항
    print("\n" + "=" * 70)
    print("🔧 권장 조치")
    print("=" * 70)

    actions = []
    for food, folders in duplicates.items():
        published = [f for f in folders if f['published']]
        unpublished = [f for f in folders if not f['published']]

        if published and unpublished:
            # 게시된 것 유지, 미게시 삭제
            for f in unpublished:
                actions.append(f"  🗑️ {f['name']} → archive/ (게시된 버전 존재)")
        elif len(unpublished) > 1:
            # 가장 최신 번호 유지
            sorted_folders = sorted(unpublished, key=lambda x: x['num'], reverse=True)
            keep = sorted_folders[0]
            for f in sorted_folders[1:]:
                actions.append(f"  🗑️ {f['name']} → archive/ (최신 {keep['name']} 유지)")

    if actions:
        for action in actions[:30]:
            print(action)
        if len(actions) > 30:
            print(f"  ... 외 {len(actions) - 30}개")
    else:
        print("  ✅ 필요한 조치 없음")

    return duplicates

def main():
    analyze_duplicates()

if __name__ == "__main__":
    main()
