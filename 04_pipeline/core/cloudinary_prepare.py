#!/usr/bin/env python3
"""
Project Sunshine — Cloudinary 자동 준비 모듈
버전: v1.0
작성: 김부장 + 레드2
승인: 박세준 PD
일시: 2026-02-04

핵심 원칙:
- body_ready 진입 = Cloudinary 업로드 완료 상태
- 게시 버튼 = Instagram API 호출만 (업로드 코드 없음)
- 게시 실패 시 원인 = Instagram API 하나로 한정
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Optional

# Cloudinary 설정
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    print("[WARN] cloudinary 라이브러리 없음: pip install cloudinary")

PROJECT_ROOT = Path(__file__).parent.parent


def configure_cloudinary():
    """Cloudinary 설정 초기화"""
    if not CLOUDINARY_AVAILABLE:
        return False

    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')

    if not all([cloud_name, api_key, api_secret]):
        print("[WARN] Cloudinary 환경변수 미설정")
        return False

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    return True


def prepare_cloudinary(folder_path: Path, food_id: str) -> Tuple[bool, str]:
    """
    body_ready 폴더의 Cloudinary 준비

    호출 시점:
    - 본문 생성 완료 직후
    - body_ready 폴더 이동 직후

    Args:
        folder_path: 콘텐츠 폴더 경로
        food_id: 음식 ID

    Returns:
        (성공 여부, 메시지)
    """
    if not CLOUDINARY_AVAILABLE:
        return (False, "cloudinary 라이브러리 없음")

    if not configure_cloudinary():
        return (False, "Cloudinary 설정 실패")

    print(f"[CLOUDINARY] 준비 시작: {food_id}")

    # ═══════════════════════════════════════════
    # STEP 1: 이미 업로드됐는지 확인
    # ═══════════════════════════════════════════
    metadata_path = folder_path / "metadata.json"

    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 이미 완료된 경우 스킵
            image_urls = metadata.get("image_urls", [])
            if (metadata.get("cloudinary_uploaded") and
                isinstance(image_urls, list) and
                len(image_urls) >= 4):
                print(f"[CLOUDINARY] 이미 준비됨: {food_id}")
                return (True, "이미 준비됨")
        except Exception as e:
            print(f"[CLOUDINARY] metadata 로드 실패: {e}")
            metadata = {"food_id": food_id}
    else:
        metadata = {"food_id": food_id}

    # ═══════════════════════════════════════════
    # STEP 2: 이미지 파일 수집
    # ═══════════════════════════════════════════
    image_files = sorted(folder_path.glob(f"{food_id}_*.png"))
    image_files = [f for f in image_files if 'metadata' not in f.name.lower()]

    if len(image_files) < 4:
        # 다른 패턴 시도
        all_pngs = sorted(folder_path.glob("*.png"))
        all_pngs = [f for f in all_pngs if 'metadata' not in f.name.lower()]
        if len(all_pngs) >= 4:
            image_files = all_pngs[:4]
        else:
            return (False, f"이미지 부족: {len(image_files)}장 (4장 필요)")

    print(f"[CLOUDINARY] 이미지 {len(image_files)}장 발견")

    # ═══════════════════════════════════════════
    # STEP 3: Cloudinary 업로드
    # ═══════════════════════════════════════════
    try:
        urls = []

        for img_path in image_files[:4]:  # 최대 4장
            result = cloudinary.uploader.upload(
                str(img_path),
                folder=f"project_sunshine/{food_id}",
                public_id=img_path.stem,
                overwrite=True
            )

            url = result.get('secure_url')
            if url:
                urls.append(url)
                print(f"[CLOUDINARY] 업로드: {img_path.name} → {url[:60]}...")
            else:
                print(f"[CLOUDINARY] URL 없음: {img_path.name}")

    except Exception as e:
        return (False, f"업로드 실패: {str(e)}")

    # ═══════════════════════════════════════════
    # STEP 4: 검증 — URL 개수/타입
    # ═══════════════════════════════════════════
    if len(urls) < 4:
        return (False, f"업로드 불완전: {len(urls)}장만 성공")

    # 타입 검증
    for i, url in enumerate(urls):
        if not isinstance(url, str):
            return (False, f"URL[{i}] 타입 오류: {type(url).__name__}")
        if not url.startswith("https://"):
            return (False, f"URL[{i}] 형식 오류")

    print(f"[CLOUDINARY] URL 검증 통과: {len(urls)}개, type=list[str]")

    # ═══════════════════════════════════════════
    # STEP 5: metadata.json 저장
    # ═══════════════════════════════════════════
    metadata["image_urls"] = urls  # 반드시 list[str]
    metadata["cloudinary_uploaded"] = True
    metadata["cloudinary_uploaded_at"] = datetime.now().isoformat()
    metadata["cloudinary_folder"] = f"project_sunshine/{food_id}"

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # ═══════════════════════════════════════════
    # STEP 6: 저장 검증 (재로드)
    # ═══════════════════════════════════════════
    with open(metadata_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)

    saved_urls = verify.get("image_urls")

    if not isinstance(saved_urls, list):
        return (False, f"저장 검증 실패: type={type(saved_urls).__name__}")

    if len(saved_urls) < 4:
        return (False, f"저장 검증 실패: {len(saved_urls)}개만 저장됨")

    print(f"[CLOUDINARY] 준비 완료: {food_id} ({len(urls)}장)")

    return (True, f"준비 완료: {len(urls)}장")


def is_cloudinary_ready(folder_path: Path, food_id: str) -> Tuple[bool, List[str]]:
    """
    Cloudinary 준비 상태 확인만 (준비 안 함)

    Args:
        folder_path: 콘텐츠 폴더 경로
        food_id: 음식 ID

    Returns:
        (준비됨 여부, 에러 리스트)
    """
    errors = []
    metadata_path = folder_path / "metadata.json"

    if not metadata_path.exists():
        errors.append("metadata.json 없음")
        return (False, errors)

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        errors.append(f"metadata.json 읽기 실패: {e}")
        return (False, errors)

    # Cloudinary 업로드 플래그 확인
    if not metadata.get("cloudinary_uploaded"):
        errors.append("Cloudinary 업로드 안 됨")

    # image_urls 검증
    image_urls = metadata.get("image_urls")

    if image_urls is None:
        errors.append("image_urls 없음")
    elif not isinstance(image_urls, list):
        errors.append(f"image_urls 타입 오류: {type(image_urls).__name__} (list 필요)")
    elif len(image_urls) < 4:
        errors.append(f"image_urls 부족: {len(image_urls)}개 (4개 필요)")
    else:
        # URL 형식 검증
        invalid = []
        for i, url in enumerate(image_urls):
            if not isinstance(url, str):
                invalid.append(f"[{i}] type={type(url).__name__}")
            elif not url.startswith("https://"):
                invalid.append(f"[{i}] not https")

        if invalid:
            errors.append(f"잘못된 URL: {invalid}")

    return (len(errors) == 0, errors)


def ensure_cloudinary_ready(folder_path: Path, food_id: str) -> Tuple[bool, List[str]]:
    """
    Cloudinary 준비 상태 확인 + 미준비 시 자동 준비

    게시 전 필수 호출

    Args:
        folder_path: 콘텐츠 폴더 경로
        food_id: 음식 ID

    Returns:
        (준비됨 여부, 에러 리스트)
    """
    # 먼저 상태 확인
    ready, errors = is_cloudinary_ready(folder_path, food_id)

    if ready:
        return (True, [])

    # 미준비 시 자동 준비
    print(f"[CLOUDINARY] 자동 준비 시작: {food_id}")
    success, message = prepare_cloudinary(folder_path, food_id)

    if success:
        return (True, [])
    else:
        return (False, [message])


def is_body_ready_complete(folder_path: Path, food_id: str) -> Tuple[bool, List[str]]:
    """
    body_ready 상태 완전성 검증

    body_ready = 게시 준비 완료 상태
    - 이미지 4장 존재
    - Cloudinary 업로드 완료
    - image_urls 4개 확보 (list[str])

    Args:
        folder_path: 콘텐츠 폴더 경로
        food_id: 음식 ID

    Returns:
        (완전성 여부, 에러 리스트)
    """
    errors = []

    if not folder_path.exists():
        errors.append("폴더 없음")
        return (False, errors)

    # 1. 이미지 파일 확인
    image_files = list(folder_path.glob(f"{food_id}_*.png"))
    image_files = [f for f in image_files if 'metadata' not in f.name.lower()]

    if len(image_files) < 4:
        errors.append(f"이미지 부족: {len(image_files)}장 (4장 필요)")

    # 2. metadata.json 확인
    metadata_path = folder_path / "metadata.json"

    if not metadata_path.exists():
        errors.append("metadata.json 없음")
        return (False, errors)

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        errors.append(f"metadata.json 읽기 실패: {e}")
        return (False, errors)

    # 3. Cloudinary 업로드 확인
    if not metadata.get("cloudinary_uploaded"):
        errors.append("Cloudinary 업로드 안 됨")

    # 4. image_urls 타입/개수 확인
    image_urls = metadata.get("image_urls")

    if image_urls is None:
        errors.append("image_urls 없음")
    elif not isinstance(image_urls, list):
        errors.append(f"image_urls 타입 오류: {type(image_urls).__name__}")
    elif len(image_urls) < 4:
        errors.append(f"image_urls 부족: {len(image_urls)}개")
    else:
        # URL 형식 검증
        invalid = [u for u in image_urls if not isinstance(u, str) or not u.startswith("https://")]
        if invalid:
            errors.append(f"잘못된 URL: {len(invalid)}개")

    # 5. 캡션 확인
    caption = metadata.get("caption", "")
    if not caption:
        caption_files = [
            folder_path / "caption_instagram.txt",
            folder_path / "caption.txt",
        ]
        for cf in caption_files:
            if cf.exists():
                caption = cf.read_text(encoding='utf-8').strip()
                break

    if not caption:
        errors.append("캡션 없음")

    return (len(errors) == 0, errors)


def get_image_urls(folder_path: Path, food_id: str) -> Optional[List[str]]:
    """
    metadata.json에서 image_urls 가져오기

    Returns:
        list[str] 또는 None (없거나 타입 오류 시)
    """
    metadata_path = folder_path / "metadata.json"

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        image_urls = metadata.get("image_urls")

        if not isinstance(image_urls, list):
            return None

        if len(image_urls) < 2:
            return None

        return image_urls

    except Exception:
        return None


# ═══════════════════════════════════════════
# CLI 테스트
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cloudinary_prepare.py <command> [args]")
        print("")
        print("Commands:")
        print("  prepare <folder_path> <food_id>  - Cloudinary 준비")
        print("  check <folder_path> <food_id>    - 준비 상태 확인")
        print("  batch                            - body_ready 전체 처리")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "prepare" and len(sys.argv) >= 4:
        folder = Path(sys.argv[2])
        food_id = sys.argv[3]
        success, msg = prepare_cloudinary(folder, food_id)
        print(f"{'✅' if success else '❌'} {msg}")

    elif cmd == "check" and len(sys.argv) >= 4:
        folder = Path(sys.argv[2])
        food_id = sys.argv[3]
        ready, errors = is_cloudinary_ready(folder, food_id)
        if ready:
            print(f"✅ Cloudinary 준비됨: {food_id}")
        else:
            print(f"❌ 미준비: {errors}")

    elif cmd == "batch":
        body_ready_dir = PROJECT_ROOT / "contents" / "2_body_ready"
        if not body_ready_dir.exists():
            print(f"❌ 폴더 없음: {body_ready_dir}")
            sys.exit(1)

        print(f"[BATCH] body_ready 폴더 일괄 처리")

        for folder in sorted(body_ready_dir.iterdir()):
            if not folder.is_dir():
                continue

            # 폴더명에서 food_id 추출 (예: 036_potato_감자 → potato)
            parts = folder.name.split('_')
            if len(parts) >= 2:
                food_id = parts[1]
            else:
                food_id = folder.name

            ready, errors = is_cloudinary_ready(folder, food_id)

            if ready:
                print(f"  ✅ {folder.name}: 준비됨")
            else:
                print(f"  ⏳ {folder.name}: 준비 중...")
                success, msg = prepare_cloudinary(folder, food_id)
                print(f"     {'✅' if success else '❌'} {msg}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
