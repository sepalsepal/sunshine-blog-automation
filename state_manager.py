import json
import os
import streamlit as st

STATE_FILE = "app_state.json"

def save_state():
    """현재 세션 상태를 파일로 저장"""
    state_data = {
        "pipeline": st.session_state.pipeline,
        "progress": st.session_state.progress,
        "final_data": st.session_state.final_data,
        "auto_upload_triggered": st.session_state.get("auto_upload_triggered", False)
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state_data, f, indent=4, default=str)
    except Exception as e:
        print(f"❌ State save failed: {e}")

def load_state():
    """파일에서 상태를 불러와 세션에 적용"""
    if not os.path.exists(STATE_FILE):
        return False
        
    try:
        with open(STATE_FILE, "r") as f:
            state_data = json.load(f)
            
        # 세션 상태 업데이트
        st.session_state.pipeline = state_data.get("pipeline", st.session_state.pipeline)
        st.session_state.progress = state_data.get("progress", st.session_state.progress)
        st.session_state.final_data = state_data.get("final_data", st.session_state.final_data)
        st.session_state.auto_upload_triggered = state_data.get("auto_upload_triggered", False)
        return True
    except Exception as e:
        print(f"❌ State load failed: {e}")
        return False

def clear_state():
    """상태 파일 초기화"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
