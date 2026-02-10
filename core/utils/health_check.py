"""
SunFlow Health Check (P1)
- 시스템 상태 점검
- API 연결 확인
- 리소스 모니터링
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent


class HealthStatus(Enum):
    """상태 레벨"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """컴포넌트 상태"""
    name: str
    status: HealthStatus
    message: str
    last_check: str
    details: Optional[Dict] = None


@dataclass
class SystemHealth:
    """시스템 전체 상태"""
    overall_status: HealthStatus
    timestamp: str
    components: Dict[str, ComponentHealth]
    uptime_seconds: float
    version: str = "1.0.0"


class HealthChecker:
    """시스템 헬스체크"""

    _start_time = datetime.now()

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.checks = {
            "filesystem": self._check_filesystem,
            "config": self._check_config,
            "instagram_token": self._check_instagram_token,
            "cloudinary": self._check_cloudinary,
            "telegram": self._check_telegram,
            "content_queue": self._check_content_queue,
            "disk_space": self._check_disk_space,
        }

    async def run_all_checks(self) -> SystemHealth:
        """모든 헬스체크 실행"""
        components = {}

        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                components[name] = result
            except Exception as e:
                components[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(e)}",
                    last_check=datetime.now().isoformat()
                )

        # 전체 상태 결정
        overall = self._determine_overall_status(components)

        return SystemHealth(
            overall_status=overall,
            timestamp=datetime.now().isoformat(),
            components=components,
            uptime_seconds=(datetime.now() - self._start_time).total_seconds()
        )

    def _determine_overall_status(self, components: Dict[str, ComponentHealth]) -> HealthStatus:
        """전체 상태 결정"""
        statuses = [c.status for c in components.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN

    async def _check_filesystem(self) -> ComponentHealth:
        """파일시스템 체크"""
        required_dirs = [
            "core/agents",
            "core/utils",
            "services/scripts",
            "services/dashboard",
            "config/settings",
            "config/data",
            "content/images",
        ]

        missing = []
        for d in required_dirs:
            if not (self.project_root / d).exists():
                missing.append(d)

        if not missing:
            return ComponentHealth(
                name="filesystem",
                status=HealthStatus.HEALTHY,
                message="All required directories exist",
                last_check=datetime.now().isoformat()
            )
        else:
            return ComponentHealth(
                name="filesystem",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing directories: {missing}",
                last_check=datetime.now().isoformat(),
                details={"missing": missing}
            )

    async def _check_config(self) -> ComponentHealth:
        """설정 파일 체크"""
        required_files = [
            "config/settings/publishing_history.json",
        ]

        optional_files = [
            "config/settings/publish_schedule.json",
        ]

        missing_required = []
        missing_optional = []

        for f in required_files:
            if not (self.project_root / f).exists():
                missing_required.append(f)

        for f in optional_files:
            if not (self.project_root / f).exists():
                missing_optional.append(f)

        if missing_required:
            return ComponentHealth(
                name="config",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing required config: {missing_required}",
                last_check=datetime.now().isoformat()
            )
        elif missing_optional:
            return ComponentHealth(
                name="config",
                status=HealthStatus.DEGRADED,
                message=f"Missing optional config: {missing_optional}",
                last_check=datetime.now().isoformat()
            )
        else:
            return ComponentHealth(
                name="config",
                status=HealthStatus.HEALTHY,
                message="All config files present",
                last_check=datetime.now().isoformat()
            )

    async def _check_instagram_token(self) -> ComponentHealth:
        """Instagram 토큰 체크"""
        token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

        if not token:
            # .env 파일에서 읽기 시도
            env_file = self.project_root / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("INSTAGRAM_ACCESS_TOKEN="):
                            token = line.split("=", 1)[1].strip().strip('"\'')
                            break

        if not token:
            return ComponentHealth(
                name="instagram_token",
                status=HealthStatus.UNHEALTHY,
                message="Instagram token not found",
                last_check=datetime.now().isoformat()
            )

        # 토큰 만료 체크 (60일 장기 토큰 기준)
        # 실제로는 API 호출이 필요하지만, 여기서는 존재 여부만 확인
        return ComponentHealth(
            name="instagram_token",
            status=HealthStatus.HEALTHY,
            message="Token configured (expiry check requires API call)",
            last_check=datetime.now().isoformat(),
            details={"token_length": len(token)}
        )

    async def _check_cloudinary(self) -> ComponentHealth:
        """Cloudinary 설정 체크"""
        required_vars = [
            "CLOUDINARY_CLOUD_NAME",
            "CLOUDINARY_API_KEY",
            "CLOUDINARY_API_SECRET"
        ]

        missing = []
        for var in required_vars:
            if not os.environ.get(var):
                # .env에서 확인
                env_file = self.project_root / ".env"
                if env_file.exists():
                    with open(env_file, 'r') as f:
                        content = f.read()
                        if f"{var}=" not in content:
                            missing.append(var)
                else:
                    missing.append(var)

        if missing:
            return ComponentHealth(
                name="cloudinary",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing Cloudinary config: {missing}",
                last_check=datetime.now().isoformat()
            )

        return ComponentHealth(
            name="cloudinary",
            status=HealthStatus.HEALTHY,
            message="Cloudinary configured",
            last_check=datetime.now().isoformat()
        )

    async def _check_telegram(self) -> ComponentHealth:
        """Telegram 봇 설정 체크"""
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not token or not chat_id:
            env_file = self.project_root / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()
                    if "TELEGRAM_BOT_TOKEN=" not in content:
                        token = None
                    else:
                        token = "configured"
                    if "TELEGRAM_CHAT_ID=" not in content:
                        chat_id = None
                    else:
                        chat_id = "configured"

        if not token or not chat_id:
            return ComponentHealth(
                name="telegram",
                status=HealthStatus.DEGRADED,
                message="Telegram bot not fully configured",
                last_check=datetime.now().isoformat()
            )

        return ComponentHealth(
            name="telegram",
            status=HealthStatus.HEALTHY,
            message="Telegram bot configured",
            last_check=datetime.now().isoformat()
        )

    async def _check_content_queue(self) -> ComponentHealth:
        """콘텐츠 큐 체크"""
        queue_file = self.project_root / "config" / "data" / "content_queue.json"

        if not queue_file.exists():
            return ComponentHealth(
                name="content_queue",
                status=HealthStatus.DEGRADED,
                message="Content queue not initialized",
                last_check=datetime.now().isoformat()
            )

        try:
            with open(queue_file, 'r') as f:
                queue_data = json.load(f)

            pending = len([q for q in queue_data.get("queue", []) if q.get("status") == "pending"])

            return ComponentHealth(
                name="content_queue",
                status=HealthStatus.HEALTHY,
                message=f"{pending} items pending in queue",
                last_check=datetime.now().isoformat(),
                details={"pending_count": pending}
            )
        except Exception as e:
            return ComponentHealth(
                name="content_queue",
                status=HealthStatus.DEGRADED,
                message=f"Queue read error: {str(e)}",
                last_check=datetime.now().isoformat()
            )

    async def _check_disk_space(self) -> ComponentHealth:
        """디스크 공간 체크"""
        import shutil

        total, used, free = shutil.disk_usage(self.project_root)
        free_gb = free / (1024 ** 3)
        used_percent = (used / total) * 100

        if free_gb < 1:
            status = HealthStatus.UNHEALTHY
            message = f"Critical: Only {free_gb:.1f}GB free"
        elif free_gb < 5:
            status = HealthStatus.DEGRADED
            message = f"Warning: {free_gb:.1f}GB free"
        else:
            status = HealthStatus.HEALTHY
            message = f"{free_gb:.1f}GB free ({used_percent:.1f}% used)"

        return ComponentHealth(
            name="disk_space",
            status=status,
            message=message,
            last_check=datetime.now().isoformat(),
            details={
                "free_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 2)
            }
        )

    def to_dict(self, health: SystemHealth) -> Dict:
        """SystemHealth를 딕셔너리로 변환"""
        return {
            "overall_status": health.overall_status.value,
            "timestamp": health.timestamp,
            "version": health.version,
            "uptime_seconds": health.uptime_seconds,
            "components": {
                name: {
                    "name": comp.name,
                    "status": comp.status.value,
                    "message": comp.message,
                    "last_check": comp.last_check,
                    "details": comp.details
                }
                for name, comp in health.components.items()
            }
        }


async def get_health_status() -> Dict:
    """헬스 상태 조회 (API용)"""
    checker = HealthChecker()
    health = await checker.run_all_checks()
    return checker.to_dict(health)


# CLI 실행
if __name__ == "__main__":
    import sys

    async def main():
        checker = HealthChecker()
        health = await checker.run_all_checks()
        result = checker.to_dict(health)

        # 출력
        print("\n" + "=" * 50)
        print("        SunFlow Health Check Report")
        print("=" * 50)
        print(f"\nOverall Status: {result['overall_status'].upper()}")
        print(f"Timestamp: {result['timestamp'][:19]}")
        print(f"Uptime: {result['uptime_seconds']:.0f} seconds")
        print(f"Version: {result['version']}")
        print("\n" + "-" * 50)
        print("Components:")
        print("-" * 50)

        status_icons = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓"
        }

        for name, comp in result["components"].items():
            icon = status_icons.get(comp["status"], "❓")
            print(f"  {icon} {name}: {comp['message']}")

        print("\n" + "=" * 50)

        # JSON 출력 옵션
        if "--json" in sys.argv:
            print("\nJSON Output:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(main())
