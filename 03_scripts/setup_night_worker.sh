#!/bin/bash
# Night Worker 설치/제거 스크립트
# 사용법:
#   ./setup_night_worker.sh install   # 설치
#   ./setup_night_worker.sh uninstall # 제거
#   ./setup_night_worker.sh status    # 상태 확인
#   ./setup_night_worker.sh test      # 테스트 실행

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PLIST_NAME="com.sunshine.nightworker"
PLIST_SOURCE="$SCRIPT_DIR/$PLIST_NAME.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

case "$1" in
    install)
        echo -e "${GREEN}🌙 Night Worker 설치 중...${NC}"

        # logs 폴더 생성
        mkdir -p "$PROJECT_ROOT/logs"

        # 실행 권한 부여
        chmod +x "$PROJECT_ROOT/services/scripts/night_worker.py"

        # plist 복사
        cp "$PLIST_SOURCE" "$PLIST_DEST"
        echo "   ✅ plist 복사 완료: $PLIST_DEST"

        # launchd에 등록
        launchctl load "$PLIST_DEST"
        echo "   ✅ launchd 등록 완료"

        echo -e "${GREEN}✅ Night Worker 설치 완료!${NC}"
        echo "   매일 23:00에 자동 실행됩니다."
        ;;

    uninstall)
        echo -e "${YELLOW}🗑️  Night Worker 제거 중...${NC}"

        # launchd에서 제거
        if [ -f "$PLIST_DEST" ]; then
            launchctl unload "$PLIST_DEST" 2>/dev/null
            rm "$PLIST_DEST"
            echo "   ✅ launchd 제거 완료"
        else
            echo "   ⚠️  설치되어 있지 않음"
        fi

        echo -e "${GREEN}✅ Night Worker 제거 완료${NC}"
        ;;

    status)
        echo -e "${GREEN}📊 Night Worker 상태${NC}"
        echo ""

        if [ -f "$PLIST_DEST" ]; then
            echo "   설치 상태: ✅ 설치됨"
            echo "   plist 경로: $PLIST_DEST"
        else
            echo "   설치 상태: ❌ 미설치"
        fi

        echo ""
        echo "   launchd 상태:"
        launchctl list | grep "$PLIST_NAME" || echo "   (등록되지 않음)"

        echo ""
        echo "   최근 로그:"
        if [ -f "$PROJECT_ROOT/logs/night_worker_stdout.log" ]; then
            tail -5 "$PROJECT_ROOT/logs/night_worker_stdout.log"
        else
            echo "   (로그 없음)"
        fi
        ;;

    test)
        echo -e "${GREEN}🧪 Night Worker 테스트 실행${NC}"
        echo ""

        cd "$PROJECT_ROOT"
        source .env 2>/dev/null

        echo "드라이런 모드로 실행..."
        python3 services/scripts/night_worker.py --dry-run
        ;;

    run)
        echo -e "${GREEN}🚀 Night Worker 즉시 실행${NC}"
        echo ""

        cd "$PROJECT_ROOT"
        source .env 2>/dev/null

        python3 services/scripts/night_worker.py
        ;;

    *)
        echo "사용법: $0 {install|uninstall|status|test|run}"
        echo ""
        echo "  install   - Night Worker 설치 (매일 23:00 실행)"
        echo "  uninstall - Night Worker 제거"
        echo "  status    - 상태 확인"
        echo "  test      - 드라이런 테스트"
        echo "  run       - 즉시 실행"
        exit 1
        ;;
esac
