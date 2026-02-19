#!/usr/bin/env python3
"""
이미지 해시 기반 중복 검출 스크립트
- 파일 크기 + 이미지 해시로 중복 감지
- 중복 이미지 자동 삭제 (원본 1개만 유지)
"""

import os
import hashlib
from pathlib import Path
from PIL import Image
from collections import defaultdict

BEST_FOLDER = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents/sunshine photos/00_Best")

def get_image_hash(img_path: Path) -> str:
    """이미지 콘텐츠 해시 생성 (리사이즈 후 비교)"""
    try:
        img = Image.open(img_path).convert('RGB')
        # 작은 크기로 리사이즈하여 비교 (빠른 처리)
        img_small = img.resize((64, 64), Image.Resampling.LANCZOS)
        
        # 픽셀 데이터로 해시 생성
        pixels = list(img_small.getdata())
        pixel_str = str(pixels)
        return hashlib.md5(pixel_str.encode()).hexdigest()
    except Exception as e:
        return None


def get_file_hash(file_path: Path) -> str:
    """파일 바이너리 해시 (완전 동일 파일)"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None


def find_duplicates():
    """중복 이미지 검출"""
    print("=" * 60)
    print("이미지 중복 검출 (해시 기반)")
    print("=" * 60)
    print()
    
    # 1단계: 파일 크기로 그룹화
    print("[1/3] 파일 크기로 그룹화...")
    size_groups = defaultdict(list)
    
    for img_path in BEST_FOLDER.glob("*.jpg"):
        size = img_path.stat().st_size
        size_groups[size].append(img_path)
    
    # 같은 크기 그룹만 추출
    same_size_groups = {k: v for k, v in size_groups.items() if len(v) > 1}
    print(f"     동일 크기 그룹: {len(same_size_groups)}개")
    
    # 2단계: 파일 해시로 완전 동일 파일 검출
    print("\n[2/3] 파일 해시로 완전 동일 검출...")
    exact_duplicates = []
    
    for size, files in same_size_groups.items():
        hash_groups = defaultdict(list)
        for f in files:
            h = get_file_hash(f)
            if h:
                hash_groups[h].append(f)
        
        for h, group in hash_groups.items():
            if len(group) > 1:
                # 첫 번째 파일 유지, 나머지 삭제 대상
                exact_duplicates.extend(group[1:])
    
    print(f"     완전 동일 파일: {len(exact_duplicates)}개")
    
    # 3단계: 이미지 해시로 유사 이미지 검출
    print("\n[3/3] 이미지 해시로 유사 검출...")
    
    all_images = list(BEST_FOLDER.glob("*.jpg"))
    # 이미 삭제 대상인 파일 제외
    remaining = [f for f in all_images if f not in exact_duplicates]
    
    image_hash_groups = defaultdict(list)
    for img_path in remaining:
        h = get_image_hash(img_path)
        if h:
            image_hash_groups[h].append(img_path)
    
    similar_duplicates = []
    for h, group in image_hash_groups.items():
        if len(group) > 1:
            # 가장 큰 파일 유지, 나머지 삭제
            group_sorted = sorted(group, key=lambda x: x.stat().st_size, reverse=True)
            similar_duplicates.extend(group_sorted[1:])
    
    print(f"     유사 이미지: {len(similar_duplicates)}개")
    
    # 결과 합산
    all_duplicates = list(set(exact_duplicates + similar_duplicates))
    
    return all_duplicates


def delete_duplicates(duplicates: list, dry_run: bool = True):
    """중복 파일 삭제"""
    if not duplicates:
        print("\n✅ 중복 파일 없음!")
        return
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}삭제 대상: {len(duplicates)}개")
    print("-" * 60)
    
    total_size = 0
    for f in sorted(duplicates):
        size = f.stat().st_size
        total_size += size
        print(f"  {'[삭제예정]' if dry_run else '❌ 삭제:'} {f.name} ({size/1024:.1f}KB)")
        
        if not dry_run:
            f.unlink()
    
    print("-" * 60)
    print(f"{'예상 ' if dry_run else ''}절감 용량: {total_size/1024/1024:.1f}MB")
    
    if dry_run:
        print("\n⚠️  실제 삭제하려면 dry_run=False로 다시 실행하세요")


def main():
    # 중복 검출
    duplicates = find_duplicates()
    
    print()
    print("=" * 60)
    print("검출 결과")
    print("=" * 60)
    
    if duplicates:
        # 먼저 dry run으로 확인
        delete_duplicates(duplicates, dry_run=True)
        
        # 사용자 확인
        print("\n" + "=" * 60)
        response = input("삭제 진행할까요? (y/N): ").strip().lower()
        
        if response == 'y':
            delete_duplicates(duplicates, dry_run=False)
            print("\n✅ 삭제 완료!")
        else:
            print("\n취소됨.")
    else:
        print("\n✅ 중복 파일 없음!")
    
    # 최종 상태
    remaining = len(list(BEST_FOLDER.glob("*.jpg")))
    print(f"\n📁 남은 파일: {remaining}개")


if __name__ == "__main__":
    main()
