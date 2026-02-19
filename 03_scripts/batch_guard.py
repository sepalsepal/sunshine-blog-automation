#!/usr/bin/env python3
"""
batch_guard.py - WO-FREEZE-001 배치 안전장치
모든 batch 계열 스크립트에서 import하여 사용
"""

import sys
import os

# ═══════════════════════════════════════════════════════════════
# 배치 상한 설정
# ═══════════════════════════════════════════════════════════════
MAX_BATCH_SIZE = 21
CLOUDINARY_FROZEN = True


def check_batch_limit(targets: list, force_approved: bool = False) -> bool:
    """배치 실행 전 상한 체크

    Args:
        targets: 처리할 대상 리스트
        force_approved: PD 승인 플래그

    Returns:
        True면 진행 가능, False면 차단
    """
    if len(targets) > MAX_BATCH_SIZE:
        if force_approved or os.environ.get("FORCE_PD_APPROVED") == "true":
            print(f"⚠️ WARNING: {len(targets)}건 > 최대 {MAX_BATCH_SIZE}건")
            print("   PD 승인 플래그로 진행합니다.")
            return True
        else:
            print(f"🔴 BLOCKED: {len(targets)}건 > 최대 {MAX_BATCH_SIZE}건")
            print(f"   21건 초과 실행은 PD 승인 필요.")
            print(f"   해제: FORCE_PD_APPROVED=true 환경변수 설정")
            print(f"   또는: --force-pd-approved 플래그 사용")
            return False
    return True


def check_cloudinary_frozen() -> bool:
    """Cloudinary 업로드 동결 여부 체크

    Returns:
        True면 동결 상태 (업로드 차단)
    """
    if CLOUDINARY_FROZEN:
        if os.environ.get("CLOUDINARY_UNFROZEN") == "true":
            print("⚠️ WARNING: Cloudinary 동결 해제됨 (환경변수)")
            return False
        return True
    return False


def cloudinary_upload_guard(func):
    """Cloudinary 업로드 함수 데코레이터"""
    def wrapper(*args, **kwargs):
        if check_cloudinary_frozen():
            print("🔴 FROZEN: Cloudinary 업로드 동결 중")
            print("   사유: WO-FREEZE-001 동결 조치")
            print("   해제: CLOUDINARY_UNFROZEN=true 환경변수 설정")
            return None
        return func(*args, **kwargs)
    return wrapper


def check_qc_passed(folder_path: str, asset_type: str = "blog_06") -> bool:
    """QC 통과 여부 체크

    Args:
        folder_path: 콘텐츠 폴더 경로
        asset_type: 어셋 타입

    Returns:
        True면 QC 통과, False면 미통과
    """
    from pathlib import Path
    qc_file = Path(folder_path) / "qc_result.json"

    if not qc_file.exists():
        print(f"⚠️ QC 결과 파일 없음: {folder_path}")
        return False

    import json
    try:
        with open(qc_file, "r") as f:
            qc_data = json.load(f)
        return qc_data.get(asset_type, {}).get("passed", False)
    except Exception as e:
        print(f"⚠️ QC 파일 읽기 실패: {e}")
        return False


def require_pipeline_auth():
    """파이프라인 인증 요구"""
    if os.environ.get("PIPELINE_AUTHORIZED") != "true":
        print("🔴 FROZEN: WO-FREEZE-001 동결 중. 직접 실행 차단됨.")
        print("   사유: 파이프라인 외부 단독 실행 금지")
        print("   해제: cli.py 통해 실행하거나 PIPELINE_AUTHORIZED=true 설정")
        sys.exit(1)


# 테스트용
if __name__ == "__main__":
    print("batch_guard.py - WO-FREEZE-001 안전장치 모듈")
    print(f"MAX_BATCH_SIZE: {MAX_BATCH_SIZE}")
    print(f"CLOUDINARY_FROZEN: {CLOUDINARY_FROZEN}")

    # 테스트
    test_targets = list(range(30))
    print(f"\n[테스트] {len(test_targets)}건 배치 실행 시도...")
    if not check_batch_limit(test_targets):
        print("→ 차단됨 (정상)")
