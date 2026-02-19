#!/bin/bash
#
# pre-bash-validate.sh - Bash 명령 실행 전 게시 관련 검증
# WO-036: 기억 의존 제거 - Hook 자동 실행
#
# 트리거: PreToolUse (Bash)
# Exit 0: 진행 허용
# Exit 2: 블로킹 (FAIL)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="$PROJECT_ROOT/config/logs/validator"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# stdin에서 JSON 입력 읽기 (Python으로 파싱 - jq 의존성 제거)
INPUT=$(cat)

# Python으로 명령어 추출
COMMAND=$(echo "$INPUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('tool_input', {}).get('command', ''))" 2>/dev/null)

# 명령어가 없으면 스킵
if [ -z "$COMMAND" ]; then
    exit 0
fi

# 로그 함수
log_result() {
    local validator="$1"
    local result="$2"
    local details="$3"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $validator: $result" >> "$LOG_DIR/validator_$TIMESTAMP.log"
    echo "Command: $COMMAND" >> "$LOG_DIR/validator_$TIMESTAMP.log"
    echo "$details" >> "$LOG_DIR/validator_$TIMESTAMP.log"
    echo "---" >> "$LOG_DIR/validator_$TIMESTAMP.log"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Validator 명령은 재귀 방지를 위해 스킵
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if echo "$COMMAND" | grep -qE "pre_publish_validator|caption_validator|caption_safety_validator"; then
    exit 0
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 게시 관련 명령 감지
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 게시 관련 키워드: publish, 게시, instagram, threads, graph api
if echo "$COMMAND" | grep -qiE "publish|게시|instagram.*post|threads.*post|graph.*api.*publish|carousel.*create"; then
    echo "[Validator] 게시 명령 감지: 전체 Validator 실행" >&2

    # 명령어에서 콘텐츠 번호 추출
    # 1. threads_post.py 8 또는 instagram_post.py 8 형태
    # 2. --number 8 또는 -n 8 형태
    CONTENT_NUM=""
    if echo "$COMMAND" | grep -qE "_post\.py\s+[0-9]+"; then
        CONTENT_NUM=$(echo "$COMMAND" | grep -oE "_post\.py\s+[0-9]+" | grep -oE "[0-9]+")
    elif echo "$COMMAND" | grep -qE "(--number|-n)\s+[0-9]+"; then
        CONTENT_NUM=$(echo "$COMMAND" | grep -oE "(--number|-n)\s+[0-9]+" | grep -oE "[0-9]+")
    fi

    # 플랫폼 감지 (threads vs instagram)
    PLATFORM=""
    if echo "$COMMAND" | grep -qiE "threads"; then
        PLATFORM="--platform threads"
    elif echo "$COMMAND" | grep -qiE "instagram|insta"; then
        PLATFORM="--platform instagram"
    fi

    # 콘텐츠 번호가 있으면 전달
    CONTENT_ARG=""
    if [ -n "$CONTENT_NUM" ]; then
        CONTENT_ARG="--number $CONTENT_NUM"
    fi

    # 전체 Validator 실행
    RESULT=$(python3 "$PROJECT_ROOT/.claude/hooks/validators/pre_publish_validator.py" $CONTENT_ARG $PLATFORM 2>&1)
    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        log_result "PRE_PUBLISH_VALIDATOR" "FAIL" "$RESULT"
        echo "" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "PRE-PUBLISH VALIDATOR FAIL" >&2
        echo "게시 차단됨" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "$RESULT" >&2
        echo "" >&2
        echo "FAIL 항목 수정 후 재시도하세요." >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        exit 2
    fi

    log_result "PRE_PUBLISH_VALIDATOR" "PASS" "$RESULT"
    echo "[Validator] 게시 전 검증 PASS - 게시 진행 허용" >&2
fi

# 게시 관련 아닌 명령은 그냥 통과
exit 0
