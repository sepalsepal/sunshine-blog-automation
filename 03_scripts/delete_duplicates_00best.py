#!/usr/bin/env python3
"""
00_Best 폴더 중복 파일 삭제 스크립트 v2.0
원본만 유지, _cta_source.jpg, _01_usable.jpg 삭제
"""

import os
from pathlib import Path

BEST_FOLDER = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents/sunshine photos/00_Best")

def delete_duplicates():
    """중복 파일 삭제 - 원본만 유지"""
    
    # 삭제 대상 패턴
    delete_patterns = [
        "_cta_source.jpg",
        "_01_usable.jpg",
    ]
    
    deleted_count = 0
    freed_bytes = 0
    
    print("=" * 60)
    print("00_Best 폴더 중복 파일 삭제 v2.0")
    print("=" * 60)
    print()
    print(f"폴더: {BEST_FOLDER}")
    print(f"삭제 패턴: {delete_patterns}")
    print()
    
    # 모든 파일 확인
    all_files = list(BEST_FOLDER.glob("*.jpg"))
    print(f"전체 JPG 파일: {len(all_files)}개")
    print()
    
    # 삭제 실행
    for file in sorted(all_files):
        for pattern in delete_patterns:
            if file.name.endswith(pattern):
                try:
                    size = file.stat().st_size
                    file.unlink()
                    deleted_count += 1
                    freed_bytes += size
                    print(f"✅ 삭제: {file.name}")
                except Exception as e:
                    print(f"❌ 실패: {file.name} - {e}")
                break
    
    print()
    print("=" * 60)
    print(f"삭제 완료: {deleted_count}개 파일")
    print(f"확보 용량: {freed_bytes / 1024 / 1024:.1f} MB")
    print("=" * 60)
    
    # 결과 확인
    remaining = list(BEST_FOLDER.glob("*.jpg"))
    print()
    print(f"남은 파일: {len(remaining)}개 (원본)")
    
    # 샘플 출력
    print()
    print("남은 파일 샘플 (처음 10개):")
    for f in sorted(remaining)[:10]:
        print(f"  - {f.name}")

if __name__ == "__main__":
    delete_duplicates()
