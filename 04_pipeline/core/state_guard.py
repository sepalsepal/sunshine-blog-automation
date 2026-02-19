#!/usr/bin/env python3
"""
Project Sunshine — 상태 전이 가드
버전: v1.0
작성: 김부장 + 레드2
승인: 박세준 PD
일시: 2026-02-04

핵심 원칙:
- 상태 전이 = "실행 완료" (결과 검증됨)
- 상태 전이 ≠ "의도 완료" (버튼 눌림)
- 모든 상태 전이는 보장 조건 충족 후에만 발생
"""

import json
import time
from pathlib import Path
from typing import Tuple, List, Optional
from datetime import datetime


class StateGuard:
    """상태 전이 전 필수 조건 검증"""

    @staticmethod
    def check_reoverlay_complete(folder_path: Path, food_id: str) -> Tuple[bool, List[str]]:
        """
        reoverlay 완료 검증

        보장 조건:
        1. text_overlay.py 실행 성공
        2. 결과 이미지 파일 존재
        3. 이미지 파일 수정 시간이 최근 (5분 이내)

        Returns:
            (성공 여부, 실패 사유 리스트)
        """
        errors = []

        if not folder_path or not folder_path.exists():
            errors.append("폴더가 존재하지 않음")
            return (False, errors)

        # 1. 이미지 파일 존재 확인
        image_files = list(folder_path.glob(f"{food_id}_*.png"))
        # metadata 이미지 제외
        image_files = [f for f in image_files if 'metadata' not in f.name.lower()]

        if len(image_files) < 4:
            errors.append(f"이미지 부족: {len(image_files)}장 (4장 필요)")

        # 2. 이미지 수정 시간 확인 (5분 이내)
        current_time = time.time()
        recent_modified = False

        for img in image_files:
            if current_time - img.stat().st_mtime < 300:  # 5분
                recent_modified = True
                break

        if not recent_modified and image_files:
            errors.append("이미지가 최근 수정되지 않음 (reoverlay 미실행)")

        return (len(errors) == 0, errors)

    @staticmethod
    def check_approval_ready(folder_path: Path, food_id: str) -> Tuple[bool, List[str]]:
        """
        승인 준비 완료 검증

        보장 조건:
        1. 이미지 4장 존재
        2. Cloudinary 업로드 완료 (선택적 - 없으면 경고만)
        3. image_urls 확보 (선택적)
        4. 캡션 존재

        Returns:
            (성공 여부, 실패 사유 리스트)
        """
        errors = []
        warnings = []

        if not folder_path or not folder_path.exists():
            errors.append("폴더가 존재하지 않음")
            return (False, errors)

        # 1. 이미지 4장 확인
        image_files = list(folder_path.glob(f"{food_id}_*.png"))
        image_files = [f for f in image_files if 'metadata' not in f.name.lower()]

        if len(image_files) < 4:
            errors.append(f"이미지 부족: {len(image_files)}장 (4장 필요)")

        # 2. metadata.json 확인
        metadata_path = folder_path / "metadata.json"
        metadata = {}

        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                errors.append(f"metadata.json 읽기 실패: {str(e)}")

        # 3. Cloudinary 업로드 확인 (경고만, 에러 아님)
        if not metadata.get("cloudinary_uploaded"):
            warnings.append("Cloudinary 업로드 안 됨 (게시 전 필요)")

        # 4. image_urls 확인 (경고만)
        image_urls = metadata.get("image_urls", [])
        if len(image_urls) < 4:
            warnings.append(f"image_urls 부족: {len(image_urls)}개 (게시 전 4개 필요)")

        # 5. 캡션 확인
        caption = metadata.get("caption") or ""
        caption_files = [
            folder_path / "caption_instagram.txt",
            folder_path / "caption.txt",
        ]

        caption_exists = bool(caption)
        for cf in caption_files:
            if cf.exists():
                caption_exists = True
                break

        if not caption_exists:
            errors.append("캡션 없음")

        # 경고가 있으면 에러에 추가 (but 통과는 가능)
        # 현재는 이미지 + 캡션만 필수로 체크
        return (len(errors) == 0, errors)

    @staticmethod
    def check_post_ready(folder_path: Path, food_id: str) -> Tuple[bool, List[str]]:
        """
        게시 준비 완료 검증

        보장 조건:
        1. approved 상태
        2. image_urls >= 2 (Instagram 캐러셀 최소 요구)
        3. 캡션 존재
        4. URL 유효성 (https로 시작)

        Returns:
            (성공 여부, 실패 사유 리스트)
        """
        errors = []

        if not folder_path or not folder_path.exists():
            errors.append("폴더가 존재하지 않음")
            return (False, errors)

        # 1. metadata.json 확인
        metadata_path = folder_path / "metadata.json"

        if not metadata_path.exists():
            errors.append("metadata.json 없음")
            return (False, errors)

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            errors.append(f"metadata.json 읽기 실패: {str(e)}")
            return (False, errors)

        # 2. 상태 확인
        status = metadata.get("status")
        if status != "approved":
            errors.append(f"상태 오류: {status} (approved 필요)")

        # 3. image_urls 최소 2개 확인
        image_urls = metadata.get("image_urls", [])
        if len(image_urls) < 2:
            errors.append(f"image_urls 부족: {len(image_urls)}개 (최소 2개 필요)")

        # 4. URL 유효성 확인
        if image_urls:
            invalid_urls = [url for url in image_urls if not url.startswith("https://")]
            if invalid_urls:
                errors.append(f"잘못된 URL 형식: {len(invalid_urls)}개")

        # 5. 캡션 확인
        caption = metadata.get("caption") or ""
        if not caption:
            caption_files = [
                folder_path / "caption_instagram.txt",
                folder_path / "caption.txt",
            ]
            for cf in caption_files:
                if cf.exists():
                    try:
                        caption = cf.read_text(encoding='utf-8')
                        break
                    except:
                        pass

        if not caption:
            errors.append("캡션 없음")

        return (len(errors) == 0, errors)

    @staticmethod
    def check_cloudinary_uploaded(folder_path: Path, food_id: str) -> Tuple[bool, List[str], List[str]]:
        """
        Cloudinary 업로드 상태 확인

        Returns:
            (업로드 완료 여부, 에러 리스트, 업로드된 URL 리스트)
        """
        errors = []
        urls = []

        if not folder_path or not folder_path.exists():
            errors.append("폴더가 존재하지 않음")
            return (False, errors, urls)

        metadata_path = folder_path / "metadata.json"

        if not metadata_path.exists():
            errors.append("metadata.json 없음")
            return (False, errors, urls)

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            errors.append(f"metadata.json 읽기 실패: {str(e)}")
            return (False, errors, urls)

        if not metadata.get("cloudinary_uploaded"):
            errors.append("Cloudinary 업로드 안 됨")
            return (False, errors, urls)

        urls = metadata.get("image_urls", [])
        if len(urls) < 4:
            errors.append(f"업로드된 이미지 부족: {len(urls)}개")
            return (False, errors, urls)

        return (True, [], urls)


def update_metadata(metadata_path: Path, updates: dict) -> bool:
    """
    metadata.json 업데이트 헬퍼

    Args:
        metadata_path: metadata.json 경로
        updates: 업데이트할 키-값 딕셔너리

    Returns:
        성공 여부
    """
    try:
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

        metadata.update(updates)
        metadata["updated_at"] = datetime.now().isoformat()

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"[update_metadata] 오류: {e}")
        return False


# ═══════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("StateGuard 테스트")
    print("=" * 50)

    # 테스트 폴더 (실제 존재하는 폴더로 테스트)
    test_folder = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents/3_approved/044_burdock_우엉")
    test_food_id = "burdock"

    if test_folder.exists():
        print(f"\n테스트 폴더: {test_folder}")

        # 승인 준비 검증
        success, errors = StateGuard.check_approval_ready(test_folder, test_food_id)
        print(f"\n승인 준비 검증: {'✅ 통과' if success else '❌ 실패'}")
        if errors:
            for e in errors:
                print(f"  - {e}")

        # 게시 준비 검증
        success, errors = StateGuard.check_post_ready(test_folder, test_food_id)
        print(f"\n게시 준비 검증: {'✅ 통과' if success else '❌ 실패'}")
        if errors:
            for e in errors:
                print(f"  - {e}")

        # Cloudinary 업로드 확인
        success, errors, urls = StateGuard.check_cloudinary_uploaded(test_folder, test_food_id)
        print(f"\nCloudinary 업로드: {'✅ 완료' if success else '❌ 미완료'}")
        if errors:
            for e in errors:
                print(f"  - {e}")
        if urls:
            print(f"  URLs: {len(urls)}개")
    else:
        print(f"\n테스트 폴더 없음: {test_folder}")

    print("\n✅ StateGuard 테스트 완료")
