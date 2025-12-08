"""
스케줄러 서비스 - Railway Cron Job용
매일 오전 8시, 오후 7시 (KST) 자동 실행
"""
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

STREAMLIT_APP_URL = os.getenv("STREAMLIT_APP_URL", "https://sunshine-blog.streamlit.app")

def trigger_workflow():
    """Streamlit 앱에 자동 워크플로우 시작 요청"""
    url = f"{STREAMLIT_APP_URL}?action=start&topic=auto"
    
    try:
        print(f"🚀 [{datetime.now()}] 스케줄러 실행: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Scheduler/1.0'})
        urllib.request.urlopen(req, timeout=30)
        print("✅ 워크플로우 트리거 성공!")
        return True
    except Exception as e:
        print(f"⚠️ 트리거 실패 (정상일 수 있음): {e}")
        return True  # Streamlit redirect 때문에 에러여도 OK

def run_scheduler():
    """스케줄러 메인 루프"""
    kst = pytz.timezone('Asia/Seoul')
    target_hours = [8, 19]  # 오전 8시, 오후 7시
    
    print("⏰ 스케줄러 시작됨 (대상 시간: 오전 8시, 오후 7시 KST)")
    
    last_run_hour = -1
    
    while True:
        now = datetime.now(kst)
        current_hour = now.hour
        
        # 대상 시간이고, 이번 시간에 아직 실행 안 했으면
        if current_hour in target_hours and current_hour != last_run_hour:
            print(f"🕐 [{now.strftime('%Y-%m-%d %H:%M')}] 스케줄 실행!")
            trigger_workflow()
            last_run_hour = current_hour
        
        # 1분마다 체크
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
