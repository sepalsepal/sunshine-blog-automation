#!/bin/bash
# 텔레그램 알림 스크립트 - 이미지 분류 작업 재개 알림

cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine
source .env

MESSAGE="🔔 <b>이미지 분류 작업 재개 시간!</b>

📁 with_human 폴더: 420장 남음
📊 현재 진행률: 58%

분류 현황:
• cuddle: 205장
• daily: 88장
• walk: 43장
• travel: 52장
• group: 10장

Claude Code를 실행해서 작업을 이어가세요!"

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"${TELEGRAM_CHAT_ID}\", \"text\": \"${MESSAGE}\", \"parse_mode\": \"HTML\"}" > /dev/null

echo "알림 전송 완료: $(date)"
