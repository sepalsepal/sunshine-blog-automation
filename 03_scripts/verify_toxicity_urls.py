#!/usr/bin/env python3
"""
verify_toxicity_urls.py - 독성 매핑 테이블 URL 검증
WO-OVERNIGHT Task 1 URL Verification

검증 규칙:
- HTTP 200 응답 필요
- 3회 재시도 (간격 2초, 타임아웃 5초)
- 리다이렉트 추적 (최대 5회)
- FAIL 시 PD_MANUAL_CHECK.json에 추가
"""

import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import urllib.request
import urllib.error
import ssl

PROJECT_ROOT = Path(__file__).parent.parent
TOXICITY_PATH = PROJECT_ROOT / "config" / "toxicity_mapping.json"
LOGS_DIR = PROJECT_ROOT / "logs" / "overnight" / "20260212"
PD_CHECK_DIR = PROJECT_ROOT / "박PD_확인용"

# 검증 설정
MAX_RETRIES = 3
RETRY_DELAY = 2
TIMEOUT = 5
MAX_REDIRECTS = 5


def verify_url(url: str) -> Tuple[bool, str, int]:
    """
    URL 검증

    Returns:
        (성공여부, 상태메시지, HTTP코드)
    """
    for attempt in range(MAX_RETRIES):
        try:
            # SSL 컨텍스트 (인증서 검증 완화)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; ProjectSunshine/1.0)'}
            )

            response = urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx)
            code = response.getcode()

            if code == 200:
                return True, "OK", code
            else:
                return False, f"Unexpected status: {code}", code

        except urllib.error.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return False, f"HTTPError: {e.code}", e.code

        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return False, f"URLError: {str(e.reason)[:50]}", 0

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return False, f"Error: {str(e)[:50]}", 0

    return False, "Max retries exceeded", 0


def validate_sources(category: Dict) -> List[Dict]:
    """
    출처 유효성 검증

    Rules:
    - sources 필드 필수
    - type: blog 단독 FAIL
    - academic/vet_org/gov 중 최소 1개 필수
    """
    errors = []
    sources = category.get("sources", [])

    if not sources:
        errors.append({
            "error": "NO_SOURCES",
            "message": "sources 필드 없음"
        })
        return errors

    types = [s.get("type") for s in sources]

    # blog 단독 체크
    if types == ["blog"]:
        errors.append({
            "error": "BLOG_ONLY",
            "message": "type: blog 단독 - 신뢰할 수 있는 출처 필요"
        })

    # 신뢰할 수 있는 출처 확인
    trusted_types = {"academic", "vet_org", "gov"}
    has_trusted = any(t in trusted_types for t in types)

    if not has_trusted:
        errors.append({
            "error": "NO_TRUSTED_SOURCE",
            "message": "academic/vet_org/gov 중 최소 1개 필요"
        })

    return errors


def run_verification():
    """URL 검증 실행"""
    print("=" * 60)
    print("독성 매핑 테이블 URL 검증")
    print("=" * 60)

    # 로그 디렉토리 생성
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    with open(TOXICITY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("toxicity_categories", {})

    results = {
        "verified_at": datetime.now().isoformat(),
        "total_urls": 0,
        "pass_count": 0,
        "fail_count": 0,
        "details": [],
        "manual_check_required": []
    }

    # 각 카테고리 검증
    for cat_name, cat_data in categories.items():
        print(f"\n[{cat_name}] {cat_data.get('name_ko', '')}")

        # 출처 유효성 검증
        source_errors = validate_sources(cat_data)
        if source_errors:
            for err in source_errors:
                print(f"  ⚠️ {err['message']}")
                results["manual_check_required"].append({
                    "category": cat_name,
                    "error": err["error"],
                    "message": err["message"]
                })

        # URL 검증
        sources = cat_data.get("sources", [])
        for source in sources:
            url = source.get("url", "")
            source_name = source.get("name", "Unknown")
            source_type = source.get("type", "unknown")

            results["total_urls"] += 1

            print(f"  검증: {source_name[:30]}... ", end="", flush=True)

            success, message, code = verify_url(url)

            if success:
                print(f"✅ PASS ({code})")
                results["pass_count"] += 1
                source["verified"] = True
            else:
                print(f"❌ FAIL ({message})")
                results["fail_count"] += 1
                source["verified"] = False
                results["manual_check_required"].append({
                    "category": cat_name,
                    "url": url,
                    "name": source_name,
                    "type": source_type,
                    "error": message,
                    "code": code
                })

            results["details"].append({
                "category": cat_name,
                "url": url,
                "name": source_name,
                "type": source_type,
                "success": success,
                "message": message,
                "code": code
            })

    # 메타데이터 업데이트
    data["_metadata"]["source_verification"] = {
        "verified_at": results["verified_at"],
        "total_urls": results["total_urls"],
        "pass_count": results["pass_count"],
        "fail_count": results["fail_count"],
        "pending_manual_check": [
            item["url"] for item in results["manual_check_required"]
            if "url" in item
        ]
    }

    # 업데이트된 데이터 저장
    with open(TOXICITY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 검증 로그 저장
    log_path = LOGS_DIR / "url_verification.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("URL Verification Log\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Timestamp: {results['verified_at']}\n")
        f.write(f"Total URLs: {results['total_urls']}\n")
        f.write(f"PASS: {results['pass_count']}\n")
        f.write(f"FAIL: {results['fail_count']}\n\n")

        f.write("[DETAILS]\n")
        for detail in results["details"]:
            status = "PASS" if detail["success"] else "FAIL"
            f.write(f"{status}: [{detail['category']}] {detail['name']}\n")
            f.write(f"       URL: {detail['url']}\n")
            f.write(f"       {detail['message']}\n\n")

    # PD 수동 확인 필요 항목 저장
    if results["manual_check_required"]:
        PD_CHECK_DIR.mkdir(parents=True, exist_ok=True)
        manual_check_path = PD_CHECK_DIR / "PD_MANUAL_CHECK.json"
        with open(manual_check_path, "w", encoding="utf-8") as f:
            json.dump({
                "created_at": results["verified_at"],
                "total_items": len(results["manual_check_required"]),
                "items": results["manual_check_required"]
            }, f, ensure_ascii=False, indent=2)
        print(f"\n⚠️ PD 수동 확인 필요: {manual_check_path}")

    # 요약
    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)
    print(f"총 URL: {results['total_urls']}")
    print(f"PASS: {results['pass_count']}")
    print(f"FAIL: {results['fail_count']}")
    print(f"수동 확인 필요: {len(results['manual_check_required'])}건")
    print(f"\n로그: {log_path}")

    return results


if __name__ == "__main__":
    run_verification()
