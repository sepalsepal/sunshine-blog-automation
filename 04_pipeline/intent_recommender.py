#!/usr/bin/env python3
"""
intent_recommender.py - 데이터 기반 Intent 추천 모듈
WO-PERFORMANCE-LOOP

책임:
- Safety + Platform 조합에서 최적 Intent 추천
- 데이터 부족 시 룰 기반 폴백
- 통계 기반 추천 (50건 이상)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent

from pipeline.performance_aggregator import PerformanceAggregator


class IntentRecommender:
    """
    데이터 기반 Intent 추천

    전략:
    - 50건 미만: 룰 기반 추천 (intent_safety_map.json)
    - 50건 이상: 통계 기반 추천 (최고 save_rate Intent)
    """

    MIN_SAMPLES_STATS = 50  # 통계 기반 전환 임계값
    MIN_SAMPLES_PARTIAL = 10  # 부분 통계 활용 임계값

    def __init__(self):
        self.aggregator = PerformanceAggregator()
        self.intent_safety_map_path = (
            PROJECT_ROOT / "config" / "templates" / "strategic" /
            "intent_safety_map.json"
        )
        self._intent_safety_map = None

    # =========================================================================
    # 설정 로더
    # =========================================================================

    @property
    def intent_safety_map(self) -> Dict:
        """intent_safety_map.json 로드"""
        if self._intent_safety_map is None:
            if self.intent_safety_map_path.exists():
                with open(self.intent_safety_map_path, "r", encoding="utf-8") as f:
                    self._intent_safety_map = json.load(f)
            else:
                self._intent_safety_map = {}
        return self._intent_safety_map

    # =========================================================================
    # 추천 API
    # =========================================================================

    def recommend(
        self,
        safety: str,
        platform: str
    ) -> Dict:
        """
        Intent 추천

        Args:
            safety: SAFE/CAUTION/FORBIDDEN
            platform: blog/insta/thread

        Returns:
            {
                "intent": "TRUST",
                "confidence": "HIGH/MEDIUM/LOW",
                "basis": "STATS/PARTIAL/RULE",
                "sample_size": 52,
                "alternatives": ["AUTHORITY", "SAVE"]
            }
        """
        data_count = self._get_data_count(safety, platform)

        if data_count >= self.MIN_SAMPLES_STATS:
            # 통계 기반 추천
            return self._stats_based_recommend(safety, platform, data_count)
        elif data_count >= self.MIN_SAMPLES_PARTIAL:
            # 부분 통계 + 룰 혼합
            return self._partial_stats_recommend(safety, platform, data_count)
        else:
            # 룰 기반 추천
            return self._rule_based_recommend(safety, platform, data_count)

    def get_all_recommendations(self) -> Dict:
        """모든 Safety × Platform 조합에 대한 추천"""
        recommendations = {}

        for platform in ["blog", "insta", "thread"]:
            recommendations[platform] = {}
            for safety in ["SAFE", "CAUTION", "FORBIDDEN"]:
                recommendations[platform][safety] = self.recommend(safety, platform)

        return recommendations

    # =========================================================================
    # 추천 전략
    # =========================================================================

    def _stats_based_recommend(
        self,
        safety: str,
        platform: str,
        data_count: int
    ) -> Dict:
        """통계 기반 추천 (50건 이상)"""
        combination_stats = self.aggregator.aggregate_by_combination(
            safety, platform
        )

        if not combination_stats:
            return self._rule_based_recommend(safety, platform, data_count)

        # 최고 save_rate Intent
        best_intent = max(
            combination_stats,
            key=lambda x: combination_stats[x].get("avg_save_rate", 0)
        )

        # 대안 Intent (2위, 3위)
        sorted_intents = sorted(
            combination_stats.keys(),
            key=lambda x: combination_stats[x].get("avg_save_rate", 0),
            reverse=True
        )
        alternatives = sorted_intents[1:3] if len(sorted_intents) > 1 else []

        return {
            "intent": best_intent,
            "confidence": "HIGH",
            "basis": "STATS",
            "sample_size": data_count,
            "avg_save_rate": combination_stats[best_intent].get("avg_save_rate", 0),
            "alternatives": alternatives,
            "detail": {
                "all_intents": combination_stats
            }
        }

    def _partial_stats_recommend(
        self,
        safety: str,
        platform: str,
        data_count: int
    ) -> Dict:
        """부분 통계 기반 추천 (10~50건)"""
        # 통계 시도
        combination_stats = self.aggregator.aggregate_by_combination(
            safety, platform
        )

        # 룰 기반 기본값
        rule_result = self._rule_based_recommend(safety, platform, data_count)
        default_intent = rule_result["intent"]

        # 통계가 있으면 참고
        if combination_stats:
            stats_best = max(
                combination_stats,
                key=lambda x: combination_stats[x].get("avg_save_rate", 0)
            )

            # 통계 결과가 룰과 다르면 통계 우선 (단, confidence는 MEDIUM)
            return {
                "intent": stats_best,
                "confidence": "MEDIUM",
                "basis": "PARTIAL",
                "sample_size": data_count,
                "rule_fallback": default_intent,
                "alternatives": [default_intent] if stats_best != default_intent else [],
                "detail": {
                    "stats": combination_stats,
                    "note": "부분 통계 기반, 50건 이상 시 HIGH 신뢰도"
                }
            }

        # 통계 없으면 룰 사용
        rule_result["confidence"] = "MEDIUM"
        rule_result["basis"] = "PARTIAL"
        return rule_result

    def _rule_based_recommend(
        self,
        safety: str,
        platform: str,
        data_count: int
    ) -> Dict:
        """룰 기반 추천 (10건 미만)"""
        rules = self.intent_safety_map.get("safety_intent_rules", {})
        safety_rules = rules.get(safety.upper(), {})

        default_intent = safety_rules.get("default_intent", "AUTHORITY")
        allowed_intents = safety_rules.get("allowed_intents", ["AUTHORITY"])

        # 플랫폼별 미세 조정
        if platform.lower() == "thread" and "ENGAGEMENT" in allowed_intents:
            # 쓰레드는 대화 유도가 효과적
            alternatives = [default_intent]
            recommended = "ENGAGEMENT" if safety != "FORBIDDEN" else default_intent
        else:
            recommended = default_intent
            alternatives = [i for i in allowed_intents if i != default_intent][:2]

        return {
            "intent": recommended,
            "confidence": "LOW",
            "basis": "RULE",
            "sample_size": data_count,
            "alternatives": alternatives,
            "detail": {
                "rule_source": "intent_safety_map.json",
                "note": f"데이터 부족 ({data_count}건), 50건 이상 수집 필요"
            }
        }

    # =========================================================================
    # 유틸리티
    # =========================================================================

    def _get_data_count(self, safety: str, platform: str) -> int:
        """Safety + Platform 조합의 데이터 수"""
        combination_stats = self.aggregator.aggregate_by_combination(
            safety, platform
        )
        return sum(s.get("count", 0) for s in combination_stats.values())

    def get_confidence_threshold(self) -> Dict:
        """신뢰도 기준 설명"""
        return {
            "HIGH": f"통계 기반 ({self.MIN_SAMPLES_STATS}건 이상)",
            "MEDIUM": f"부분 통계 ({self.MIN_SAMPLES_PARTIAL}~{self.MIN_SAMPLES_STATS}건)",
            "LOW": f"룰 기반 ({self.MIN_SAMPLES_PARTIAL}건 미만)"
        }

    def generate_recommendation_report(self) -> Dict:
        """전체 추천 리포트 생성"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "thresholds": self.get_confidence_threshold(),
            "recommendations": self.get_all_recommendations()
        }

        # 저장
        report_path = (
            PROJECT_ROOT / "logs" / "performance" / "aggregated" /
            "intent_recommendations.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report
