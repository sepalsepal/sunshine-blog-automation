#!/usr/bin/env python3
"""
API 비용 분석 대시보드 - fal.ai 스타일
깔끔하고 미래적인 UI
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 모듈 경로 추가
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from services.dashboard.api_usage_tracker import (
    get_tracker, API_PRICING, log_fal_usage
)

# 페이지 설정 (독립 실행 시에만 적용, app.py에서 호출 시 무시됨)
try:
    st.set_page_config(
        page_title="Usage & Billing - Project Sunshine",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except st.errors.StreamlitAPIException:
    pass


def format_currency(amount: float) -> str:
    """통화 포맷팅"""
    return f"${amount:,.2f}"


def format_krw(amount: float, rate: float = 1400) -> str:
    """원화 변환"""
    return f"₩{amount * rate:,.0f}"


def main():
    """메인 앱"""
    tracker = get_tracker()
    stats = tracker.get_api_stats()
    report = tracker.export_report()

    # 페이지 헤더 (다크모드 - app.py 통합)
    st.markdown('''
    <div class="page-header">
        <h1 class="page-title">Usage & Billing</h1>
        <p class="page-subtitle">API 사용량과 비용을 한눈에 확인하세요</p>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("")

    # ==========================================
    # 크레딧/비용 카드
    # ==========================================
    total_cost = report["summary"]["total_cost_usd"]
    month_cost = report["summary"]["month_cost_usd"]

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card st-published">
            <div class="stat-value" style="color: #34d399;">{format_currency(total_cost)}</div>
            <div class="stat-label">Total Spend</div>
        </div>
        <div class="stat-card st-ready">
            <div class="stat-value" style="color: #22d3ee;">{format_currency(month_cost)}</div>
            <div class="stat-label">This Month</div>
        </div>
        <div class="stat-card st-cover">
            <div class="stat-value" style="color: #fbbf24;">{format_krw(month_cost)}</div>
            <div class="stat-label">KRW Estimate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # Usage Breakdown 차트 (다크모드)
    # ==========================================
    daily_data = tracker.data.get("daily_summary", {})
    dates = sorted(daily_data.keys())[-7:]

    st.markdown('<div class="section-title" style="margin-top:1.5rem;">Usage Breakdown</div>', unsafe_allow_html=True)

    if dates:
        max_cost = max(
            sum(v.get("cost", 0) for v in daily_data.get(d, {}).values())
            for d in dates
        ) or 1

        bars_html = ""
        labels_html = ""
        colors = ["#7c3aed", "#f97316", "#10b981", "#3b82f6", "#8b5cf6", "#fb923c", "#34d399"]

        for i, date in enumerate(dates):
            day_data = daily_data.get(date, {})
            day_cost = sum(v.get("cost", 0) for v in day_data.values())
            height_pct = (day_cost / max_cost) * 100 if max_cost > 0 else 0
            height_pct = max(height_pct, 5)
            color = colors[i % len(colors)]
            day_label = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
            bars_html += f'''<div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:0.3rem;">
                <span style="font-size:0.6rem; color:#6e6e84;">${day_cost:.2f}</span>
                <div style="width:100%; height:{height_pct}%; min-height:4px; background:linear-gradient(180deg,{color},{color}88); border-radius:4px 4px 0 0;"></div>
                <span style="font-size:0.6rem; color:#4e4e64;">{day_label}</span>
            </div>'''

        st.markdown(f'''
        <div style="background:#111117; border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:1.2rem; margin-bottom:1.2rem;">
            <div style="display:flex; align-items:flex-end; gap:6px; height:160px;">
                {bars_html}
            </div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#111117; border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:2rem; text-align:center; color:#4e4e64; margin-bottom:1.2rem;">No chart data available</div>', unsafe_allow_html=True)

    # ==========================================
    # Usage per model 테이블 (st.dataframe 사용 - 안정적)
    # ==========================================
    st.markdown('<div class="section-title">Usage per Model</div>', unsafe_allow_html=True)

    import pandas as pd

    table_data = []
    for api_key, pricing in API_PRICING.items():
        api_stat = stats.get(api_key, {})
        month_count = api_stat.get("month_count", 0)
        month_cost = api_stat.get("month_cost", 0.0)

        if api_key == "anthropic":
            unit, unit_price = "Tokens", "$3.00/1M"
        elif api_key == "fal_ai":
            unit, unit_price = "Images", "$0.05"
        elif api_key == "cloudinary":
            unit, unit_price = "Uploads", "Free"
        else:
            unit, unit_price = "Requests", "Free"

        table_data.append({
            "Model": pricing.get("model_id", api_key),
            "Quantity": f"{month_count:,.2f}",
            "Unit": unit,
            "Price": unit_price,
            "Cost": format_currency(month_cost)
        })

    table_data = sorted(table_data, key=lambda x: float(x["Cost"].replace("$", "").replace(",", "")), reverse=True)

    # DataFrame으로 변환하여 표시
    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Model": st.column_config.TextColumn("Model", width="medium"),
            "Quantity": st.column_config.TextColumn("Qty", width="small"),
            "Unit": st.column_config.TextColumn("Unit", width="small"),
            "Price": st.column_config.TextColumn("Price", width="small"),
            "Cost": st.column_config.TextColumn("Cost", width="small"),
        }
    )

    # ==========================================
    # 비용 예측 (다크모드)
    # ==========================================
    proj = report["projection"]
    st.markdown('<div class="section-title">Cost Projection</div>', unsafe_allow_html=True)

    st.markdown(f'''
    <div style="display:flex; gap:0.8rem; margin-bottom:1.2rem;">
        <div style="flex:1; background:#111117; border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:1.2rem; text-align:center;">
            <div style="font-size:0.7rem; color:#4e4e64; text-transform:uppercase; letter-spacing:0.1em; font-weight:700; margin-bottom:0.4rem;">Daily Avg</div>
            <div style="font-size:1.5rem; font-weight:800; color:#d8d8e4;">{format_currency(proj["avg_daily_cost"])}</div>
        </div>
        <div style="flex:1; background:#111117; border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:1.2rem; text-align:center;">
            <div style="font-size:0.7rem; color:#4e4e64; text-transform:uppercase; letter-spacing:0.1em; font-weight:700; margin-bottom:0.4rem;">Monthly Est.</div>
            <div style="font-size:1.5rem; font-weight:800; color:#7c3aed;">{format_currency(proj["projected_monthly"])}</div>
        </div>
        <div style="flex:1; background:#111117; border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:1.2rem; text-align:center;">
            <div style="font-size:0.7rem; color:#4e4e64; text-transform:uppercase; letter-spacing:0.1em; font-weight:700; margin-bottom:0.4rem;">KRW Est.</div>
            <div style="font-size:1.5rem; font-weight:800; color:#fbbf24;">{format_krw(proj["projected_monthly"])}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
