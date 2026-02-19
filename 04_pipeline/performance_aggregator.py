#!/usr/bin/env python3
"""
performance_aggregator.py - 성과 데이터 집계 모듈
WO-PERFORMANCE-LOOP

책임:
- Intent/Safety/Platform별 성과 집계
- 평균/최고/최저 성과 계산
- 일간/주간 요약 생성
- 최적 Intent 추천 데이터 제공
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent


class PerformanceAggregator:
    """
    성과 데이터 집계 및 분석

    기능:
    - Intent/Safety/Platform별 평균 성과
    - 시계열 요약 (일간/주간)
    - 최적 조합 분석
    """

    def __init__(self):
        self.log_root = PROJECT_ROOT / "logs" / "performance"
        self.aggregated_path = self.log_root / "aggregated"
        self.aggregated_path.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Intent별 집계
    # =========================================================================

    def aggregate_by_intent(self) -> Dict:
        """
        Intent별 평균 성과 집계

        Returns:
            {
                "TRUST": {"avg_save_rate": 3.5, "avg_engagement": 5.2, "count": 15},
                "AUTHORITY": {...},
                ...
            }
        """
        intents = ["TRUST", "AUTHORITY", "ENGAGEMENT", "SAVE", "CTA"]
        result = {}

        for intent in intents:
            records = self._load_records_by_intent(intent)

            if not records:
                result[intent] = {
                    "avg_save_rate": 0.0,
                    "avg_engagement_rate": 0.0,
                    "avg_CTR": 0.0,
                    "count": 0
                }
                continue

            save_rates = [
                r.get("calculated", {}).get("save_rate", 0)
                for r in records
            ]
            engagement_rates = [
                r.get("calculated", {}).get("engagement_rate", 0)
                for r in records
            ]
            ctrs = [
                r.get("calculated", {}).get("CTR", 0)
                for r in records
            ]

            result[intent] = {
                "avg_save_rate": round(sum(save_rates) / len(save_rates), 2) if save_rates else 0.0,
                "avg_engagement_rate": round(sum(engagement_rates) / len(engagement_rates), 2) if engagement_rates else 0.0,
                "avg_CTR": round(sum(ctrs) / len(ctrs), 2) if ctrs else 0.0,
                "count": len(records)
            }

        return result

    # =========================================================================
    # Safety별 집계
    # =========================================================================

    def aggregate_by_safety(self) -> Dict:
        """
        Safety별 평균 성과 집계

        Returns:
            {
                "SAFE": {"avg_save_rate": 2.1, "count": 20},
                "CAUTION": {...},
                "FORBIDDEN": {...}
            }
        """
        safeties = ["SAFE", "CAUTION", "FORBIDDEN"]
        result = {}

        for safety in safeties:
            records = self._load_records_by_safety(safety)

            if not records:
                result[safety] = {
                    "avg_save_rate": 0.0,
                    "avg_engagement_rate": 0.0,
                    "count": 0
                }
                continue

            save_rates = [
                r.get("calculated", {}).get("save_rate", 0)
                for r in records
            ]
            engagement_rates = [
                r.get("calculated", {}).get("engagement_rate", 0)
                for r in records
            ]

            result[safety] = {
                "avg_save_rate": round(sum(save_rates) / len(save_rates), 2) if save_rates else 0.0,
                "avg_engagement_rate": round(sum(engagement_rates) / len(engagement_rates), 2) if engagement_rates else 0.0,
                "count": len(records)
            }

        return result

    # =========================================================================
    # Platform별 집계
    # =========================================================================

    def aggregate_by_platform(self) -> Dict:
        """
        플랫폼별 평균 성과 집계

        Returns:
            {
                "blog": {"avg_time_on_page": 145, "count": 10},
                "insta": {"avg_save_rate": 3.2, "count": 25},
                "thread": {"avg_replies": 12, "count": 8}
            }
        """
        platforms = ["blog", "insta", "thread"]
        result = {}

        for platform in platforms:
            records = self._load_records_by_platform(platform)

            if not records:
                result[platform] = self._empty_platform_stats(platform)
                continue

            if platform == "blog":
                times = [
                    r.get("metrics", {}).get("avg_time_on_page", 0)
                    for r in records
                ]
                result[platform] = {
                    "avg_time_on_page": round(sum(times) / len(times), 1) if times else 0,
                    "count": len(records)
                }

            elif platform == "insta":
                save_rates = [
                    r.get("calculated", {}).get("save_rate", 0)
                    for r in records
                ]
                result[platform] = {
                    "avg_save_rate": round(sum(save_rates) / len(save_rates), 2) if save_rates else 0.0,
                    "count": len(records)
                }

            elif platform == "thread":
                replies = [
                    r.get("metrics", {}).get("replies", 0)
                    for r in records
                ]
                result[platform] = {
                    "avg_replies": round(sum(replies) / len(replies), 1) if replies else 0,
                    "count": len(records)
                }

        return result

    # =========================================================================
    # 조합별 집계
    # =========================================================================

    def aggregate_by_combination(
        self,
        safety: str,
        platform: str
    ) -> Dict:
        """
        Safety + Platform 조합에서 Intent별 성과

        Args:
            safety: SAFE/CAUTION/FORBIDDEN
            platform: blog/insta/thread

        Returns:
            {
                "TRUST": {"avg_save_rate": 4.2, "count": 5},
                "AUTHORITY": {"avg_save_rate": 2.8, "count": 3},
                ...
            }
        """
        records = self._load_records_by_safety(safety)

        # 플랫폼 필터링
        records = [r for r in records if r.get("platform") == platform.lower()]

        # Intent별 그룹화
        by_intent = defaultdict(list)
        for r in records:
            intent = r.get("strategy", {}).get("intent", "AUTHORITY")
            by_intent[intent].append(r)

        result = {}
        for intent, intent_records in by_intent.items():
            save_rates = [
                r.get("calculated", {}).get("save_rate", 0)
                for r in intent_records
            ]
            result[intent] = {
                "avg_save_rate": round(sum(save_rates) / len(save_rates), 2) if save_rates else 0.0,
                "count": len(intent_records)
            }

        return result

    def get_best_intent_for(
        self,
        safety: str,
        platform: str,
        min_samples: int = 5
    ) -> Optional[str]:
        """
        Safety + Platform 조합에서 최고 성과 Intent 반환

        Args:
            safety: Safety 등급
            platform: 플랫폼
            min_samples: 최소 샘플 수 (미만이면 None)

        Returns:
            최적 Intent 또는 None
        """
        combination_stats = self.aggregate_by_combination(safety, platform)

        # 최소 샘플 필터링
        valid_intents = {
            intent: stats
            for intent, stats in combination_stats.items()
            if stats.get("count", 0) >= min_samples
        }

        if not valid_intents:
            return None

        # 최고 save_rate Intent 선택
        best_intent = max(
            valid_intents,
            key=lambda x: valid_intents[x].get("avg_save_rate", 0)
        )

        return best_intent

    # =========================================================================
    # 시계열 요약
    # =========================================================================

    def generate_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """일간 요약 생성"""
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        summary = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "by_intent": self.aggregate_by_intent(),
            "by_safety": self.aggregate_by_safety(),
            "by_platform": self.aggregate_by_platform()
        }

        # 저장
        summary_file = self.aggregated_path / f"daily_{date_str}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary

    def generate_intent_performance_report(self) -> Dict:
        """Intent 성과 리포트 생성"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "by_intent": self.aggregate_by_intent(),
            "recommendations": {}
        }

        # 플랫폼별 최적 Intent 추천
        for platform in ["blog", "insta", "thread"]:
            report["recommendations"][platform] = {}
            for safety in ["SAFE", "CAUTION", "FORBIDDEN"]:
                best = self.get_best_intent_for(safety, platform, min_samples=3)
                report["recommendations"][platform][safety] = best

        # 저장
        report_file = self.aggregated_path / "intent_performance.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    # =========================================================================
    # 내부 메서드
    # =========================================================================

    def _load_records_by_intent(self, intent: str) -> List[Dict]:
        """Intent별 레코드 로드"""
        intent_path = self.log_root / "by_intent" / intent.upper()
        return self._load_records_from_path(intent_path)

    def _load_records_by_safety(self, safety: str) -> List[Dict]:
        """Safety별 레코드 로드"""
        safety_path = self.log_root / "by_safety" / safety.upper()
        return self._load_records_from_path(safety_path)

    def _load_records_by_platform(self, platform: str) -> List[Dict]:
        """플랫폼별 레코드 로드"""
        platform_path = self.log_root / "by_platform" / platform.lower()
        return self._load_records_from_path(platform_path)

    def _load_records_from_path(self, path: Path) -> List[Dict]:
        """경로에서 모든 레코드 로드"""
        records = []
        if not path.exists():
            return records

        for json_file in path.rglob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    records.append(json.load(f))
            except (json.JSONDecodeError, IOError):
                continue

        return records

    def _empty_platform_stats(self, platform: str) -> Dict:
        """빈 플랫폼 통계"""
        if platform == "blog":
            return {"avg_time_on_page": 0, "count": 0}
        elif platform == "insta":
            return {"avg_save_rate": 0.0, "count": 0}
        elif platform == "thread":
            return {"avg_replies": 0, "count": 0}
        return {"count": 0}
