#!/usr/bin/env python3
"""
performance_logger.py - 콘텐츠 성과 기록 모듈
WO-PERFORMANCE-LOOP

책임:
- 게시 완료 후 성과 레코드 생성
- 성과 데이터 업데이트
- 파생 지표 계산
- 다중 경로 저장 (플랫폼/Intent/Safety별)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

PROJECT_ROOT = Path(__file__).parent.parent


class PerformanceLogger:
    """
    콘텐츠 성과 기록 및 관리

    기능:
    - 레코드 생성/업데이트
    - 파생 지표 자동 계산
    - 다중 경로 저장
    """

    def __init__(self):
        self.log_root = PROJECT_ROOT / "logs" / "performance"
        self.schema_path = PROJECT_ROOT / "config" / "performance_schema.json"
        self.platform_kpi_path = PROJECT_ROOT / "config" / "platform_kpi_map.json"
        self._schema = None
        self._platform_kpi = None

    # =========================================================================
    # 설정 로더
    # =========================================================================

    @property
    def schema(self) -> Dict:
        """performance_schema.json 로드"""
        if self._schema is None:
            if self.schema_path.exists():
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    self._schema = json.load(f)
            else:
                self._schema = {}
        return self._schema

    @property
    def platform_kpi(self) -> Dict:
        """platform_kpi_map.json 로드"""
        if self._platform_kpi is None:
            if self.platform_kpi_path.exists():
                with open(self.platform_kpi_path, "r", encoding="utf-8") as f:
                    self._platform_kpi = json.load(f)
            else:
                self._platform_kpi = {}
        return self._platform_kpi

    # =========================================================================
    # 레코드 관리
    # =========================================================================

    def create_record(
        self,
        content_id: str,
        food_id: int,
        food_name: str,
        platform: str,
        strategic_meta: Dict,
        post_url: Optional[str] = None
    ) -> Dict:
        """
        게시 직후 초기 레코드 생성

        Args:
            content_id: 콘텐츠 ID (예: ALLIUM_127)
            food_id: 음식 ID
            food_name: 음식명
            platform: 플랫폼 (blog/insta/thread)
            strategic_meta: 전략 메타데이터
            post_url: 게시물 URL

        Returns:
            생성된 레코드
        """
        record = {
            "content_id": content_id,
            "food_id": food_id,
            "food_name": food_name,
            "strategy": {
                "safety": strategic_meta.get("safety", "SAFE"),
                "intent": strategic_meta.get("intent", "AUTHORITY"),
                "format": strategic_meta.get("format", "DATA"),
                "emotion_axis": strategic_meta.get("emotion_axis", "trust")
            },
            "platform": platform.lower(),
            "post_url": post_url,
            "published_at": datetime.now().isoformat(),
            "metrics": self._empty_metrics(platform),
            "calculated": {},
            "measured_at": None,
            "measurement_count": 0
        }

        # 저장
        self._save_record(record)

        return record

    def update_metrics(
        self,
        content_id: str,
        platform: str,
        metrics: Dict
    ) -> Dict:
        """
        성과 데이터 업데이트

        Args:
            content_id: 콘텐츠 ID
            platform: 플랫폼
            metrics: 원시 지표 딕셔너리

        Returns:
            업데이트된 레코드
        """
        record = self.load_record(content_id, platform)

        if record is None:
            raise ValueError(f"레코드 없음: {content_id}/{platform}")

        # 지표 업데이트
        record["metrics"].update(metrics)

        # 파생 지표 계산
        record["calculated"] = self._calculate_rates(record)

        # 측정 메타데이터 업데이트
        record["measured_at"] = datetime.now().isoformat()
        record["measurement_count"] += 1

        # 저장
        self._save_record(record)

        return record

    def load_record(
        self,
        content_id: str,
        platform: str
    ) -> Optional[Dict]:
        """레코드 로드"""
        platform = platform.lower()
        file_path = self._get_primary_path(content_id, platform)

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_records(
        self,
        platform: Optional[str] = None,
        intent: Optional[str] = None,
        safety: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """조건에 맞는 레코드 목록 반환"""
        records = []

        if platform:
            search_path = self.log_root / "by_platform" / platform.lower()
        elif intent:
            search_path = self.log_root / "by_intent" / intent.upper()
        elif safety:
            search_path = self.log_root / "by_safety" / safety.upper()
        else:
            search_path = self.log_root / "by_platform"

        if not search_path.exists():
            return []

        for json_file in search_path.rglob("*.json"):
            if len(records) >= limit:
                break
            with open(json_file, "r", encoding="utf-8") as f:
                records.append(json.load(f))

        return records

    # =========================================================================
    # 내부 메서드
    # =========================================================================

    def _empty_metrics(self, platform: str) -> Dict:
        """플랫폼별 빈 지표 딕셔너리 생성"""
        platform = platform.lower()
        platform_config = self.platform_kpi.get("platforms", {}).get(platform, {})
        metrics_def = platform_config.get("metrics", {})

        return {key: 0 for key in metrics_def.keys()}

    def _calculate_rates(self, record: Dict) -> Dict:
        """파생 지표 계산"""
        metrics = record.get("metrics", {})
        platform = record.get("platform", "insta")

        calculated = {}

        # 공통: reach 또는 impressions 기준
        reach = metrics.get("reach", metrics.get("impressions", 1))
        if reach == 0:
            reach = 1  # 0 나눗셈 방지

        if platform == "insta":
            # save_rate
            saves = metrics.get("saves", 0)
            calculated["save_rate"] = round(saves / reach * 100, 2)

            # engagement_rate
            comments = metrics.get("comments", 0)
            shares = metrics.get("shares", 0)
            calculated["engagement_rate"] = round(
                (saves + comments + shares) / reach * 100, 2
            )

            # CTR
            profile_clicks = metrics.get("profile_clicks", 0)
            calculated["CTR"] = round(profile_clicks / reach * 100, 2)

        elif platform == "blog":
            # search_CTR
            search_impressions = metrics.get("search_impressions", 1)
            if search_impressions == 0:
                search_impressions = 1
            search_clicks = metrics.get("search_clicks", 0)
            calculated["search_CTR"] = round(
                search_clicks / search_impressions * 100, 2
            )

        elif platform == "thread":
            # reply_rate
            impressions = metrics.get("impressions", 1)
            if impressions == 0:
                impressions = 1
            replies = metrics.get("replies", 0)
            calculated["reply_rate"] = round(replies / impressions * 100, 2)

            # viral_rate
            reposts = metrics.get("reposts", 0)
            quote_posts = metrics.get("quote_posts", 0)
            calculated["viral_rate"] = round(
                (reposts + quote_posts) / impressions * 100, 2
            )

        return calculated

    def _save_record(self, record: Dict) -> None:
        """다중 경로에 레코드 저장"""
        content_id = record["content_id"]
        platform = record["platform"]
        intent = record["strategy"]["intent"]
        safety = record["strategy"]["safety"]

        # 1. 기본 경로 (by_platform)
        primary_path = self._get_primary_path(content_id, platform)
        primary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(primary_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # 2. Intent별 경로 (심볼릭 링크 대신 복사)
        intent_path = self.log_root / "by_intent" / intent / f"{content_id}_{platform}.json"
        intent_path.parent.mkdir(parents=True, exist_ok=True)
        with open(intent_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # 3. Safety별 경로
        safety_path = self.log_root / "by_safety" / safety / f"{content_id}_{platform}.json"
        safety_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safety_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    def _get_primary_path(self, content_id: str, platform: str) -> Path:
        """기본 저장 경로 생성"""
        now = datetime.now()
        month_folder = now.strftime("%Y-%m")
        filename = f"{content_id}.json"

        return (
            self.log_root / "by_platform" / platform.lower() /
            month_folder / filename
        )

    # =========================================================================
    # 유틸리티
    # =========================================================================

    def get_record_count(
        self,
        platform: Optional[str] = None,
        intent: Optional[str] = None,
        safety: Optional[str] = None
    ) -> int:
        """조건에 맞는 레코드 수 반환"""
        return len(self.list_records(
            platform=platform,
            intent=intent,
            safety=safety,
            limit=10000
        ))

    def get_primary_kpi(self, platform: str) -> str:
        """플랫폼의 주요 KPI 반환"""
        platform_config = self.platform_kpi.get("platforms", {}).get(
            platform.lower(), {}
        )
        return platform_config.get("primary_kpi", "impressions")
