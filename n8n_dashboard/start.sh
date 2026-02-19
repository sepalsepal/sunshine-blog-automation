#!/bin/bash
# Dashboard 시작 스크립트

echo "=================================================="
echo "🌻 Project Sunshine Dashboard"
echo "=================================================="

cd "$(dirname "$0")"

# 가상환경 확인/생성
if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# Flask 의존성 확인
pip show flask flask-cors > /dev/null 2>&1 || {
    echo "📦 Flask 설치 중..."
    pip install flask flask-cors
}

# API 서버 시작 (백그라운드)
echo "🚀 API 서버 시작 (포트 5001)..."
python3 api_server.py &
API_PID=$!

sleep 2

# 프론트엔드 서버 시작
echo "🌐 프론트엔드 서버 시작 (포트 8080)..."
python3 -m http.server 8080 &
FRONT_PID=$!

echo ""
echo "=================================================="
echo "✅ Dashboard 시작 완료"
echo ""
echo "📊 Dashboard: http://localhost:8080"
echo "🔌 API: http://localhost:5001"
echo ""
echo "종료: Ctrl+C"
echo "=================================================="

# 종료 시 프로세스 정리
trap "kill $API_PID $FRONT_PID 2>/dev/null; echo '종료됨'" EXIT

wait
