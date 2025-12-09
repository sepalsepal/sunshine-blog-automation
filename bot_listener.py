import os
import json
import time
import streamlit as st

STATE_FILE = "bot_command.json"

def check_for_commands():
    """텔레그램 봇 명령 확인 및 처리"""
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r") as f:
            cmd_data = json.load(f)
        
        # 5초 제한 제거: 파일이 존재하면 무조건 처리 (처리 후 삭제하므로 안전)
        # if time.time() - cmd_data.get('timestamp', 0) < 5:
        if True:
            command = cmd_data.get('command')
            
            if command == "START_WORKFLOW":
                st.toast(f"🤖 텔레그램 명령 수신: {cmd_data['data']['topic']} 시작")
                st.session_state.final_data['topic'] = cmd_data['data']['topic']
                st.session_state.pipeline['step'] = 1
                # 파일 삭제하여 중복 실행 방지
                os.remove(STATE_FILE)
                return "START_WORKFLOW"
                
            elif command == "APPROVE_UPLOAD":
                st.toast("🤖 텔레그램 승인 수신: 업로드 시작")
                st.session_state.auto_upload_triggered = True
                os.remove(STATE_FILE)
                return "APPROVE_UPLOAD"
                
    except Exception as e:
        print(f"Bot command error: {e}")
    
    return None

def auto_refresh_if_idle():
    """대기 상태 또는 승인 대기 중일 때 자동 새로고침"""
    # Step 0: 시작 대기, Step 6: 승인 대기
    if st.session_state.pipeline['step'] in [0, 6]:
        time.sleep(3)  # 3초마다 확인
        st.rerun()
