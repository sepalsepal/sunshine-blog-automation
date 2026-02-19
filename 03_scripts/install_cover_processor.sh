#!/bin/bash
# 커버 프로세서 launchd 설치/관리 스크립트

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PLIST_NAME="com.sunshine.cover.plist"
PLIST_SRC="$SCRIPT_DIR/launchd/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"

case "$1" in
    install)
        echo "커버 프로세서 설치 중..."

        # LaunchAgents 폴더 확인
        mkdir -p "$HOME/Library/LaunchAgents"

        # 기존 서비스 언로드 (있으면)
        launchctl unload "$PLIST_DST" 2>/dev/null

        # plist 복사
        cp "$PLIST_SRC" "$PLIST_DST"

        # 로드
        launchctl load "$PLIST_DST"

        echo "✅ 설치 완료!"
        echo "   매일 오전 9시에 자동 실행됩니다."
        echo ""
        echo "매핑 파일 위치:"
        echo "   $PROJECT_ROOT/content/images/000_cover/03_cover_sources/cover_mapping.json"
        ;;

    uninstall)
        echo "커버 프로세서 제거 중..."
        launchctl unload "$PLIST_DST" 2>/dev/null
        rm -f "$PLIST_DST"
        echo "✅ 제거 완료!"
        ;;

    status)
        echo "=== 커버 프로세서 상태 ==="
        if launchctl list | grep -q "com.sunshine.cover"; then
            echo "상태: 실행 중"
            launchctl list | grep "com.sunshine.cover"
        else
            echo "상태: 미설치 또는 중지됨"
        fi
        echo ""
        echo "=== 소스 폴더 현황 ==="
        python3 "$SCRIPT_DIR/cover_processor.py" --status
        ;;

    test)
        echo "커버 프로세서 테스트 실행..."
        python3 "$SCRIPT_DIR/cover_processor.py" --dry-run
        ;;

    run)
        echo "커버 프로세서 즉시 실행..."
        python3 "$SCRIPT_DIR/cover_processor.py" --notify
        ;;

    init)
        echo "매핑 템플릿 생성 중..."
        python3 "$SCRIPT_DIR/cover_processor.py" --init
        ;;

    *)
        echo "사용법: $0 {install|uninstall|status|test|run|init}"
        echo ""
        echo "명령어:"
        echo "  install   - launchd 서비스 설치 (매일 오전 9시 실행)"
        echo "  uninstall - launchd 서비스 제거"
        echo "  status    - 현재 상태 및 소스 폴더 현황"
        echo "  test      - 드라이런 테스트"
        echo "  run       - 즉시 실행"
        echo "  init      - 매핑 템플릿 생성"
        exit 1
        ;;
esac
