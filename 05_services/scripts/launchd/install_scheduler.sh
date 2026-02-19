#!/bin/bash
# Project Sunshine - 스케줄러 설치 스크립트
#
# 사용법:
#   bash install_scheduler.sh install   # 스케줄러 설치
#   bash install_scheduler.sh uninstall # 스케줄러 제거
#   bash install_scheduler.sh status    # 상태 확인

PLIST_NAME="com.sunshine.scheduler"
PLIST_SOURCE="$(dirname "$0")/com.sunshine.scheduler.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

case "$1" in
    install)
        echo "📦 스케줄러 설치 중..."

        # LaunchAgents 디렉토리 확인
        mkdir -p "$HOME/Library/LaunchAgents"

        # plist 복사
        cp "$PLIST_SOURCE" "$PLIST_DEST"

        # 기존 서비스 언로드
        launchctl unload "$PLIST_DEST" 2>/dev/null

        # 서비스 로드
        launchctl load "$PLIST_DEST"

        echo "✅ 스케줄러 설치 완료!"
        echo ""
        echo "📅 스케줄:"
        echo "   - 07:00 KST 첫 번째 게시"
        echo "   - 19:00 KST 두 번째 게시"
        echo ""
        launchctl list | grep sunshine
        ;;

    uninstall)
        echo "🗑️  스케줄러 제거 중..."
        launchctl unload "$PLIST_DEST" 2>/dev/null
        rm -f "$PLIST_DEST"
        echo "✅ 스케줄러 제거 완료"
        ;;

    status)
        echo "📊 스케줄러 상태:"
        if launchctl list | grep -q sunshine; then
            echo "   ✅ 실행 중"
            launchctl list | grep sunshine
        else
            echo "   ❌ 실행 안 됨"
        fi

        echo ""
        echo "📂 로그 파일:"
        ls -la ~/Desktop/Jun_AI/Dog_Contents/project_sunshine/config/logs/scheduler*.log 2>/dev/null || echo "   (로그 없음)"
        ;;

    test)
        echo "🧪 스케줄러 테스트 실행..."
        cd ~/Desktop/Jun_AI/Dog_Contents/project_sunshine
        source .env
        python3 services/scripts/auto_scheduler.py run --dry-run
        ;;

    *)
        echo "사용법: $0 {install|uninstall|status|test}"
        exit 1
        ;;
esac
