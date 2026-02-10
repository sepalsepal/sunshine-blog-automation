#!/bin/bash
#
# Project Sunshine - 자동 스케줄러 설치 스크립트
#
# 기능:
#   - launchd plist 파일 생성 및 설치
#   - 매일 오후 6시(KST) 자동 게시 설정
#   - 로그 파일 경로 설정
#
# 사용법:
#   ./install_scheduler.sh          # 설치
#   ./install_scheduler.sh --uninstall  # 제거
#   ./install_scheduler.sh --status    # 상태 확인
#   ./install_scheduler.sh --test      # 즉시 테스트 실행
#
# Author: 송지영 대리
# Date: 2026-01-30

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 경로 (스크립트 위치 기준)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# launchd 관련 경로
PLIST_NAME="com.sunshine.scheduler"
PLIST_TEMPLATE="$SCRIPT_DIR/launchd/${PLIST_NAME}.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# 로그 경로
LOG_DIR="$PROJECT_ROOT/config/logs"

# Python 경로 확인
find_python() {
    # 프로젝트 venv 확인
    if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        echo "$PROJECT_ROOT/.venv/bin/python"
        return
    fi

    # pyenv 확인
    if command -v pyenv &> /dev/null; then
        PYENV_ROOT="$(pyenv root)"
        VERSION="$(pyenv version-name)"
        if [ -f "$PYENV_ROOT/versions/$VERSION/bin/python" ]; then
            echo "$PYENV_ROOT/versions/$VERSION/bin/python"
            return
        fi
    fi

    # 시스템 python3
    if command -v python3 &> /dev/null; then
        echo "$(which python3)"
        return
    fi

    echo ""
}

# 헤더 출력
print_header() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Project Sunshine - 자동 스케줄러 설치${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

# 상태 확인
check_status() {
    echo -e "${BLUE}📊 스케줄러 상태 확인${NC}"
    echo "----------------------------------------"

    if [ -f "$PLIST_DEST" ]; then
        echo -e "  plist 파일: ${GREEN}설치됨${NC}"
        echo "  경로: $PLIST_DEST"
    else
        echo -e "  plist 파일: ${YELLOW}미설치${NC}"
    fi

    echo ""

    # launchctl 상태 확인
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo -e "  launchd 상태: ${GREEN}로드됨${NC}"

        # 다음 실행 시간 계산
        NOW_HOUR=$(date +%H)
        if [ "$NOW_HOUR" -lt 18 ]; then
            NEXT_RUN=$(date -v18H -v0M +"%Y-%m-%d %H:%M")
        else
            NEXT_RUN=$(date -v+1d -v18H -v0M +"%Y-%m-%d %H:%M")
        fi
        echo "  다음 실행: $NEXT_RUN (KST)"
    else
        echo -e "  launchd 상태: ${YELLOW}언로드됨${NC}"
    fi

    echo ""
    echo "----------------------------------------"

    # 최근 로그 확인
    if [ -f "$LOG_DIR/scheduler.log" ]; then
        echo -e "${BLUE}📄 최근 로그 (마지막 5줄):${NC}"
        tail -5 "$LOG_DIR/scheduler.log"
    fi
}

# 설치
install_scheduler() {
    print_header

    echo -e "${BLUE}🔍 환경 확인 중...${NC}"

    # Python 경로 확인
    PYTHON_PATH=$(find_python)
    if [ -z "$PYTHON_PATH" ]; then
        echo -e "${RED}❌ Python을 찾을 수 없습니다.${NC}"
        exit 1
    fi
    echo "  Python: $PYTHON_PATH"
    echo "  프로젝트: $PROJECT_ROOT"

    # 템플릿 확인
    if [ ! -f "$PLIST_TEMPLATE" ]; then
        echo -e "${RED}❌ plist 템플릿을 찾을 수 없습니다: $PLIST_TEMPLATE${NC}"
        exit 1
    fi

    # 로그 디렉토리 생성
    mkdir -p "$LOG_DIR"
    echo "  로그 디렉토리: $LOG_DIR"

    # LaunchAgents 디렉토리 확인
    mkdir -p "$HOME/Library/LaunchAgents"

    echo ""
    echo -e "${BLUE}📝 plist 파일 생성 중...${NC}"

    # 템플릿에서 plist 생성 (경로 치환)
    sed -e "s|PYTHON_PATH_PLACEHOLDER|$PYTHON_PATH|g" \
        -e "s|PROJECT_ROOT_PLACEHOLDER|$PROJECT_ROOT|g" \
        "$PLIST_TEMPLATE" > "$PLIST_DEST"

    echo "  생성됨: $PLIST_DEST"

    # 기존 에이전트 언로드 (있으면)
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo ""
        echo -e "${YELLOW}기존 에이전트 언로드 중...${NC}"
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
    fi

    # 새 에이전트 로드
    echo ""
    echo -e "${BLUE}🚀 에이전트 로드 중...${NC}"
    launchctl load "$PLIST_DEST"

    # 확인
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo -e "${GREEN}✅ 스케줄러 설치 완료!${NC}"
    else
        echo -e "${RED}❌ 에이전트 로드 실패${NC}"
        exit 1
    fi

    echo ""
    echo "================================================"
    echo -e "${GREEN}📅 매일 오후 6시(KST)에 자동 게시됩니다.${NC}"
    echo ""
    echo "유용한 명령어:"
    echo "  상태 확인:  $0 --status"
    echo "  즉시 실행:  $0 --test"
    echo "  제거:       $0 --uninstall"
    echo ""
    echo "로그 확인:"
    echo "  tail -f $LOG_DIR/scheduler.log"
    echo "================================================"
}

# 제거
uninstall_scheduler() {
    print_header

    echo -e "${BLUE}🗑️  스케줄러 제거 중...${NC}"

    # 에이전트 언로드
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo "  에이전트 언로드..."
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
    fi

    # plist 파일 삭제
    if [ -f "$PLIST_DEST" ]; then
        echo "  plist 파일 삭제..."
        rm "$PLIST_DEST"
    fi

    echo ""
    echo -e "${GREEN}✅ 스케줄러 제거 완료!${NC}"
    echo ""
    echo "참고: 로그 파일은 유지됩니다."
    echo "로그 삭제: rm -rf $LOG_DIR/scheduler*.log"
}

# 즉시 테스트 실행
test_run() {
    print_header

    echo -e "${BLUE}🧪 스케줄러 테스트 실행 (dry-run)${NC}"
    echo "----------------------------------------"

    PYTHON_PATH=$(find_python)
    if [ -z "$PYTHON_PATH" ]; then
        echo -e "${RED}❌ Python을 찾을 수 없습니다.${NC}"
        exit 1
    fi

    cd "$PROJECT_ROOT"
    "$PYTHON_PATH" services/scripts/auto_scheduler.py run --dry-run
}

# 메인 로직
case "${1:-}" in
    --uninstall|-u)
        uninstall_scheduler
        ;;
    --status|-s)
        check_status
        ;;
    --test|-t)
        test_run
        ;;
    --help|-h)
        echo "사용법: $0 [옵션]"
        echo ""
        echo "옵션:"
        echo "  (없음)      스케줄러 설치"
        echo "  --uninstall 스케줄러 제거"
        echo "  --status    상태 확인"
        echo "  --test      즉시 테스트 실행 (dry-run)"
        echo "  --help      도움말"
        ;;
    *)
        install_scheduler
        ;;
esac
