"""
파이프라인 상태 영구 저장
- JSON 파일 기반
- 재시작 시 상태 복구
- 히스토리 관리

Phase 3: 상태 저장소
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

ROOT = Path(__file__).parent.parent


class StateStore:
    """
    파이프라인 상태 영구 저장소

    Features:
    - JSON 파일 기반 저장
    - 재시작 시 상태 복구
    - 미완료 파이프라인 조회
    - 히스토리 관리
    """

    def __init__(self, store_path: str = "data/pipeline_states.json"):
        self.store_path = ROOT / store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """저장된 상태 로드"""
        if self.store_path.exists():
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    self.states = json.load(f)
            except json.JSONDecodeError:
                self.states = {}
        else:
            self.states = {}

    def _save(self):
        """상태 저장"""
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.states, f, ensure_ascii=False, indent=2, default=str)

    def save_state(self, food_name: str, state: Any) -> None:
        """
        파이프라인 상태 저장

        Args:
            food_name: 음식명 (키)
            state: PipelineState 또는 dict
        """
        if hasattr(state, "to_dict"):
            state_dict = state.to_dict()
        elif hasattr(state, "__dict__"):
            state_dict = state.__dict__.copy()
            # Enum 처리
            if hasattr(state_dict.get("status"), "value"):
                state_dict["status"] = state_dict["status"].value
        else:
            state_dict = dict(state)

        state_dict["_saved_at"] = datetime.now().isoformat()

        self.states[food_name] = state_dict
        self._save()

    def get_state(self, food_name: str) -> Optional[Dict]:
        """
        파이프라인 상태 조회

        Args:
            food_name: 음식명

        Returns:
            상태 dict 또는 None
        """
        return self.states.get(food_name)

    def get_pending_pipelines(self) -> Dict[str, Dict]:
        """
        미완료 파이프라인 조회

        Returns:
            {food_name: state} 형태의 dict
        """
        return {
            k: v for k, v in self.states.items()
            if v.get("status") not in ["completed", "failed"]
        }

    def get_failed_pipelines(self) -> Dict[str, Dict]:
        """
        실패한 파이프라인 조회

        Returns:
            {food_name: state} 형태의 dict
        """
        return {
            k: v for k, v in self.states.items()
            if v.get("status") == "failed"
        }

    def get_completed_pipelines(self) -> Dict[str, Dict]:
        """
        완료된 파이프라인 조회

        Returns:
            {food_name: state} 형태의 dict
        """
        return {
            k: v for k, v in self.states.items()
            if v.get("status") == "completed"
        }

    def get_all_states(self) -> Dict[str, Dict]:
        """전체 상태 조회"""
        return self.states.copy()

    def delete_state(self, food_name: str) -> bool:
        """
        파이프라인 상태 삭제

        Args:
            food_name: 음식명

        Returns:
            삭제 성공 여부
        """
        if food_name in self.states:
            del self.states[food_name]
            self._save()
            return True
        return False

    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        최근 파이프라인 히스토리

        Args:
            limit: 반환할 최대 개수

        Returns:
            최근 상태 리스트 (최신순)
        """
        sorted_states = sorted(
            self.states.items(),
            key=lambda x: x[1].get("updated_at", ""),
            reverse=True
        )
        return [{"food_name": k, **v} for k, v in sorted_states[:limit]]

    def get_statistics(self) -> Dict[str, Any]:
        """
        파이프라인 통계

        Returns:
            통계 정보 dict
        """
        total = len(self.states)
        completed = len(self.get_completed_pipelines())
        failed = len(self.get_failed_pipelines())
        pending = len(self.get_pending_pipelines())

        # 평균 점수 계산
        tech_scores = []
        creative_scores = []

        for state in self.states.values():
            if state.get("tech_review_score"):
                tech_scores.append(state["tech_review_score"])
            if state.get("creative_review_score"):
                creative_scores.append(state["creative_review_score"])

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "avg_tech_score": sum(tech_scores) / len(tech_scores) if tech_scores else 0,
            "avg_creative_score": sum(creative_scores) / len(creative_scores) if creative_scores else 0
        }

    def clear_all(self) -> None:
        """모든 상태 삭제 (주의!)"""
        self.states = {}
        self._save()


# 테스트
if __name__ == "__main__":
    store = StateStore()

    # 테스트 상태 저장
    store.save_state("watermelon", {
        "food_name": "watermelon",
        "food_name_kr": "수박",
        "status": "completed",
        "tech_review_score": 95.0,
        "creative_review_score": 88.5,
        "instagram_url": "https://instagram.com/p/test123"
    })

    # 조회
    state = store.get_state("watermelon")
    print(f"상태: {state}")

    # 통계
    stats = store.get_statistics()
    print(f"통계: {stats}")

    # 히스토리
    history = store.get_history()
    print(f"히스토리: {len(history)}개")
