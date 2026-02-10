#!/usr/bin/env python3
"""
Project Sunshine - Status Updater
파이프라인에서 대시보드 상태를 업데이트하는 모듈

사용법:
    from services.dashboard.status_updater import StatusUpdater

    updater = StatusUpdater()
    updater.start_pipeline("cherry")
    updater.start_step("김차장")
    updater.complete_step("김차장", duration=12.5)
    updater.set_error("에러 메시지")
    updater.finish_pipeline(result={...})
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

STATUS_FILE = Path(__file__).parent / "status.json"

# v5 파이프라인 - 14단계
PIPELINE_STEPS = [
    {"id": 0,  "name": "김부장", "role": "지시",     "emoji": "👔", "is_gate": False},
    {"id": 1,  "name": "김작가", "role": "주제탐색", "emoji": "✍️", "is_gate": False},
    {"id": 2,  "name": "최검증", "role": "주제검증", "emoji": "🔬", "is_gate": True},
    {"id": 3,  "name": "최검증", "role": "팩트체크", "emoji": "🔬", "is_gate": False},
    {"id": 4,  "name": "김작가", "role": "기획/글",  "emoji": "✍️", "is_gate": False},
    {"id": 5,  "name": "김감독", "role": "G1 검수",  "emoji": "🎬", "is_gate": True},
    {"id": 6,  "name": "이작가", "role": "이미지",   "emoji": "🎨", "is_gate": False},
    {"id": 7,  "name": "김감독", "role": "G2 검수",  "emoji": "🎬", "is_gate": True},
    {"id": 8,  "name": "박편집", "role": "합성",     "emoji": "✏️", "is_gate": False},
    {"id": 9,  "name": "김감독", "role": "G3 검수",  "emoji": "🎬", "is_gate": True},
    {"id": 10, "name": "김감독", "role": "최종승인", "emoji": "⭐", "is_gate": True},
    {"id": 11, "name": "김대리", "role": "업로드",   "emoji": "📤", "is_gate": False},
    {"id": 12, "name": "김대리", "role": "인스타",   "emoji": "📸", "is_gate": False},
    {"id": 13, "name": "김대리", "role": "웹페이지", "emoji": "🌐", "is_gate": False},
]

# 하위 호환성을 위한 별칭
AGENT_ORDER = PIPELINE_STEPS


class StatusUpdater:
    """파이프라인 상태 업데이터"""

    def __init__(self, status_file: Path = STATUS_FILE):
        self.status_file = status_file
        self._load()

    def _load(self):
        """상태 로드"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self._reset()
        except:
            self._reset()

    def _save(self):
        """상태 저장"""
        self.data["last_updated"] = datetime.now().isoformat()
        self.status_file.parent.mkdir(exist_ok=True)
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _reset(self):
        """상태 초기화"""
        self.data = {
            "topic": None,
            "started_at": None,
            "current_step": -1,
            "total_progress": 0,
            "steps": [
                {
                    "id": step["id"],
                    "name": step["name"],
                    "role": step["role"],
                    "emoji": step["emoji"],
                    "is_gate": step["is_gate"],
                    "status": "pending",
                    "duration": None,
                    "progress": None
                }
                for step in PIPELINE_STEPS
            ],
            "errors": [],
            "result": None,
            "last_updated": None
        }
        self._save()

    def _get_step_index(self, identifier) -> int:
        """단계 ID 또는 이름으로 인덱스 찾기"""
        for i, step in enumerate(self.data["steps"]):
            # ID로 찾기 (숫자)
            if isinstance(identifier, int) and step["id"] == identifier:
                return i
            # 이름으로 찾기 (문자열)
            if isinstance(identifier, str) and step["name"] == identifier:
                return i
            # role로 찾기
            if isinstance(identifier, str) and step["role"] == identifier:
                return i
        return -1

    def _update_progress(self):
        """전체 진행률 계산"""
        total = len(self.data["steps"])
        done = sum(1 for s in self.data["steps"] if s["status"] == "done")
        self.data["total_progress"] = int((done / total) * 100) if total > 0 else 0

    def start_pipeline(self, topic: str):
        """파이프라인 시작"""
        self._reset()
        self.data["topic"] = topic
        self.data["started_at"] = datetime.now().isoformat()
        self._save()
        print(f"📊 대시보드: {topic} 파이프라인 시작")

    def start_step(self, name: str, progress: str = None):
        """단계 시작"""
        idx = self._get_step_index(name)
        if idx >= 0:
            self.data["steps"][idx]["status"] = "running"
            self.data["steps"][idx]["progress"] = progress
            self.data["current_step"] = idx + 1
            self._save()

    def update_step_progress(self, name: str, progress: str):
        """단계 진행 상황 업데이트"""
        idx = self._get_step_index(name)
        if idx >= 0:
            self.data["steps"][idx]["progress"] = progress
            self._save()

    def complete_step(self, name: str, duration: float = None):
        """단계 완료"""
        idx = self._get_step_index(name)
        if idx >= 0:
            self.data["steps"][idx]["status"] = "done"
            self.data["steps"][idx]["duration"] = duration
            self.data["steps"][idx]["progress"] = None
            self._update_progress()
            self._save()

    def fail_step(self, name: str, error: str = None):
        """단계 실패"""
        idx = self._get_step_index(name)
        if idx >= 0:
            self.data["steps"][idx]["status"] = "error"
            if error:
                self.data["errors"].append(f"[{name}] {error}")
            self._save()

    def set_error(self, message: str):
        """에러 추가"""
        self.data["errors"].append(message)
        self._save()

    def finish_pipeline(self, result: Dict[str, Any] = None, success: bool = True):
        """파이프라인 종료"""
        self.data["result"] = result
        if success:
            self.data["current_step"] = len(self.data["steps"]) + 1

            # 🔄 자동 동기화: 파이프라인 완료 시 모든 데이터 파일 동기화
            try:
                from core.utils.sync_manager import sync_all_data
                sync_result = sync_all_data()
                print(f"🔄 데이터 동기화 완료: {sync_result}")
            except Exception as e:
                print(f"⚠️ 동기화 실패: {e}")

        self._save()
        print(f"📊 대시보드: 파이프라인 {'완료' if success else '실패'}")

    def reset(self):
        """상태 초기화"""
        self._reset()
        print("📊 대시보드: 상태 초기화됨")


# 싱글톤 인스턴스
_updater = None

def get_updater() -> StatusUpdater:
    """싱글톤 업데이터 반환"""
    global _updater
    if _updater is None:
        _updater = StatusUpdater()
    return _updater


# 편의 함수
def start_pipeline(topic: str):
    get_updater().start_pipeline(topic)

def start_step(name: str, progress: str = None):
    get_updater().start_step(name, progress)

def update_progress(name: str, progress: str):
    get_updater().update_step_progress(name, progress)

def complete_step(name: str, duration: float = None):
    get_updater().complete_step(name, duration)

def fail_step(name: str, error: str = None):
    get_updater().fail_step(name, error)

def set_error(message: str):
    get_updater().set_error(message)

def finish_pipeline(result: Dict = None, success: bool = True):
    get_updater().finish_pipeline(result, success)

def reset():
    get_updater().reset()


if __name__ == "__main__":
    # 테스트
    import time

    print("테스트 시작...")

    reset()
    start_pipeline("apple")
    time.sleep(1)

    for agent in AGENT_ORDER:
        name = agent["name"]
        print(f"  {name} 시작...")
        start_step(name)

        if name == "이작가":
            for i in range(1, 11):
                update_progress(name, f"{i}/10장")
                time.sleep(0.3)

        time.sleep(0.5)
        complete_step(name, duration=2.5)

    finish_pipeline(result={"status": "success"})
    print("테스트 완료!")
