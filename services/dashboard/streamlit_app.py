#!/usr/bin/env python3
"""
Project Sunshine - Streamlit Dashboard
웹 브라우저에서 파이프라인 진행 상태를 실시간으로 확인

실행: streamlit run dashboard/streamlit_app.py
접속: http://localhost:8501
"""

import json
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# 설정
STATUS_FILE = Path(__file__).parent / "status.json"
REFRESH_INTERVAL = 2  # 초

# 페이지 설정
st.set_page_config(
    page_title="Project Sunshine",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 다크 테마 CSS
st.markdown("""
<style>
    /* 다크 테마 */
    .stApp {
        background-color: #1a1a2e;
        color: #eaeaea;
    }

    /* 메인 컨테이너 */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem;
    }

    /* 헤더 */
    .header {
        text-align: center;
        padding: 1rem 0 2rem 0;
    }

    .header h1 {
        color: #ffd93d;
        font-size: 2.5rem;
        margin: 0;
    }

    .topic-badge {
        display: inline-block;
        background: #4a4a6a;
        color: #ffd93d;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 1rem;
        margin-top: 0.5rem;
    }

    /* 파이프라인 */
    .pipeline {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem 0;
        flex-wrap: wrap;
    }

    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 0 0.2rem;
    }

    .step-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        font-weight: bold;
    }

    .step-icon.done {
        background: #00c853;
        color: white;
    }

    .step-icon.running {
        background: #ffd93d;
        color: #1a1a2e;
        animation: pulse 1s infinite;
    }

    .step-icon.pending {
        background: #4a4a6a;
        color: #888;
    }

    .step-icon.error {
        background: #ff5252;
        color: white;
    }

    .step-name {
        font-size: 0.75rem;
        margin-top: 0.3rem;
        color: #aaa;
    }

    .step-connector {
        width: 30px;
        height: 3px;
        margin: 0 2px;
        margin-bottom: 20px;
    }

    .step-connector.done {
        background: #00c853;
    }

    .step-connector.pending {
        background: #4a4a6a;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    /* 현재 단계 */
    .current-step {
        background: #2a2a4e;
        border: 2px solid #ffd93d;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin: 2rem 0;
    }

    .current-step h3 {
        color: #ffd93d;
        margin: 0 0 0.5rem 0;
    }

    .current-step p {
        color: #eaeaea;
        margin: 0;
        font-size: 1.2rem;
    }

    /* 프로그레스 바 */
    .progress-container {
        background: #2a2a4e;
        border-radius: 10px;
        padding: 1rem 2rem;
        margin: 1rem 0;
    }

    .progress-bar {
        background: #4a4a6a;
        border-radius: 5px;
        height: 20px;
        overflow: hidden;
    }

    .progress-fill {
        background: linear-gradient(90deg, #00c853, #69f0ae);
        height: 100%;
        transition: width 0.5s ease;
    }

    .progress-text {
        text-align: center;
        margin-top: 0.5rem;
        color: #aaa;
    }

    /* 시간 정보 */
    .time-info {
        text-align: center;
        color: #888;
        font-size: 0.9rem;
        margin: 1rem 0;
    }

    /* 에러 */
    .error-box {
        background: #3a2a2a;
        border: 1px solid #ff5252;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .error-box h4 {
        color: #ff5252;
        margin: 0 0 0.5rem 0;
    }

    /* 결과 */
    .result-box {
        background: #2a3a2a;
        border: 2px solid #00c853;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin: 2rem 0;
    }

    .result-box h3 {
        color: #00c853;
        margin: 0;
    }

    /* Streamlit 기본 요소 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 에이전트 정보
AGENTS = {
    "김차장": {"emoji": "👔", "role": "기획"},
    "최검증": {"emoji": "🔍", "role": "팩트체크"},
    "김작가": {"emoji": "✍️", "role": "프롬프트"},
    "이작가": {"emoji": "🎨", "role": "이미지"},
    "박편집": {"emoji": "🎬", "role": "오버레이"},
    "박과장": {"emoji": "📋", "role": "품질검수"},
    "이카피": {"emoji": "📝", "role": "캡션"},
    "김대리": {"emoji": "📤", "role": "게시"},
    "정분석": {"emoji": "📊", "role": "분석"}
}


def load_status() -> dict:
    """상태 파일 로드"""
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "topic": None,
        "current_step": 0,
        "total_progress": 0,
        "steps": [],
        "errors": []
    }


def format_duration(seconds: float) -> str:
    """시간 포맷팅"""
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{int(seconds)}초"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}분 {secs}초"


def render_pipeline(steps: list):
    """파이프라인 시각화"""
    html = '<div class="pipeline">'

    for i, step in enumerate(steps):
        name = step.get("name", "?")
        status = step.get("status", "pending")
        agent_info = AGENTS.get(name, {"emoji": "🐕", "role": "?"})

        # 연결선 (첫 번째 제외)
        if i > 0:
            prev_status = steps[i-1].get("status", "pending")
            connector_class = "done" if prev_status == "done" else "pending"
            html += f'<div class="step-connector {connector_class}"></div>'

        # 아이콘
        icon = "✓" if status == "done" else "▶" if status == "running" else "·" if status == "pending" else "✗"

        html += f'''
        <div class="step">
            <div class="step-icon {status}">{icon}</div>
            <div class="step-name">{name[:2]}</div>
        </div>
        '''

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_current_step(status: dict):
    """현재 단계 표시"""
    steps = status.get("steps", [])
    current_idx = status.get("current_step", 0)

    if current_idx > 0 and current_idx <= len(steps):
        step = steps[current_idx - 1]
        name = step.get("name", "?")
        progress = step.get("progress", "")
        agent_info = AGENTS.get(name, {"emoji": "🐕", "role": "?"})

        content = f"{agent_info['emoji']} {name} - {agent_info['role']}"
        if progress:
            content += f" ({progress})"

        st.markdown(f'''
        <div class="current-step">
            <h3>🔄 현재 진행</h3>
            <p>{content}</p>
        </div>
        ''', unsafe_allow_html=True)

    elif status.get("result"):
        st.markdown('''
        <div class="result-box">
            <h3>✅ 파이프라인 완료!</h3>
        </div>
        ''', unsafe_allow_html=True)


def render_progress(status: dict):
    """진행률 바"""
    steps = status.get("steps", [])
    total = len(steps) or 9
    completed = sum(1 for s in steps if s.get("status") == "done")
    pct = int((completed / total) * 100)

    st.markdown(f'''
    <div class="progress-container">
        <div class="progress-bar">
            <div class="progress-fill" style="width: {pct}%;"></div>
        </div>
        <div class="progress-text">{pct}% 완료 ({completed}/{total})</div>
    </div>
    ''', unsafe_allow_html=True)


def render_time_info(status: dict):
    """시간 정보"""
    started_at = status.get("started_at")
    if started_at:
        try:
            start_time = datetime.fromisoformat(started_at)
            elapsed = (datetime.now() - start_time).total_seconds()
            elapsed_str = format_duration(elapsed)
            st.markdown(f'<div class="time-info">⏱️ 소요 시간: {elapsed_str}</div>', unsafe_allow_html=True)
        except:
            pass


def render_errors(status: dict):
    """에러 표시"""
    errors = status.get("errors", [])
    if errors:
        error_list = "<br>".join(f"• {e}" for e in errors[-5:])
        st.markdown(f'''
        <div class="error-box">
            <h4>⚠️ 에러 발생</h4>
            <p>{error_list}</p>
        </div>
        ''', unsafe_allow_html=True)


def main():
    """메인 앱"""
    # 상태 로드
    status = load_status()
    topic = status.get("topic", "없음")

    # 헤더
    st.markdown(f'''
    <div class="header">
        <h1>🌞 Project Sunshine</h1>
        <div class="topic-badge">{topic.upper() if topic else "대기 중"}</div>
    </div>
    ''', unsafe_allow_html=True)

    # 파이프라인
    steps = status.get("steps", [])
    if steps:
        render_pipeline(steps)
    else:
        # 기본 스텝 표시
        default_steps = [
            {"name": name, "status": "pending"}
            for name in AGENTS.keys()
        ]
        render_pipeline(default_steps)

    # 현재 단계
    render_current_step(status)

    # 진행률
    render_progress(status)

    # 시간 정보
    render_time_info(status)

    # 에러
    render_errors(status)

    # 자동 새로고침
    time.sleep(REFRESH_INTERVAL)
    st.rerun()


if __name__ == "__main__":
    main()
