#!/usr/bin/env python3
"""
Project Sunshine - Cloudinary 이미지 자동 업로드 스크립트
사용법: python upload_to_cloudinary.py --folder [폴더명] --path [이미지경로]
예시: python upload_to_cloudinary.py --folder sweet_potato --path ./images/sweet_potato/
"""

import cloudinary
import cloudinary.uploader
import os
import argparse
import re
from pathlib import Path

# Cloudinary 설정
cloudinary.config(
    cloud_name="ddzbnrfei",
    api_key="786297442195463",
    api_secret="5XOALKL3aV3yUy_eE2QO5cFmI3k",
    secure=True
)

def natural_sort_key(filename):
    """파일명에서 숫자를 추출하여 자연스러운 정렬"""
    numbers = re.findall(r'\d+', filename)
    if numbers:
        return int(numbers[0])
    return 0

def upload_images(folder_name, image_path):
    """
    지정된 폴더의 이미지들을 Cloudinary에 업로드
    
    Args:
        folder_name: Cloudinary 폴더명 (예: 'carrot', 'sweet_potato')
        image_path: 로컬 이미지 폴더 경로
    """
    
    # 경로 확인
    path = Path(image_path)
    if not path.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {image_path}")
        return
    
    # 이미지 파일 필터링 (jpg, jpeg, png, webp)
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = [f for f in path.iterdir() 
              if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return
    
    # 파일명 기준 정렬
    images.sort(key=lambda x: natural_sort_key(x.name))
    
    print(f"\n🚀 Cloudinary 업로드 시작")
    print(f"📁 대상 폴더: {folder_name}")
    print(f"🖼️  이미지 수: {len(images)}장\n")
    print("-" * 50)
    
    uploaded_urls = []
    
    for idx, image in enumerate(images, 1):
        # public_id 생성 (폴더명_순번_슬라이드유형)
        original_name = image.stem  # 확장자 제외 파일명
        
        # 원본 파일명에서 중복 방지: sweet_potato_01_hook → 01_hook 추출
        # 패턴: [폴더명]_[숫자]_[나머지] 에서 [숫자]_[나머지]만 추출
        if original_name.startswith(f"{folder_name}_"):
            # 이미 폴더명이 포함된 파일명 (예: pineapple_01) -> 그대로 사용
            public_id = f"{folder_name}/{original_name}"
        else:
            # 일반 파일명 -> 순번 + 원본파일명
            public_id = f"{folder_name}/{folder_name}_{idx:02d}_{original_name}"
        
        try:
            # 업로드 실행
            result = cloudinary.uploader.upload(
                str(image),
                public_id=public_id,
                asset_folder=folder_name,
                overwrite=True,
                resource_type="image"
            )
            
            secure_url = result.get('secure_url', '')
            uploaded_urls.append(secure_url)
            
            print(f"✅ [{idx:02d}/{len(images)}] {image.name}")
            print(f"   → {secure_url}\n")
            
        except Exception as e:
            print(f"❌ [{idx:02d}/{len(images)}] {image.name} 업로드 실패")
            print(f"   → 에러: {str(e)}\n")
    
    print("-" * 50)
    print(f"\n🎉 업로드 완료! ({len(uploaded_urls)}/{len(images)}장)")
    print(f"\n📋 업로드된 URL 목록:")
    for idx, url in enumerate(uploaded_urls, 1):
        print(f"{idx:02d}: {url}")
    
    return uploaded_urls

def main():
    parser = argparse.ArgumentParser(
        description='Project Sunshine - Cloudinary 이미지 업로드',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python upload_to_cloudinary.py --folder sweet_potato --path ./images/sweet_potato/
  python upload_to_cloudinary.py -f apple -p ~/Desktop/apple_images/
        """
    )
    
    parser.add_argument(
        '--folder', '-f',
        required=True,
        help='Cloudinary 폴더명 (예: carrot, sweet_potato, apple)'
    )
    
    parser.add_argument(
        '--path', '-p',
        required=True,
        help='로컬 이미지 폴더 경로'
    )
    
    args = parser.parse_args()
    
    upload_images(args.folder, args.path)

if __name__ == "__main__":
    main()
