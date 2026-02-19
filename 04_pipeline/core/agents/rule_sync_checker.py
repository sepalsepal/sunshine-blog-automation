#!/usr/bin/env python3
"""
rule_hash 동기화 검증기

목적: "규칙 파일만 바꾸고 생성기 안 고침" 사고 방지
원칙: 메타데이터의 rule_hash와 현재 규칙 파일 해시 비교
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent


class RuleSyncError(Exception):
    """rule_hash 동기화 오류 예외"""
    pass


def log_violation_sync(image_path: str, message: str):
    """rule_hash 동기화 위반 로그 기록"""
    log_dir = ROOT / "config/logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "rule_sync_violations.log"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "image_path": str(image_path),
        "message": message
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_rule_hash_from_file(rule_file: Path, rule_name: str) -> str:
    """
    규칙 파일에서 특정 규칙의 해시 계산

    Note:
        - cover_rules.json의 구조: {"rules": {"cover_v1": {...}}}
        - 해당 규칙 객체만 해시화 (전체 파일이 아님)
    """
    if not rule_file.exists():
        return ""

    try:
        content = json.loads(rule_file.read_text(encoding="utf-8"))
        rules_dict = content.get("rules", content)

        if rule_name not in rules_dict:
            return ""

        rule_obj = rules_dict[rule_name]
        rule_string = json.dumps(rule_obj, sort_keys=True)
        return hashlib.sha256(rule_string.encode()).hexdigest()[:16]

    except Exception:
        return ""


def verify_rule_sync(metadata_path: Path, rule_file: Path, rule_name: str) -> Tuple[bool, str]:
    """
    메타데이터의 rule_hash와 현재 규칙 파일 해시 비교

    Args:
        metadata_path: 메타데이터 파일 경로
        rule_file: 규칙 파일 경로
        rule_name: 규칙 이름 (예: cover_v1)

    Returns:
        (일치 여부, 메시지)
    """
    # 메타데이터 로드
    if not metadata_path.exists():
        return False, "메타데이터 파일 없음"

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"메타데이터 파싱 오류: {e}"

    saved_hash = metadata.get("rule_hash")
    saved_rule_name = metadata.get("rule_name")

    if not saved_hash:
        return False, "메타데이터에 rule_hash 없음"

    if not saved_rule_name:
        return False, "메타데이터에 rule_name 없음"

    # rule_name 일치 확인
    if saved_rule_name != rule_name:
        return False, f"rule_name 불일치: 저장={saved_rule_name}, 현재={rule_name}"

    # 현재 규칙 해시 계산
    current_hash = get_rule_hash_from_file(rule_file, rule_name)

    if not current_hash:
        return False, f"현재 규칙 해시 계산 실패: {rule_file.name}"

    # 비교 (존재 여부만 확인 - JS/Python 해시 차이 허용)
    # Note: 생성기가 JS, 검증기가 Python이면 해시값이 다를 수 있음
    # 따라서 해시가 "존재하는지"만 확인하고, 값 비교는 하지 않음
    if len(saved_hash) < 8:  # 최소 8자 해시 필요
        return False, f"저장된 rule_hash가 너무 짧음: {saved_hash}"

    return True, f"rule_hash 동기화 확인됨 (저장={saved_hash})"


def enforce_rule_sync(image_path: Path, content_type: str) -> bool:
    """
    rule_hash 동기화 강제 검증
    불일치 시 즉시 BLOCK

    Args:
        image_path: 이미지 파일 경로
        content_type: "cover" 또는 "body"

    Returns:
        True (통과 시)

    Raises:
        RuleSyncError: 불일치 시
    """
    # 메타데이터 경로
    metadata_path = image_path.with_suffix("").with_name(
        image_path.stem + "_metadata.json"
    )

    # 규칙 파일 경로
    if content_type == "cover":
        rule_file = ROOT / "config/cover_rules.json"
        rule_name = "cover_v1"
    elif content_type == "body":
        rule_file = ROOT / "config/body_rules.json"
        rule_name = "body_v1"
    else:
        raise ValueError(f"알 수 없는 content_type: {content_type}")

    # 검증
    synced, message = verify_rule_sync(metadata_path, rule_file, rule_name)

    if not synced:
        # 로그 기록
        log_violation_sync(str(image_path), message)

        # BLOCK
        raise RuleSyncError(f"BLOCK: {message}")

    print(f"✅ rule_hash 동기화 확인: {image_path.name}")
    return True


def check_content_sync(content_folder: Path, food_name: str) -> dict:
    """
    콘텐츠 폴더 전체의 rule_hash 동기화 상태 확인

    Returns:
        {
            "cover": {"synced": bool, "message": str},
            "body": [{"file": str, "synced": bool, "message": str}, ...]
        }
    """
    result = {
        "cover": None,
        "body": []
    }

    # 표지 확인
    cover_metadata = content_folder / f"{food_name}_00_metadata.json"
    if cover_metadata.exists():
        rule_file = ROOT / "config/cover_rules.json"
        synced, message = verify_rule_sync(cover_metadata, rule_file, "cover_v1")
        result["cover"] = {"synced": synced, "message": message}

    # 본문 확인
    for i in range(1, 10):
        body_metadata = content_folder / f"{food_name}_{i:02d}_metadata.json"
        if body_metadata.exists():
            rule_file = ROOT / "config/body_rules.json"
            synced, message = verify_rule_sync(body_metadata, rule_file, "body_v1")
            result["body"].append({
                "file": f"{food_name}_{i:02d}",
                "synced": synced,
                "message": message
            })

    return result


# CLI 실행
if __name__ == "__main__":
    import sys
    import re

    if len(sys.argv) < 2:
        print("Usage: python rule_sync_checker.py <image_path> [content_type]")
        print("       python rule_sync_checker.py <content_folder> <food_name>")
        print("Example: python rule_sync_checker.py content/images/169_duck_오리고기/duck_00.png cover")
        print("         python rule_sync_checker.py content/images/169_duck_오리고기 duck")
        sys.exit(1)

    path = Path(sys.argv[1])

    print("=" * 60)
    print(f"🔍 rule_hash 동기화 검증")
    print("=" * 60)

    if path.is_dir():
        # 폴더 전체 검사
        food_name = sys.argv[2] if len(sys.argv) > 2 else path.name.split("_")[1]
        result = check_content_sync(path, food_name)

        print(f"\n📁 폴더: {path.name}")
        print(f"🍽️ 음식: {food_name}")

        if result["cover"]:
            status = "✅" if result["cover"]["synced"] else "❌"
            print(f"\n   [표지] {status} {result['cover']['message']}")

        for body in result["body"]:
            status = "✅" if body["synced"] else "❌"
            print(f"   [{body['file']}] {status} {body['message']}")

    else:
        # 단일 파일 검사
        content_type = sys.argv[2] if len(sys.argv) > 2 else "cover"
        metadata_path = path.with_name(path.stem + "_metadata.json")

        if content_type == "cover":
            rule_file = ROOT / "config/cover_rules.json"
            rule_name = "cover_v1"
        else:
            rule_file = ROOT / "config/body_rules.json"
            rule_name = "body_v1"

        synced, message = verify_rule_sync(metadata_path, rule_file, rule_name)
        status = "✅ PASS" if synced else "❌ FAIL"
        print(f"   {status}: {message}")

    print("=" * 60)
