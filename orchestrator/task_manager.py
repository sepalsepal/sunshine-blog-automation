#!/usr/bin/env python3
"""
Task Manager - task.yaml 생성/관리
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class TaskManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tasks_dir = self.project_root / "tasks"
        self.tasks_dir.mkdir(exist_ok=True)

    def list_tasks(self) -> List[Dict]:
        """모든 task 목록 조회"""
        tasks = []
        for task_file in self.tasks_dir.glob("task_*.yaml"):
            task = json.loads(task_file.read_text())
            tasks.append(task)
        return tasks

    def get_task(self, food_name: str) -> Optional[Dict]:
        """특정 음식의 task 조회"""
        task_path = self.tasks_dir / f"task_{food_name}.yaml"
        if task_path.exists():
            return json.loads(task_path.read_text())
        return None

    def get_status(self, food_name: str) -> Optional[Dict]:
        """특정 음식의 status 조회"""
        status_path = self.tasks_dir / f"status_{food_name}.json"
        if status_path.exists():
            return json.loads(status_path.read_text())
        return None

    def list_pending_tasks(self) -> List[Dict]:
        """pending 상태인 task 목록"""
        tasks = []
        for task in self.list_tasks():
            status = self.get_status(task["food_name"])
            if not status or not status.get("all_passed"):
                tasks.append(task)
        return tasks

    def list_completed_tasks(self) -> List[Dict]:
        """완료된 task 목록"""
        tasks = []
        for task in self.list_tasks():
            status = self.get_status(task["food_name"])
            if status and status.get("all_passed"):
                tasks.append({**task, "status": status})
        return tasks

    def print_summary(self):
        """태스크 현황 요약 출력"""
        all_tasks = self.list_tasks()
        completed = self.list_completed_tasks()
        pending = self.list_pending_tasks()

        print("=" * 50)
        print("📋 Task 현황")
        print("=" * 50)
        print(f"전체: {len(all_tasks)}")
        print(f"완료: {len(completed)}")
        print(f"대기: {len(pending)}")
        print()

        if completed:
            print("✅ 완료된 작업:")
            for t in completed:
                print(f"   - {t['food_name']} ({t['safety_level']}, {t['text_color']})")

        if pending:
            print("⏳ 대기 중인 작업:")
            for t in pending:
                print(f"   - {t['food_name']} ({t['safety_level']})")

        print("=" * 50)


if __name__ == "__main__":
    manager = TaskManager()
    manager.print_summary()
