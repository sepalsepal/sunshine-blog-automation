#!/usr/bin/env python3
"""
터미널 기반 파이프라인 상태 표시기
WO-DASHBOARD-002 + WO-AGENT-001 (서브태스크 지원)
"""

# ANSI 색상 코드
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"

# 상태 아이콘 + 색상 매핑
STATUS_MAP = {
    "완료": (f"{Colors.GREEN}✅ 완료{Colors.RESET}", Colors.GREEN),
    "진행중": (f"{Colors.BLUE}🔄 진행중{Colors.RESET}", Colors.BLUE),
    "실패": (f"{Colors.RED}❌ 실패{Colors.RESET}", Colors.RED),
    "부분실패": (f"{Colors.YELLOW}⚠️ 부분실패{Colors.RESET}", Colors.YELLOW),
    "대기": (f"{Colors.GRAY}⏸️ 대기{Colors.RESET}", Colors.GRAY),
}

# 서브태스크 상태 아이콘
SUBTASK_STATUS = {
    "완료": f"{Colors.GREEN}✅{Colors.RESET}",
    "실패": f"{Colors.RED}❌{Colors.RESET}",
    "진행중": f"{Colors.BLUE}🔄{Colors.RESET}",
    "대기": f"{Colors.GRAY}⏸️{Colors.RESET}",
}

# 6개 고정 노드 템플릿 (서브태스크 포함)
DEFAULT_NODES = [
    {
        "name": "입력/기획",
        "agent": "김차장",
        "status": "대기",
        "subtasks": [
            {"id": "1-1", "name": "입력 파싱", "status": "대기"},
            {"id": "1-2", "name": "데이터 검증", "status": "대기"},
            {"id": "1-3", "name": "기획서 생성", "status": "대기"},
        ]
    },
    {
        "name": "팩트체크",
        "agent": "최검증",
        "status": "대기",
        "subtasks": [
            {"id": "2-1", "name": "안전도 확인", "status": "대기"},
            {"id": "2-2", "name": "독성 정보 검증", "status": "대기"},
            {"id": "2-3", "name": "출처 확인", "status": "대기"},
        ]
    },
    {
        "name": "텍스트작성",
        "agent": "김작가",
        "status": "대기",
        "subtasks": [
            {"id": "3-1", "name": "인스타 캡션", "status": "대기"},
            {"id": "3-2", "name": "쓰레드 캡션", "status": "대기"},
            {"id": "3-3", "name": "블로그 본문", "status": "대기"},
        ]
    },
    {
        "name": "이미지제작",
        "agent": "이작가",
        "status": "대기",
        "subtasks": [
            {"id": "4-1", "name": "표지 생성", "status": "대기"},
            {"id": "4-2", "name": "슬라이드 생성", "status": "대기"},
            {"id": "4-3", "name": "인포그래픽", "status": "대기"},
            {"id": "4-4", "name": "클린 이미지", "status": "대기"},
        ]
    },
    {
        "name": "검수",
        "agent": "박과장",
        "status": "대기",
        "subtasks": [
            {"id": "5-1", "name": "텍스트 검수", "status": "대기"},
            {"id": "5-2", "name": "이미지 검수", "status": "대기"},
            {"id": "5-3", "name": "규칙 검증", "status": "대기"},
        ]
    },
    {
        "name": "게시",
        "agent": "김대리",
        "status": "대기",
        "subtasks": [
            {"id": "6-1", "name": "인스타 게시", "status": "대기"},
            {"id": "6-2", "name": "쓰레드 게시", "status": "대기"},
            {"id": "6-3", "name": "블로그 게시", "status": "대기"},
        ]
    },
]


def calculate_node_status(node: dict) -> tuple:
    """서브태스크 기반으로 노드 상태 계산"""
    subtasks = node.get("subtasks", [])
    if not subtasks:
        return node.get("status", "대기"), None

    completed = sum(1 for st in subtasks if st.get("status") == "완료")
    failed = sum(1 for st in subtasks if st.get("status") == "실패")
    total = len(subtasks)

    if failed > 0 and completed > 0:
        return "부분실패", f"({completed}/{total})"
    elif failed > 0:
        return "실패", None
    elif completed == total:
        return "완료", None
    elif completed > 0:
        return "진행중", f"({completed}/{total})"
    else:
        return "대기", None


def print_subtasks(subtasks: list, indent: str = "    "):
    """서브태스크 출력"""
    for i, st in enumerate(subtasks):
        is_last = (i == len(subtasks) - 1)
        prefix = "└─" if is_last else "├─"
        status_icon = SUBTASK_STATUS.get(st.get("status", "대기"), "⏸️")
        reason = st.get("reason", "")
        reason_text = f' → "{reason}"' if reason else ""

        print(f"{indent}{prefix} {st['id']} {st['name']}  {status_icon}{reason_text}")


def print_pipeline_status(status: dict, show_subtasks: bool = True):
    """
    파이프라인 상태를 터미널에 출력

    status = {
        "content": "사과",
        "nodes": [
            {
                "name": "텍스트작성",
                "agent": "김작가",
                "status": "부분실패",
                "subtasks": [
                    {"id": "3-1", "name": "인스타 캡션", "status": "완료"},
                    {"id": "3-2", "name": "쓰레드 캡션", "status": "실패", "reason": "안전도 톤 불일치"},
                    {"id": "3-3", "name": "블로그 본문", "status": "완료"},
                ]
            },
            ...
        ]
    }
    """
    content_name = status.get("content", "콘텐츠")
    nodes = status.get("nodes", DEFAULT_NODES)

    # 진행률 계산
    completed = 0
    has_failure = False
    has_partial = False
    has_running = False

    for n in nodes:
        node_status, _ = calculate_node_status(n)
        if node_status == "완료":
            completed += 1
        elif node_status == "실패":
            has_failure = True
        elif node_status == "부분실패":
            has_partial = True
        elif node_status == "진행중":
            has_running = True

    total = len(nodes)

    # 전체 상태 결정
    if has_failure:
        overall_status = f"{Colors.RED}❌ 실패{Colors.RESET}"
    elif has_partial:
        overall_status = f"{Colors.YELLOW}⚠️ 부분실패{Colors.RESET}"
    elif completed == total:
        overall_status = f"{Colors.GREEN}✅ 완료{Colors.RESET}"
    elif has_running:
        overall_status = f"{Colors.BLUE}🔄 진행중{Colors.RESET}"
    else:
        overall_status = f"{Colors.GRAY}⏸️ 대기{Colors.RESET}"

    # 헤더
    print()
    print("━" * 60)
    print(f"{Colors.BOLD}🎬 {content_name} 콘텐츠 진행 현황{Colors.RESET}")
    print("━" * 60)
    print()

    # 노드 출력
    for i, node in enumerate(nodes):
        node_num = i + 1
        name = node.get("name", f"노드{node_num}")
        agent = node.get("agent", "담당자")
        reason = node.get("reason", "")
        attempts = node.get("attempts", 0)
        subtasks = node.get("subtasks", [])

        # 서브태스크 기반 상태 계산
        node_status, progress = calculate_node_status(node)

        # 상태 텍스트 생성
        status_text, color = STATUS_MAP.get(node_status, (node_status, Colors.RESET))

        # 부분실패/진행중 시 진행률 표시
        if progress:
            status_text = status_text.replace(Colors.RESET, f" {progress}{Colors.RESET}")

        # 실패 시 횟수 및 원인 추가
        if node_status == "실패" and attempts > 0:
            status_text = f"{Colors.RED}❌ 실패({attempts}회){Colors.RESET}"
        if reason:
            status_text += f' → "{reason}"'

        # 노드 라인 출력
        print(f"[{node_num}] {name:12} │ {agent:6} │ {status_text}")

        # 서브태스크 출력 (show_subtasks=True이고 부분실패/실패/진행중일 때)
        if show_subtasks and subtasks and node_status in ("부분실패", "실패", "진행중"):
            print_subtasks(subtasks)

        # 화살표 (마지막 노드 제외)
        if i < len(nodes) - 1:
            print("        ↓")

    # 푸터
    print()
    print("━" * 60)
    print(f"진행: {completed}/{total} 완료 │ 상태: {overall_status}")
    print("━" * 60)
    print()


def create_pipeline_status(content: str, node_updates: dict = None) -> dict:
    """
    파이프라인 상태 객체 생성

    node_updates = {
        1: {"status": "완료"},
        3: {
            "subtasks": [
                {"id": "3-1", "status": "완료"},
                {"id": "3-2", "status": "실패", "reason": "안전도 톤 불일치"},
                {"id": "3-3", "status": "완료"},
            ]
        },
    }
    """
    import copy

    status = {
        "content": content,
        "nodes": copy.deepcopy(DEFAULT_NODES)
    }

    if node_updates:
        for node_num, updates in node_updates.items():
            if 1 <= node_num <= len(status["nodes"]):
                node = status["nodes"][node_num - 1]

                # 서브태스크 업데이트
                if "subtasks" in updates:
                    for st_update in updates["subtasks"]:
                        st_id = st_update.get("id")
                        for st in node.get("subtasks", []):
                            if st["id"] == st_id:
                                st.update(st_update)
                                break

                # 일반 필드 업데이트
                for key, value in updates.items():
                    if key != "subtasks":
                        node[key] = value

    return status


def update_node_status(status: dict, node_num: int, new_status: str,
                       reason: str = None, attempts: int = None) -> dict:
    """단일 노드 상태 업데이트"""
    if 1 <= node_num <= len(status["nodes"]):
        node = status["nodes"][node_num - 1]
        node["status"] = new_status
        if reason:
            node["reason"] = reason
        if attempts is not None:
            node["attempts"] = attempts
    return status


def update_subtask_status(status: dict, node_num: int, subtask_id: str,
                          new_status: str, reason: str = None) -> dict:
    """서브태스크 상태 업데이트"""
    if 1 <= node_num <= len(status["nodes"]):
        node = status["nodes"][node_num - 1]
        for st in node.get("subtasks", []):
            if st["id"] == subtask_id:
                st["status"] = new_status
                if reason:
                    st["reason"] = reason
                break
    return status


def rerun_subtask(status: dict, subtask_id: str) -> dict:
    """서브태스크 재실행 (상태를 '진행중'으로 변경)"""
    for node in status["nodes"]:
        for st in node.get("subtasks", []):
            if st["id"] == subtask_id:
                st["status"] = "진행중"
                st.pop("reason", None)
                print(f"{Colors.CYAN}🔄 재실행: {subtask_id} {st['name']}{Colors.RESET}")
                return status
    print(f"{Colors.RED}❌ 서브태스크를 찾을 수 없습니다: {subtask_id}{Colors.RESET}")
    return status


# 테스트/데모
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("터미널 파이프라인 상태 표시기 데모 (서브태스크 지원)")
    print("=" * 60)

    # 데모 1: 부분실패 (서브태스크 표시)
    print("\n📌 데모 1: 부분실패 상태 (서브태스크 표시)")
    demo1 = create_pipeline_status("사과", {
        1: {"subtasks": [
            {"id": "1-1", "status": "완료"},
            {"id": "1-2", "status": "완료"},
            {"id": "1-3", "status": "완료"},
        ]},
        2: {"subtasks": [
            {"id": "2-1", "status": "완료"},
            {"id": "2-2", "status": "완료"},
            {"id": "2-3", "status": "완료"},
        ]},
        3: {"subtasks": [
            {"id": "3-1", "status": "완료"},
            {"id": "3-2", "status": "실패", "reason": "안전도 톤 불일치"},
            {"id": "3-3", "status": "완료"},
        ]},
    })
    print_pipeline_status(demo1)

    # 데모 2: 진행 중
    print("\n📌 데모 2: 진행 중 (서브태스크 진행 표시)")
    demo2 = create_pipeline_status("감자", {
        1: {"subtasks": [
            {"id": "1-1", "status": "완료"},
            {"id": "1-2", "status": "완료"},
            {"id": "1-3", "status": "완료"},
        ]},
        2: {"subtasks": [
            {"id": "2-1", "status": "완료"},
            {"id": "2-2", "status": "완료"},
            {"id": "2-3", "status": "완료"},
        ]},
        3: {"subtasks": [
            {"id": "3-1", "status": "완료"},
            {"id": "3-2", "status": "완료"},
            {"id": "3-3", "status": "완료"},
        ]},
        4: {"subtasks": [
            {"id": "4-1", "status": "완료"},
            {"id": "4-2", "status": "진행중"},
            {"id": "4-3", "status": "대기"},
            {"id": "4-4", "status": "대기"},
        ]},
    })
    print_pipeline_status(demo2)

    # 데모 3: 서브태스크 재실행
    print("\n📌 데모 3: 서브태스크 재실행")
    demo3 = rerun_subtask(demo1, "3-2")
    print_pipeline_status(demo3)
