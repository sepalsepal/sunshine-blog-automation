#!/usr/bin/env python3
"""
로컬 이미지 폴더를 Cloudinary에 업로드하는 스크립트
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트로 이동
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import cloudinary
import cloudinary.uploader
import cloudinary.api

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

IMAGES_DIR = ROOT / "content" / "images"
SKIP_FOLDERS = {"reference", "sunshine", "temp", ".DS_Store"}


def get_cloudinary_folders():
    """Cloudinary의 기존 폴더 목록"""
    try:
        result = cloudinary.api.root_folders()
        return [f["name"] for f in result.get("folders", [])]
    except Exception as e:
        print(f"Error getting folders: {e}")
        return []


def delete_cloudinary_folder(folder_name):
    """Cloudinary 폴더 삭제"""
    try:
        # 폴더 내 모든 리소스 삭제
        cloudinary.api.delete_resources_by_prefix(f"{folder_name}/")
        # 폴더 삭제
        cloudinary.api.delete_folder(folder_name)
        print(f"  ✓ Deleted: {folder_name}")
    except Exception as e:
        print(f"  ✗ Error deleting {folder_name}: {e}")


def upload_folder(folder_path):
    """폴더 내 이미지들을 Cloudinary에 업로드"""
    folder_name = folder_path.name
    images = sorted(list(folder_path.glob("*.png")) + list(folder_path.glob("*.jpg")))

    if not images:
        print(f"  ⊘ No images in {folder_name}")
        return 0

    uploaded = 0
    for img in images:
        try:
            public_id = f"{folder_name}/{img.stem}"
            result = cloudinary.uploader.upload(
                str(img),
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            uploaded += 1
            print(f"  ✓ {img.name}")
        except Exception as e:
            print(f"  ✗ {img.name}: {e}")

    return uploaded


def main():
    print("=" * 50)
    print("로컬 → Cloudinary 동기화")
    print("=" * 50)

    # 1. 로컬 폴더 목록
    local_folders = []
    for folder in sorted(IMAGES_DIR.iterdir()):
        if folder.is_dir() and folder.name not in SKIP_FOLDERS:
            local_folders.append(folder.name)

    print(f"\n로컬 폴더: {len(local_folders)}개")

    # 2. Cloudinary 폴더 목록
    cloud_folders = get_cloudinary_folders()
    print(f"Cloudinary 폴더: {len(cloud_folders)}개")

    # 3. 삭제할 폴더 (Cloudinary에만 있는 것)
    to_delete = set(cloud_folders) - set(local_folders)
    if to_delete:
        print(f"\n[1/3] Cloudinary에서 삭제할 폴더: {len(to_delete)}개")
        for folder in to_delete:
            delete_cloudinary_folder(folder)
    else:
        print("\n[1/3] 삭제할 폴더 없음")

    # 4. 업로드할 폴더
    print(f"\n[2/3] 업로드할 폴더: {len(local_folders)}개")
    total_uploaded = 0
    for folder_name in local_folders:
        folder_path = IMAGES_DIR / folder_name
        print(f"\n📁 {folder_name}")
        count = upload_folder(folder_path)
        total_uploaded += count

    print("\n" + "=" * 50)
    print(f"[3/3] 완료! 총 {total_uploaded}개 이미지 업로드")
    print("=" * 50)


if __name__ == "__main__":
    main()
