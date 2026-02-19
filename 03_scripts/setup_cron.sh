#!/bin/bash
# setup_cron.sh - 노션 동기화 정기 실행 설정

PLIST_SRC="/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/scripts/launchd/com.sunshine.notion-sync.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.sunshine.notion-sync.plist"

case "$1" in
    install)
        echo "📦 노션 동기화 정기 실행 설치 중..."
        cp "$PLIST_SRC" "$PLIST_DST"
        launchctl load "$PLIST_DST"
        echo "✅ 설치 완료 - 1시간마다 자동 동기화"
        ;;
    uninstall)
        echo "🗑️ 노션 동기화 정기 실행 제거 중..."
        launchctl unload "$PLIST_DST" 2>/dev/null
        rm -f "$PLIST_DST"
        echo "✅ 제거 완료"
        ;;
    status)
        if launchctl list | grep -q "com.sunshine.notion-sync"; then
            echo "✅ 실행 중"
            launchctl list | grep "com.sunshine.notion-sync"
        else
            echo "❌ 설치 안 됨"
        fi
        ;;
    *)
        echo "사용법: $0 {install|uninstall|status}"
        exit 1
        ;;
esac
