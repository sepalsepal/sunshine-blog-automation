#!/usr/bin/env python3
"""
API 사용량 추적 및 비용 분석 모듈
- fal.ai (FLUX 2.0 Pro)
- Instagram Graph API
- Cloudinary
- Claude API (Anthropic)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os

# 데이터 파일 경로
ROOT = Path(__file__).parent.parent.parent
USAGE_FILE = ROOT / "config" / "data" / "api_usage.json"
USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)


# ============================================
# API 가격 정보 (2026년 1월 기준)
# ============================================

API_PRICING = {
    "fal_ai": {
        "name": "fal.ai",
        "model": "FLUX 2.0 Pro",
        "model_id": "fal-ai/flux-2-pro",
        "unit": "image",
        "price_per_unit": 0.05,  # $0.05 per image (1024x1024)
        "currency": "USD",
        "description": "AI 이미지 생성",
        "docs_url": "https://fal.ai/models/fal-ai/flux-2-pro",
        "tier": "Pro",
    },
    "cloudinary": {
        "name": "Cloudinary",
        "model": "Media Management",
        "model_id": "cloudinary-api",
        "unit": "transformation + storage",
        "price_per_unit": 0.0,  # Free tier: 25GB storage, 25GB bandwidth
        "currency": "USD",
        "description": "이미지 호스팅 및 CDN",
        "docs_url": "https://cloudinary.com/pricing",
        "tier": "Free",
        "free_limits": {
            "storage_gb": 25,
            "bandwidth_gb": 25,
            "transformations": 25000,
        }
    },
    "instagram": {
        "name": "Instagram Graph API",
        "model": "Business/Creator API",
        "model_id": "instagram-graph-api",
        "unit": "request",
        "price_per_unit": 0.0,  # Free
        "currency": "USD",
        "description": "Instagram 게시 자동화",
        "docs_url": "https://developers.facebook.com/docs/instagram-api",
        "tier": "Free",
        "rate_limits": {
            "posts_per_day": 25,
            "api_calls_per_hour": 200,
        }
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "model": "Claude 3.5 Sonnet",
        "model_id": "claude-3-5-sonnet-20241022",
        "unit": "1M tokens",
        "price_input": 3.00,   # $3.00 per 1M input tokens
        "price_output": 15.00, # $15.00 per 1M output tokens
        "currency": "USD",
        "description": "텍스트 생성 및 분석",
        "docs_url": "https://www.anthropic.com/pricing",
        "tier": "API",
    },
}


@dataclass
class APIUsageRecord:
    """API 사용 기록"""
    timestamp: str
    api_name: str
    operation: str
    count: int = 1
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class APIUsageTracker:
    """API 사용량 추적 클래스"""

    def __init__(self):
        self.usage_file = USAGE_FILE
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """데이터 로드"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "records": [],
            "daily_summary": {},
            "monthly_summary": {},
            "total_cost": 0.0,
            "last_updated": None
        }

    def _save_data(self):
        """데이터 저장"""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.usage_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def log_usage(self,
                  api_name: str,
                  operation: str,
                  count: int = 1,
                  tokens_input: int = 0,
                  tokens_output: int = 0,
                  metadata: Dict = None):
        """API 사용 기록"""
        now = datetime.now()

        # 비용 계산
        cost = self._calculate_cost(api_name, count, tokens_input, tokens_output)

        # 기록 생성
        record = APIUsageRecord(
            timestamp=now.isoformat(),
            api_name=api_name,
            operation=operation,
            count=count,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost,
            metadata=metadata or {}
        )

        # 저장
        self.data["records"].append(asdict(record))
        self.data["total_cost"] += cost

        # 일별 요약 업데이트
        date_key = now.strftime("%Y-%m-%d")
        if date_key not in self.data["daily_summary"]:
            self.data["daily_summary"][date_key] = {}

        if api_name not in self.data["daily_summary"][date_key]:
            self.data["daily_summary"][date_key][api_name] = {
                "count": 0,
                "cost": 0.0,
                "tokens_input": 0,
                "tokens_output": 0
            }

        summary = self.data["daily_summary"][date_key][api_name]
        summary["count"] += count
        summary["cost"] += cost
        summary["tokens_input"] += tokens_input
        summary["tokens_output"] += tokens_output

        # 월별 요약 업데이트
        month_key = now.strftime("%Y-%m")
        if month_key not in self.data["monthly_summary"]:
            self.data["monthly_summary"][month_key] = {}

        if api_name not in self.data["monthly_summary"][month_key]:
            self.data["monthly_summary"][month_key][api_name] = {
                "count": 0,
                "cost": 0.0,
                "tokens_input": 0,
                "tokens_output": 0
            }

        month_summary = self.data["monthly_summary"][month_key][api_name]
        month_summary["count"] += count
        month_summary["cost"] += cost
        month_summary["tokens_input"] += tokens_input
        month_summary["tokens_output"] += tokens_output

        self._save_data()
        return record

    def _calculate_cost(self, api_name: str, count: int,
                       tokens_input: int, tokens_output: int) -> float:
        """비용 계산"""
        pricing = API_PRICING.get(api_name, {})

        if api_name == "fal_ai":
            return count * pricing.get("price_per_unit", 0.05)

        elif api_name == "anthropic":
            input_cost = (tokens_input / 1_000_000) * pricing.get("price_input", 3.0)
            output_cost = (tokens_output / 1_000_000) * pricing.get("price_output", 15.0)
            return input_cost + output_cost

        elif api_name in ["cloudinary", "instagram"]:
            return 0.0  # Free tier

        return 0.0

    def get_today_summary(self) -> Dict:
        """오늘 사용량 요약"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data["daily_summary"].get(today, {})

    def get_month_summary(self) -> Dict:
        """이번 달 사용량 요약"""
        month = datetime.now().strftime("%Y-%m")
        return self.data["monthly_summary"].get(month, {})

    def get_total_cost(self) -> float:
        """총 누적 비용"""
        return self.data.get("total_cost", 0.0)

    def get_api_stats(self) -> Dict:
        """API별 통계"""
        stats = {}
        for api_name, pricing in API_PRICING.items():
            month_data = self.get_month_summary().get(api_name, {})
            total_count = sum(
                d.get(api_name, {}).get("count", 0)
                for d in self.data["daily_summary"].values()
            )
            total_cost = sum(
                d.get(api_name, {}).get("cost", 0.0)
                for d in self.data["daily_summary"].values()
            )

            stats[api_name] = {
                "name": pricing["name"],
                "model": pricing["model"],
                "tier": pricing.get("tier", "Unknown"),
                "month_count": month_data.get("count", 0),
                "month_cost": month_data.get("cost", 0.0),
                "total_count": total_count,
                "total_cost": total_cost,
                "pricing": pricing,
            }

        return stats

    def get_cost_projection(self, days: int = 30) -> Dict:
        """비용 예측"""
        # 최근 7일 평균 계산
        recent_days = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.data["daily_summary"].get(date, {})
            daily_cost = sum(v.get("cost", 0.0) for v in daily.values())
            recent_days.append(daily_cost)

        avg_daily = sum(recent_days) / len(recent_days) if recent_days else 0

        return {
            "avg_daily_cost": avg_daily,
            "projected_monthly": avg_daily * 30,
            "projected_days": avg_daily * days,
        }

    def export_report(self) -> Dict:
        """분석 리포트 생성"""
        stats = self.get_api_stats()
        projection = self.get_cost_projection()

        return {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": min(self.data["daily_summary"].keys()) if self.data["daily_summary"] else None,
                "end": max(self.data["daily_summary"].keys()) if self.data["daily_summary"] else None,
            },
            "summary": {
                "total_cost_usd": self.get_total_cost(),
                "month_cost_usd": sum(
                    s.get("month_cost", 0.0) for s in stats.values()
                ),
                "today_cost_usd": sum(
                    v.get("cost", 0.0) for v in self.get_today_summary().values()
                ),
            },
            "by_api": stats,
            "projection": projection,
            "cost_breakdown": self._get_cost_breakdown(),
        }

    def _get_cost_breakdown(self) -> List[Dict]:
        """비용 구성 분석"""
        stats = self.get_api_stats()
        total = sum(s.get("total_cost", 0.0) for s in stats.values())

        breakdown = []
        for api_name, data in stats.items():
            cost = data.get("total_cost", 0.0)
            percentage = (cost / total * 100) if total > 0 else 0
            breakdown.append({
                "api": data["name"],
                "cost_usd": cost,
                "percentage": round(percentage, 1),
                "count": data.get("total_count", 0),
            })

        return sorted(breakdown, key=lambda x: x["cost_usd"], reverse=True)


# 싱글톤 인스턴스
_tracker = None

def get_tracker() -> APIUsageTracker:
    """트래커 인스턴스 반환"""
    global _tracker
    if _tracker is None:
        _tracker = APIUsageTracker()
    return _tracker


# 편의 함수
def log_fal_usage(count: int = 1, topic: str = None):
    """fal.ai 사용 기록"""
    tracker = get_tracker()
    tracker.log_usage(
        api_name="fal_ai",
        operation="image_generation",
        count=count,
        metadata={"topic": topic} if topic else None
    )

def log_cloudinary_usage(count: int = 1, operation: str = "upload"):
    """Cloudinary 사용 기록"""
    tracker = get_tracker()
    tracker.log_usage(
        api_name="cloudinary",
        operation=operation,
        count=count
    )

def log_instagram_usage(operation: str = "post"):
    """Instagram 사용 기록"""
    tracker = get_tracker()
    tracker.log_usage(
        api_name="instagram",
        operation=operation,
        count=1
    )

def log_claude_usage(tokens_input: int, tokens_output: int, operation: str = "chat"):
    """Claude API 사용 기록"""
    tracker = get_tracker()
    tracker.log_usage(
        api_name="anthropic",
        operation=operation,
        tokens_input=tokens_input,
        tokens_output=tokens_output
    )


if __name__ == "__main__":
    # 테스트
    tracker = get_tracker()

    # 샘플 데이터 생성
    log_fal_usage(3, "strawberry")
    log_fal_usage(3, "mango")
    log_cloudinary_usage(7, "upload")
    log_instagram_usage("carousel_post")

    # 리포트 출력
    report = tracker.export_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
