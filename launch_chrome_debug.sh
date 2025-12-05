#!/bin/bash
echo "🚀 크롬 디버깅 모드 실행 중..."
echo "⚠️  새로운 크롬 창이 열리면 Tistory에 로그인해주세요!"
echo "⚠️  로그인이 완료되면 이 창을 닫지 말고 두세요."

/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_debug_profile"
