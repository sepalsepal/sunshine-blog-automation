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
# 게시 관련 명령 감지
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 게시 관련 키워드: publish, 게시, instagram, threads, graph api
if echo "$COMMAND" | grep -qiE "publish|게시|instagram.*post|threads.*post|graph.*api.*publish|carousel.*create"; then
    echo "[Validator] 게시 명령 감지: 전체 Validator 실행" >&2

    # 전체 Validator 실행
    RESULT=$(python3 "$PROJECT_ROOT/.claude/hooks/validators/pre_publish_validator.py" 2>&1)
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
