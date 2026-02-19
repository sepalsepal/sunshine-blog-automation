#!/bin/bash
#
# post-write-validate.sh - Write 도구 실행 후 Validator 자동 실행
# WO-036: 기억 의존 제거 - Hook 자동 실행
#
# 트리거: PostToolUse (Write)
# Exit 0: 진행 허용
# Exit 2: 블로킹 (FAIL)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="$PROJECT_ROOT/config/logs/validator"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
NOTION_UPDATE_SCRIPT="$PROJECT_ROOT/scripts/notion_update.py"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# stdin에서 JSON 입력 읽기 (Python으로 파싱 - jq 의존성 제거)
INPUT=$(cat)

# Python으로 파일 경로 추출
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('tool_input', {}).get('file_path', ''))" 2>/dev/null)

# 파일 경로가 없으면 스킵
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# 로그 함수
log_result() {
    local validator="$1"
    local result="$2"
    local details="$3"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $validator: $result - $FILE_PATH" >> "$LOG_DIR/validator_$TIMESTAMP.log"
    echo "$details" >> "$LOG_DIR/validator_$TIMESTAMP.log"
    echo "---" >> "$LOG_DIR/validator_$TIMESTAMP.log"
}

# 콘텐츠 번호 추출 함수
extract_content_num() {
    local path="$1"
    # 패턴: /contents/X_folder/NNN_food_name/...
    echo "$path" | grep -oE '/[0-9]{3}_' | head -1 | tr -d '/_'
}

# Notion 업데이트 함수 (백그라운드 실행)
update_notion() {
    local content_num="$1"
    local validator_status="$2"

    if [ -z "$content_num" ] || [ ! -f "$NOTION_UPDATE_SCRIPT" ]; then
        return 0
    fi

    # 백그라운드에서 Notion 업데이트 (실패해도 무시)
    python3 "$NOTION_UPDATE_SCRIPT" "$content_num" --validator "$validator_status" --quiet 2>/dev/null &
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 표지 이미지 검증 (blog/01_표지_*.png)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$FILE_PATH" == */blog/01_* && "$FILE_PATH" == *.png ]]; then
    echo "[Validator] 표지 검증 실행: $FILE_PATH" >&2

    # Python Validator 호출
    RESULT=$(python3 "$PROJECT_ROOT/.claude/hooks/validators/cover_validator.py" "$FILE_PATH" 2>&1)
    EXIT_CODE=$?

    CONTENT_NUM=$(extract_content_num "$FILE_PATH")

    if [ $EXIT_CODE -ne 0 ]; then
        log_result "COVER_VALIDATOR" "FAIL" "$RESULT"
        update_notion "$CONTENT_NUM" "FAIL"
        echo "" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "COVER VALIDATOR FAIL" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "$RESULT" >&2
        echo "" >&2
        echo "RULES.md 8 참조. 재제작 필요." >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        exit 2
    fi

    log_result "COVER_VALIDATOR" "PASS" "$RESULT"
    update_notion "$CONTENT_NUM" "PASS"
    echo "[Validator] 표지 검증 PASS" >&2
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. C2 인포그래픽 검증 (blog/03~07_*.png)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$FILE_PATH" == */blog/0[3-7]_* && "$FILE_PATH" == *.png ]]; then
    echo "[Validator] C2 인포그래픽 검증 실행: $FILE_PATH" >&2

    RESULT=$(python3 "$PROJECT_ROOT/.claude/hooks/validators/c2_validator.py" "$FILE_PATH" 2>&1)
    EXIT_CODE=$?
    CONTENT_NUM=$(extract_content_num "$FILE_PATH")

    if [ $EXIT_CODE -ne 0 ]; then
        log_result "C2_VALIDATOR" "FAIL" "$RESULT"
        update_notion "$CONTENT_NUM" "FAIL"
        echo "" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "C2 INFOGRAPHIC VALIDATOR FAIL" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "$RESULT" >&2
        echo "" >&2
        echo "RULES.md 2.4 참조. 재제작 필요." >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        exit 2
    fi

    log_result "C2_VALIDATOR" "PASS" "$RESULT"
    update_notion "$CONTENT_NUM" "PASS"
    echo "[Validator] C2 인포그래픽 검증 PASS" >&2
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 본문 검증 (blog/본문.txt)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$FILE_PATH" == */blog/*본문* || "$FILE_PATH" == */blog/*.txt ]]; then
    echo "[Validator] 본문 검증 실행: $FILE_PATH" >&2

    RESULT=$(python3 "$PROJECT_ROOT/.claude/hooks/validators/body_validator.py" "$FILE_PATH" 2>&1)
    EXIT_CODE=$?
    CONTENT_NUM=$(extract_content_num "$FILE_PATH")

    if [ $EXIT_CODE -ne 0 ]; then
        log_result "BODY_VALIDATOR" "FAIL" "$RESULT"
        update_notion "$CONTENT_NUM" "FAIL"
        echo "" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "BODY VALIDATOR FAIL" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "$RESULT" >&2
        echo "" >&2
        echo "RULES.md 2.1, 6 참조. 수정 필요." >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        exit 2
    fi

    log_result "BODY_VALIDATOR" "PASS" "$RESULT"
    update_notion "$CONTENT_NUM" "PASS"
    echo "[Validator] 본문 검증 PASS" >&2
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 캡션 검증 (caption*.txt)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$FILE_PATH" == *caption* && "$FILE_PATH" == *.txt ]]; then
    echo "[Validator] 캡션 검증 실행: $FILE_PATH" >&2

    RESULT=$(python3 "$PROJECT_ROOT/.claude/hooks/validators/caption_validator.py" "$FILE_PATH" 2>&1)
    EXIT_CODE=$?
    CONTENT_NUM=$(extract_content_num "$FILE_PATH")

    if [ $EXIT_CODE -ne 0 ]; then
        log_result "CAPTION_VALIDATOR" "FAIL" "$RESULT"
        update_notion "$CONTENT_NUM" "FAIL"
        echo "" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "CAPTION VALIDATOR FAIL" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "$RESULT" >&2
        echo "" >&2
        echo "RULES.md 6.2~6.6 참조. 수정 필요." >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        exit 2
    fi

    log_result "CAPTION_VALIDATOR" "PASS" "$RESULT"
    update_notion "$CONTENT_NUM" "PASS"
    echo "[Validator] 캡션 검증 PASS" >&2
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 노션 동기화 (insta/, blog/ 폴더 변경 시)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYNC_SCRIPT="$PROJECT_ROOT/scripts/auto_sync_notion.py"

if [[ "$FILE_PATH" == */insta/* || "$FILE_PATH" == */blog/* ]]; then
    CONTENT_NUM=$(extract_content_num "$FILE_PATH")

    if [ -n "$CONTENT_NUM" ] && [ -f "$SYNC_SCRIPT" ]; then
        # 백그라운드에서 노션 동기화 실행
        python3 "$SYNC_SCRIPT" "$CONTENT_NUM" > /dev/null 2>&1 &
        echo "[Hook] 노션 동기화 트리거: #$CONTENT_NUM" >&2
    fi
fi

# 검증 대상 아닌 파일은 그냥 통과
exit 0
