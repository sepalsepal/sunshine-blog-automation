#!/usr/bin/env python3
"""
WO-2026-0209-023: 승인 게이트

approved 전환 가능 여부 검증 (4개 게이트 모두 통과 필수):
1. P열 캡션 검증 (파스타 규칙 8단계)
2. Q열 캡션 검증 (Threads 규칙)
3. Cloudinary 이미지 존재 (4장 이상)
4. 메타데이터 존재

사용법:
    python validators/approval_gate.py --check 030
    python validators/approval_gate.py --scan-pending
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from validators.caption_validator import (
    validate_instagram_caption,
    validate_threads_caption,
    get_sheet_data
)


def get_cloudinary_urls(content_id: str, eng_name: str) -> List[str]:
    """Cloudinary 이미지 URL 조회"""
    import os
    import cloudinary
    import cloudinary.api
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )

    try:
        result = cloudinary.api.resources(
            type='upload',
            prefix=f'dog_food/{eng_name}',
            max_results=10
        )
        return [r['secure_url'] for r in result.get('resources', [])]
    except Exception as e:
        return []


def get_metadata(content_id: str) -> Optional[Dict]:
    """메타데이터 조회"""
    # 콘텐츠 폴더 탐색
    search_dirs = [
        PROJECT_ROOT / "contents" / "3_approved",
        PROJECT_ROOT / "contents" / "2_body_ready",
        PROJECT_ROOT / "contents" / "1_cover_only",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for folder in search_dir.iterdir():
            if folder.is_dir() and folder.name.startswith(content_id):
                metadata_path = folder / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except:
                        pass
    return None


def can_approve(content_id: str) -> Dict[str, Any]:
    """
    approved 전환 가능 여부 검증

    Args:
        content_id: 콘텐츠 번호 (예: "030")

    Returns:
        {
            "can_approve": bool,
            "blocks": list,
            "gates": dict
        }
    """
    blocks = []
    gates = {
        "p_caption": {"passed": False, "details": None},
        "q_caption": {"passed": False, "details": None},
        "cloudinary": {"passed": False, "details": None},
        "metadata": {"passed": False, "details": None}
    }

    # 시트 데이터 조회
    sheet_data = get_sheet_data()
    item = None
    for row in sheet_data:
        if row['num'] == content_id.zfill(3):
            item = row
            break

    if not item:
        return {
            "can_approve": False,
            "blocks": [{"gate": "데이터", "errors": [f"콘텐츠 {content_id} 없음"]}],
            "gates": gates
        }

    # 게이트 1: P열 캡션 검증
    p_caption = item.get('p_caption', '')
    safety_level = item.get('safety_level', 'SAFE')

    if p_caption and p_caption != '-':
        p_result = validate_instagram_caption(p_caption, safety_level)
        gates["p_caption"]["details"] = p_result

        if p_result['valid']:
            gates["p_caption"]["passed"] = True
        else:
            blocks.append({
                "gate": "P열 캡션",
                "errors": p_result['errors']
            })
    else:
        blocks.append({
            "gate": "P열 캡션",
            "errors": ["캡션 없음"]
        })

    # 게이트 2: Q열 캡션 검증
    q_caption = item.get('q_caption', '')

    if q_caption and q_caption != '-':
        q_result = validate_threads_caption(q_caption)
        gates["q_caption"]["details"] = q_result

        if q_result['valid']:
            gates["q_caption"]["passed"] = True
        else:
            blocks.append({
                "gate": "Q열 캡션",
                "errors": q_result['errors']
            })
    else:
        blocks.append({
            "gate": "Q열 캡션",
            "errors": ["캡션 없음"]
        })

    # 게이트 3: Cloudinary 이미지
    eng_name = item.get('eng_name', '')
    cloudinary_urls = get_cloudinary_urls(content_id, eng_name)
    gates["cloudinary"]["details"] = {"count": len(cloudinary_urls), "urls": cloudinary_urls[:4]}

    if len(cloudinary_urls) >= 4:
        gates["cloudinary"]["passed"] = True
    else:
        blocks.append({
            "gate": "Cloudinary",
            "errors": [f"이미지 부족 ({len(cloudinary_urls)}/4)"]
        })

    # 게이트 4: 메타데이터
    metadata = get_metadata(content_id)
    gates["metadata"]["details"] = {"exists": metadata is not None}

    if metadata:
        gates["metadata"]["passed"] = True
    else:
        blocks.append({
            "gate": "메타데이터",
            "errors": ["metadata.json 없음"]
        })

    return {
        "can_approve": len(blocks) == 0,
        "blocks": blocks,
        "gates": gates
    }


def check_approval_gate(content_id: str) -> None:
    """단일 콘텐츠 승인 게이트 확인"""
    result = can_approve(content_id)

    print(f"\n{'=' * 60}")
    print(f"🚦 승인 게이트 검사: {content_id}")
    print(f"{'=' * 60}")

    # 각 게이트 상태
    gates = result['gates']
    gate_names = {
        'p_caption': 'P열 캡션 (Instagram)',
        'q_caption': 'Q열 캡션 (Threads)',
        'cloudinary': 'Cloudinary 이미지',
        'metadata': '메타데이터'
    }

    for key, name in gate_names.items():
        gate = gates[key]
        status = "✅" if gate['passed'] else "❌"
        print(f"\n{status} {name}")

        if gate['details']:
            if key == 'p_caption' and not gate['passed']:
                for err in gate['details'].get('errors', []):
                    print(f"   - {err}")
            elif key == 'q_caption' and not gate['passed']:
                for err in gate['details'].get('errors', []):
                    print(f"   - {err}")
            elif key == 'cloudinary':
                print(f"   이미지 수: {gate['details'].get('count', 0)}")
            elif key == 'metadata':
                print(f"   존재: {gate['details'].get('exists', False)}")

    # 최종 판정
    print(f"\n{'=' * 60}")
    if result['can_approve']:
        print("✅ 승인 가능 (모든 게이트 통과)")
    else:
        print("❌ 승인 불가")
        print(f"   차단 게이트: {len(result['blocks'])}개")
        for block in result['blocks']:
            print(f"   - {block['gate']}: {block['errors'][0]}")


def scan_pending() -> None:
    """body_ready 상태 콘텐츠 승인 가능 여부 스캔"""
    data = get_sheet_data()

    print(f"\n{'=' * 60}")
    print("🔍 승인 대기 콘텐츠 스캔")
    print(f"{'=' * 60}")

    can_approve_list = []
    blocked_list = []

    for item in data:
        if item['status'].lower() != 'body_ready':
            continue

        result = can_approve(item['num'])

        if result['can_approve']:
            can_approve_list.append(item)
            print(f"✅ [{item['num']}] {item['eng_name']} - 승인 가능")
        else:
            blocked_list.append({
                'item': item,
                'blocks': result['blocks']
            })
            block_summary = ', '.join([b['gate'] for b in result['blocks']])
            print(f"❌ [{item['num']}] {item['eng_name']} - 차단: {block_summary}")

    print(f"\n{'=' * 60}")
    print(f"📊 요약")
    print(f"   승인 가능: {len(can_approve_list)}건")
    print(f"   차단: {len(blocked_list)}건")


def main():
    parser = argparse.ArgumentParser(description="승인 게이트 검증기")
    parser.add_argument("--check", type=str, help="단일 콘텐츠 게이트 확인")
    parser.add_argument("--scan-pending", action="store_true", help="body_ready 전체 스캔")

    args = parser.parse_args()

    if args.check:
        check_approval_gate(args.check)
    elif args.scan_pending:
        scan_pending()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
