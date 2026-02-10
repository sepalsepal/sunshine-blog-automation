"""
성과 차트 시각화 모듈 v1.0

기능:
- 게시물 성과 시계열 차트
- 주제별 성과 비교
- 통계 카드
- 인게이지먼트 트렌드

Author: 송지영 대리
Date: 2026-01-30
"""

import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# 경로 설정
ROOT = Path(__file__).parent.parent.parent.parent
STATS_FILE = ROOT / "config/data/instagram_stats.json"
HISTORY_FILE = ROOT / "config/settings/publishing_history.json"

# 차트 색상
CHART_COLORS = {
    "likes": "#e74c3c",
    "comments": "#3498db",
    "saves": "#2ecc71",
    "reach": "#9b59b6",
    "engagement": "#f39c12"
}


def load_instagram_stats() -> Dict[str, Any]:
    """Instagram 통계 데이터 로드"""
    if STATS_FILE.exists():
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"posts": {}, "daily_summary": []}


def load_publish_history() -> Dict[str, Any]:
    """게시 이력 로드"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"published": [], "pending": []}


def render_stats_cards(stats: Dict[str, Any]) -> None:
    """통계 카드 렌더링"""
    # summary가 있으면 사용, 없으면 계산
    summary = stats.get("summary", {})
    posts = stats.get("posts", {})

    if summary:
        total_posts = summary.get("total_posts", len(posts))
        total_likes = summary.get("total_likes", 0)
        total_comments = summary.get("total_comments", 0)
        avg_likes = summary.get("avg_likes", 0)
    else:
        total_posts = len(posts)
        # 새 형식: posts[id].likes / 구 형식: posts[id].stats.likes
        total_likes = sum(p.get("likes", p.get("stats", {}).get("likes", 0)) for p in posts.values())
        total_comments = sum(p.get("comments", p.get("stats", {}).get("comments", 0)) for p in posts.values())
        avg_likes = total_likes / total_posts if total_posts > 0 else 0

    st.markdown("""
    <style>
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        .analytics-card {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #333;
        }
        .analytics-value {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 4px;
        }
        .analytics-label {
            font-size: 0.85rem;
            color: #888;
            text-transform: uppercase;
        }
    </style>
    """, unsafe_allow_html=True)

    # 계정 정보
    account = stats.get("account", {})
    followers = account.get("followers", 0)

    cards_html = f"""
    <div class="analytics-grid">
        <div class="analytics-card">
            <div class="analytics-value" style="color: #a78bfa;">{followers}</div>
            <div class="analytics-label">Followers</div>
        </div>
        <div class="analytics-card">
            <div class="analytics-value" style="color: #f87171;">{total_likes}</div>
            <div class="analytics-label">Total Likes</div>
        </div>
        <div class="analytics-card">
            <div class="analytics-value" style="color: #60a5fa;">{total_comments}</div>
            <div class="analytics-label">Total Comments</div>
        </div>
        <div class="analytics-card">
            <div class="analytics-value" style="color: #34d399;">{avg_likes:.1f}</div>
            <div class="analytics-label">Avg Likes</div>
        </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)


def render_post_performance_chart(stats: Dict[str, Any]) -> None:
    """게시물별 성과 차트"""
    import html

    posts = stats.get("posts", {})

    if not posts:
        st.info("📊 게시물 데이터가 없습니다.")
        return

    # 데이터 준비 (새/구 형식 모두 지원)
    chart_data = []
    for post_id, data in posts.items():
        # 캡션에서 주제 추출 시도
        caption = data.get("caption_preview", "")
        topic_kr = data.get("topic_kr", "")
        if not topic_kr and caption:
            # 캡션 첫 줄에서 음식명 추출 - 이모지와 "우리 강아지도" 제거
            first_line = caption.split("\n")[0]
            # "🫒 우리 강아지도 올리브 먹어도..." -> "올리브"
            import re
            match = re.search(r'강아지도\s*(.+?)\s*먹어도', first_line)
            if match:
                topic_kr = match.group(1).strip()
            else:
                topic_kr = first_line[:10]
        if not topic_kr:
            topic_kr = post_id[:8]

        # HTML 이스케이프 (특수문자 처리)
        topic_kr = html.escape(topic_kr)

        # 날짜 처리 (timestamp 또는 publish_date)
        date = data.get("publish_date", "")
        if not date and data.get("timestamp"):
            date = data.get("timestamp", "")[:10]

        chart_data.append({
            "topic": topic_kr,
            "likes": data.get("likes", data.get("stats", {}).get("likes", 0)),
            "comments": data.get("comments", data.get("stats", {}).get("comments", 0)),
            "date": date,
            "permalink": data.get("permalink", data.get("instagram_url", ""))
        })

    # 좋아요 기준 정렬 (높은 순)
    chart_data.sort(key=lambda x: x["likes"], reverse=True)

    # 최대 10개만 표시
    chart_data = chart_data[:10]

    st.markdown("### 📊 게시물별 성과 (Top 10)")

    # Streamlit 네이티브 컴포넌트 사용
    for item in chart_data:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{item['topic']}**")
        with col2:
            st.write(f"❤️ {item['likes']}")
        with col3:
            st.write(f"💬 {item['comments']}")

        # 프로그레스 바
        max_val = max(d["likes"] for d in chart_data) or 1
        st.progress(item["likes"] / max_val)


def render_daily_trend_chart(stats: Dict[str, Any]) -> None:
    """일별 게시 트렌드"""
    posts = stats.get("posts", {})

    if not posts:
        return

    # 날짜별 집계
    daily_counts = {}
    for topic, data in posts.items():
        date = data.get("publish_date", "")
        if date:
            daily_counts[date] = daily_counts.get(date, 0) + 1

    if not daily_counts:
        return

    st.markdown("### 📈 일별 게시 현황")

    # 최근 7일
    dates = sorted(daily_counts.keys())[-7:]
    max_count = max(daily_counts.values()) or 1

    chart_html = '<div style="display: flex; align-items: flex-end; gap: 8px; height: 150px; margin: 20px 0; padding: 0 20px;">'

    for date in dates:
        count = daily_counts.get(date, 0)
        height = (count / max_count * 100)
        day = date.split("-")[-1] if date else ""

        chart_html += f"""
        <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
            <div style="width: 100%; height: {height}%; min-height: 20px; background: linear-gradient(180deg, #a78bfa 0%, #7c3aed 100%); border-radius: 4px 4px 0 0; display: flex; align-items: flex-start; justify-content: center; padding-top: 4px;">
                <span style="color: white; font-weight: 700; font-size: 14px;">{count}</span>
            </div>
            <span style="margin-top: 8px; color: #888; font-size: 12px;">{day}일</span>
        </div>
        """

    chart_html += '</div>'
    st.markdown(chart_html, unsafe_allow_html=True)


def render_top_posts(stats: Dict[str, Any], limit: int = 5) -> None:
    """상위 성과 게시물"""
    posts = stats.get("posts", {})

    if not posts:
        return

    # 좋아요 기준 정렬 (새/구 형식 모두 지원)
    sorted_posts = sorted(
        posts.items(),
        key=lambda x: x[1].get("likes", x[1].get("stats", {}).get("likes", 0)),
        reverse=True
    )[:limit]

    st.markdown("### 🏆 Top 성과 게시물")

    for i, (post_id, data) in enumerate(sorted_posts, 1):
        likes = data.get("likes", data.get("stats", {}).get("likes", 0))
        comments = data.get("comments", data.get("stats", {}).get("comments", 0))

        # 주제명 추출
        topic_kr = data.get("topic_kr", "")
        if not topic_kr:
            caption = data.get("caption_preview", "")
            if caption:
                first_line = caption.split("\n")[0]
                topic_kr = first_line[:20] + "..." if len(first_line) > 20 else first_line
            else:
                topic_kr = post_id[:8]

        url = data.get("permalink", data.get("instagram_url", ""))

        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: #1e1e2e;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 3px solid {'#ffd700' if i == 1 else '#c0c0c0' if i == 2 else '#cd7f32' if i == 3 else '#444'};
        ">
            <span style="font-size: 1.5rem; margin-right: 12px;">{medal}</span>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: #e0e0e0;">{topic_kr}</div>
                <div style="color: #888; font-size: 12px;">
                    ❤️ {likes} &nbsp;&nbsp; 💬 {comments}
                </div>
            </div>
            {'<a href="' + url + '" target="_blank" style="color: #a78bfa; text-decoration: none;">View →</a>' if url else ''}
        </div>
        """, unsafe_allow_html=True)


def render_analytics_page() -> None:
    """Analytics 페이지 렌더링"""
    st.header("📊 성과 분석")

    # 데이터 로드
    stats = load_instagram_stats()

    # 새로고침 버튼
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 새로고침", key="refresh_analytics"):
            st.rerun()

    # 통계 카드
    render_stats_cards(stats)

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 성과 차트", "📈 트렌드", "🏆 Top Posts"])

    with tab1:
        render_post_performance_chart(stats)

    with tab2:
        render_daily_trend_chart(stats)

        # 추가 인사이트
        st.markdown("### 💡 인사이트")
        posts = stats.get("posts", {})
        if posts:
            total = len(posts)
            recent_week = sum(1 for p in posts.values()
                           if p.get("publish_date", "") >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
            st.info(f"최근 7일간 **{recent_week}개** 게시물 발행 (전체 {total}개)")
        else:
            st.info("아직 게시물 데이터가 없습니다.")

    with tab3:
        render_top_posts(stats)

    # 데이터 안내
    st.divider()
    st.caption("💡 Instagram Graph API 토큰을 설정하면 실시간 통계가 자동으로 수집됩니다.")


# 단독 실행 시
if __name__ == "__main__":
    st.set_page_config(
        page_title="성과 분석",
        page_icon="📊",
        layout="wide"
    )
    render_analytics_page()
