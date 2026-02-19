"""
게시 스케줄 캘린더 뷰 모듈 v1.0

기능:
- 월간/주간 게시 일정 시각화
- 스케줄 추가/수정/삭제
- 드래그앤드롭 일정 변경 (향후)
- 게시 상태별 색상 표시
"""

import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import calendar

# 경로 설정
ROOT = Path(__file__).parent.parent.parent.parent
SCHEDULE_FILE = ROOT / "config/settings/publish_schedule.json"
HISTORY_FILE = ROOT / "config/settings/publishing_history.json"

# 상태별 색상
STATUS_COLORS = {
    "pending": "#FFA500",      # 주황
    "scheduled": "#3498db",    # 파랑
    "completed": "#27ae60",    # 초록
    "failed": "#e74c3c",       # 빨강
    "published": "#9b59b6",    # 보라
}

# 상태별 이모지
STATUS_EMOJI = {
    "pending": "⏳",
    "scheduled": "📅",
    "completed": "✅",
    "failed": "❌",
    "published": "📸",
}


def load_schedule() -> Dict[str, Any]:
    """스케줄 데이터 로드"""
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"scheduled": [], "completed": [], "failed": [], "settings": {}}


def load_history() -> Dict[str, Any]:
    """게시 이력 로드"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"published": [], "pending": []}


def save_schedule(schedule: Dict[str, Any]):
    """스케줄 저장"""
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def get_month_data(year: int, month: int) -> Dict[str, List[Dict]]:
    """월간 데이터 조회"""
    schedule = load_schedule()
    history = load_history()

    month_data = {}
    month_prefix = f"{year}-{month:02d}"

    # 스케줄된 항목
    for item in schedule.get("scheduled", []):
        date = item.get("scheduled_date", "")
        if date.startswith(month_prefix):
            if date not in month_data:
                month_data[date] = []
            month_data[date].append({
                "topic": item["topic"],
                "topic_kr": item["topic_kr"],
                "time": item.get("scheduled_time", "18:00"),
                "status": "scheduled",
                "priority": item.get("priority", 5)
            })

    # 완료된 항목
    for item in schedule.get("completed", []):
        date = item.get("scheduled_date", "")
        if date.startswith(month_prefix):
            if date not in month_data:
                month_data[date] = []
            month_data[date].append({
                "topic": item["topic"],
                "topic_kr": item["topic_kr"],
                "time": item.get("scheduled_time", "18:00"),
                "status": "completed",
                "instagram_url": item.get("result", {}).get("instagram_url", "")
            })

    # 게시 이력에서 추가
    for item in history.get("published", []):
        date = item.get("date", "")
        if date and date.startswith(month_prefix):
            # 중복 체크
            existing = [d for d in month_data.get(date, []) if d["topic"] == item["topic"]]
            if not existing:
                if date not in month_data:
                    month_data[date] = []
                month_data[date].append({
                    "topic": item["topic"],
                    "topic_kr": item.get("topic_kr", item["topic"]),
                    "time": "18:00",
                    "status": "published",
                    "instagram_url": item.get("instagram_url", ""),
                    "score": item.get("score")
                })

    return month_data


def render_month_calendar(year: int, month: int):
    """월간 캘린더 렌더링"""
    month_data = get_month_data(year, month)

    # 월 이름
    month_name = calendar.month_name[month]
    st.subheader(f"📅 {year}년 {month}월 ({month_name})")

    # 달력 생성
    cal = calendar.Calendar(firstweekday=0)  # 월요일 시작
    month_days = cal.monthdayscalendar(year, month)
    today = datetime.now()

    # 전체 캘린더 HTML 생성
    calendar_html = """
    <style>
        .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
        .cal-header { text-align: center; font-weight: bold; padding: 8px; }
        .cal-header.sat { color: #3498db; }
        .cal-header.sun { color: #e74c3c; }
        .cal-day {
            background: #1e1e2e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 8px;
            min-height: 90px;
        }
        .cal-day.today { border: 2px solid #3498db; background: #1a3a4a; }
        .cal-day.empty { background: transparent; border: none; }
        .day-num { font-weight: bold; margin-bottom: 4px; color: #e0e0e0; }
        .day-num.sat { color: #3498db; }
        .day-num.sun { color: #e74c3c; }
        .cal-event {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            margin: 2px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: white;
        }
    </style>
    <div class="cal-grid">
    """

    # 요일 헤더
    days = ["월", "화", "수", "목", "금", "토", "일"]
    for i, day in enumerate(days):
        day_class = "sat" if i == 5 else "sun" if i == 6 else ""
        calendar_html += f'<div class="cal-header {day_class}">{day}</div>'

    # 날짜 셀
    for week in month_days:
        for i, day in enumerate(week):
            if day == 0:
                calendar_html += '<div class="cal-day empty"></div>'
                continue

            date_str = f"{year}-{month:02d}-{day:02d}"
            date_obj = datetime(year, month, day)
            is_today = (date_obj.date() == today.date())

            day_class = "today" if is_today else ""
            num_class = "sat" if i == 5 else "sun" if i == 6 else ""

            calendar_html += f'<div class="cal-day {day_class}">'
            calendar_html += f'<div class="day-num {num_class}">{day}</div>'

            # 이벤트
            if date_str in month_data:
                for event in month_data[date_str]:
                    emoji = STATUS_EMOJI.get(event["status"], "📌")
                    color = STATUS_COLORS.get(event["status"], "#999")
                    topic_kr = event["topic_kr"]
                    topic_short = topic_kr[:6] if len(topic_kr) > 6 else topic_kr
                    event_time = event["time"]

                    calendar_html += f'<div class="cal-event" style="background:{color};" title="{topic_kr} ({event_time})">{emoji} {topic_short}</div>'

            calendar_html += '</div>'

    calendar_html += '</div>'

    st.markdown(calendar_html, unsafe_allow_html=True)


def render_upcoming_list(days: int = 7):
    """향후 N일 일정 목록"""
    schedule = load_schedule()

    st.subheader(f"📋 향후 {days}일 일정")

    today = datetime.now()
    end_date = today + timedelta(days=days)

    upcoming = []
    for item in schedule.get("scheduled", []):
        try:
            date = datetime.strptime(item["scheduled_date"], "%Y-%m-%d")
            if today.date() <= date.date() <= end_date.date():
                upcoming.append(item)
        except:
            continue

    if not upcoming:
        st.info("예정된 게시가 없습니다.")
        return

    # 날짜순 정렬
    upcoming.sort(key=lambda x: x["scheduled_date"])

    for item in upcoming:
        date = datetime.strptime(item["scheduled_date"], "%Y-%m-%d")
        days_until = (date.date() - today.date()).days

        if days_until == 0:
            date_label = "오늘"
            bg = "#fff3cd"
        elif days_until == 1:
            date_label = "내일"
            bg = "#d4edda"
        else:
            date_label = f"{days_until}일 후"
            bg = "#f8f9fa"

        emoji = "🔥" if item.get("priority", 5) >= 8 else "📅"

        st.markdown(f"""
        <div style='
            background:{bg};
            padding:12px;
            border-radius:8px;
            margin:8px 0;
            border-left:4px solid {STATUS_COLORS["scheduled"]};
        '>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <strong>{emoji} {item["topic_kr"]}</strong>
                    <span style='color:#666;margin-left:8px;'>({item["topic"]})</span>
                </div>
                <div style='color:#666;'>
                    {item["scheduled_date"]} {item.get("scheduled_time", "18:00")}
                    <span style='
                        background:#3498db;
                        color:white;
                        padding:2px 8px;
                        border-radius:12px;
                        margin-left:8px;
                        font-size:12px;
                    '>{date_label}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_add_schedule_form():
    """스케줄 추가 폼"""
    st.subheader("➕ 새 스케줄 추가")

    with st.form("add_schedule"):
        col1, col2 = st.columns(2)

        with col1:
            topic = st.text_input("영문 주제명", placeholder="avocado")
            topic_kr = st.text_input("한글 주제명", placeholder="아보카도")

        with col2:
            date = st.date_input("게시 날짜", datetime.now() + timedelta(days=1))
            time = st.time_input("게시 시간", datetime.strptime("18:00", "%H:%M").time())

        priority = st.slider("우선순위", 1, 10, 5)

        if st.form_submit_button("추가", type="primary"):
            if topic and topic_kr:
                schedule = load_schedule()

                new_item = {
                    "id": len(schedule.get("scheduled", [])) + len(schedule.get("completed", [])) + 1,
                    "topic": topic,
                    "topic_kr": topic_kr,
                    "scheduled_date": date.strftime("%Y-%m-%d"),
                    "scheduled_time": time.strftime("%H:%M"),
                    "priority": priority,
                    "status": "pending",
                    "retries": 0,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                schedule.setdefault("scheduled", []).append(new_item)
                save_schedule(schedule)

                st.success(f"✅ '{topic_kr}' 스케줄 추가 완료!")
                st.rerun()
            else:
                st.error("주제명을 입력해주세요.")


def sync_all_data():
    """데이터 동기화 실행"""
    try:
        from core.utils.sync_manager import sync_all_data as _sync
        return _sync()
    except Exception as e:
        return {"error": str(e)}


def render_calendar_page():
    """캘린더 페이지 렌더링"""
    st.header("📅 게시 스케줄 캘린더")

    # 페이지 로드 시 자동 동기화 (세션당 1회)
    if "calendar_synced" not in st.session_state:
        sync_all_data()
        st.session_state.calendar_synced = True

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["월간 캘린더", "향후 일정", "스케줄 추가"])

    with tab1:
        # 월 선택
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            year = st.selectbox("년도", range(2026, 2028), index=0)
        with col2:
            month = st.selectbox("월", range(1, 13), index=datetime.now().month - 1)

        render_month_calendar(year, month)

    with tab2:
        days = st.selectbox("기간", [7, 14, 30], format_func=lambda x: f"{x}일")
        render_upcoming_list(days)

    with tab3:
        render_add_schedule_form()

    # 범례
    st.divider()
    st.caption("**범례:**")
    legend_cols = st.columns(5)
    for i, (status, color) in enumerate(STATUS_COLORS.items()):
        with legend_cols[i]:
            emoji = STATUS_EMOJI.get(status, "📌")
            label = {
                "pending": "대기",
                "scheduled": "예정",
                "completed": "완료",
                "failed": "실패",
                "published": "게시됨"
            }.get(status, status)
            st.markdown(f"""
            <span style='
                background:{color};
                color:white;
                padding:4px 8px;
                border-radius:4px;
                font-size:12px;
            '>{emoji} {label}</span>
            """, unsafe_allow_html=True)


# 단독 실행 시
if __name__ == "__main__":
    st.set_page_config(
        page_title="게시 캘린더",
        page_icon="📅",
        layout="wide"
    )
    render_calendar_page()
