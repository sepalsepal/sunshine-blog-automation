#!/usr/bin/env python3
"""
url_fail_handler.py - URL 검증 FAIL 처리 및 조건부 PASS 로직
RULES.md §22.14

조건부 PASS 요건:
1. 동일 카테고리 내 신뢰 출처 1개 이상 PASS
2. FAIL URL과 대체 URL의 정보 일치 확인
3. PD_MANUAL_CHECK.json에 기록
4. 30일 이내 URL 업데이트 의무
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent.parent

# 설정 파일 경로
TOXICITY_MAPPING_PATH = PROJECT_ROOT / "config" / "toxicity_mapping.json"
TOXICITY_KEYWORDS_PATH = PROJECT_ROOT / "config" / "toxicity_keywords.json"
PD_MANUAL_CHECK_PATH = PROJECT_ROOT / "박PD_확인용" / "PD_MANUAL_CHECK.json"


class FailCode(Enum):
    """URL 검증 FAIL 코드 (§22.14.1)"""
    HTTP_404 = "404"
    HTTP_403 = "403"
    HTTP_429 = "429"
    HTTP_5XX = "5xx"
    SSL_ERROR = "SSL"
    TIMEOUT = "Timeout"
    REDIRECT_LOOP = "Redirect Loop"


class SourceGrade(Enum):
    """출처 신뢰도 등급 (§22.16.1)"""
    S = "academic"
    A = "vet_org"
    B = "gov"
    C = "blog"


# 등급별 단독 허용 여부
STANDALONE_ALLOWED = {
    SourceGrade.S: True,
    SourceGrade.A: True,
    SourceGrade.B: True,
    SourceGrade.C: False,
}


@dataclass
class UrlVerificationResult:
    """URL 검증 결과"""
    url: str
    status: str  # PASS, FAIL_{code}
    fail_code: Optional[FailCode] = None
    source_type: Optional[str] = None
    source_grade: Optional[SourceGrade] = None


@dataclass
class ConditionalPassResult:
    """조건부 PASS 판정 결과"""
    category: str
    original_url: str
    original_status: str
    alternative_url: Optional[str]
    alternative_status: Optional[str]
    keyword_match: Dict[str, any]
    match_score: str  # "N/3"
    result: str  # INFO_MATCH_PASS, CONDITIONAL_FAIL
    verified_by: str
    timestamp: str
    expiry_date: str  # 30일 후


def load_json(path: Path) -> Dict:
    """JSON 파일 로드"""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict):
    """JSON 파일 저장"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_source_grade(source_type: str) -> Optional[SourceGrade]:
    """소스 타입에서 등급 추출"""
    type_map = {
        "academic": SourceGrade.S,
        "vet_org": SourceGrade.A,
        "gov": SourceGrade.B,
        "blog": SourceGrade.C,
    }
    return type_map.get(source_type)


def check_keyword_match(
    category: str,
    content_keywords: Dict[str, List[str]]
) -> Tuple[Dict[str, any], int, int]:
    """
    정보 일치 판정 (§22.14.3)

    Returns:
        (match_result, matched_count, total_count)
    """
    keywords = load_json(TOXICITY_KEYWORDS_PATH)
    if not keywords or "categories" not in keywords:
        return {}, 0, 3

    category_keywords = keywords["categories"].get(category, {})
    if not category_keywords:
        return {}, 0, 3

    match_result = {}
    matched_count = 0
    total_count = 3  # toxin_name, symptoms, severity

    # 1. toxin_name 일치 확인
    expected_toxins = category_keywords.get("toxin_name", [])
    provided_toxins = content_keywords.get("toxin_name", [])
    toxin_matches = [t for t in expected_toxins if t in provided_toxins]
    if toxin_matches:
        matched_count += 1
        match_result["toxin_name"] = toxin_matches

    # 2. symptoms 일치 확인
    expected_symptoms = category_keywords.get("symptoms", [])
    provided_symptoms = content_keywords.get("symptoms", [])
    symptom_matches = [s for s in expected_symptoms if s in provided_symptoms]
    if symptom_matches:
        matched_count += 1
        match_result["symptoms"] = symptom_matches

    # 3. severity 일치 확인
    expected_severity = category_keywords.get("severity", "")
    provided_severity = content_keywords.get("severity", "")
    if expected_severity == provided_severity:
        matched_count += 1
        match_result["severity"] = expected_severity

    return match_result, matched_count, total_count


def can_conditional_pass(
    category: str,
    failed_urls: List[UrlVerificationResult],
    passed_urls: List[UrlVerificationResult],
    content_keywords: Optional[Dict[str, List[str]]] = None
) -> ConditionalPassResult:
    """
    조건부 PASS 가능 여부 판정 (§22.14.2)

    조건:
    1. 동일 카테고리 내 신뢰 출처 1개 이상 PASS
    2. FAIL URL과 대체 URL의 정보 일치 확인
    3. 30일 이내 URL 업데이트 의무
    """
    now = datetime.now()

    # 조건 1: 신뢰 출처 PASS 확인
    trusted_pass = [
        url for url in passed_urls
        if url.source_grade and STANDALONE_ALLOWED.get(url.source_grade, False)
    ]

    if not trusted_pass:
        return ConditionalPassResult(
            category=category,
            original_url=failed_urls[0].url if failed_urls else "",
            original_status="FAIL",
            alternative_url=None,
            alternative_status=None,
            keyword_match={},
            match_score="0/3",
            result="CONDITIONAL_FAIL_NO_TRUSTED_SOURCE",
            verified_by="auto",
            timestamp=now.isoformat(),
            expiry_date=""
        )

    # 조건 2: 정보 일치 확인
    if content_keywords:
        match_result, matched, total = check_keyword_match(category, content_keywords)
        match_score = f"{matched}/{total}"

        # 2/3 미만이면 조건부 PASS 불가 (§22.14.4)
        if matched < 2:
            return ConditionalPassResult(
                category=category,
                original_url=failed_urls[0].url if failed_urls else "",
                original_status="FAIL",
                alternative_url=trusted_pass[0].url,
                alternative_status="PASS",
                keyword_match=match_result,
                match_score=match_score,
                result="CONDITIONAL_FAIL_INFO_MISMATCH",
                verified_by="auto",
                timestamp=now.isoformat(),
                expiry_date=""
            )
    else:
        match_result = {}
        match_score = "N/A"

    # 조건 충족 → 조건부 PASS
    from datetime import timedelta
    expiry_date = (now + timedelta(days=30)).strftime("%Y-%m-%d")

    return ConditionalPassResult(
        category=category,
        original_url=failed_urls[0].url if failed_urls else "",
        original_status="FAIL",
        alternative_url=trusted_pass[0].url,
        alternative_status="PASS",
        keyword_match=match_result,
        match_score=match_score,
        result="INFO_MATCH_PASS",
        verified_by="auto",
        timestamp=now.isoformat(),
        expiry_date=expiry_date
    )


def save_verification_log(result: ConditionalPassResult, date: Optional[str] = None):
    """검증 로그 저장"""
    if date is None:
        date = datetime.now().strftime("%Y%m%d")

    log_dir = PROJECT_ROOT / "logs" / "url_verification" / date
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{result.category}_match.json"

    log_data = {
        "category": result.category,
        "original_url": result.original_url,
        "original_status": result.original_status,
        "alternative_url": result.alternative_url,
        "alternative_status": result.alternative_status,
        "keyword_match": result.keyword_match,
        "match_score": result.match_score,
        "result": result.result,
        "verified_by": result.verified_by,
        "timestamp": result.timestamp,
        "expiry_date": result.expiry_date
    }

    save_json(log_file, log_data)
    return log_file


def add_to_pd_manual_check(
    url: str,
    fail_code: str,
    category: str,
    conditional_pass: bool = False,
    expiry_date: str = ""
):
    """PD_MANUAL_CHECK.json에 항목 추가"""
    check_data = load_json(PD_MANUAL_CHECK_PATH)

    if "items" not in check_data:
        check_data["items"] = []

    # 중복 확인
    existing = [item for item in check_data["items"] if item.get("url") == url]
    if existing:
        return  # 이미 존재

    check_data["items"].append({
        "url": url,
        "fail_code": fail_code,
        "category": category,
        "conditional_pass": conditional_pass,
        "expiry_date": expiry_date,
        "added_at": datetime.now().isoformat(),
        "resolved": False
    })

    check_data["updated_at"] = datetime.now().isoformat()
    save_json(PD_MANUAL_CHECK_PATH, check_data)


def process_url_failures(
    category: str,
    verification_results: List[UrlVerificationResult],
    content_keywords: Optional[Dict[str, List[str]]] = None
) -> Tuple[str, Optional[ConditionalPassResult]]:
    """
    카테고리별 URL FAIL 처리

    Returns:
        (status, conditional_pass_result)
        status: "ALL_PASS", "CONDITIONAL_PASS", "FAIL"
    """
    failed = [r for r in verification_results if r.status.startswith("FAIL")]
    passed = [r for r in verification_results if r.status == "PASS"]

    # 모두 PASS
    if not failed:
        return "ALL_PASS", None

    # 모두 FAIL (§22.14.4)
    if not passed:
        for f in failed:
            add_to_pd_manual_check(
                url=f.url,
                fail_code=f.fail_code.value if f.fail_code else "UNKNOWN",
                category=category,
                conditional_pass=False
            )
        return "FAIL", None

    # 조건부 PASS 시도
    result = can_conditional_pass(category, failed, passed, content_keywords)

    # 로그 저장
    save_verification_log(result)

    if result.result == "INFO_MATCH_PASS":
        # PD_MANUAL_CHECK에 조건부 PASS로 기록
        for f in failed:
            add_to_pd_manual_check(
                url=f.url,
                fail_code=f.fail_code.value if f.fail_code else "UNKNOWN",
                category=category,
                conditional_pass=True,
                expiry_date=result.expiry_date
            )
        return "CONDITIONAL_PASS", result
    else:
        # 조건부 PASS 실패
        for f in failed:
            add_to_pd_manual_check(
                url=f.url,
                fail_code=f.fail_code.value if f.fail_code else "UNKNOWN",
                category=category,
                conditional_pass=False
            )
        return "FAIL", result


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="URL FAIL 처리 (§22.14)")
    parser.add_argument("--category", required=True, help="독성 카테고리")
    parser.add_argument("--check-keywords", action="store_true", help="키워드 일치 확인")

    args = parser.parse_args()

    # 예시 실행
    print(f"Category: {args.category}")

    keywords = load_json(TOXICITY_KEYWORDS_PATH)
    if keywords and "categories" in keywords:
        cat_data = keywords["categories"].get(args.category, {})
        if cat_data:
            print(f"Keywords loaded:")
            print(f"  - toxin_name: {cat_data.get('toxin_name', [])}")
            print(f"  - symptoms: {cat_data.get('symptoms', [])}")
            print(f"  - severity: {cat_data.get('severity', '')}")
        else:
            print(f"Category '{args.category}' not found")
    else:
        print("toxicity_keywords.json not found")
