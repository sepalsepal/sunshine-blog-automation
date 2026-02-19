"""
SunFlow Rollback Manager (P2)
- 게시 취소 및 복구
- 설정 롤백
- 긴급 복구 기능
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent


class RollbackType(Enum):
    """롤백 유형"""
    CONFIG = "config"           # 설정 파일 롤백
    CONTENT = "content"         # 콘텐츠 폴더 롤백
    PUBLISH = "publish"         # 게시 취소
    FULL = "full"               # 전체 복원


@dataclass
class RollbackPoint:
    """롤백 포인트"""
    point_id: str
    created_at: str
    rollback_type: RollbackType
    description: str
    files: List[str]
    metadata: Dict


class RollbackManager:
    """롤백 관리자"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.rollback_dir = self.project_root / "config" / "rollback_points"
        self.rollback_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.rollback_dir / "manifest.json"
        self._load_manifest()

    def _load_manifest(self):
        """매니페스트 로드"""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {"points": [], "last_rollback": None}

    def _save_manifest(self):
        """매니페스트 저장"""
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

    def create_rollback_point(
        self,
        rollback_type: RollbackType,
        description: str,
        files: List[str] = None,
        metadata: Dict = None
    ) -> RollbackPoint:
        """롤백 포인트 생성"""
        timestamp = datetime.now()
        point_id = f"RP-{timestamp.strftime('%Y%m%d-%H%M%S')}"
        point_dir = self.rollback_dir / point_id
        point_dir.mkdir(exist_ok=True)

        # 파일 백업
        backed_up_files = []
        if files:
            for file_path in files:
                source = self.project_root / file_path
                if source.exists():
                    dest = point_dir / Path(file_path).name
                    if source.is_dir():
                        shutil.copytree(source, dest)
                    else:
                        shutil.copy2(source, dest)
                    backed_up_files.append(file_path)

        # 롤백 포인트 정보 저장
        point_info = {
            "point_id": point_id,
            "created_at": timestamp.isoformat(),
            "rollback_type": rollback_type.value,
            "description": description,
            "files": backed_up_files,
            "metadata": metadata or {}
        }

        with open(point_dir / "point_info.json", 'w', encoding='utf-8') as f:
            json.dump(point_info, f, ensure_ascii=False, indent=2)

        # 매니페스트 업데이트
        self.manifest["points"].append(point_info)
        self._save_manifest()

        return RollbackPoint(
            point_id=point_id,
            created_at=timestamp.isoformat(),
            rollback_type=rollback_type,
            description=description,
            files=backed_up_files,
            metadata=metadata or {}
        )

    def rollback_to_point(self, point_id: str) -> Tuple[bool, str]:
        """특정 롤백 포인트로 복원"""
        point_dir = self.rollback_dir / point_id

        if not point_dir.exists():
            return False, f"Rollback point not found: {point_id}"

        # 포인트 정보 로드
        with open(point_dir / "point_info.json", 'r', encoding='utf-8') as f:
            point_info = json.load(f)

        restored_files = []

        for file_path in point_info["files"]:
            backup_file = point_dir / Path(file_path).name
            dest = self.project_root / file_path

            if backup_file.exists():
                # 현재 파일 임시 백업
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()

                # 복원
                if backup_file.is_dir():
                    shutil.copytree(backup_file, dest)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, dest)

                restored_files.append(file_path)

        # 롤백 기록
        self.manifest["last_rollback"] = {
            "point_id": point_id,
            "timestamp": datetime.now().isoformat(),
            "restored_files": restored_files
        }
        self._save_manifest()

        return True, f"Restored {len(restored_files)} files from {point_id}"

    def create_pre_publish_point(self, topic: str, content_folder: str) -> RollbackPoint:
        """게시 전 롤백 포인트 생성"""
        files = [
            "services/dashboard/publish_history.json",
            "config/settings/publishing_history.json",
            content_folder
        ]

        return self.create_rollback_point(
            rollback_type=RollbackType.PUBLISH,
            description=f"Pre-publish checkpoint for {topic}",
            files=files,
            metadata={"topic": topic, "content_folder": content_folder}
        )

    def undo_last_publish(self) -> Tuple[bool, str]:
        """마지막 게시 취소"""
        # 가장 최근 PUBLISH 타입 롤백 포인트 찾기
        publish_points = [
            p for p in self.manifest["points"]
            if p["rollback_type"] == RollbackType.PUBLISH.value
        ]

        if not publish_points:
            return False, "No publish rollback points found"

        latest = sorted(publish_points, key=lambda x: x["created_at"], reverse=True)[0]
        return self.rollback_to_point(latest["point_id"])

    def list_rollback_points(self, limit: int = 10, rollback_type: RollbackType = None) -> List[Dict]:
        """롤백 포인트 목록"""
        points = self.manifest.get("points", [])

        if rollback_type:
            points = [p for p in points if p["rollback_type"] == rollback_type.value]

        return sorted(points, key=lambda x: x["created_at"], reverse=True)[:limit]

    def delete_old_points(self, days: int = 7) -> int:
        """오래된 롤백 포인트 삭제"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0

        points_to_keep = []
        for point in self.manifest.get("points", []):
            point_time = datetime.fromisoformat(point["created_at"])
            if point_time < cutoff:
                # 삭제
                point_dir = self.rollback_dir / point["point_id"]
                if point_dir.exists():
                    shutil.rmtree(point_dir)
                deleted += 1
            else:
                points_to_keep.append(point)

        self.manifest["points"] = points_to_keep
        self._save_manifest()

        return deleted

    def get_status(self) -> Dict:
        """롤백 시스템 상태"""
        points = self.manifest.get("points", [])

        return {
            "total_points": len(points),
            "by_type": {
                rt.value: len([p for p in points if p["rollback_type"] == rt.value])
                for rt in RollbackType
            },
            "last_rollback": self.manifest.get("last_rollback"),
            "oldest_point": min([p["created_at"] for p in points]) if points else None,
            "newest_point": max([p["created_at"] for p in points]) if points else None
        }


# 편의 함수
def create_checkpoint(description: str, files: List[str]) -> str:
    """빠른 체크포인트 생성"""
    manager = RollbackManager()
    point = manager.create_rollback_point(
        rollback_type=RollbackType.CONFIG,
        description=description,
        files=files
    )
    return point.point_id


def quick_rollback(point_id: str) -> bool:
    """빠른 롤백"""
    manager = RollbackManager()
    success, message = manager.rollback_to_point(point_id)
    print(message)
    return success


# CLI 실행
if __name__ == "__main__":
    import sys

    manager = RollbackManager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "list":
            points = manager.list_rollback_points(20)
            print("\n=== 롤백 포인트 목록 ===\n")
            for p in points:
                print(f"  {p['point_id']} | {p['rollback_type']} | {p['description'][:40]}")

        elif cmd == "create" and len(sys.argv) > 2:
            desc = sys.argv[2]
            files = sys.argv[3:] if len(sys.argv) > 3 else []
            point = manager.create_rollback_point(
                rollback_type=RollbackType.CONFIG,
                description=desc,
                files=files
            )
            print(f"\n✅ 롤백 포인트 생성: {point.point_id}")

        elif cmd == "rollback" and len(sys.argv) > 2:
            point_id = sys.argv[2]
            success, message = manager.rollback_to_point(point_id)
            print(f"\n{'✅' if success else '❌'} {message}")

        elif cmd == "undo-publish":
            success, message = manager.undo_last_publish()
            print(f"\n{'✅' if success else '❌'} {message}")

        elif cmd == "status":
            status = manager.get_status()
            print("\n=== 롤백 시스템 상태 ===\n")
            print(f"  총 포인트: {status['total_points']}")
            print(f"  유형별:")
            for t, count in status['by_type'].items():
                print(f"    - {t}: {count}")
            if status['last_rollback']:
                print(f"  마지막 롤백: {status['last_rollback']['point_id']}")

        elif cmd == "cleanup" and len(sys.argv) > 2:
            days = int(sys.argv[2])
            deleted = manager.delete_old_points(days)
            print(f"\n✅ {deleted}개 오래된 포인트 삭제")

        else:
            print("Usage: python rollback_manager.py [list|create <desc> [files...]|rollback <id>|undo-publish|status|cleanup <days>]")
    else:
        status = manager.get_status()
        print(f"\n롤백 포인트: {status['total_points']}개")
