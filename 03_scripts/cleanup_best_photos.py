#!/usr/bin/env python3
"""
00_Best 폴더 중복 이미지 정리 스크립트
- _cta_source.jpg 삭제
- _01_usable.jpg 삭제
- 원본만 유지
"""

import os
from pathlib import Path

BEST_FOLDER = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents/sunshine photos/00_Best"

def cleanup_duplicates():
    folder = Path(BEST_FOLDER)
    
    delete_patterns = ['_cta_source.jpg', '_01_usable.jpg']
    
    deleted_count = 0
    deleted_size = 0
    kept_count = 0
    
    print("=" * 60)
    print("00_Best 폴더 중복 정리")
    print("=" * 60)
    print()
    print("삭제 대상: _cta_source.jpg, _01_usable.jpg")
    print()
    
    for file in sorted(folder.glob("*.jpg")):
        filename = file.name
        
        # 삭제 대상 확인
        should_delete = any(pattern in filename for pattern in delete_patterns)
        
        if should_delete:
            size = file.stat().st_size
            print(f"❌ 삭제: {filename} ({size/1024:.1f}KB)")
            file.unlink()
            deleted_count += 1
            deleted_size += size
        else:
            kept_count += 1
    
    print()
    print("=" * 60)
    print(f"✅ 완료")
    print(f"   삭제: {deleted_count}개 ({deleted_size/1024/1024:.1f}MB)")
    print(f"   유지: {kept_count}개")
    print("=" * 60)

if __name__ == "__main__":
    cleanup_duplicates()
