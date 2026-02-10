#!/usr/bin/env python3
"""
📝 포워딩 로거 (업무 13번)

김부장 포워딩 요청 로그
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs" / "forwards"


def log_forward(
    from_agent: str,
    to_agent: str,
    task_type: str,
    content: dict,
    priority: str = "normal"
):
    """
    포워딩 요청 로그

    Args:
        from_agent: 요청자 (예: "김부장")
        to_agent: 수신자 (예: "김과장")
        task_type: 작업 유형 (예: "IMAGE_GENERATION")
        content: 작업 내용
        priority: 우선순위 (low, normal, high, urgent)
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y%m%d")
    time_str = timestamp.strftime("%H%M%S")

    log_entry = {
        "timestamp": timestamp.isoformat(),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "task_type": task_type,
        "priority": priority,
        "content": content,
        "status": "pending"
    }

    # 날짜별 로그 파일
    log_file = LOG_DIR / f"forward_{date_str}.jsonl"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"📝 포워딩 로그: {from_agent} → {to_agent} ({task_type})")

    return log_entry


def get_pending_forwards(agent: str = None) -> list:
    """
    대기 중인 포워딩 요청 조회

    Args:
        agent: 특정 에이전트만 조회 (None이면 전체)
    """
    if not LOG_DIR.exists():
        return []

    pending = []
    today = datetime.now().strftime("%Y%m%d")
    log_file = LOG_DIR / f"forward_{today}.jsonl"

    if not log_file.exists():
        return []

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("status") == "pending":
                    if agent is None or entry.get("to_agent") == agent:
                        pending.append(entry)
            except json.JSONDecodeError:
                continue

    return pending


def mark_completed(timestamp: str):
    """포워딩 요청 완료 처리"""
    # 구현 필요시 추가
    pass


def format_forward_message(text: str, user_name: str = "PD") -> str:
    """
    김부장 포워딩 메시지 포맷

    Args:
        text: 원본 텍스트
        user_name: 사용자 이름

    Returns:
        포맷된 메시지
    """
    return f"""
📨 <b>김부장에게 전달됨</b>

발신: {user_name}
내용: {text}

━━━━━━━━━━━━━━━━━━
명령어로 인식되지 않은 메시지입니다.
슬래시 명령어(예: /생성, /승인)를 사용해 주세요.
"""


# 테스트
if __name__ == "__main__":
    # 테스트 로그
    log_forward(
        from_agent="김부장",
        to_agent="김과장",
        task_type="IMAGE_GENERATION",
        content={"food_id": "potato", "slides": [1, 2, 3]},
        priority="high"
    )

    # 대기 중인 포워딩 확인
    pending = get_pending_forwards()
    print(f"\n대기 중: {len(pending)}개")
