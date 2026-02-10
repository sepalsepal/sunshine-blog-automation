#!/usr/bin/env python3
"""
Status Checker - status.json 검증
완료 기준 = status.json 파일 기반
"""

import json
from pathlib import Path
from typing import Dict, Tuple


class StatusChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tasks_dir = self.project_root / "tasks"
        self.snapshots_dir = self.project_root / "snapshots"

    def verify_rules_loaded(self) -> Tuple[bool, str]:
        """
        RULES 읽기 증거 확인
        이 파일 없으면 다음 단계 진행 금지
        """
        snapshot_path = self.snapshots_dir / "rules_snapshot.json"

        if not snapshot_path.exists():
            return False, "rules_snapshot.json 없음"

        snapshot = json.loads(snapshot_path.read_text())

        required = ["rules_hash", "safety_colors", "reference_contents"]
        for field in required:
            if field not in snapshot:
                return False, f"스냅샷에 {field} 없음"

        return True, f"RULES 스냅샷 확인됨 (해시: {snapshot['rules_hash']})"

    def verify_task_exists(self, food_name: str) -> Tuple[bool, str]:
        """Task 파일 존재 확인"""
        task_path = self.tasks_dir / f"task_{food_name}.yaml"

        if not task_path.exists():
            return False, f"task_{food_name}.yaml 없음"

        task = json.loads(task_path.read_text())

        required = ["task_id", "food_name", "safety_level", "text_color", "rules_hash"]
        for field in required:
            if field not in task:
                return False, f"Task에 {field} 없음"

        return True, f"Task 확인됨: {task['task_id']}"

    def verify_status(self, food_name: str) -> Tuple[bool, str]:
        """Status 파일 검증 - 진짜 완료 여부"""
        status_path = self.tasks_dir / f"status_{food_name}.json"

        if not status_path.exists():
            return False, f"status_{food_name}.json 없음"

        status = json.loads(status_path.read_text())

        # 필수 필드 확인
        required = ["task_id", "food_name", "visual_guard", "sheet_updated",
                    "telegram_sent", "all_passed", "completed_at"]
        for field in required:
            if field not in status:
                return False, f"Status에 {field} 없음"

        # 완료 조건 검증
        if status.get("visual_guard") != "PASS":
            return False, f"visual_guard: {status.get('visual_guard')} (PASS 필요)"

        if not status.get("sheet_updated"):
            return False, "sheet_updated: False"

        if not status.get("telegram_sent"):
            return False, "telegram_sent: False"

        if not status.get("all_passed"):
            return False, "all_passed: False"

        if not status.get("completed_at"):
            return False, "completed_at: None"

        return True, f"✅ 완료 확인됨: {status['completed_at']}"

    def is_truly_completed(self, food_name: str) -> bool:
        """
        진짜 완료인지 검증
        이 함수가 True 반환해야만 완료 인정
        """
        rules_ok, _ = self.verify_rules_loaded()
        task_ok, _ = self.verify_task_exists(food_name)
        status_ok, _ = self.verify_status(food_name)

        return rules_ok and task_ok and status_ok

    def full_check(self, food_name: str) -> Dict:
        """전체 검증 실행 및 결과 반환"""
        results = {
            "food_name": food_name,
            "checks": {}
        }

        # 1. RULES 스냅샷
        ok, msg = self.verify_rules_loaded()
        results["checks"]["rules_snapshot"] = {"passed": ok, "message": msg}

        # 2. Task 파일
        ok, msg = self.verify_task_exists(food_name)
        results["checks"]["task_file"] = {"passed": ok, "message": msg}

        # 3. Status 파일
        ok, msg = self.verify_status(food_name)
        results["checks"]["status_file"] = {"passed": ok, "message": msg}

        # 최종 결과
        results["all_passed"] = all(c["passed"] for c in results["checks"].values())

        return results

    def print_check_result(self, food_name: str):
        """검증 결과 출력"""
        result = self.full_check(food_name)

        print("=" * 50)
        print(f"🔍 완료 검증: {food_name}")
        print("=" * 50)

        for name, check in result["checks"].items():
            icon = "✅" if check["passed"] else "❌"
            print(f"{icon} {name}: {check['message']}")

        print("-" * 50)
        if result["all_passed"]:
            print("✅ 최종 결과: 완료 인정")
        else:
            print("❌ 최종 결과: 미완료")
        print("=" * 50)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python status_checker.py <food_name>")
        print("예시: python status_checker.py duck")
        sys.exit(1)

    food_name = sys.argv[1]
    checker = StatusChecker()
    checker.print_check_result(food_name)
