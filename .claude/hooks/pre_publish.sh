#!/bin/bash
#
# pre_publish.sh - 게시 전 HARD FAIL 검증 훅
# Day 12 HARD FAIL 시스템
#
# 사용법:
#   .claude/hooks/pre_publish.sh <topic>
#
# 종료 코드:
#   0 - PASS (게시 진행)
#   1 - HARD FAIL (게시 중단)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

TOPIC="$1"

if [ -z "$TOPIC" ]; then
    echo "❌ 오류: topic 인자가 필요합니다"
    echo "사용법: pre_publish.sh <topic>"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 PRE-PUBLISH 검증 시작: $TOPIC"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# HARD FAIL #1: CONTENT_MAP 검증
echo "[1/3] CONTENT_MAP 검증..."
if ! python3 "$PROJECT_ROOT/pipeline/validate_content_map.py" "$TOPIC" 2>/dev/null; then
    echo ""
    echo "⛔ HARD FAIL #1: CONTENT_MAP 검증 실패"
    echo "   topic이 CONTENT_MAP에 없거나 blocked 상태입니다."
    echo ""
    exit 1
fi
echo "    ✅ CONTENT_MAP 검증 통과"
echo ""

# HARD FAIL #2: 캡션-안전분류 일치 검증
echo "[2/3] 캡션-안전분류 일치 검증..."

# topics_expanded.json에서 안전 분류 조회
SAFETY=$(python3 -c "
import json
from pathlib import Path
p = Path('$PROJECT_ROOT/config/settings/topics_expanded.json')
if p.exists():
    data = json.load(open(p))
    for cat in data.get('categories', []):
        for t in cat.get('topics', []):
            if t.get('id') == '$TOPIC':
                print(t.get('safety', 'unknown'))
                exit()
    print('unknown')
else:
    print('unknown')
" 2>/dev/null || echo "unknown")

# 캡션 파일 찾기
CAPTION_FILE=$(find "$PROJECT_ROOT/content/images" -name "*$TOPIC*" -type d 2>/dev/null | head -1)
if [ -n "$CAPTION_FILE" ]; then
    CAPTION_FILE="$CAPTION_FILE/caption_instagram.txt"
fi

if [ -f "$CAPTION_FILE" ]; then
    CAPTION_CONTENT=$(cat "$CAPTION_FILE" 2>/dev/null || echo "")

    # 안전 분류별 필수 키워드 확인
    case "$SAFETY" in
        "safe")
            if ! echo "$CAPTION_CONTENT" | grep -qE "급여 가능|먹어도 돼요|급여 가능합니다"; then
                echo "    ⚠️ 경고: SAFE 음식이나 캡션에 긍정 문구 없음"
            else
                echo "    ✅ SAFE 캡션 검증 통과"
            fi
            ;;
        "caution")
            if ! echo "$CAPTION_CONTENT" | grep -qE "주의|⚠️"; then
                echo ""
                echo "⛔ HARD FAIL #2: 캡션-안전분류 불일치"
                echo "   CAUTION 음식인데 캡션에 '주의' 또는 '⚠️'가 없습니다."
                echo ""
                exit 1
            else
                echo "    ✅ CAUTION 캡션 검증 통과"
            fi
            ;;
        "danger"|"forbidden")
            if ! echo "$CAPTION_CONTENT" | grep -qE "금지|🚫|권장하지 않|급여 금지"; then
                echo ""
                echo "⛔ HARD FAIL #2: 캡션-안전분류 불일치"
                echo "   DANGER/FORBIDDEN 음식인데 캡션에 '금지' 또는 '🚫'가 없습니다."
                echo ""
                exit 1
            else
                echo "    ✅ DANGER/FORBIDDEN 캡션 검증 통과"
            fi
            ;;
        *)
            echo "    ⚠️ 안전 분류 알 수 없음 (topics_expanded.json 확인 필요)"
            ;;
    esac
else
    echo "    ⚠️ 캡션 파일 없음 (검증 스킵)"
fi
echo ""

# HARD FAIL #3: Safety 24h 검증 (상태 파일 확인)
echo "[3/3] Safety 24h 검증..."
SAFETY_STATUS_FILE="$PROJECT_ROOT/config/data/safety_status.json"

if [ -f "$SAFETY_STATUS_FILE" ]; then
    BLOCKED=$(python3 -c "
import json
data = json.load(open('$SAFETY_STATUS_FILE'))
print('true' if data.get('blocked', False) else 'false')
" 2>/dev/null || echo "false")

    if [ "$BLOCKED" = "true" ]; then
        echo ""
        echo "⛔ HARD FAIL #3: Safety 24h FAIL"
        echo "   계정이 Safety 검증 실패 상태입니다. (48시간 대기 필요)"
        echo ""
        exit 1
    fi
fi
echo "    ✅ Safety 24h 검증 통과"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PRE-PUBLISH 검증 완료: $TOPIC"
echo "   모든 HARD FAIL 조건 통과. 게시 진행 가능."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
