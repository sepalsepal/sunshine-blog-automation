"""
데이터 동기화 관리자 v1.0

기능:
- publishing_history.json을 단일 소스(Single Source of Truth)로 관리
- publish_schedule.json, publish_history.json 자동 동기화
- 게시 완료 시 모든 파일 일괄 업데이트
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# 경로 설정
ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = ROOT / "config"
DASHBOARD_DIR = ROOT / "services" / "dashboard"

# 데이터 파일 경로
PUBLISHING_HISTORY = CONFIG_DIR / "settings" / "publishing_history.json"
PUBLISH_SCHEDULE = CONFIG_DIR / "settings" / "publish_schedule.json"
DASHBOARD_HISTORY = DASHBOARD_DIR / "publish_history.json"


class SyncManager:
    """데이터 동기화 관리자"""

    def __init__(self):
        self.publishing_history = self._load_json(PUBLISHING_HISTORY) or {"published": [], "pending": []}
        self.publish_schedule = self._load_json(PUBLISH_SCHEDULE) or {"scheduled": [], "completed": [], "failed": []}
        self.dashboard_history = self._load_json(DASHBOARD_HISTORY) or {}

    def _load_json(self, path: Path) -> Optional[Dict]:
        """JSON 파일 로드"""
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 파일 로드 실패: {path} - {e}")
        return None

    def _save_json(self, path: Path, data: Dict):
        """JSON 파일 저장 (atomic write)"""
        import tempfile
        import os

        path.parent.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def sync_all(self) -> Dict[str, int]:
        """모든 파일 동기화

        Returns:
            동기화 결과 통계
        """
        stats = {"added": 0, "updated": 0, "removed": 0}

        # 1. publishing_history를 기준으로 다른 파일들 동기화
        published_topics = {item["topic"] for item in self.publishing_history.get("published", [])}

        # 2. publish_schedule 동기화
        # - scheduled에서 이미 published된 항목 → completed로 이동
        new_scheduled = []
        for item in self.publish_schedule.get("scheduled", []):
            if item["topic"] in published_topics:
                # 이미 게시됨 → completed로 이동
                hist_item = next(
                    (h for h in self.publishing_history["published"] if h["topic"] == item["topic"]),
                    None
                )
                if hist_item:
                    completed_item = {
                        **item,
                        "status": "completed",
                        "scheduled_date": hist_item.get("date", item.get("scheduled_date")),
                        "completed_at": hist_item.get("date", "") + "T18:00:00",
                        "result": {
                            "instagram_url": hist_item.get("instagram_url"),
                            "post_id": hist_item.get("post_id")
                        }
                    }
                    # 중복 체크 후 추가
                    existing = [c for c in self.publish_schedule.get("completed", []) if c["topic"] == item["topic"]]
                    if not existing:
                        self.publish_schedule.setdefault("completed", []).append(completed_item)
                        stats["updated"] += 1
            else:
                new_scheduled.append(item)

        self.publish_schedule["scheduled"] = new_scheduled

        # 3. dashboard_history 동기화
        for item in self.publishing_history.get("published", []):
            topic = item["topic"]
            date = item.get("date", "")

            # 폴더 찾기
            content_dir = ROOT / "content" / "images"
            folder_name = None
            if content_dir.exists():
                for folder in content_dir.iterdir():
                    if folder.is_dir() and topic in folder.name.lower():
                        folder_name = folder.name
                        break

            if folder_name:
                key = folder_name.replace("_published", "")
                if "_published" in folder_name:
                    key = folder_name
                else:
                    # 번호 추출 시도
                    parts = folder_name.split("_")
                    if parts[0].isdigit():
                        key = f"{parts[0]}_{topic}"
                    else:
                        key = topic

                if key not in self.dashboard_history:
                    self.dashboard_history[key] = {
                        "published_at": date + "T18:00:00" if date and "T" not in date else date,
                        "platform": "instagram",
                        "images": 4,  # 기본값
                        "url": item.get("instagram_url"),
                        "post_id": item.get("post_id")
                    }
                    stats["added"] += 1

        # 4. 저장
        self._save_json(PUBLISH_SCHEDULE, self.publish_schedule)
        self._save_json(DASHBOARD_HISTORY, self.dashboard_history)

        # publishing_history 타임스탬프 업데이트
        self.publishing_history["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        self._save_json(PUBLISHING_HISTORY, self.publishing_history)

        return stats

    def on_publish_complete(
        self,
        topic: str,
        topic_kr: str,
        date: str,
        instagram_url: Optional[str] = None,
        post_id: Optional[str] = None,
        score: int = 95
    ):
        """게시 완료 시 호출 - 모든 파일 자동 업데이트

        Args:
            topic: 영문 주제명
            topic_kr: 한글 주제명
            date: 게시 날짜 (YYYY-MM-DD)
            instagram_url: Instagram 게시물 URL
            post_id: Instagram post ID
            score: 품질 점수
        """
        # 1. publishing_history 업데이트
        existing = [i for i, item in enumerate(self.publishing_history.get("published", []))
                   if item["topic"] == topic]

        new_item = {
            "topic": topic,
            "topic_kr": topic_kr,
            "date": date,
            "instagram_url": instagram_url,
            "post_id": post_id,
            "score": score
        }

        if existing:
            self.publishing_history["published"][existing[0]] = new_item
        else:
            self.publishing_history.setdefault("published", []).append(new_item)

        # pending에서 제거
        self.publishing_history["pending"] = [
            p for p in self.publishing_history.get("pending", [])
            if p.lower() != topic.lower()
        ]

        # 2. 전체 동기화 실행
        stats = self.sync_all()

        print(f"✅ 동기화 완료: {topic_kr} ({topic})")
        print(f"   추가: {stats['added']}, 업데이트: {stats['updated']}")

        return stats


def sync_all_data() -> Dict[str, int]:
    """전체 데이터 동기화 (외부 호출용)"""
    manager = SyncManager()
    return manager.sync_all()


def on_publish_complete(
    topic: str,
    topic_kr: str,
    date: str,
    instagram_url: Optional[str] = None,
    post_id: Optional[str] = None,
    score: int = 95
):
    """게시 완료 핸들러 (외부 호출용)"""
    manager = SyncManager()
    return manager.on_publish_complete(topic, topic_kr, date, instagram_url, post_id, score)


if __name__ == "__main__":
    # 테스트 실행
    print("🔄 데이터 동기화 시작...")
    stats = sync_all_data()
    print(f"✅ 동기화 완료: {stats}")
