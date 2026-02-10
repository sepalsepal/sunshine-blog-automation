"""
SunFlow Backup Manager (P1)
- 설정 및 데이터 자동 백업
- Cloudinary 동기화
- 복원 기능
"""

import os
import json
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / "config" / "backups"


@dataclass
class BackupInfo:
    """백업 정보"""
    backup_id: str
    timestamp: str
    files: List[str]
    size_bytes: int
    checksum: str
    backup_type: str  # "auto" or "manual"


class BackupManager:
    """백업 관리자"""

    # 백업 대상 파일/폴더
    BACKUP_TARGETS = {
        "config": [
            "config/settings/publishing_history.json",
            "config/settings/publish_schedule.json",
            "config/data/content_queue.json",
            "config/data/instagram_stats.json",
            "config/data/ab_tests.json",
        ],
        "data": [
            "services/dashboard/publish_history.json",
            "services/dashboard/status.json",
        ],
        "covers": [
            "content/images/000_cover/02_ready",
            "content/images/000_cover/03_cover_sources/cover_mapping.json",
        ]
    }

    # 백업 보존 기간 (일)
    RETENTION_DAYS = 30

    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.backup_dir / "manifest.json"
        self._load_manifest()

    def _load_manifest(self):
        """백업 매니페스트 로드"""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {"backups": [], "last_auto_backup": None}

    def _save_manifest(self):
        """백업 매니페스트 저장"""
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

    def _calculate_checksum(self, file_path: Path) -> str:
        """파일 체크섬 계산"""
        if file_path.is_dir():
            # 디렉토리인 경우 모든 파일의 체크섬 조합
            checksums = []
            for f in sorted(file_path.rglob("*")):
                if f.is_file():
                    checksums.append(self._calculate_checksum(f))
            return hashlib.md5("".join(checksums).encode()).hexdigest()[:8]
        else:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:8]

    def create_backup(self, backup_type: str = "manual", categories: List[str] = None) -> BackupInfo:
        """백업 생성"""
        timestamp = datetime.now()
        backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        if categories is None:
            categories = list(self.BACKUP_TARGETS.keys())

        backed_up_files = []
        total_size = 0

        for category in categories:
            if category not in self.BACKUP_TARGETS:
                continue

            category_dir = backup_path / category
            category_dir.mkdir(exist_ok=True)

            for target in self.BACKUP_TARGETS[category]:
                source = PROJECT_ROOT / target

                if not source.exists():
                    continue

                if source.is_dir():
                    # 디렉토리 복사
                    dest = category_dir / source.name
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                    # 크기 계산
                    for f in dest.rglob("*"):
                        if f.is_file():
                            total_size += f.stat().st_size
                else:
                    # 파일 복사
                    dest = category_dir / source.name
                    shutil.copy2(source, dest)
                    total_size += dest.stat().st_size

                backed_up_files.append(target)

        # 체크섬 계산
        checksum = self._calculate_checksum(backup_path)

        # 백업 정보 저장
        backup_info = BackupInfo(
            backup_id=backup_id,
            timestamp=timestamp.isoformat(),
            files=backed_up_files,
            size_bytes=total_size,
            checksum=checksum,
            backup_type=backup_type
        )

        # 매니페스트 업데이트
        self.manifest["backups"].append({
            "backup_id": backup_id,
            "timestamp": timestamp.isoformat(),
            "files": backed_up_files,
            "size_bytes": total_size,
            "checksum": checksum,
            "backup_type": backup_type
        })

        if backup_type == "auto":
            self.manifest["last_auto_backup"] = timestamp.isoformat()

        self._save_manifest()

        # 오래된 백업 정리
        self._cleanup_old_backups()

        return backup_info

    def restore_backup(self, backup_id: str, categories: List[str] = None) -> bool:
        """백업 복원"""
        backup_path = self.backup_dir / backup_id

        if not backup_path.exists():
            raise ValueError(f"Backup not found: {backup_id}")

        if categories is None:
            categories = list(self.BACKUP_TARGETS.keys())

        restored_files = []

        for category in categories:
            category_dir = backup_path / category

            if not category_dir.exists():
                continue

            for target in self.BACKUP_TARGETS[category]:
                source_name = Path(target).name
                backup_source = category_dir / source_name

                if not backup_source.exists():
                    continue

                dest = PROJECT_ROOT / target

                # 기존 파일 백업 (복원 전)
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()

                # 복원
                if backup_source.is_dir():
                    shutil.copytree(backup_source, dest)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_source, dest)

                restored_files.append(target)

        return True

    def list_backups(self, limit: int = 10) -> List[Dict]:
        """백업 목록 조회"""
        backups = sorted(
            self.manifest.get("backups", []),
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]

        return backups

    def get_backup_info(self, backup_id: str) -> Optional[Dict]:
        """특정 백업 정보 조회"""
        for backup in self.manifest.get("backups", []):
            if backup["backup_id"] == backup_id:
                return backup
        return None

    def delete_backup(self, backup_id: str) -> bool:
        """백업 삭제"""
        backup_path = self.backup_dir / backup_id

        if backup_path.exists():
            shutil.rmtree(backup_path)

        self.manifest["backups"] = [
            b for b in self.manifest["backups"]
            if b["backup_id"] != backup_id
        ]
        self._save_manifest()

        return True

    def _cleanup_old_backups(self):
        """오래된 백업 정리"""
        cutoff = datetime.now() - timedelta(days=self.RETENTION_DAYS)

        to_delete = []
        for backup in self.manifest.get("backups", []):
            backup_time = datetime.fromisoformat(backup["timestamp"])
            if backup_time < cutoff:
                to_delete.append(backup["backup_id"])

        for backup_id in to_delete:
            self.delete_backup(backup_id)

    def should_auto_backup(self) -> bool:
        """자동 백업 필요 여부 확인"""
        last_backup = self.manifest.get("last_auto_backup")

        if not last_backup:
            return True

        last_time = datetime.fromisoformat(last_backup)
        return datetime.now() - last_time > timedelta(hours=24)

    def run_auto_backup(self) -> Optional[BackupInfo]:
        """자동 백업 실행 (필요시)"""
        if self.should_auto_backup():
            return self.create_backup(backup_type="auto")
        return None

    def get_status(self) -> Dict:
        """백업 상태 조회"""
        backups = self.manifest.get("backups", [])

        total_size = sum(b.get("size_bytes", 0) for b in backups)

        return {
            "total_backups": len(backups),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "last_auto_backup": self.manifest.get("last_auto_backup"),
            "retention_days": self.RETENTION_DAYS,
            "auto_backup_needed": self.should_auto_backup()
        }


# CLI 실행
if __name__ == "__main__":
    import sys

    manager = BackupManager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "create":
            backup_type = sys.argv[2] if len(sys.argv) > 2 else "manual"
            info = manager.create_backup(backup_type=backup_type)
            print(f"\n✅ 백업 생성 완료!")
            print(f"   ID: {info.backup_id}")
            print(f"   파일 수: {len(info.files)}")
            print(f"   크기: {info.size_bytes / 1024:.1f} KB")
            print(f"   체크섬: {info.checksum}")

        elif cmd == "list":
            backups = manager.list_backups(20)
            print("\n=== 백업 목록 ===\n")
            for b in backups:
                size_kb = b.get("size_bytes", 0) / 1024
                print(f"  {b['backup_id']} | {b['timestamp'][:19]} | {size_kb:.1f}KB | {b['backup_type']}")

        elif cmd == "restore" and len(sys.argv) > 2:
            backup_id = sys.argv[2]
            try:
                manager.restore_backup(backup_id)
                print(f"\n✅ 백업 복원 완료: {backup_id}")
            except ValueError as e:
                print(f"\n❌ 오류: {e}")

        elif cmd == "delete" and len(sys.argv) > 2:
            backup_id = sys.argv[2]
            manager.delete_backup(backup_id)
            print(f"\n✅ 백업 삭제 완료: {backup_id}")

        elif cmd == "status":
            status = manager.get_status()
            print("\n=== 백업 상태 ===\n")
            print(f"  총 백업 수: {status['total_backups']}")
            print(f"  총 용량: {status['total_size_mb']} MB")
            print(f"  마지막 자동 백업: {status['last_auto_backup'] or '없음'}")
            print(f"  보존 기간: {status['retention_days']}일")
            print(f"  자동 백업 필요: {'예' if status['auto_backup_needed'] else '아니오'}")

        elif cmd == "auto":
            info = manager.run_auto_backup()
            if info:
                print(f"\n✅ 자동 백업 완료: {info.backup_id}")
            else:
                print("\n⏭️ 자동 백업 불필요 (24시간 이내 백업 존재)")

        else:
            print("Usage: python backup_manager.py [create|list|restore <id>|delete <id>|status|auto]")
    else:
        print("Usage: python backup_manager.py [create|list|restore <id>|delete <id>|status|auto]")
