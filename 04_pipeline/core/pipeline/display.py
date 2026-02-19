"""
# ============================================================
# 🎨 Pipeline Display - 팀 스타일 CLI 출력
# ============================================================
#
# 📋 이 파일의 역할:
#    파이프라인 실행 상태를 팀처럼 보여줘요!
#    - 6명의 에이전트가 순차적으로 작업
#    - 데이터가 다음 에이전트로 전달되는 흐름 표시
#
# 💡 에이전트 팀:
#    👔 김차장 → ✍️ 김작가 → 🎨 이작가 →
#    ✏️ 박편집 → 🔍 박과장 → 📤 김대리
#
# Author: 최기술 대리
# ============================================================
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# ============================================================
# 📦 rich 라이브러리 불러오기
# ============================================================
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.box import ROUNDED, DOUBLE, HEAVY
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class StepStatus(Enum):
    """단계 상태"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentInfo:
    """
    에이전트 정보

    각 에이전트의 이름, 역할, 이모지 등을 저장해요.
    """
    id: str              # 에이전트 ID (예: "planner")
    name: str            # 한글 이름 (예: "김차장")
    role: str            # 역할 (예: "기획")
    icon: str            # 이모지
    output_desc: str     # 출력 설명 (예: "슬라이드 데이터")
    status: StepStatus = StepStatus.PENDING
    elapsed: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None


class PipelineDisplay:
    """
    ╔════════════════════════════════════════════════════════╗
    ║  🎨 팀 스타일 파이프라인 시각화                          ║
    ╠════════════════════════════════════════════════════════╣
    ║  6명의 에이전트가 팀처럼 협업하는 모습을 보여줘요!        ║
    ║                                                        ║
    ║  👔 김차장 → ✍️ 김작가 → 🎨 이작가 →                    ║
    ║  ✏️ 박편집 → 🔍 박과장 → 📤 김대리                      ║
    ╚════════════════════════════════════════════════════════╝
    """

    # --------------------------------------------------------
    # 📋 에이전트 팀 정의
    #
    # 각 에이전트의 정보를 정의해요.
    # id는 기존 코드와 매핑됩니다.
    # --------------------------------------------------------
    AGENTS = [
        AgentInfo("planner", "김차장", "기획", "👔", "슬라이드 데이터"),
        AgentInfo("prompt", "김작가", "프롬프트", "✍️", "프롬프트"),
        AgentInfo("image", "이작가", "이미지", "🎨", "이미지 경로"),
        AgentInfo("overlay", "박편집", "텍스트합성", "✏️", "최종 이미지"),
        AgentInfo("qa", "박과장", "검수", "🔍", "승인된 이미지"),
        AgentInfo("caption", "이카피", "캡션", "📝", "캡션+해시태그"),
        AgentInfo("publish", "김대리", "업로드", "📤", "게시 완료"),
    ]

    def __init__(self, topic: str):
        """
        초기화

        Args:
            topic: 주제 (예: "apple", "cherry")
        """
        self.topic = topic
        # 에이전트 정보 복사 (원본 변경 방지)
        self.agents = [
            AgentInfo(a.id, a.name, a.role, a.icon, a.output_desc)
            for a in self.AGENTS
        ]
        self.start_time = None
        self.current_agent_idx = 0

        # rich 콘솔 초기화
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    # ============================================================
    # 🎨 상태 아이콘 가져오기
    # ============================================================
    def _get_status_icon(self, status: StepStatus) -> str:
        """상태에 맞는 이모지 반환"""
        icons = {
            StepStatus.PENDING: "⏸️",
            StepStatus.RUNNING: "⏳",
            StepStatus.SUCCESS: "✅",
            StepStatus.FAILED: "❌",
            StepStatus.SKIPPED: "⏭️",
        }
        return icons.get(status, "?")

    # ============================================================
    # ⏱️ 시간 포맷팅
    # ============================================================
    def _format_time(self, seconds: float) -> str:
        """초를 읽기 좋은 형식으로 변환"""
        if seconds < 60:
            return f"{seconds:.1f}초"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}분 {secs}초"

    def _get_elapsed_str(self) -> str:
        """경과 시간 문자열"""
        if not self.start_time:
            return "0초"
        elapsed = time.time() - self.start_time
        return self._format_time(elapsed)

    # ============================================================
    # 🚀 파이프라인 시작
    # ============================================================
    def start(self):
        """파이프라인 시작 화면 표시"""
        self.start_time = time.time()

        if not RICH_AVAILABLE:
            print(f"\n{'╭' + '─'*50 + '╮'}")
            print(f"│  🌞 Project Sunshine - {self.topic:<25} │")
            print(f"{'╰' + '─'*50 + '╯'}\n")
            return

        # --------------------------------------------------------
        # 🎨 Rich 헤더 출력
        # --------------------------------------------------------
        self.console.print()

        # 메인 헤더 패널
        header = Panel(
            f"[bold yellow]🌞 Project Sunshine[/bold yellow]\n"
            f"[cyan]Topic: {self.topic}[/cyan]",
            box=ROUNDED,
            border_style="yellow",
            padding=(0, 2)
        )
        self.console.print(header)
        self.console.print()

    # ============================================================
    # 📝 에이전트 상태 업데이트
    # ============================================================
    def update_step(self, step_name: str, status: StepStatus, progress: int = 0,
                    elapsed: float = 0.0, result: str = None, error: str = None):
        """에이전트 정보 업데이트"""
        for agent in self.agents:
            if agent.id == step_name:
                agent.status = status
                agent.elapsed = elapsed
                agent.result = result
                agent.error = error
                break

    # ============================================================
    # ▶️ 에이전트 작업 시작
    # ============================================================
    def start_step(self, step_name: str):
        """에이전트 작업 시작 표시"""
        self.update_step(step_name, StepStatus.RUNNING, 0)
        agent = next((a for a in self.agents if a.id == step_name), None)

        if agent:
            if not RICH_AVAILABLE:
                print(f"\n{agent.icon} {agent.name}({agent.role})")
                print(f"└─ 작업 중...")
            else:
                self.console.print()
                self.console.print(
                    f"[bold]{agent.icon} {agent.name}[/bold]"
                    f"[dim]({agent.role})[/dim]"
                )
                self.console.print(
                    f"[dim]└─ 작업 중...[/dim]"
                )

    # ============================================================
    # ✅ 에이전트 작업 완료
    # ============================================================
    def complete_step(self, step_name: str, elapsed: float, result: str = None, success: bool = True):
        """에이전트 작업 완료 표시"""
        status = StepStatus.SUCCESS if success else StepStatus.FAILED
        self.update_step(step_name, status, 100, elapsed, result)

        agent = next((a for a in self.agents if a.id == step_name), None)
        next_agent = None

        if agent:
            idx = self.agents.index(agent)
            if idx < len(self.agents) - 1:
                next_agent = self.agents[idx + 1]

        if agent:
            time_str = self._format_time(elapsed)
            status_icon = self._get_status_icon(status)

            if not RICH_AVAILABLE:
                # 단순 텍스트 출력
                result_str = f" ({result})" if result else ""
                status_text = "완료" if success else "실패"
                print(f"\r{agent.icon} {agent.name}({agent.role})")
                print(f"└─ {status_icon} {status_text}{result_str} [{time_str}]")

                # 다음 에이전트로 데이터 전달 표시
                if next_agent and success:
                    print(f"    ↓ {agent.output_desc} 전달")
            else:
                # Rich 출력
                if success:
                    color = "green"
                    status_text = "완료"
                else:
                    color = "red"
                    status_text = "실패"

                result_str = f" ({result})" if result else ""

                # 이전 줄 덮어쓰기 효과 (커서 위로)
                self.console.print(
                    f"\r[bold]{agent.icon} {agent.name}[/bold]"
                    f"[dim]({agent.role})[/dim]"
                )
                self.console.print(
                    f"└─ [{color}]{status_icon} {status_text}[/{color}]"
                    f"[dim]{result_str}[/dim] "
                    f"[yellow][{time_str}][/yellow]"
                )

                # 다음 에이전트로 데이터 전달 표시
                if next_agent and success:
                    self.console.print(
                        f"    [dim]↓ {agent.output_desc} 전달[/dim]"
                    )

    # ============================================================
    # ❌ 에이전트 작업 실패
    # ============================================================
    def fail_step(self, step_name: str, elapsed: float, error: str):
        """에이전트 작업 실패 표시"""
        self.update_step(step_name, StepStatus.FAILED, 0, elapsed, error=error)
        self.complete_step(step_name, elapsed, f"Error: {error}", success=False)

    # ============================================================
    # ⏭️ 에이전트 작업 건너뜀
    # ============================================================
    def skip_step(self, step_name: str):
        """에이전트 작업 건너뜀 표시"""
        self.update_step(step_name, StepStatus.SKIPPED, 0)
        agent = next((a for a in self.agents if a.id == step_name), None)

        if agent:
            if not RICH_AVAILABLE:
                print(f"\n{agent.icon} {agent.name}({agent.role})")
                print(f"└─ ⏭️ 건너뜀")
            else:
                self.console.print()
                self.console.print(
                    f"[dim]{agent.icon} {agent.name}({agent.role})[/dim]"
                )
                self.console.print(
                    f"[dim]└─ ⏭️ 건너뜀[/dim]"
                )

    # ============================================================
    # 📊 최종 요약 표시
    # ============================================================
    def show_summary(self, results: Dict):
        """완료 후 요약 정보 표시"""
        total_time = time.time() - self.start_time if self.start_time else 0
        success = results.get("success", False)

        if not RICH_AVAILABLE:
            self._show_summary_simple(results, total_time, success)
        else:
            self._show_summary_rich(results, total_time, success)

    def _show_summary_simple(self, results: Dict, total_time: float, success: bool):
        """단순 텍스트 요약"""
        print(f"\n{'╭' + '─'*50 + '╮'}")
        if success:
            print(f"│  ✅ 파이프라인 완료! 총 소요시간: {self._format_time(total_time):<12} │")
        else:
            print(f"│  ❌ 파이프라인 실패!                              │")
        print(f"{'╰' + '─'*50 + '╯'}")

        # 에이전트별 결과
        print("\n📊 에이전트별 결과:")
        for agent in self.agents:
            icon = self._get_status_icon(agent.status)
            result = agent.result or ""
            time_str = f"[{self._format_time(agent.elapsed)}]" if agent.elapsed > 0 else ""
            print(f"  {agent.icon} {agent.name:<6} {icon} {result} {time_str}")

        # 출력 경로
        if "results" in results:
            overlay_data = results["results"].get("overlay", {})
            if overlay_data.get("output_dir"):
                print(f"\n📁 Output: {overlay_data.get('output_dir')}")

            publish_data = results["results"].get("publish", {})
            if publish_data and not publish_data.get("skipped"):
                instagram = publish_data.get("publish_results", {}).get("instagram", {})
                if instagram.get("permalink"):
                    print(f"🔗 Instagram: {instagram.get('permalink')}")

        print()

    def _show_summary_rich(self, results: Dict, total_time: float, success: bool):
        """Rich 요약 표시"""
        self.console.print()

        # --------------------------------------------------------
        # 🎉 결과 헤더
        # --------------------------------------------------------
        if success:
            header_text = (
                f"[bold green]✅ 파이프라인 완료![/bold green]\n"
                f"[dim]총 소요시간: {self._format_time(total_time)}[/dim]"
            )
            border_style = "green"
        else:
            header_text = "[bold red]❌ 파이프라인 실패![/bold red]"
            border_style = "red"

        header = Panel(
            header_text,
            box=ROUNDED,
            border_style=border_style,
            padding=(0, 2)
        )
        self.console.print(header)
        self.console.print()

        # --------------------------------------------------------
        # 📊 에이전트별 결과
        # --------------------------------------------------------
        self.console.print("[bold]📊 에이전트별 결과[/bold]")
        self.console.print()

        for i, agent in enumerate(self.agents):
            icon = self._get_status_icon(agent.status)
            prefix = "└──" if i == len(self.agents) - 1 else "├──"

            # 상태별 색상
            if agent.status == StepStatus.SUCCESS:
                color = "green"
            elif agent.status == StepStatus.FAILED:
                color = "red"
            elif agent.status == StepStatus.SKIPPED:
                color = "dim"
            else:
                color = "white"

            result = agent.result or ""
            time_str = f"[yellow][{self._format_time(agent.elapsed)}][/yellow]" if agent.elapsed > 0 else ""

            self.console.print(
                f"   {prefix} {agent.icon} [{color}]{agent.name:<6}[/{color}] "
                f"{icon} [dim]{result}[/dim] {time_str}"
            )

        self.console.print()

        # --------------------------------------------------------
        # 📁 출력 정보
        # --------------------------------------------------------
        if "results" in results:
            overlay_data = results["results"].get("overlay", {})
            publish_data = results["results"].get("publish", {})

            info_lines = []

            if overlay_data.get("output_dir"):
                info_lines.append(f"[bold]📁 Output[/bold]  {overlay_data.get('output_dir')}")

            if publish_data and not publish_data.get("skipped"):
                instagram = publish_data.get("publish_results", {}).get("instagram", {})
                if instagram.get("success"):
                    if instagram.get("permalink"):
                        info_lines.append(
                            f"[bold]🔗 Instagram[/bold]  {instagram.get('permalink')}"
                        )
                    if instagram.get("post_id"):
                        info_lines.append(
                            f"[bold]📱 Post ID[/bold]  {instagram.get('post_id')}"
                        )

            if info_lines:
                info_panel = Panel(
                    "\n".join(info_lines),
                    box=ROUNDED,
                    border_style="blue",
                    title="📋 결과 정보",
                    title_align="left"
                )
                self.console.print(info_panel)
                self.console.print()


# ============================================================
# 📤 업로드 진행률 표시 클래스 (유지)
# ============================================================
class UploadProgressDisplay:
    """업로드 진행률을 예쁘게 표시하는 클래스"""

    def __init__(self, title: str, total: int):
        self.title = title
        self.total = total
        self.current = 0
        self.console = Console() if RICH_AVAILABLE else None

    def __enter__(self):
        if RICH_AVAILABLE:
            self.console.print()
            self.console.print(f"[bold blue]📤 {self.title}[/bold blue]")
            self.console.print("[dim]" + "─" * 50 + "[/dim]")
        else:
            print(f"\n📤 {self.title}")
            print("-" * 50)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if RICH_AVAILABLE:
            self.console.print("[dim]" + "─" * 50 + "[/dim]")
            self.console.print(
                f"[green]✅ 완료![/green] "
                f"[dim]{self.current}/{self.total} 파일[/dim]"
            )
            self.console.print()
        else:
            print("-" * 50)
            print(f"✅ 완료! {self.current}/{self.total} 파일")
            print()

    def update(self, file_name: str, success: bool = True):
        """파일 업로드 상태 업데이트"""
        self.current += 1
        progress = int((self.current / self.total) * 100)
        bar = "█" * (progress // 5) + "░" * (20 - progress // 5)

        if RICH_AVAILABLE:
            status = "[green]✅[/green]" if success else "[red]❌[/red]"
            self.console.print(
                f"   {status} {file_name:<30} "
                f"[dim]{bar}[/dim] {self.current}/{self.total}"
            )
        else:
            status = "✅" if success else "❌"
            print(f"   {status} {file_name:<30} {bar} {self.current}/{self.total}")
