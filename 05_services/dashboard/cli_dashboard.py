#!/usr/bin/env python3
"""
Project Sunshine - CLI Dashboard (Rich)
터미널에서 파이프라인 진행 상태를 실시간으로 확인

실행: python dashboard/cli_dashboard.py
"""

import json
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.align import Align

# 상수
STATUS_FILE = Path(__file__).parent / "status.json"
REFRESH_RATE = 1  # 초

# 상태별 스타일
STATUS_STYLES = {
    "done": ("●", "green", "완료"),
    "running": ("▶", "yellow", "진행"),
    "pending": ("○", "dim", "대기"),
    "error": ("✗", "red", "에러"),
}

# 에이전트 이모지
AGENT_EMOJI = {
    "김차장": "👔", "최검증": "🔍", "김작가": "✍️",
    "이작가": "🎨", "박편집": "🎬", "박과장": "📋",
    "이카피": "📝", "김대리": "📤", "정분석": "📊"
}


def load_status() -> dict:
    """상태 파일 로드"""
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "topic": None,
        "current_step": 0,
        "total_progress": 0,
        "steps": [],
        "errors": []
    }


def format_duration(seconds: float) -> str:
    """시간 포맷팅"""
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{int(seconds)}초"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}분 {secs}초"


def create_pipeline_display(status: dict) -> Table:
    """파이프라인 진행 상태 테이블"""
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 1),
        expand=True
    )

    steps = status.get("steps", [])

    # 진행 바 라인
    progress_line = ""
    for i, step in enumerate(steps):
        s = step.get("status", "pending")
        symbol, color, _ = STATUS_STYLES.get(s, ("○", "dim", "대기"))

        if i == 0:
            progress_line += f"[{color}]{symbol}[/{color}]"
        else:
            # 연결선
            prev_status = steps[i-1].get("status", "pending")
            line_color = "green" if prev_status == "done" else "dim"
            progress_line += f"[{line_color}]━━━[/{line_color}][{color}]{symbol}[/{color}]"

    table.add_row(progress_line)

    # 이름 라인
    names_line = ""
    for i, step in enumerate(steps):
        name = step.get("name", "?")[:2]  # 2글자만
        s = step.get("status", "pending")
        _, color, _ = STATUS_STYLES.get(s, ("○", "dim", "대기"))

        if i == 0:
            names_line += f"[{color}]{name}[/{color}]"
        else:
            names_line += f"    [{color}]{name}[/{color}]"

    table.add_row(names_line)

    return table


def create_current_step_panel(status: dict) -> Panel:
    """현재 단계 패널"""
    steps = status.get("steps", [])
    current_idx = status.get("current_step", 0)

    if current_idx > 0 and current_idx <= len(steps):
        step = steps[current_idx - 1]
        name = step.get("name", "?")
        role = step.get("role", "?")
        progress = step.get("progress", "")
        emoji = AGENT_EMOJI.get(name, "🐕")

        content = f"{emoji} [bold yellow]{name}[/] - {role}"
        if progress:
            content += f" ({progress})"

        return Panel(
            content,
            title="[yellow]현재 진행[/]",
            border_style="yellow"
        )
    elif status.get("result"):
        return Panel(
            "[green]✅ 파이프라인 완료![/]",
            title="[green]완료[/]",
            border_style="green"
        )
    else:
        return Panel(
            "[dim]대기 중...[/]",
            title="상태",
            border_style="dim"
        )


def create_progress_bar(status: dict) -> Progress:
    """진행률 바"""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        expand=True
    )

    total = len(status.get("steps", [])) or 9
    completed = sum(1 for s in status.get("steps", []) if s.get("status") == "done")

    task = progress.add_task("전체 진행", total=total, completed=completed)

    return progress


def create_time_info(status: dict) -> Text:
    """시간 정보"""
    started_at = status.get("started_at")
    if started_at:
        try:
            start_time = datetime.fromisoformat(started_at)
            elapsed = (datetime.now() - start_time).total_seconds()
            elapsed_str = format_duration(elapsed)
            return Text(f"소요 시간: {elapsed_str}", style="cyan")
        except:
            pass
    return Text("대기 중", style="dim")


def create_error_panel(status: dict) -> Panel:
    """에러 패널"""
    errors = status.get("errors", [])
    if errors:
        error_text = "\n".join(f"• {e}" for e in errors[-3:])
        return Panel(
            f"[red]{error_text}[/]",
            title="[red]⚠️ 에러[/]",
            border_style="red"
        )
    return None


def create_dashboard(status: dict) -> Panel:
    """전체 대시보드"""
    topic = status.get("topic", "없음")
    topic_display = f"[cyan bold]{topic.upper()}[/]" if topic else "[dim]없음[/]"

    # 메인 레이아웃
    layout = Layout()

    # 헤더
    header = Text()
    header.append("🌞 Project Sunshine", style="bold yellow")
    header.append("                    ", style="")
    header.append(f"[{topic_display}]", style="")

    # 파이프라인 진행도
    pipeline = create_pipeline_display(status)

    # 현재 단계
    current_panel = create_current_step_panel(status)

    # 시간 정보
    time_info = create_time_info(status)

    # 진행률
    steps = status.get("steps", [])
    total = len(steps) or 9
    completed = sum(1 for s in steps if s.get("status") == "done")
    progress_pct = int((completed / total) * 100)

    # 프로그레스 바 (텍스트)
    bar_width = 40
    filled = int(bar_width * completed / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    progress_text = f"[green]{bar}[/]  {progress_pct}%"

    # 조합
    content = Table.grid(padding=(1, 0))
    content.add_row(Align.center(header))
    content.add_row("")
    content.add_row(Align.center(pipeline))
    content.add_row("")
    content.add_row(current_panel)
    content.add_row("")
    content.add_row(Align.center(Text(progress_text)))
    content.add_row(Align.center(time_info))

    # 에러 표시
    error_panel = create_error_panel(status)
    if error_panel:
        content.add_row("")
        content.add_row(error_panel)

    return Panel(
        content,
        border_style="blue",
        padding=(1, 2)
    )


def main():
    """메인 실행"""
    console = Console()

    console.clear()
    console.print("[bold yellow]🌞 Project Sunshine Dashboard[/]")
    console.print("[dim]Ctrl+C로 종료[/]\n")

    try:
        with Live(console=console, refresh_per_second=1, screen=True) as live:
            while True:
                status = load_status()
                dashboard = create_dashboard(status)
                live.update(dashboard)
                time.sleep(REFRESH_RATE)

    except KeyboardInterrupt:
        console.print("\n[yellow]대시보드 종료[/]")


if __name__ == "__main__":
    main()
