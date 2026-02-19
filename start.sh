#!/bin/bash

echo "🛑 [초기화] 기존 프로세스 정리 중..."
pkill -f streamlit
pkill -f scheduler_service.py

echo "🛠️ [설치] 라이브러리 강제 재설치 및 업데이트..."
# --force-reinstall 옵션으로 꼬인 것들을 풀고 다시 깝니다.
pip3 install --upgrade --force-reinstall gspread oauth2client streamlit google-generativeai replicate google-cloud-aiplatform feedparser pytrends Pillow opencv-python graphviz python-dotenv selenium webdriver-manager

echo "🚀 [가동 1] Antigravity 웹 대시보드 실행..."
nohup python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > app_log.out 2>&1 &

echo "⏰ [가동 2] 24시간 분석 스케줄러 실행..."
nohup python3 scheduler_service.py > scheduler_log.out 2>&1 &

echo "⏳ 시스템 안정화 대기 중 (5초)..."
sleep 5

if pgrep -f "streamlit" > /dev/null
then
    echo "✅ [성공] 시스템 정상 가동! (http://34.158.212.245:8501)"
else
    echo "❌ [실패] 서버 실행 중 오류 발생."
    tail -n 20 app_log.out
fi
