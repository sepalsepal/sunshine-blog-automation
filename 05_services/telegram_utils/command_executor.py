#!/usr/bin/env python3
"""
Command Executor - 파싱된 명령 실행

각 intent별 실행 로직:
- REJECT: 콘텐츠 반려 처리
- APPROVE: 콘텐츠 승인 처리
- SYNC: 3중 동기화 실행
- STATUS: 상태별 콘텐츠 목록 조회
- HELP: 도움말 표시
"""

from dataclasses import dataclass
from typing import Optional
from utils.command_parser import ParsedCommand, parse_command
from utils.entity_mapper import get_food_display_name


@dataclass
class ExecutionResult:
    """명령 실행 결과"""
    success: bool
    message: str
    data: Optional[dict] = None


def execute_command(parsed: ParsedCommand) -> ExecutionResult:
    """
    파싱된 명령 실행

    Args:
        parsed: ParsedCommand 객체

    Returns:
        ExecutionResult 객체
    """
    if parsed.intent == "REJECT":
        return execute_reject(parsed.food_id)
    elif parsed.intent == "APPROVE":
        return execute_approve(parsed.food_id)
    elif parsed.intent == "SYNC":
        return execute_sync(parsed.food_id)
    elif parsed.intent == "STATUS":
        return execute_status()
    elif parsed.intent == "HELP":
        return execute_help()
    else:
        return ExecutionResult(
            success=False,
            message="❓ 알 수 없는 명령입니다.\n'/도움' 또는 '도움말'을 입력하세요."
        )


def execute_reject(food_id: Optional[str]) -> ExecutionResult:
    """반려 명령 실행"""
    if not food_id:
        return ExecutionResult(
            success=False,
            message="⚠️ 반려할 콘텐츠를 지정해주세요.\n예: '딸기 반려' 또는 'reject strawberry'"
        )

    try:
        from core.publish_gate import reject_content

        result = reject_content(food_id, rejected_by="PD_telegram")

        if result:
            display_name = get_food_display_name(food_id)
            return ExecutionResult(
                success=True,
                message=f"❌ [{display_name}] 반려 완료",
                data={"food_id": food_id, "action": "rejected"}
            )
        else:
            return ExecutionResult(
                success=False,
                message=f"⚠️ [{food_id}] 반려 실패 - 콘텐츠를 찾을 수 없습니다"
            )
    except ImportError:
        return ExecutionResult(
            success=False,
            message=f"⚠️ publish_gate 모듈을 찾을 수 없습니다"
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            message=f"⚠️ 반려 처리 오류: {str(e)}"
        )


def execute_approve(food_id: Optional[str]) -> ExecutionResult:
    """승인 명령 실행"""
    if not food_id:
        return ExecutionResult(
            success=False,
            message="⚠️ 승인할 콘텐츠를 지정해주세요.\n예: '딸기 승인' 또는 'approve strawberry'"
        )

    try:
        from core.publish_gate import approve_content

        result = approve_content(food_id, approved_by="PD_telegram")

        if result:
            display_name = get_food_display_name(food_id)
            return ExecutionResult(
                success=True,
                message=f"✅ [{display_name}] 승인 완료\n게시 준비가 완료되었습니다.",
                data={"food_id": food_id, "action": "approved"}
            )
        else:
            return ExecutionResult(
                success=False,
                message=f"⚠️ [{food_id}] 승인 실패 - 콘텐츠를 찾을 수 없습니다"
            )
    except ImportError:
        return ExecutionResult(
            success=False,
            message=f"⚠️ publish_gate 모듈을 찾을 수 없습니다"
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            message=f"⚠️ 승인 처리 오류: {str(e)}"
        )


def execute_sync(food_id: Optional[str]) -> ExecutionResult:
    """동기화 명령 실행"""
    try:
        from utils.sync_status import sync_content_status, sync_all_contents

        if food_id:
            # 특정 콘텐츠 동기화
            result = sync_content_status(food_id)
            display_name = get_food_display_name(food_id)

            return ExecutionResult(
                success=True,
                message=(
                    f"🔄 [{display_name}] 동기화 완료\n"
                    f"상태: {result['final_status']}\n"
                    f"출처: {result['source']}"
                ),
                data=result
            )
        else:
            # 전체 동기화
            stats = sync_all_contents()

            return ExecutionResult(
                success=True,
                message=(
                    f"🔄 전체 동기화 완료\n"
                    f"처리: {stats['synced']}개\n"
                    f"이동: {stats['moved_to_posted']}개\n"
                    f"오류: {stats['errors']}개"
                ),
                data=stats
            )

    except Exception as e:
        return ExecutionResult(
            success=False,
            message=f"⚠️ 동기화 오류: {str(e)}"
        )


def execute_status() -> ExecutionResult:
    """상태 조회 명령 실행"""
    try:
        from utils.sync_status import get_contents_by_status

        status_data = get_contents_by_status()

        lines = ["📊 콘텐츠 상태 현황\n"]

        # v3: status_enum 통일
        status_labels = {
            "cover_only": "📁 표지완료",
            "body_ready": "🟡 본문완료",
            "approved": "🟢 승인완료",
            "rejected": "❌ 반려됨",
            "posted": "📤 게시완료"
        }

        for status, label in status_labels.items():
            items = status_data.get(status, [])
            count = len(items)
            lines.append(f"{label}: {count}개")
            if items and status != "published":
                # 게시완료 외에는 목록 표시
                items_str = ", ".join(items[:5])
                if len(items) > 5:
                    items_str += f" 외 {len(items)-5}개"
                lines.append(f"  └ {items_str}")

        return ExecutionResult(
            success=True,
            message="\n".join(lines),
            data=status_data
        )

    except Exception as e:
        return ExecutionResult(
            success=False,
            message=f"⚠️ 상태 조회 오류: {str(e)}"
        )


def execute_help() -> ExecutionResult:
    """도움말 표시"""
    help_text = """📖 명령어 도움말

🔹 승인/반려 명령
  '케일 승인' / 'approve kale'
  '딸기 반려' / 'reject strawberry'

🔹 동기화 명령
  '동기화' - 전체 동기화
  '케일 동기화' - 특정 콘텐츠만

🔹 상태 확인
  '상태' / 'status' - 현황 조회

🔹 기타
  '/생성' - 콘텐츠 목록
  '/신고' - 신고 메뉴
  '도움말' - 이 메시지

💡 한글/영문 모두 가능합니다."""

    return ExecutionResult(
        success=True,
        message=help_text
    )


def process_text_message(text: str) -> ExecutionResult:
    """
    텍스트 메시지 처리 (파싱 + 실행)

    Args:
        text: 사용자 입력 텍스트

    Returns:
        ExecutionResult 객체
    """
    parsed = parse_command(text)

    # 신뢰도가 낮으면 김부장에게 전달
    if parsed.confidence < 0.5:
        return ExecutionResult(
            success=False,
            message=None,  # None이면 김부장에게 전달
            data={"forward_to_manager": True, "raw_text": text}
        )

    return execute_command(parsed)


if __name__ == "__main__":
    # 테스트
    test_cases = [
        "케일 승인",
        "딸기 반려",
        "동기화",
        "상태",
        "도움말",
        "안녕하세요",  # UNKNOWN → 김부장 전달
    ]

    print("Command Executor 테스트:")
    print("=" * 50)
    for text in test_cases:
        print(f"\n입력: '{text}'")
        result = process_text_message(text)
        print(f"  성공: {result.success}")
        print(f"  메시지: {result.message[:50] if result.message else '(김부장 전달)'}...")
