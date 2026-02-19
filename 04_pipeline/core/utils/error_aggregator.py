"""
SunFlow Error Aggregator (P2)
- 에러 수집 및 분류
- 일일/주간 요약 리포트
- 패턴 감지 및 알림
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent


class ErrorSeverity(Enum):
    """에러 심각도"""
    CRITICAL = "critical"   # 서비스 중단
    ERROR = "error"         # 기능 실패
    WARNING = "warning"     # 잠재적 문제
    INFO = "info"           # 정보성


class ErrorCategory(Enum):
    """에러 카테고리"""
    API = "api"                 # 외부 API 오류
    NETWORK = "network"         # 네트워크 오류
    AUTH = "auth"               # 인증 오류
    VALIDATION = "validation"   # 검증 오류
    SYSTEM = "system"           # 시스템 오류
    UNKNOWN = "unknown"         # 미분류


@dataclass
class ErrorRecord:
    """에러 기록"""
    error_id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    source: str                 # 발생 위치
    trace_id: Optional[str]     # 연관 Trace ID
    context: Dict               # 추가 컨텍스트
    fingerprint: str            # 에러 고유 식별자


class ErrorAggregator:
    """에러 집계자"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.error_dir = self.project_root / "config" / "logs" / "errors"
        self.error_dir.mkdir(parents=True, exist_ok=True)
        self.today_file = self.error_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.json"
        self._load_today_errors()

    def _load_today_errors(self):
        """오늘 에러 로드"""
        if self.today_file.exists():
            with open(self.today_file, 'r', encoding='utf-8') as f:
                self.errors = json.load(f)
        else:
            self.errors = {"date": datetime.now().strftime('%Y-%m-%d'), "records": []}

    def _save_errors(self):
        """에러 저장"""
        with open(self.today_file, 'w', encoding='utf-8') as f:
            json.dump(self.errors, f, ensure_ascii=False, indent=2)

    def _generate_fingerprint(self, message: str, source: str, category: str) -> str:
        """에러 핑거프린트 생성 (동일 에러 식별)"""
        content = f"{source}:{category}:{message[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _categorize_error(self, message: str, source: str) -> Tuple[ErrorCategory, ErrorSeverity]:
        """에러 자동 분류"""
        message_lower = message.lower()

        # API 관련
        if any(kw in message_lower for kw in ["api", "request", "response", "http", "status"]):
            if "401" in message or "403" in message or "unauthorized" in message_lower:
                return ErrorCategory.AUTH, ErrorSeverity.CRITICAL
            if "429" in message or "rate limit" in message_lower:
                return ErrorCategory.API, ErrorSeverity.WARNING
            if "500" in message or "502" in message or "503" in message:
                return ErrorCategory.API, ErrorSeverity.ERROR
            return ErrorCategory.API, ErrorSeverity.ERROR

        # 네트워크 관련
        if any(kw in message_lower for kw in ["timeout", "connection", "network", "socket"]):
            return ErrorCategory.NETWORK, ErrorSeverity.ERROR

        # 인증 관련
        if any(kw in message_lower for kw in ["token", "auth", "credential", "expired"]):
            return ErrorCategory.AUTH, ErrorSeverity.CRITICAL

        # 검증 관련
        if any(kw in message_lower for kw in ["valid", "invalid", "missing", "required"]):
            return ErrorCategory.VALIDATION, ErrorSeverity.WARNING

        # 시스템 관련
        if any(kw in message_lower for kw in ["memory", "disk", "file", "permission"]):
            return ErrorCategory.SYSTEM, ErrorSeverity.ERROR

        return ErrorCategory.UNKNOWN, ErrorSeverity.ERROR

    def record_error(
        self,
        message: str,
        source: str,
        severity: ErrorSeverity = None,
        category: ErrorCategory = None,
        trace_id: str = None,
        context: Dict = None
    ) -> ErrorRecord:
        """에러 기록"""
        # 자동 분류
        if category is None or severity is None:
            auto_category, auto_severity = self._categorize_error(message, source)
            category = category or auto_category
            severity = severity or auto_severity

        # 핑거프린트 생성
        fingerprint = self._generate_fingerprint(message, source, category.value)

        # 에러 ID
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{fingerprint[:6]}"

        record = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            message=message,
            source=source,
            trace_id=trace_id,
            context=context or {},
            fingerprint=fingerprint
        )

        # 저장
        self.errors["records"].append({
            "error_id": error_id,
            "timestamp": record.timestamp,
            "severity": severity.value,
            "category": category.value,
            "message": message,
            "source": source,
            "trace_id": trace_id,
            "context": context or {},
            "fingerprint": fingerprint
        })
        self._save_errors()

        return record

    def get_daily_summary(self, date: str = None) -> Dict:
        """일일 요약"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # 해당 날짜 파일 로드
        date_file = self.error_dir / f"errors_{date.replace('-', '')}.json"
        if not date_file.exists():
            return {"date": date, "total": 0, "by_severity": {}, "by_category": {}}

        with open(date_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        records = data.get("records", [])

        # 심각도별 집계
        by_severity = defaultdict(int)
        for r in records:
            by_severity[r["severity"]] += 1

        # 카테고리별 집계
        by_category = defaultdict(int)
        for r in records:
            by_category[r["category"]] += 1

        # 핑거프린트별 집계 (동일 에러 그룹화)
        by_fingerprint = defaultdict(list)
        for r in records:
            by_fingerprint[r["fingerprint"]].append(r)

        # 상위 반복 에러
        top_errors = sorted(
            [(fp, len(errors), errors[0]["message"][:50]) for fp, errors in by_fingerprint.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "date": date,
            "total": len(records),
            "by_severity": dict(by_severity),
            "by_category": dict(by_category),
            "unique_errors": len(by_fingerprint),
            "top_errors": [{"fingerprint": fp, "count": cnt, "message": msg} for fp, cnt, msg in top_errors]
        }

    def get_weekly_summary(self) -> Dict:
        """주간 요약"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())

        daily_summaries = []
        for i in range(7):
            date = (week_start + timedelta(days=i)).strftime('%Y-%m-%d')
            daily_summaries.append(self.get_daily_summary(date))

        total_errors = sum(d["total"] for d in daily_summaries)
        all_severities = defaultdict(int)
        all_categories = defaultdict(int)

        for d in daily_summaries:
            for sev, cnt in d.get("by_severity", {}).items():
                all_severities[sev] += cnt
            for cat, cnt in d.get("by_category", {}).items():
                all_categories[cat] += cnt

        return {
            "week_start": week_start.strftime('%Y-%m-%d'),
            "week_end": (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
            "total_errors": total_errors,
            "daily_average": total_errors / 7,
            "by_severity": dict(all_severities),
            "by_category": dict(all_categories),
            "daily_breakdown": [{"date": d["date"], "count": d["total"]} for d in daily_summaries]
        }

    def get_recent_critical(self, hours: int = 24) -> List[Dict]:
        """최근 심각 에러"""
        cutoff = datetime.now() - timedelta(hours=hours)

        critical_errors = []
        for record in self.errors.get("records", []):
            if record["severity"] in ["critical", "error"]:
                record_time = datetime.fromisoformat(record["timestamp"])
                if record_time >= cutoff:
                    critical_errors.append(record)

        return sorted(critical_errors, key=lambda x: x["timestamp"], reverse=True)

    def should_alert(self) -> Tuple[bool, Optional[str]]:
        """알림 필요 여부 판단"""
        recent = self.get_recent_critical(hours=1)

        # 최근 1시간 내 심각 에러 3개 이상
        critical_count = len([r for r in recent if r["severity"] == "critical"])
        if critical_count >= 3:
            return True, f"최근 1시간 내 {critical_count}개의 CRITICAL 에러 발생"

        # 동일 에러 5회 이상 반복
        fingerprints = defaultdict(int)
        for r in recent:
            fingerprints[r["fingerprint"]] += 1

        for fp, count in fingerprints.items():
            if count >= 5:
                error = next(r for r in recent if r["fingerprint"] == fp)
                return True, f"동일 에러 {count}회 반복: {error['message'][:50]}"

        return False, None


# 편의 함수
def log_error(message: str, source: str, **kwargs) -> str:
    """에러 로깅"""
    aggregator = ErrorAggregator()
    record = aggregator.record_error(message, source, **kwargs)
    return record.error_id


def get_error_summary() -> Dict:
    """에러 요약"""
    aggregator = ErrorAggregator()
    return aggregator.get_daily_summary()


# CLI 실행
if __name__ == "__main__":
    import sys

    aggregator = ErrorAggregator()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "daily":
            date = sys.argv[2] if len(sys.argv) > 2 else None
            summary = aggregator.get_daily_summary(date)
            print("\n=== 일일 에러 요약 ===\n")
            print(f"  날짜: {summary['date']}")
            print(f"  총 에러: {summary['total']}")
            print(f"  고유 에러: {summary.get('unique_errors', 0)}")
            print("\n  심각도별:")
            for sev, cnt in summary.get('by_severity', {}).items():
                print(f"    - {sev}: {cnt}")
            print("\n  카테고리별:")
            for cat, cnt in summary.get('by_category', {}).items():
                print(f"    - {cat}: {cnt}")
            if summary.get('top_errors'):
                print("\n  상위 반복 에러:")
                for e in summary['top_errors']:
                    print(f"    - [{e['count']}회] {e['message']}")

        elif cmd == "weekly":
            summary = aggregator.get_weekly_summary()
            print("\n=== 주간 에러 요약 ===\n")
            print(f"  기간: {summary['week_start']} ~ {summary['week_end']}")
            print(f"  총 에러: {summary['total_errors']}")
            print(f"  일평균: {summary['daily_average']:.1f}")
            print("\n  일별:")
            for d in summary['daily_breakdown']:
                bar = "█" * min(d['count'], 20)
                print(f"    {d['date']}: {bar} ({d['count']})")

        elif cmd == "critical":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            errors = aggregator.get_recent_critical(hours)
            print(f"\n=== 최근 {hours}시간 심각 에러 ===\n")
            for e in errors[:10]:
                print(f"  [{e['severity']}] {e['timestamp'][:19]} | {e['message'][:50]}")

        elif cmd == "test":
            # 테스트 에러 생성
            aggregator.record_error("Test API timeout error", "test_source", context={"test": True})
            aggregator.record_error("401 Unauthorized", "instagram_api")
            aggregator.record_error("Connection refused", "cloudinary")
            print("\n✅ 테스트 에러 3개 생성")

        elif cmd == "alert":
            should_alert, reason = aggregator.should_alert()
            if should_alert:
                print(f"\n🚨 알림 필요: {reason}")
            else:
                print("\n✅ 알림 불필요")

        else:
            print("Usage: python error_aggregator.py [daily [date]|weekly|critical [hours]|test|alert]")
    else:
        summary = aggregator.get_daily_summary()
        print(f"\n오늘 에러: {summary['total']}건")
