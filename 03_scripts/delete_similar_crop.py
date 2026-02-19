#!/usr/bin/env python3
"""
crop 폴더 유사/중복 이미지 삭제 스크립트
수동 검토 후 확정된 삭제 목록
"""

import os
from pathlib import Path

CROP_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents/sunshine photos/00_Best/crop")

# 삭제 대상 파일 목록 (수동 검토 완료)
DELETE_LIST = [
    # 잔디 구르기 그룹 1 (0001 보관)
    "haetsali_happy_sit_indoor_0002.png",
    "haetsali_happy_sit_indoor_0003.png",
    "haetsali_happy_sit_indoor_0004.png",

    # 잔디 구르기 그룹 2 (0011 보관)
    "haetsali_happy_sit_indoor_0012.png",

    # 잔디 구르기 그룹 3 (0042 보관)
    "haetsali_happy_sit_indoor_0043.png",
    "haetsali_happy_sit_indoor_0044.png",
    "haetsali_happy_sit_indoor_0046.png",
    "haetsali_happy_sit_indoor_0047.png",
    "haetsali_happy_sit_indoor_0050.png",

    # 빨간 리드 누움 (0005 보관)
    "haetsali_happy_sit_indoor_0006.png",

    # 나무 옆 누움 (0014 보관)
    "haetsali_happy_sit_indoor_0015.png",
    "haetsali_happy_sit_indoor_0016.png",
    "haetsali_happy_sit_indoor_0018.png",

    # 노랑 우비 빨간 꽃 (0019 보관)
    "haetsali_happy_sit_indoor_0020.png",

    # 노랑 우비 보라 꽃 (0021 보관)
    "haetsali_happy_sit_indoor_0022.png",

    # 잔디 누움 (0027 보관)
    "haetsali_happy_sit_indoor_0028.png",

    # 꽃 배경 누움 (0032 보관)
    "haetsali_happy_sit_indoor_0031.png",
    "haetsali_happy_sit_indoor_0033.png",
    "haetsali_happy_sit_indoor_0034.png",

    # 노랑 우비 숲 (0024 보관)
    "haetsali_happy_sit_indoor_0038.png",
    "haetsali_happy_sit_indoor_0039.png",

    # 바닥 발잡기 (0142 보관)
    "haetsali_happy_sit_indoor_0143.png",
    "haetsali_happy_sit_indoor_0144.png",

    # 사무실 바닥 (0180 보관)
    "haetsali_happy_sit_indoor_0181.png",
    "haetsali_happy_sit_indoor_0182.png",

    # 텐트 (0205 보관)
    "haetsali_happy_sit_indoor_0207.png",
]

def main():
    print("=" * 60)
    print("유사/중복 이미지 삭제")
    print("=" * 60)

    deleted = 0
    not_found = 0
    total_size = 0

    for filename in DELETE_LIST:
        filepath = CROP_DIR / filename
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            filepath.unlink()
            print(f"✅ 삭제: {filename}")
            deleted += 1
        else:
            print(f"⚠️ 없음: {filename}")
            not_found += 1

    print("\n" + "=" * 60)
    print(f"삭제 완료: {deleted}개")
    print(f"없는 파일: {not_found}개")
    print(f"확보 용량: {total_size / 1024 / 1024:.1f} MB")
    print("=" * 60)

    # 남은 파일 수 확인
    remaining = len(list(CROP_DIR.glob("*.png")))
    print(f"\n남은 이미지: {remaining}개")

if __name__ == "__main__":
    main()
