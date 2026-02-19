#!/usr/bin/env python3
"""
cloudinary_download.py - Cloudinary에서 모든 이미지 다운로드
폴더/파일명 구조 유지하면서 contents/에 저장
"""

import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

CONTENTS_DIR = PROJECT_ROOT / "01_contents" / "cloudinary_restore"


def list_all_resources(resource_type="image", max_results=500):
    """Cloudinary에서 모든 리소스 목록 조회"""
    resources = []
    next_cursor = None

    print(f"\n📋 Cloudinary 리소스 조회 중...")

    while True:
        url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/resources/{resource_type}"
        params = {
            "max_results": max_results,
        }
        if next_cursor:
            params["next_cursor"] = next_cursor

        response = requests.get(
            url,
            params=params,
            auth=(API_KEY, API_SECRET)
        )

        if response.status_code != 200:
            print(f"   ❌ API 오류: {response.status_code}")
            print(f"   {response.text}")
            break

        data = response.json()
        batch = data.get("resources", [])
        resources.extend(batch)
        print(f"   조회: {len(resources)}개...")

        next_cursor = data.get("next_cursor")
        if not next_cursor:
            break

    return resources


def list_folders():
    """Cloudinary 폴더 목록 조회"""
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/folders"
    response = requests.get(url, auth=(API_KEY, API_SECRET))

    if response.status_code == 200:
        return response.json().get("folders", [])
    return []


def list_resources_in_folder(folder_path, resource_type="image"):
    """특정 폴더의 리소스 조회"""
    resources = []
    next_cursor = None

    while True:
        url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/resources/{resource_type}"
        params = {
            "type": "upload",
            "prefix": folder_path,
            "max_results": 500,
        }
        if next_cursor:
            params["next_cursor"] = next_cursor

        response = requests.get(url, params=params, auth=(API_KEY, API_SECRET))

        if response.status_code != 200:
            break

        data = response.json()
        batch = data.get("resources", [])
        resources.extend(batch)

        next_cursor = data.get("next_cursor")
        if not next_cursor:
            break

    return resources


def download_resource(resource, base_dir):
    """리소스 다운로드"""
    public_id = resource.get("public_id", "")
    secure_url = resource.get("secure_url", "")
    format_ext = resource.get("format", "jpg")

    if not secure_url:
        return False

    # 폴더 구조 유지
    # public_id: "sunshine/001_pumpkin/blog/slide_01" -> 해당 경로로 저장
    relative_path = f"{public_id}.{format_ext}"
    local_path = base_dir / relative_path

    # 디렉토리 생성
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # 다운로드
    try:
        response = requests.get(secure_url, timeout=30)
        if response.status_code == 200:
            local_path.write_bytes(response.content)
            return True
    except Exception as e:
        print(f"   ❌ 다운로드 실패: {public_id} - {e}")

    return False


def main():
    if not all([CLOUD_NAME, API_KEY, API_SECRET]):
        print("❌ Cloudinary 설정이 없습니다")
        return

    print("━" * 60)
    print("📥 Cloudinary → 로컬 다운로드")
    print("━" * 60)

    # 저장 디렉토리 생성
    CONTENTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 저장 위치: {CONTENTS_DIR}")

    # 1. 모든 리소스 조회
    resources = list_all_resources()
    print(f"\n📊 총 {len(resources)}개 리소스 발견")

    if not resources:
        print("⚠️ 다운로드할 리소스가 없습니다")
        return

    # 2. 리소스 분석 (폴더별 그룹화)
    folders = {}
    for r in resources:
        public_id = r.get("public_id", "")
        parts = public_id.split("/")
        if len(parts) > 1:
            folder = parts[0]
        else:
            folder = "_root"
        folders.setdefault(folder, []).append(r)

    print(f"\n📂 폴더 구조:")
    for folder, items in sorted(folders.items()):
        print(f"   {folder}/: {len(items)}개")

    # 3. 다운로드 실행
    print(f"\n⬇️ 다운로드 시작...")
    downloaded = 0
    failed = 0

    for i, resource in enumerate(resources):
        if download_resource(resource, CONTENTS_DIR):
            downloaded += 1
        else:
            failed += 1

        if (i + 1) % 20 == 0:
            print(f"   진행: {i + 1}/{len(resources)} (성공: {downloaded}, 실패: {failed})")

    # 4. 결과 보고
    print("\n" + "━" * 60)
    print("📊 다운로드 완료")
    print("━" * 60)
    print(f"📥 총 리소스: {len(resources)}개")
    print(f"✅ 다운로드: {downloaded}개")
    print(f"❌ 실패: {failed}개")
    print(f"📁 저장 위치: {CONTENTS_DIR}")
    print("━" * 60)


if __name__ == "__main__":
    main()
