#!/usr/bin/env python3
"""
Project Sunshine - Content Manager
Premium AI Content Management Platform

Design System: Linear/Vercel + Runway/Pika inspired
- Near-black background (#08090a)
- Glassmorphism cards with backdrop-blur
- Inter Variable typography
- Smooth micro-interactions
- Bento grid layout

실행: streamlit run services/dashboard/content_manager.py
"""

import asyncio
import base64
import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
from dotenv import load_dotenv

# Import publisher agent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project_sunshine/
try:
    from core.agents.publisher import PublisherAgent
    PUBLISHER_AVAILABLE = True
except ImportError:
    PUBLISHER_AVAILABLE = False

# .env 파일 로드 (로컬 개발용)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Cloudinary 설정
import cloudinary
import cloudinary.api

def init_cloudinary():
    """Cloudinary 초기화"""
    cloud_name = get_secret("CLOUDINARY_CLOUD_NAME")
    api_key = get_secret("CLOUDINARY_API_KEY")
    api_secret = get_secret("CLOUDINARY_API_SECRET")

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        return True
    return False

CLOUDINARY_AVAILABLE = False  # Will be set after get_secret is defined

def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variable.

    Priority:
    1. Streamlit secrets (for Streamlit Cloud deployment)
    2. Environment variables (for local development)
    3. Default value
    """
    # Try Streamlit secrets first (for Cloud deployment)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    # Fall back to environment variables (for local development)
    return os.getenv(key, default)

# 경로 설정
ROOT = Path(__file__).parent.parent.parent  # project_sunshine/
DASHBOARD_DIR = Path(__file__).parent  # services/dashboard/
IMAGES_DIR = ROOT / "content" / "images"
SCHEDULE_FILE = DASHBOARD_DIR / "schedule.json"
HISTORY_FILE = DASHBOARD_DIR / "publish_history.json"
QUEUE_FILE = DASHBOARD_DIR / "work_queue.json"
TAGS_FILE = DASHBOARD_DIR / "content_tags.json"
METADATA_FILE = DASHBOARD_DIR / "content_metadata.json"

# Cloudinary 초기화 (get_secret 정의 후)
CLOUDINARY_AVAILABLE = init_cloudinary()

def get_cloudinary_content_folders() -> List[Dict[str, Any]]:
    """Cloudinary에서 콘텐츠 폴더 목록 조회 (리소스에서 폴더 추출)"""
    contents = []

    if not CLOUDINARY_AVAILABLE:
        return contents

    try:
        # 모든 리소스 가져오기
        result = cloudinary.api.resources(type="upload", max_results=500)
        resources = result.get("resources", [])

        # public_id에서 폴더명 추출
        folder_resources = {}
        for r in resources:
            public_id = r.get("public_id", "")
            if "/" in public_id:
                folder_name = public_id.split("/")[0]
                if folder_name and not folder_name.startswith('.'):
                    if folder_name not in folder_resources:
                        folder_resources[folder_name] = []
                    folder_resources[folder_name].append(r)

        # 각 폴더별로 콘텐츠 생성
        for folder_name, images in sorted(folder_resources.items()):
            # 이미지를 파일명 기준으로 정렬
            images = sorted(images, key=lambda x: x.get("public_id", ""))

            # display_name 추출 (001_pumpkin_published -> PUMPKIN)
            parts = folder_name.split('_', 1)
            display_name = parts[1].upper() if len(parts) > 1 else folder_name.upper()
            display_name = display_name.replace('_PUBLISHED', '').replace('_DRAFT', '').replace('_', ' ')

            content_info = {
                "name": folder_name,
                "display_name": display_name,
                "path": folder_name,
                "image_count": len(images),
                "images": [img.get("secure_url") for img in images],
                "thumbnail": images[0].get("secure_url") if images else "",
                "created": datetime.fromisoformat(images[0].get("created_at", "").replace("Z", "+00:00")) if images and images[0].get("created_at") else datetime.now(),
                "status": "draft",
                "tags": [],
                "source": "cloudinary"
            }

            # 폴더명에서 상태 추출
            if "published" in folder_name.lower():
                content_info["status"] = "published"

            contents.append(content_info)

    except Exception as e:
        print(f"Cloudinary API error: {e}")

    return contents

# Predefined tags with colors
AVAILABLE_TAGS = {
    "fruit": {"label": "Fruit", "color": "#ef4444", "icon": "🍎"},
    "vegetable": {"label": "Vegetable", "color": "#22c55e", "icon": "🥬"},
    "safe": {"label": "Safe", "color": "#10b981", "icon": "✅"},
    "caution": {"label": "Caution", "color": "#f59e0b", "icon": "⚠️"},
    "danger": {"label": "Danger", "color": "#ef4444", "icon": "🚫"},
    "trending": {"label": "Trending", "color": "#8b5cf6", "icon": "🔥"},
    "popular": {"label": "Popular", "color": "#ec4899", "icon": "⭐"},
    "seasonal": {"label": "Seasonal", "color": "#06b6d4", "icon": "🌸"},
    "new": {"label": "New", "color": "#3b82f6", "icon": "🆕"},
}

# 페이지 설정
st.set_page_config(
    page_title="Sunshine Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PREMIUM CSS - Inspired by Linear, Vercel, Runway, Pika
# ============================================================
def get_theme_css():
    """Generate CSS based on current theme setting"""
    theme = st.session_state.get("settings", {}).get("theme", "dark")

    if theme == "light":
        return """
        /* Light Theme Variables */
        --bg-primary: #ffffff;
        --bg-secondary: #f8f9fa;
        --bg-tertiary: #f1f3f4;
        --bg-elevated: #ffffff;

        /* Glass effects - Light */
        --glass-bg: rgba(0, 0, 0, 0.02);
        --glass-border: rgba(0, 0, 0, 0.08);
        --glass-hover: rgba(0, 0, 0, 0.05);

        /* Text hierarchy - Light */
        --text-primary: rgba(0, 0, 0, 0.9);
        --text-secondary: rgba(0, 0, 0, 0.6);
        --text-tertiary: rgba(0, 0, 0, 0.4);
        """
    else:  # dark (default)
        return """
        /* Dark Theme Variables */
        --bg-primary: #08090a;
        --bg-secondary: #0f1012;
        --bg-tertiary: #161719;
        --bg-elevated: #1a1b1e;

        /* Glass effects - Dark */
        --glass-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.06);
        --glass-hover: rgba(255, 255, 255, 0.08);

        /* Text hierarchy - Dark */
        --text-primary: rgba(255, 255, 255, 0.95);
        --text-secondary: rgba(255, 255, 255, 0.65);
        --text-tertiary: rgba(255, 255, 255, 0.4);
        """


theme_vars = get_theme_css()

st.markdown("""
<style>
    /* ========================================
       1. FOUNDATIONS - Typography & Variables
       ======================================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        /* Dynamic Theme Colors - injected via separate style tag */

        /* Accent - Purple/Violet gradient (same for both themes) */
        --accent-start: #a855f7;
        --accent-end: #6366f1;
        --accent-glow: rgba(168, 85, 247, 0.25);

        /* Status colors */
        --status-live: #22c55e;
        --status-scheduled: #3b82f6;
        --status-draft: rgba(128, 128, 128, 0.6);

        /* Spacing */
        --space-xs: 4px;
        --space-sm: 8px;
        --space-md: 16px;
        --space-lg: 24px;
        --space-xl: 32px;

        /* Border radius */
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 16px;
        --radius-xl: 20px;

        /* Transitions */
        --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-smooth: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* ========================================
       2. GLOBAL STYLES
       ======================================== */
    .stApp {
        background: var(--bg-primary) !important;
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(120, 119, 198, 0.15), transparent),
            radial-gradient(ellipse 60% 40% at 100% 100%, rgba(168, 85, 247, 0.08), transparent) !important;
    }

    .main .block-container {
        padding: 1.5rem 2.5rem 3rem !important;
        max-width: 1600px !important;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, .stDeployButton,
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* ========================================
       3. SIDEBAR - Premium Glass Effect
       ======================================== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            rgba(15, 16, 18, 0.98) 0%,
            rgba(8, 9, 10, 0.99) 100%
        ) !important;
        border-right: 1px solid var(--glass-border) !important;
        min-width: 240px !important;
    }

    /* Ensure sidebar is visible */
    section[data-testid="stSidebar"][aria-expanded="true"] {
        transform: translateX(0) !important;
        visibility: visible !important;
    }

    /* Hide collapse button temporarily to prevent accidental hiding */
    button[data-testid="baseButton-headerNoPadding"] {
        opacity: 0.3;
    }
    button[data-testid="baseButton-headerNoPadding"]:hover {
        opacity: 1;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: var(--radius-sm) !important;
        transition: var(--transition-fast) !important;
        text-align: left !important;
        justify-content: flex-start !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 0.15rem !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: var(--glass-hover) !important;
        color: var(--text-primary) !important;
        border-color: var(--glass-border) !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: rgba(168, 85, 247, 0.15) !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        color: #c084fc !important;
        font-weight: 600 !important;
    }

    /* ========================================
       4. HEADER SECTION - Hero Style
       ======================================== */
    .main-header {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-xl);
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(168, 85, 247, 0.5),
            rgba(99, 102, 241, 0.5),
            transparent
        );
    }

    .main-header h1 {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.8) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.5rem 0;
    }

    .main-header p {
        color: var(--text-secondary);
        font-size: 0.95rem;
        font-weight: 400;
        margin: 0;
        letter-spacing: -0.01em;
    }

    /* ========================================
       5. STAT CARDS - Bento Grid Style
       ======================================== */
    .stat-card {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-lg);
        padding: 1.5rem 1.25rem;
        text-align: center;
        transition: var(--transition-smooth);
        position: relative;
        overflow: hidden;
        min-width: 120px;
    }

    .stat-card:hover {
        background: var(--glass-hover);
        border-color: rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
    }

    .stat-number {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: var(--text-primary);
        line-height: 1;
    }

    .stat-label {
        font-size: 0.65rem;
        font-weight: 600;
        color: var(--text-tertiary);
        margin-top: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        white-space: nowrap;
    }

    /* ========================================
       6. CONTENT CARDS - Premium Thumbnails
       ======================================== */
    .content-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-lg);
        padding: 12px;
        transition: var(--transition-smooth);
        position: relative;
    }

    .content-card:hover {
        background: var(--glass-hover);
        border-color: rgba(255, 255, 255, 0.12);
        transform: translateY(-4px);
        box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.5);
    }

    /* Instagram 4:5 Thumbnail */
    .insta-thumb {
        position: relative;
        width: 100%;
        padding-top: 125%; /* 4:5 ratio */
        overflow: hidden;
        border-radius: var(--radius-md);
        background: var(--bg-tertiary);
    }

    .insta-thumb img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: var(--radius-md);
        transition: var(--transition-smooth);
    }

    .content-card:hover .insta-thumb img {
        transform: scale(1.03);
    }

    /* Quick Actions Overlay */
    .quick-actions {
        position: absolute;
        top: 12px;
        right: 12px;
        left: 12px;
        display: flex;
        gap: 6px;
        justify-content: flex-end;
        opacity: 0;
        transition: opacity 0.2s ease;
        z-index: 10;
    }

    .content-card:hover .quick-actions {
        opacity: 1;
    }

    .quick-action-btn {
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s ease;
    }

    .quick-action-btn:hover {
        background: rgba(168, 85, 247, 0.8);
        transform: scale(1.1);
    }

    /* Hide card click buttons - only show hover actions */
    [data-testid="stButton"][key^="card_"] button,
    div[data-testid="column"] > div > div > button[kind="secondary"] {
        height: 4px !important;
        min-height: 4px !important;
        padding: 0 !important;
        margin: 0 !important;
        opacity: 0 !important;
        border: none !important;
        background: transparent !important;
    }

    .quick-action-btn.delete:hover {
        background: rgba(239, 68, 68, 0.8);
    }

    /* Content info */
    .content-info {
        padding: var(--space-sm) 0 0 0;
    }

    .content-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.01em;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 60%;
    }

    .content-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: var(--space-xs);
        gap: 4px;
    }

    .content-count {
        font-size: 0.7rem;
        color: var(--text-tertiary);
        font-weight: 500;
    }

    /* ========================================
       7. STATUS BADGES - Refined Pills
       ======================================== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 2px 6px;
        border-radius: 100px;
        font-size: 0.55rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .status-live {
        background: rgba(34, 197, 94, 0.12);
        color: var(--status-live);
        border: 1px solid rgba(34, 197, 94, 0.25);
    }

    .status-live::before {
        content: '';
        width: 5px;
        height: 5px;
        background: var(--status-live);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .status-scheduled {
        background: rgba(59, 130, 246, 0.12);
        color: var(--status-scheduled);
        border: 1px solid rgba(59, 130, 246, 0.25);
    }

    .status-draft {
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-tertiary);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* ========================================
       8. BUTTONS - Premium Gradient Style
       ======================================== */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-start), var(--accent-end)) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        padding: 0.5rem 0.85rem !important;
        border-radius: var(--radius-md) !important;
        transition: var(--transition-fast) !important;
        box-shadow: 0 4px 12px var(--accent-glow) !important;
        letter-spacing: -0.01em !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 24px var(--accent-glow) !important;
        filter: brightness(1.1) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--text-secondary) !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: var(--glass-hover) !important;
        color: var(--text-primary) !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    /* Quick action buttons (icon buttons in content cards) */
    div[data-testid="column"] .stButton > button:has(span:only-child) {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: rgba(255, 255, 255, 0.6) !important;
        box-shadow: none !important;
        padding: 0.35rem 0.5rem !important;
        min-height: unset !important;
        font-size: 0.85rem !important;
    }

    div[data-testid="column"] .stButton > button:has(span:only-child):hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        transform: none !important;
    }

    /* ========================================
       9. FORM INPUTS - Minimal Style
       ======================================== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-size: 0.8rem !important;
        padding: 0.6rem 0.85rem !important;
        transition: var(--transition-fast) !important;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: var(--accent-start) !important;
        box-shadow: 0 0 0 2px var(--accent-glow) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: var(--text-tertiary) !important;
    }

    /* Sidebar selectbox styling */
    section[data-testid="stSidebar"] .stSelectbox > div > div > div {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        font-size: 0.7rem !important;
        padding: 0.4rem 0.6rem !important;
        border-radius: 6px !important;
        min-height: auto !important;
    }

    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span {
        font-size: 0.7rem !important;
        color: rgba(255,255,255,0.8) !important;
    }

    section[data-testid="stSidebar"] .stSelectbox svg {
        width: 14px !important;
        height: 14px !important;
    }

    /* ========================================
       10. TABS - Underline Style
       ======================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: transparent;
        border-bottom: 1px solid var(--glass-border);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-tertiary) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        padding: 1rem 1.5rem !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        transition: var(--transition-fast) !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-secondary) !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--text-primary) !important;
        border-bottom-color: var(--accent-start) !important;
    }

    /* ========================================
       11. DIVIDERS & SPACING
       ======================================== */
    hr {
        border: none;
        border-top: 1px solid var(--glass-border);
        margin: var(--space-lg) 0;
    }

    /* ========================================
       12. SLIDER - Custom Style
       ======================================== */
    .stSlider > div > div > div {
        background: var(--bg-tertiary) !important;
    }

    .stSlider > div > div > div > div {
        background: linear-gradient(135deg, var(--accent-start), var(--accent-end)) !important;
    }

    /* ========================================
       13. METRICS - Sidebar Stats
       ======================================== */
    [data-testid="stMetric"] {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-md);
        padding: 0.75rem 0.5rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.6rem !important;
        color: var(--text-tertiary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.03em !important;
    }

    /* ========================================
       14. SCROLLBAR - Minimal
       ======================================== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* ========================================
       15. ANIMATIONS
       ======================================== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .content-card {
        animation: fadeIn 0.4s ease-out forwards;
    }

    /* ========================================
       16. CHECKBOX - Selection Style
       ======================================== */
    .stCheckbox > label > div {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 4px !important;
    }

    .stCheckbox > label > div[data-checked="true"] {
        background: linear-gradient(135deg, var(--accent-start), var(--accent-end)) !important;
        border-color: var(--accent-start) !important;
    }

    /* ========================================
       17. BULK ACTION BAR
       ======================================== */
    .bulk-action-bar {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(139, 92, 246, 0.1));
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
    }

    .bulk-count {
        background: rgba(168, 85, 247, 0.3);
        color: #c084fc;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* ========================================
       18. TOAST NOTIFICATIONS
       ======================================== */
    .toast-container {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .toast {
        background: rgba(20, 22, 25, 0.95);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0.875rem 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: toastIn 0.3s ease-out forwards;
        max-width: 320px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }

    .toast.success {
        border-left: 3px solid #22c55e;
    }

    .toast.error {
        border-left: 3px solid #ef4444;
    }

    .toast.warning {
        border-left: 3px solid #f59e0b;
    }

    .toast.info {
        border-left: 3px solid #3b82f6;
    }

    .toast-icon {
        font-size: 1.1rem;
    }

    .toast-message {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.85rem;
        font-weight: 500;
    }

    @keyframes toastIn {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes toastOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }

    /* ========================================
       19. KEYBOARD SHORTCUTS HELP
       ======================================== */
    .shortcuts-modal {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(20, 22, 25, 0.98);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        z-index: 10000;
        min-width: 400px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }

    .shortcuts-modal h3 {
        color: #fff;
        margin: 0 0 1.5rem 0;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .shortcut-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .shortcut-key {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 6px;
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-family: monospace;
        color: rgba(255, 255, 255, 0.8);
    }

    .shortcut-desc {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.85rem;
    }

    /* ========================================
       20. SKELETON LOADING
       ======================================== */
    .skeleton {
        background: linear-gradient(
            90deg,
            rgba(255, 255, 255, 0.03) 0%,
            rgba(255, 255, 255, 0.08) 50%,
            rgba(255, 255, 255, 0.03) 100%
        );
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 8px;
    }

    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    .skeleton-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-lg);
        padding: 12px;
    }

    .skeleton-thumb {
        width: 100%;
        padding-top: 125%;
        border-radius: var(--radius-md);
    }

    .skeleton-text {
        height: 12px;
        margin-top: 12px;
        width: 80%;
    }

    .skeleton-text-short {
        height: 10px;
        margin-top: 8px;
        width: 50%;
    }

    /* ========================================
       21. EMPTY STATES
       ======================================== */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        background: var(--glass-bg);
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-lg);
        margin: 2rem 0;
    }

    .empty-state-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        opacity: 0.6;
    }

    .empty-state-title {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
    }

    .empty-state-desc {
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.9rem;
        margin: 0 0 1.5rem 0;
        max-width: 400px;
        margin-left: auto;
        margin-right: auto;
    }

    .empty-state-action {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 500;
        font-size: 0.9rem;
        transition: var(--transition-fast);
    }

    .empty-state-action:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(168, 85, 247, 0.3);
    }

    /* ========================================
       22. LIGHTBOX / IMAGE PREVIEW MODAL
       ======================================== */
    .lightbox-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.95);
        backdrop-filter: blur(20px);
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeInOverlay 0.2s ease-out;
    }

    @keyframes fadeInOverlay {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    .lightbox-content {
        position: relative;
        max-width: 90vw;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .lightbox-image {
        max-width: 100%;
        max-height: 80vh;
        object-fit: contain;
        border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        animation: zoomIn 0.3s ease-out;
    }

    @keyframes zoomIn {
        from { transform: scale(0.9); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }

    .lightbox-close {
        position: absolute;
        top: -50px;
        right: 0;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.25rem;
        transition: all 0.2s ease;
    }

    .lightbox-close:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: scale(1.1);
    }

    .lightbox-nav {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.5rem;
        transition: all 0.2s ease;
    }

    .lightbox-nav:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-50%) scale(1.1);
    }

    .lightbox-prev {
        left: -70px;
    }

    .lightbox-next {
        right: -70px;
    }

    .lightbox-info {
        margin-top: 1rem;
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
    }

    .lightbox-counter {
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .lightbox-filename {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.4);
    }

    .lightbox-thumbnails {
        display: flex;
        gap: 8px;
        margin-top: 1rem;
        overflow-x: auto;
        padding: 0.5rem 0;
        max-width: 80vw;
    }

    .lightbox-thumb {
        width: 60px;
        height: 60px;
        object-fit: cover;
        border-radius: 6px;
        cursor: pointer;
        opacity: 0.5;
        transition: all 0.2s ease;
        border: 2px solid transparent;
    }

    .lightbox-thumb:hover {
        opacity: 0.8;
    }

    .lightbox-thumb.active {
        opacity: 1;
        border-color: #a855f7;
    }

    /* Clickable thumbnail in grid */
    .clickable-thumb {
        cursor: pointer;
        transition: all 0.2s ease;
        border-radius: 8px;
        overflow: hidden;
    }

    .clickable-thumb:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.3);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA FUNCTIONS
# ============================================================
def get_content_folders() -> List[Dict[str, Any]]:
    """콘텐츠 폴더 목록 조회 (로컬 우선, Cloudinary 폴백)"""
    contents = []

    # 1. 로컬 이미지 폴더 확인
    if IMAGES_DIR.exists():
        for folder in sorted(IMAGES_DIR.iterdir()):
            if folder.is_dir() and not folder.name.startswith('.') and folder.name != 'reference':
                images = sorted(list(folder.glob("*.png")) + list(folder.glob("*.jpg")))

                if images:
                    parts = folder.name.split('_', 1)
                    display_name = parts[1].upper() if len(parts) > 1 else folder.name.upper()

                    content_info = {
                        "name": folder.name,
                        "display_name": display_name,
                        "path": str(folder),
                        "image_count": len(images),
                        "images": [str(img) for img in images],
                        "thumbnail": str(images[0]),
                        "created": datetime.fromtimestamp(folder.stat().st_mtime),
                        "status": "draft",
                        "tags": get_content_tags(folder.name),
                        "source": "local"
                    }

                    # 게시 히스토리 확인
                    history = load_history()
                    if folder.name in history:
                        content_info["status"] = "published"

                    # 스케줄 확인
                    schedule = load_schedule()
                    if folder.name in schedule and content_info["status"] != "published":
                        content_info["status"] = "scheduled"

                    contents.append(content_info)

    # 2. 로컬에 콘텐츠가 없으면 Cloudinary에서 가져오기
    if not contents and CLOUDINARY_AVAILABLE:
        contents = get_cloudinary_content_folders()

    return contents


def load_schedule() -> Dict:
    try:
        if SCHEDULE_FILE.exists():
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_schedule(schedule: Dict):
    SCHEDULE_FILE.parent.mkdir(exist_ok=True)
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2, default=str)


def load_history() -> Dict:
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_history(history: Dict):
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2, default=str)


def load_tags() -> Dict[str, List[str]]:
    """Load content tags from file"""
    try:
        if TAGS_FILE.exists():
            with open(TAGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_tags(tags: Dict[str, List[str]]):
    """Save content tags to file"""
    TAGS_FILE.parent.mkdir(exist_ok=True)
    with open(TAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)


def get_content_tags(content_name: str) -> List[str]:
    """Get tags for a specific content"""
    tags = load_tags()
    return tags.get(content_name, [])


def set_content_tags(content_name: str, tag_list: List[str]):
    """Set tags for a specific content"""
    tags = load_tags()
    tags[content_name] = tag_list
    save_tags(tags)


def add_content_tag(content_name: str, tag: str):
    """Add a tag to content"""
    tags = load_tags()
    if content_name not in tags:
        tags[content_name] = []
    if tag not in tags[content_name]:
        tags[content_name].append(tag)
    save_tags(tags)


def remove_content_tag(content_name: str, tag: str):
    """Remove a tag from content"""
    tags = load_tags()
    if content_name in tags and tag in tags[content_name]:
        tags[content_name].remove(tag)
    save_tags(tags)


def get_all_used_tags() -> List[str]:
    """Get all tags that are currently in use"""
    tags = load_tags()
    used = set()
    for content_tags in tags.values():
        used.update(content_tags)
    return sorted(list(used))


def load_metadata() -> Dict[str, Dict]:
    """Load content metadata from file"""
    try:
        if METADATA_FILE.exists():
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_metadata(metadata: Dict[str, Dict]):
    """Save content metadata to file"""
    METADATA_FILE.parent.mkdir(exist_ok=True)
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def get_content_metadata(content_name: str) -> Dict:
    """Get metadata for a specific content"""
    metadata = load_metadata()
    return metadata.get(content_name, {
        "caption": "",
        "hashtags": "",
        "notes": "",
        "alt_text": ""
    })


def set_content_metadata(content_name: str, meta: Dict):
    """Set metadata for a specific content"""
    metadata = load_metadata()
    metadata[content_name] = meta
    save_metadata(metadata)


def publish_content_to_instagram(content_name: str) -> Dict[str, Any]:
    """
    Publish content directly to Instagram using PublisherAgent
    Returns: {"success": bool, "post_id": str, "url": str, "error": str}
    """
    if not PUBLISHER_AVAILABLE:
        return {"success": False, "error": "PublisherAgent not available"}

    content_path = IMAGES_DIR / content_name
    if not content_path.exists():
        return {"success": False, "error": f"Content folder not found: {content_name}"}

    images = sorted(list(content_path.glob("*.png")) + list(content_path.glob("*.jpg")))
    if not images:
        return {"success": False, "error": "No images found in content folder"}

    # Extract topic name
    parts = content_name.split('_', 1)
    topic = parts[1] if len(parts) > 1 else content_name

    try:
        # Create publisher instance
        publisher = PublisherAgent()

        # Prepare input data for publisher
        input_data = {
            "images": [str(img) for img in images],
            "topic": topic,
            "passed": True  # QA 통과 가정
        }

        # Run async publish in sync context
        async def run_publish():
            return await publisher.run(input_data)

        # Run the async function - use asyncio.new_event_loop for Streamlit compatibility
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_publish())
        finally:
            loop.close()

        if result.success:
            # Update history
            history = load_history()
            history[content_name] = {
                "published_at": datetime.now().isoformat(),
                "platform": "instagram",
                "images": len(images),
                "post_id": result.data.get("post_id", ""),
                "url": result.data.get("url", "")
            }
            save_history(history)

            # Remove from schedule if scheduled
            schedule = load_schedule()
            if content_name in schedule:
                del schedule[content_name]
                save_schedule(schedule)

            return {
                "success": True,
                "post_id": result.data.get("post_id", ""),
                "url": result.data.get("url", ""),
                "error": None
            }
        else:
            return {"success": False, "error": result.error or "Unknown error"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def update_content_status(content_name: str, new_status: str):
    """Update content status (draft/scheduled/published)"""
    history = load_history()
    schedule = load_schedule()

    if new_status == "published":
        # Add to history, remove from schedule
        if content_name not in history:
            history[content_name] = {
                "published_at": datetime.now().isoformat(),
                "platform": "instagram",
                "images": 7
            }
        if content_name in schedule:
            del schedule[content_name]
    elif new_status == "scheduled":
        # Add to schedule (default time), remove from history
        if content_name not in schedule:
            schedule[content_name] = {
                "scheduled_at": (datetime.now() + timedelta(days=1)).replace(hour=18, minute=0).isoformat(),
                "platform": "instagram"
            }
        if content_name in history:
            del history[content_name]
    else:  # draft
        # Remove from both history and schedule
        if content_name in history:
            del history[content_name]
        if content_name in schedule:
            del schedule[content_name]

    save_history(history)
    save_schedule(schedule)


def delete_content(content_name: str):
    """Delete content folder and related data"""
    import shutil

    content_path = IMAGES_DIR / content_name
    if content_path.exists():
        shutil.rmtree(content_path)

    # Remove from history and schedule
    history = load_history()
    schedule = load_schedule()

    if content_name in history:
        del history[content_name]
        save_history(history)

    if content_name in schedule:
        del schedule[content_name]
        save_schedule(schedule)


def create_content_zip(content_name: str) -> bytes:
    """Create a ZIP file containing all content images"""
    import zipfile
    import io

    content_path = IMAGES_DIR / content_name
    if not content_path.exists():
        return None

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for img in content_path.glob("*.png"):
            zip_file.write(img, img.name)
        for img in content_path.glob("*.jpg"):
            zip_file.write(img, img.name)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def duplicate_content(content_name: str) -> str:
    """Duplicate content folder with new name"""
    import shutil

    content_path = IMAGES_DIR / content_name
    if not content_path.exists():
        return None

    # Generate new name with _copy suffix
    parts = content_name.split('_', 1)
    if len(parts) > 1:
        # Find next available copy number
        base_name = parts[1]
        copy_num = 1
        while True:
            new_name = f"{parts[0]}_copy{copy_num}_{base_name}"
            new_path = IMAGES_DIR / new_name
            if not new_path.exists():
                break
            copy_num += 1
    else:
        new_name = f"{content_name}_copy"
        new_path = IMAGES_DIR / new_name

    # Copy the folder
    shutil.copytree(content_path, new_path)

    # Rename files inside to match new folder name
    for img in new_path.glob("*.png"):
        old_name = img.name
        # Replace old content name prefix with new one
        if old_name.startswith(content_name):
            new_file_name = old_name.replace(content_name, new_name, 1)
            img.rename(new_path / new_file_name)

    for img in new_path.glob("*.jpg"):
        old_name = img.name
        if old_name.startswith(content_name):
            new_file_name = old_name.replace(content_name, new_name, 1)
            img.rename(new_path / new_file_name)

    # Copy tags from original content
    original_tags = get_content_tags(content_name)
    if original_tags:
        set_content_tags(new_name, original_tags.copy())

    return new_name


def load_queue() -> List[Dict]:
    try:
        if QUEUE_FILE.exists():
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []


def save_queue(queue: List[Dict]):
    QUEUE_FILE.parent.mkdir(exist_ok=True)
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2, default=str)


def add_to_queue(topic: str, action: str = "generate"):
    """작업 큐에 추가"""
    queue = load_queue()
    queue.append({
        "topic": topic,
        "action": action,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    })
    save_queue(queue)


# ============================================================
# TOAST NOTIFICATIONS
# ============================================================
def show_toast(message: str, toast_type: str = "info"):
    """Display toast notification"""
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    icon = icons.get(toast_type, "ℹ️")

    st.markdown(f"""
    <div class="toast-container">
        <div class="toast {toast_type}">
            <span class="toast-icon">{icon}</span>
            <span class="toast-message">{message}</span>
        </div>
    </div>
    <script>
        setTimeout(function() {{
            var toasts = document.querySelectorAll('.toast');
            toasts.forEach(function(toast) {{
                toast.style.animation = 'toastOut 0.3s ease-out forwards';
                setTimeout(function() {{
                    toast.parentElement.remove();
                }}, 300);
            }});
        }}, 3000);
    </script>
    """, unsafe_allow_html=True)


def render_loading_skeleton(count: int = 6):
    """Render loading skeleton cards"""
    cols = st.columns(6)
    for i in range(count):
        with cols[i % 6]:
            st.markdown("""
            <div class="skeleton-card">
                <div class="skeleton skeleton-thumb"></div>
                <div class="skeleton skeleton-text"></div>
                <div class="skeleton skeleton-text-short"></div>
            </div>
            """, unsafe_allow_html=True)


def render_empty_state(
    icon: str,
    title: str,
    description: str,
    action_text: str = None,
    action_page: str = None
):
    """Render empty state with optional action button"""
    action_html = ""
    if action_text:
        action_html = f'<span class="empty-state-action">{action_text}</span>'

    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <p class="empty-state-title">{title}</p>
        <p class="empty-state-desc">{description}</p>
        {action_html}
    </div>
    """, unsafe_allow_html=True)

    if action_text and action_page:
        if st.button(action_text, key=f"empty_action_{action_page}", use_container_width=False):
            st.session_state.page = action_page
            st.rerun()


def render_lightbox():
    """Render image lightbox modal"""
    if not st.session_state.get("lightbox_open"):
        return

    images = st.session_state.get("lightbox_images", [])
    current_idx = st.session_state.get("lightbox_index", 0)

    if not images or current_idx >= len(images):
        st.session_state.lightbox_open = False
        return

    current_image = images[current_idx]

    # Load image as base64
    img_path = Path(current_image)
    if img_path.exists():
        with open(img_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        # Generate thumbnail strip
        thumb_html = ""
        for i, img in enumerate(images):
            thumb_path = Path(img)
            if thumb_path.exists():
                with open(thumb_path, "rb") as f:
                    thumb_data = base64.b64encode(f.read()).decode()
                active_class = "active" if i == current_idx else ""
                thumb_html += f'<img src="data:image/png;base64,{thumb_data}" class="lightbox-thumb {active_class}" data-index="{i}">'

        st.markdown(f"""
        <div class="lightbox-overlay" id="lightbox">
            <div class="lightbox-content">
                <div class="lightbox-close" id="lightbox-close">✕</div>
                <div class="lightbox-nav lightbox-prev" id="lightbox-prev">‹</div>
                <img src="data:image/png;base64,{img_data}" class="lightbox-image" id="lightbox-img">
                <div class="lightbox-nav lightbox-next" id="lightbox-next">›</div>
                <div class="lightbox-info">
                    <div class="lightbox-counter">{current_idx + 1} / {len(images)}</div>
                    <div class="lightbox-filename">{img_path.name}</div>
                </div>
                <div class="lightbox-thumbnails">
                    {thumb_html}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Navigation controls
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⬅️ Prev", key="lb_prev", disabled=current_idx == 0):
            st.session_state.lightbox_index = current_idx - 1
            st.rerun()

    with col2:
        if st.button("➡️ Next", key="lb_next", disabled=current_idx >= len(images) - 1):
            st.session_state.lightbox_index = current_idx + 1
            st.rerun()

    with col4:
        st.markdown(f"**{current_idx + 1} / {len(images)}**")

    with col5:
        if st.button("✖️ Close", key="lb_close"):
            st.session_state.lightbox_open = False
            st.rerun()


def render_keyboard_shortcuts_help():
    """Render keyboard shortcuts help modal"""
    if st.session_state.get("show_shortcuts_help"):
        st.markdown("""
        <div class="shortcuts-modal" id="shortcuts-modal">
            <h3>⌨️ Keyboard Shortcuts</h3>
            <div class="shortcut-row">
                <span class="shortcut-desc">Go to Content List</span>
                <span class="shortcut-key">G → L</span>
            </div>
            <div class="shortcut-row">
                <span class="shortcut-desc">Go to Create</span>
                <span class="shortcut-key">G → C</span>
            </div>
            <div class="shortcut-row">
                <span class="shortcut-desc">Go to Analytics</span>
                <span class="shortcut-key">G → A</span>
            </div>
            <div class="shortcut-row">
                <span class="shortcut-desc">Go to Settings</span>
                <span class="shortcut-key">G → S</span>
            </div>
            <div class="shortcut-row">
                <span class="shortcut-desc">Search Content</span>
                <span class="shortcut-key">/</span>
            </div>
            <div class="shortcut-row">
                <span class="shortcut-desc">Select All</span>
                <span class="shortcut-key">⌘ + A</span>
            </div>
            <div class="shortcut-row">
                <span class="shortcut-desc">Close Modal</span>
                <span class="shortcut-key">Esc</span>
            </div>
            <div class="shortcut-row">
                <span class="shortcut-desc">Show Shortcuts</span>
                <span class="shortcut-key">?</span>
            </div>
            <p style="color: rgba(255,255,255,0.4); font-size: 0.75rem; margin-top: 1.5rem; text-align: center;">
                Press Esc to close
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Close button
        if st.button("Close Shortcuts", key="close_shortcuts"):
            st.session_state.show_shortcuts_help = False
            st.rerun()


# ============================================================
# INSTAGRAM SYNC
# ============================================================
def get_instagram_credentials() -> Tuple[Optional[str], Optional[str]]:
    """환경변수 또는 Streamlit secrets에서 Instagram 자격증명 로드"""
    access_token = get_secret("INSTAGRAM_ACCESS_TOKEN")
    user_id = get_secret("INSTAGRAM_USER_ID", "17841478336612378")
    return access_token if access_token else None, user_id


def fetch_instagram_posts(limit: int = 50) -> List[Dict]:
    """Instagram Graph API로 게시물 목록 가져오기"""
    access_token, user_id = get_instagram_credentials()

    if not access_token:
        return []

    try:
        url = f"https://graph.instagram.com/{user_id}/media"
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
            "limit": limit,
            "access_token": access_token
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            return []
    except Exception as e:
        st.error(f"Instagram API Error: {e}")
        return []


def extract_topic_from_caption(caption: str) -> Optional[str]:
    """캡션에서 주제(음식) 추출 - 해시태그 기반"""
    if not caption:
        return None

    # 음식 관련 해시태그 매핑
    food_keywords = {
        "watermelon": ["수박", "watermelon"],
        "broccoli": ["브로콜리", "broccoli"],
        "banana": ["바나나", "banana"],
        "pineapple": ["파인애플", "pineapple"],
        "apple": ["사과", "apple"],
        "sweet_potato": ["고구마", "sweetpotato", "sweet_potato"],
        "cherry": ["체리", "cherry", "cherries"],
        "blueberry": ["블루베리", "blueberry", "blueberries"],
        "pumpkin": ["호박", "pumpkin"],
        "carrot": ["당근", "carrot"],
        "strawberry": ["딸기", "strawberry"],
        "mango": ["망고", "mango"],
    }

    caption_lower = caption.lower()

    for topic, keywords in food_keywords.items():
        for keyword in keywords:
            if keyword.lower() in caption_lower:
                return topic

    return None


def match_post_to_content(post: Dict, contents: List[Dict]) -> Optional[str]:
    """인스타 게시물을 로컬 콘텐츠와 매칭"""
    caption = post.get("caption", "")
    topic = extract_topic_from_caption(caption)

    if not topic:
        return None

    # 콘텐츠 폴더명과 매칭 (예: 008_banana → banana)
    for content in contents:
        content_topic = content["name"].split("_", 1)[-1] if "_" in content["name"] else content["name"]
        if content_topic.lower() == topic.lower():
            return content["name"]

    return None


def sync_with_instagram() -> Dict[str, Any]:
    """Instagram과 동기화 - 게시물 가져와서 history 업데이트"""
    results = {
        "success": False,
        "synced": 0,
        "new": [],
        "already_synced": [],
        "unmatched": [],
        "error": None
    }

    access_token, _ = get_instagram_credentials()
    if not access_token:
        results["error"] = "Instagram Access Token not configured. Please check .env file."
        return results

    # Fetch Instagram posts
    posts = fetch_instagram_posts(limit=50)
    if not posts:
        results["error"] = "Unable to fetch posts. Token may be expired or API error."
        return results

    # Local content list
    contents = get_content_folders()

    # Current history
    history = load_history()

    for post in posts:
        content_name = match_post_to_content(post, contents)

        if not content_name:
            results["unmatched"].append({
                "id": post.get("id"),
                "caption": (post.get("caption", "")[:50] + "...") if post.get("caption") else "No caption",
                "permalink": post.get("permalink")
            })
            continue

        if content_name in history:
            results["already_synced"].append(content_name)
            continue

        # 새로 동기화
        history[content_name] = {
            "published_at": post.get("timestamp", datetime.now().isoformat()),
            "platform": "instagram",
            "post_id": post.get("id"),
            "url": post.get("permalink"),
            "media_url": post.get("media_url") or post.get("thumbnail_url"),
            "synced_at": datetime.now().isoformat()
        }
        results["new"].append(content_name)
        results["synced"] += 1

    # 히스토리 저장
    if results["synced"] > 0:
        save_history(history)

    results["success"] = True
    return results


# ============================================================
# INSTAGRAM INSIGHTS API
# ============================================================
INSIGHTS_CACHE_FILE = ROOT / "dashboard" / "insights_cache.json"

def load_insights_cache() -> Dict:
    """인사이트 캐시 로드"""
    if INSIGHTS_CACHE_FILE.exists():
        try:
            with open(INSIGHTS_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"posts": {}, "account": {}, "updated_at": None}
    return {"posts": {}, "account": {}, "updated_at": None}


def save_insights_cache(cache: Dict):
    """인사이트 캐시 저장"""
    cache["updated_at"] = datetime.now().isoformat()
    with open(INSIGHTS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_post_insights(post_id: str) -> Optional[Dict]:
    """
    개별 게시물의 Instagram Insights 가져오기

    Returns:
        - impressions: 노출 수
        - reach: 도달 수
        - likes: 좋아요 수
        - comments: 댓글 수
        - saved: 저장 수
        - shares: 공유 수
        - engagement: 참여 수 (likes + comments + saved + shares)
        - engagement_rate: 참여율 (engagement / reach * 100)
    """
    access_token, user_id = get_instagram_credentials()

    if not access_token:
        return None

    try:
        # 기본 게시물 정보 (likes, comments는 기본 필드)
        url = f"https://graph.facebook.com/v21.0/{post_id}"
        params = {
            "fields": "id,like_count,comments_count,timestamp,permalink,caption,media_type",
            "access_token": access_token
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return None

        basic_data = response.json()

        # Insights 데이터 (Business/Creator 계정만 가능)
        # Note: impressions 메트릭은 v22.0부터 지원 중단, reach/saved/shares만 사용
        insights_url = f"https://graph.facebook.com/v21.0/{post_id}/insights"
        insights_params = {
            "metric": "reach,saved,shares",
            "access_token": access_token
        }

        insights_response = requests.get(insights_url, params=insights_params, timeout=10)

        insights_data = {}
        if insights_response.status_code == 200:
            insights_raw = insights_response.json().get("data", [])
            for item in insights_raw:
                name = item.get("name")
                value = item.get("values", [{}])[0].get("value", 0)
                insights_data[name] = value

        # 결과 조합
        likes = basic_data.get("like_count", 0)
        comments = basic_data.get("comments_count", 0)
        saved = insights_data.get("saved", 0)
        shares = insights_data.get("shares", 0)
        reach = insights_data.get("reach", 0)
        # impressions는 reach와 동일하게 처리 (v22.0+ 호환성)
        impressions = reach

        engagement = likes + comments + saved + shares
        engagement_rate = (engagement / reach * 100) if reach > 0 else 0

        return {
            "post_id": post_id,
            "likes": likes,
            "comments": comments,
            "saved": saved,
            "shares": shares,
            "impressions": impressions,
            "reach": reach,
            "engagement": engagement,
            "engagement_rate": round(engagement_rate, 2),
            "timestamp": basic_data.get("timestamp"),
            "permalink": basic_data.get("permalink"),
            "media_type": basic_data.get("media_type"),
            "fetched_at": datetime.now().isoformat()
        }

    except Exception as e:
        st.error(f"Post Insights API Error: {e}")
        return None


def fetch_account_insights(period: str = "day") -> Optional[Dict]:
    """
    계정 전체 Instagram Insights 가져오기

    Args:
        period: "day", "week", "days_28" (28일)

    Returns:
        - reach: 도달 수
        - profile_views: 프로필 방문 수
        - accounts_engaged: 참여 계정 수
        - total_interactions: 총 상호작용 수
        - follower_count: 팔로워 수
        - media_count: 게시물 수
    """
    access_token, user_id = get_instagram_credentials()

    if not access_token or not user_id:
        return None

    try:
        # 계정 기본 정보
        account_url = f"https://graph.facebook.com/v21.0/{user_id}"
        account_params = {
            "fields": "id,username,followers_count,follows_count,media_count,profile_picture_url,biography",
            "access_token": access_token
        }

        account_response = requests.get(account_url, params=account_params, timeout=10)

        account_data = {}
        if account_response.status_code == 200:
            account_data = account_response.json()

        # 계정 인사이트 (Business/Creator만 가능)
        # Note: Instagram API v21.0+ 에서 메트릭 분리 필요
        insights_url = f"https://graph.facebook.com/v21.0/{user_id}/insights"

        # period 매핑
        period_map = {
            "day": "day",
            "week": "week",
            "days_28": "days_28"
        }
        api_period = period_map.get(period, "day")

        insights_data = {}

        # 1. reach는 period 기반 메트릭
        reach_params = {
            "metric": "reach",
            "period": api_period,
            "access_token": access_token
        }
        reach_response = requests.get(insights_url, params=reach_params, timeout=10)
        if reach_response.status_code == 200:
            reach_raw = reach_response.json().get("data", [])
            for item in reach_raw:
                name = item.get("name")
                values = item.get("values", [])
                if values:
                    insights_data[name] = values[-1].get("value", 0)

        # 2. profile_views, accounts_engaged, total_interactions는 total_value 메트릭
        total_params = {
            "metric": "profile_views,accounts_engaged,total_interactions",
            "metric_type": "total_value",
            "period": api_period,
            "access_token": access_token
        }
        total_response = requests.get(insights_url, params=total_params, timeout=10)
        if total_response.status_code == 200:
            total_raw = total_response.json().get("data", [])
            for item in total_raw:
                name = item.get("name")
                total_value = item.get("total_value", {}).get("value", 0)
                insights_data[name] = total_value

        return {
            "user_id": user_id,
            "username": account_data.get("username", ""),
            "followers_count": account_data.get("followers_count", 0),
            "follows_count": account_data.get("follows_count", 0),
            "media_count": account_data.get("media_count", 0),
            "profile_picture_url": account_data.get("profile_picture_url", ""),
            "biography": account_data.get("biography", ""),
            "reach": insights_data.get("reach", 0),
            "profile_views": insights_data.get("profile_views", 0),
            "accounts_engaged": insights_data.get("accounts_engaged", 0),
            "total_interactions": insights_data.get("total_interactions", 0),
            "period": period,
            "fetched_at": datetime.now().isoformat()
        }

    except Exception as e:
        st.error(f"Account Insights API Error: {e}")
        return None


def fetch_all_posts_insights(limit: int = 20) -> List[Dict]:
    """
    모든 게시물의 인사이트 가져오기 (캐시 활용)
    """
    cache = load_insights_cache()

    # 캐시가 1시간 이내면 캐시 사용
    if cache.get("updated_at"):
        try:
            updated = datetime.fromisoformat(cache["updated_at"])
            if (datetime.now() - updated).total_seconds() < 3600:  # 1시간
                if cache.get("posts"):
                    return list(cache["posts"].values())[:limit]
        except:
            pass

    # 새로 가져오기
    posts = fetch_instagram_posts(limit=limit)

    results = []
    for post in posts:
        post_id = post.get("id")
        if not post_id:
            continue

        # 캐시에 있으면 캐시 사용
        if post_id in cache.get("posts", {}):
            cached = cache["posts"][post_id]
            # 24시간 이내 캐시는 유효
            try:
                fetched = datetime.fromisoformat(cached.get("fetched_at", ""))
                if (datetime.now() - fetched).total_seconds() < 86400:
                    results.append(cached)
                    continue
            except:
                pass

        # 새로 가져오기
        insights = fetch_post_insights(post_id)
        if insights:
            cache["posts"][post_id] = insights
            results.append(insights)

    # 캐시 저장
    save_insights_cache(cache)

    return results


def refresh_insights_cache(force: bool = False) -> Dict[str, Any]:
    """
    인사이트 캐시 새로고침

    Args:
        force: True면 캐시 무시하고 전체 새로고침
    """
    if force:
        cache = {"posts": {}, "account": {}, "updated_at": None}
    else:
        cache = load_insights_cache()

    results = {
        "success": False,
        "posts_updated": 0,
        "account_updated": False,
        "error": None
    }

    access_token, _ = get_instagram_credentials()
    if not access_token:
        results["error"] = "Instagram Access Token not configured"
        return results

    try:
        # 계정 인사이트
        account_insights = fetch_account_insights("day")
        if account_insights:
            cache["account"] = account_insights
            results["account_updated"] = True

        # 게시물 인사이트
        posts = fetch_instagram_posts(limit=30)
        for post in posts:
            post_id = post.get("id")
            if post_id:
                insights = fetch_post_insights(post_id)
                if insights:
                    cache["posts"][post_id] = insights
                    results["posts_updated"] += 1

        save_insights_cache(cache)
        results["success"] = True

    except Exception as e:
        results["error"] = str(e)

    return results


def get_top_performing_posts(limit: int = 5, metric: str = "engagement_rate") -> List[Dict]:
    """
    성과가 좋은 게시물 Top N 반환

    Args:
        metric: "engagement_rate", "likes", "reach", "saved"
    """
    all_insights = fetch_all_posts_insights(limit=50)

    if not all_insights:
        return []

    # 정렬
    sorted_posts = sorted(
        all_insights,
        key=lambda x: x.get(metric, 0),
        reverse=True
    )

    return sorted_posts[:limit]


def calculate_average_metrics(posts_insights: List[Dict]) -> Dict:
    """
    게시물들의 평균 지표 계산
    """
    if not posts_insights:
        return {
            "avg_likes": 0,
            "avg_comments": 0,
            "avg_saved": 0,
            "avg_reach": 0,
            "avg_engagement_rate": 0,
            "total_posts": 0
        }

    total = len(posts_insights)

    return {
        "avg_likes": round(sum(p.get("likes", 0) for p in posts_insights) / total, 1),
        "avg_comments": round(sum(p.get("comments", 0) for p in posts_insights) / total, 1),
        "avg_saved": round(sum(p.get("saved", 0) for p in posts_insights) / total, 1),
        "avg_reach": round(sum(p.get("reach", 0) for p in posts_insights) / total, 1),
        "avg_engagement_rate": round(sum(p.get("engagement_rate", 0) for p in posts_insights) / total, 2),
        "total_posts": total
    }


# ============================================================
# UI COMPONENTS
# ============================================================
def render_sidebar():
    """Premium Sidebar"""
    with st.sidebar:
        # Logo & Brand
        st.markdown("""
        <div style="padding: 1.5rem 0.5rem 0.5rem; text-align: center;">
            <div style="
                width: 44px;
                height: 44px;
                margin: 0 auto 0.5rem;
                background: linear-gradient(135deg, #a855f7, #6366f1);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.4rem;
                box-shadow: 0 8px 24px rgba(168, 85, 247, 0.3);
            ">✨</div>
        </div>
        """, unsafe_allow_html=True)

        # Project Selector
        st.markdown("""
        <p style="font-size: 0.6rem; color: rgba(255,255,255,0.3); font-weight: 600;
                  letter-spacing: 0.1em; text-transform: uppercase; padding: 0 0.25rem; margin-bottom: 0.35rem;">
            PROJECT
        </p>
        """, unsafe_allow_html=True)

        # Project dropdown (현재는 Sunshine만, 추후 확장 가능)
        projects = ["✨ Sunshine", "🐱 Coming Soon..."]
        selected_project = st.selectbox(
            "Project",
            projects,
            index=0,
            label_visibility="collapsed",
            key="project_selector"
        )

        st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

        current_page = st.session_state.get("page", "list")

        # Initialize sidebar section states
        if "sidebar_menu_expanded" not in st.session_state:
            st.session_state.sidebar_menu_expanded = True
        if "sidebar_tools_expanded" not in st.session_state:
            st.session_state.sidebar_tools_expanded = True
        if "sidebar_overview_expanded" not in st.session_state:
            st.session_state.sidebar_overview_expanded = True
        if "sidebar_sync_expanded" not in st.session_state:
            st.session_state.sidebar_sync_expanded = True

        # Navigation Section (Collapsible)
        menu_icon = "▼" if st.session_state.sidebar_menu_expanded else "▶"
        if st.button(f"{menu_icon}  MENU", use_container_width=True, key="toggle_menu"):
            st.session_state.sidebar_menu_expanded = not st.session_state.sidebar_menu_expanded
            st.rerun()

        if st.session_state.sidebar_menu_expanded:
            if st.button("📋  Content", use_container_width=True,
                         type="primary" if current_page == "list" else "secondary"):
                st.session_state.page = "list"
                st.rerun()

            if st.button("➕  New Content", use_container_width=True,
                         type="primary" if current_page == "create" else "secondary"):
                st.session_state.page = "create"
                st.rerun()

            if st.button("📅  Schedule", use_container_width=True,
                         type="primary" if current_page == "schedule" else "secondary"):
                st.session_state.page = "schedule"
                st.rerun()

            if st.button("📊  History", use_container_width=True,
                         type="primary" if current_page == "history" else "secondary"):
                st.session_state.page = "history"
                st.rerun()

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        # Tools Section (Collapsible)
        tools_icon = "▼" if st.session_state.sidebar_tools_expanded else "▶"
        if st.button(f"{tools_icon}  TOOLS", use_container_width=True, key="toggle_tools"):
            st.session_state.sidebar_tools_expanded = not st.session_state.sidebar_tools_expanded
            st.rerun()

        if st.session_state.sidebar_tools_expanded:
            if st.button("📈  Analytics", use_container_width=True,
                         type="primary" if current_page == "analytics" else "secondary"):
                st.session_state.page = "analytics"
                st.rerun()

            if st.button("🔍  Compare", use_container_width=True,
                         type="primary" if current_page == "compare" else "secondary"):
                st.session_state.page = "compare"
                st.rerun()

            if st.button("⚙️  Settings", use_container_width=True,
                         type="primary" if current_page == "settings" else "secondary"):
                st.session_state.page = "settings"
                st.rerun()

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        # Stats Section (Collapsible)
        contents = get_content_folders()
        total = len(contents)
        published = sum(1 for c in contents if c["status"] == "published")
        scheduled = sum(1 for c in contents if c["status"] == "scheduled")
        draft = sum(1 for c in contents if c["status"] == "draft")

        overview_icon = "▼" if st.session_state.sidebar_overview_expanded else "▶"
        if st.button(f"{overview_icon}  OVERVIEW", use_container_width=True, key="toggle_overview"):
            st.session_state.sidebar_overview_expanded = not st.session_state.sidebar_overview_expanded
            st.rerun()

        if st.session_state.sidebar_overview_expanded:
            st.markdown(f"""
            <div style="padding: 0 0.25rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
                                border-radius: 8px; padding: 0.75rem 0.5rem; text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: rgba(255,255,255,0.95);">{total}</div>
                        <div style="font-size: 0.55rem; color: rgba(255,255,255,0.4); text-transform: uppercase;
                                    letter-spacing: 0.05em; margin-top: 0.25rem;">Total</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
                                border-radius: 8px; padding: 0.75rem 0.5rem; text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #22c55e;">{published}</div>
                        <div style="font-size: 0.55rem; color: rgba(255,255,255,0.4); text-transform: uppercase;
                                    letter-spacing: 0.05em; margin-top: 0.25rem;">Published</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
                                border-radius: 8px; padding: 0.75rem 0.5rem; text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #3b82f6;">{scheduled}</div>
                        <div style="font-size: 0.55rem; color: rgba(255,255,255,0.4); text-transform: uppercase;
                                    letter-spacing: 0.05em; margin-top: 0.25rem;">Scheduled</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
                                border-radius: 8px; padding: 0.75rem 0.5rem; text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: rgba(255,255,255,0.5);">{draft}</div>
                        <div style="font-size: 0.55rem; color: rgba(255,255,255,0.4); text-transform: uppercase;
                                    letter-spacing: 0.05em; margin-top: 0.25rem;">Draft</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        # Sync Section (Collapsible)
        sync_icon = "▼" if st.session_state.sidebar_sync_expanded else "▶"
        if st.button(f"{sync_icon}  SYNC", use_container_width=True, key="toggle_sync"):
            st.session_state.sidebar_sync_expanded = not st.session_state.sidebar_sync_expanded
            st.rerun()

        if st.session_state.sidebar_sync_expanded:
            if st.button("🔄  Instagram", use_container_width=True):
                with st.spinner("Syncing with Instagram..."):
                    result = sync_with_instagram()

                if result["success"]:
                    if result["synced"] > 0:
                        st.success(f"✅ {result['synced']} items synced!")
                        for name in result["new"]:
                            st.caption(f"  + {name}")
                    else:
                        st.info("Already up to date.")

                    if result["unmatched"]:
                        with st.expander(f"⚠️ Unmatched ({len(result['unmatched'])})"):
                            for post in result["unmatched"][:5]:
                                st.caption(f"• {post['caption']}")
                else:
                    st.error(result["error"])

                st.rerun()

        # Keyboard Shortcuts Help
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        if st.button("⌨️  Shortcuts", use_container_width=True):
            st.session_state.show_shortcuts_help = True
            st.rerun()


def render_stats_cards(contents: List[Dict]):
    """Bento-style Stats Cards"""
    total = len(contents)
    published = sum(1 for c in contents if c["status"] == "published")
    scheduled = sum(1 for c in contents if c["status"] == "scheduled")
    draft = sum(1 for c in contents if c["status"] == "draft")

    col1, col2, col3, col4 = st.columns(4)

    stats = [
        (col1, total, "Total Content", ""),
        (col2, published, "Published", "#22c55e"),
        (col3, scheduled, "Scheduled", "#3b82f6"),
        (col4, draft, "Draft", "rgba(255,255,255,0.4)")
    ]

    for col, num, label, color in stats:
        with col:
            color_style = f'color: {color};' if color else ''
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="{color_style}">{num}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_content_list():
    """Premium Content Grid - 6 Columns"""

    st.markdown("""
    <div class="main-header">
        <h1>Content Manager</h1>
        <p>Manage your Instagram content library • Draft / Scheduled / Published</p>
    </div>
    """, unsafe_allow_html=True)

    contents = get_content_folders()
    render_stats_cards(contents)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    if not contents:
        render_empty_state(
            icon="📭",
            title="No content yet",
            description="Start creating amazing content for your Instagram. Generate your first post with AI-powered automation.",
            action_text="➕ Create First Content",
            action_page="create"
        )
        return

    # Initialize bulk selection state
    if "selected_contents" not in st.session_state:
        st.session_state.selected_contents = set()

    # Filters Row 1
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

    # Get all content names for autocomplete
    all_content_names = [c["display_name"] for c in contents]

    with col1:
        search = st.text_input("🔍", placeholder="Search content...", label_visibility="collapsed", key="search_input")

        # Show search suggestions if typing
        if search and len(search) >= 1:
            suggestions = [name for name in all_content_names if search.lower() in name.lower()][:5]
            if suggestions and search.upper() not in suggestions:
                st.markdown("""
                <style>
                .search-suggestions {
                    background: rgba(20, 22, 25, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    margin-top: -0.5rem;
                    padding: 0.25rem 0;
                    position: relative;
                    z-index: 100;
                }
                .search-suggestion {
                    padding: 0.5rem 0.75rem;
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 0.85rem;
                    cursor: pointer;
                    transition: background 0.2s ease;
                }
                .search-suggestion:hover {
                    background: rgba(168, 85, 247, 0.2);
                    color: white;
                }
                </style>
                """, unsafe_allow_html=True)

                st.markdown('<div class="search-suggestions">', unsafe_allow_html=True)
                for suggestion in suggestions:
                    st.markdown(f'<div class="search-suggestion">🔍 {suggestion}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        status_filter = st.selectbox("Status", ["All", "Published", "Scheduled", "Draft"], label_visibility="collapsed")
    with col3:
        sort_options = [
            "📅 Recent",
            "🔤 Name (A-Z)",
            "🔤 Name (Z-A)",
            "🖼️ Slides (Most)",
            "🖼️ Slides (Least)",
            "✅ Published First",
            "📝 Draft First"
        ]
        sort_by = st.selectbox("Sort", sort_options, label_visibility="collapsed")
    with col4:
        # Select All / Deselect All toggle
        content_names = [c["name"] for c in contents]
        all_selected = len(st.session_state.selected_contents) > 0 and all(
            name in st.session_state.selected_contents for name in content_names
        )
        if st.button("☑️ All" if not all_selected else "☐ None", use_container_width=True):
            if all_selected:
                st.session_state.selected_contents = set()
            else:
                st.session_state.selected_contents = set(content_names)
            st.rerun()

    # Apply filters
    if search:
        contents = [c for c in contents if search.lower() in c["name"].lower() or search.lower() in c["display_name"].lower()]
    if status_filter != "All":
        status_map = {"Published": "published", "Scheduled": "scheduled", "Draft": "draft"}
        contents = [c for c in contents if c["status"] == status_map.get(status_filter)]

    # Apply sorting
    if sort_by == "🔤 Name (A-Z)":
        contents = sorted(contents, key=lambda x: x["name"])
    elif sort_by == "🔤 Name (Z-A)":
        contents = sorted(contents, key=lambda x: x["name"], reverse=True)
    elif sort_by == "🖼️ Slides (Most)":
        contents = sorted(contents, key=lambda x: x["image_count"], reverse=True)
    elif sort_by == "🖼️ Slides (Least)":
        contents = sorted(contents, key=lambda x: x["image_count"])
    elif sort_by == "✅ Published First":
        status_order = {"published": 0, "scheduled": 1, "draft": 2}
        contents = sorted(contents, key=lambda x: status_order.get(x["status"], 3))
    elif sort_by == "📝 Draft First":
        status_order = {"draft": 0, "scheduled": 1, "published": 2}
        contents = sorted(contents, key=lambda x: status_order.get(x["status"], 3))
    else:  # 📅 Recent (default)
        contents = sorted(contents, key=lambda x: x["created"], reverse=True)

    # Empty state after filtering
    if not contents:
        filter_desc = []
        if search:
            filter_desc.append(f'"{search}"')
        if status_filter != "All":
            filter_desc.append(status_filter.lower())
        filter_text = " with " + ", ".join(filter_desc) if filter_desc else ""

        st.markdown(f"""
        <div class="empty-state" style="margin-top: 2rem;">
            <div class="empty-state-icon">🔍</div>
            <p class="empty-state-title">No results found</p>
            <p class="empty-state-desc">No content matches your current filters{filter_text}. Try adjusting your search or filters.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Bulk Action Bar (shows when items are selected)
    selected_count = len(st.session_state.selected_contents)
    if selected_count > 0:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(139, 92, 246, 0.1));
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="
                    background: rgba(168, 85, 247, 0.3);
                    color: #c084fc;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                ">{selected_count} selected</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Bulk action buttons
        bcol1, bcol2, bcol3, bcol4, bcol5, bcol6 = st.columns([1, 1, 1, 1, 1, 1])
        with bcol1:
            if st.button("📝 Draft", key="bulk_draft", use_container_width=True):
                for name in st.session_state.selected_contents:
                    update_content_status(name, "draft")
                st.session_state.selected_contents = set()
                st.rerun()
        with bcol2:
            if st.button("📅 Schedule", key="bulk_schedule", use_container_width=True):
                st.session_state.show_batch_schedule = True
        with bcol3:
            if st.button("✅ Publish", key="bulk_publish", use_container_width=True):
                for name in st.session_state.selected_contents:
                    update_content_status(name, "published")
                st.session_state.selected_contents = set()
                st.rerun()
        with bcol4:
            if st.button("🏷️ Tags", key="bulk_tags", use_container_width=True):
                st.session_state.show_bulk_tags = True
        with bcol5:
            if st.button("🗑️ Delete", key="bulk_delete", type="secondary", use_container_width=True):
                st.session_state.show_bulk_delete_confirm = True
        with bcol6:
            if st.button("✖️ Clear", key="clear_selection", use_container_width=True):
                st.session_state.selected_contents = set()
                st.rerun()

        # Batch Schedule dialog
        if st.session_state.get("show_batch_schedule"):
            st.markdown("""
            <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3);
                        border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                <div style="font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 0.75rem;">
                    📅 Batch Schedule Settings
                </div>
            </div>
            """, unsafe_allow_html=True)

            sch_col1, sch_col2, sch_col3 = st.columns([2, 2, 2])

            with sch_col1:
                start_date = st.date_input("Start Date", datetime.now().date(), key="batch_start_date")

            with sch_col2:
                start_time = st.time_input("Time", datetime.now().replace(hour=18, minute=0).time(), key="batch_time")

            with sch_col3:
                interval = st.selectbox("Interval", ["Same day", "1 day apart", "2 days apart", "3 days apart", "1 week apart"], key="batch_interval")

            interval_days = {"Same day": 0, "1 day apart": 1, "2 days apart": 2, "3 days apart": 3, "1 week apart": 7}

            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
            with btn_col1:
                if st.button("✅ Apply Schedule", key="apply_batch_schedule", type="primary"):
                    schedule = load_schedule()
                    selected_list = sorted(list(st.session_state.selected_contents))
                    days_gap = interval_days.get(interval, 0)

                    for i, name in enumerate(selected_list):
                        schedule_date = datetime.combine(start_date, start_time) + timedelta(days=i * days_gap)
                        schedule[name] = {
                            "scheduled_at": schedule_date.isoformat(),
                            "status": "pending"
                        }
                        # Remove from history if exists
                        history = load_history()
                        if name in history:
                            del history[name]
                            save_history(history)

                    save_schedule(schedule)
                    st.session_state.selected_contents = set()
                    st.session_state.show_batch_schedule = False
                    st.session_state.toast_message = f"Scheduled {len(selected_list)} items!"
                    st.session_state.toast_type = "success"
                    st.rerun()

            with btn_col2:
                if st.button("Cancel", key="cancel_batch_schedule"):
                    st.session_state.show_batch_schedule = False
                    st.rerun()

        # Delete confirmation dialog
        if st.session_state.get("show_bulk_delete_confirm"):
            st.warning(f"⚠️ Are you sure you want to delete {selected_count} items? This cannot be undone.")
            dcol1, dcol2, dcol3 = st.columns([1, 1, 2])
            with dcol1:
                if st.button("🗑️ Yes, Delete", key="confirm_bulk_delete", type="primary"):
                    for name in list(st.session_state.selected_contents):
                        delete_content(name)
                    st.session_state.selected_contents = set()
                    st.session_state.show_bulk_delete_confirm = False
                    st.rerun()
            with dcol2:
                if st.button("Cancel", key="cancel_bulk_delete"):
                    st.session_state.show_bulk_delete_confirm = False
                    st.rerun()

        # Bulk Tags dialog
        if st.session_state.get("show_bulk_tags"):
            st.markdown("""
            <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3);
                        border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                <div style="font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 0.75rem;">
                    🏷️ Bulk Tag Assignment
                </div>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin-bottom: 0.75rem;">
                    Select tags to add to all selected content items.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Tag selection grid
            tag_cols = st.columns(5)
            if "bulk_selected_tags" not in st.session_state:
                st.session_state.bulk_selected_tags = set()

            for i, (tag_key, tag_info) in enumerate(AVAILABLE_TAGS.items()):
                with tag_cols[i % 5]:
                    is_selected = tag_key in st.session_state.bulk_selected_tags
                    btn_type = "primary" if is_selected else "secondary"
                    if st.button(f"{tag_info['icon']} {tag_info['label']}", key=f"bulk_tag_{tag_key}", type=btn_type, use_container_width=True):
                        if is_selected:
                            st.session_state.bulk_selected_tags.discard(tag_key)
                        else:
                            st.session_state.bulk_selected_tags.add(tag_key)
                        st.rerun()

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

            # Action buttons
            tag_btn_col1, tag_btn_col2, tag_btn_col3, tag_btn_col4 = st.columns([1, 1, 1, 1])
            with tag_btn_col1:
                if st.button("➕ Add Tags", key="apply_bulk_tags", type="primary", use_container_width=True):
                    if st.session_state.bulk_selected_tags:
                        for name in st.session_state.selected_contents:
                            current_tags = get_content_tags(name)
                            new_tags = list(set(current_tags) | st.session_state.bulk_selected_tags)
                            set_content_tags(name, new_tags)
                        st.session_state.show_bulk_tags = False
                        st.session_state.bulk_selected_tags = set()
                        st.session_state.toast_message = f"Added tags to {selected_count} items!"
                        st.session_state.toast_type = "success"
                        st.rerun()

            with tag_btn_col2:
                if st.button("➖ Remove Tags", key="remove_bulk_tags", use_container_width=True):
                    if st.session_state.bulk_selected_tags:
                        for name in st.session_state.selected_contents:
                            current_tags = get_content_tags(name)
                            new_tags = [t for t in current_tags if t not in st.session_state.bulk_selected_tags]
                            set_content_tags(name, new_tags)
                        st.session_state.show_bulk_tags = False
                        st.session_state.bulk_selected_tags = set()
                        st.session_state.toast_message = f"Removed tags from {selected_count} items!"
                        st.session_state.toast_type = "info"
                        st.rerun()

            with tag_btn_col3:
                if st.button("🔄 Replace All", key="replace_bulk_tags", use_container_width=True):
                    for name in st.session_state.selected_contents:
                        set_content_tags(name, list(st.session_state.bulk_selected_tags))
                    st.session_state.show_bulk_tags = False
                    st.session_state.bulk_selected_tags = set()
                    st.session_state.toast_message = f"Replaced tags for {selected_count} items!"
                    st.session_state.toast_type = "success"
                    st.rerun()

            with tag_btn_col4:
                if st.button("Cancel", key="cancel_bulk_tags"):
                    st.session_state.show_bulk_tags = False
                    st.session_state.bulk_selected_tags = set()
                    st.rerun()

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # 6-column grid
    cols = st.columns(6)

    for idx, content in enumerate(contents):
        with cols[idx % 6]:
            # Thumbnail with 4:5 ratio - support both URL and local path
            thumbnail = content.get("thumbnail", "")
            img_src = ""

            if thumbnail.startswith("http"):
                # Cloudinary URL - use directly
                img_src = thumbnail
            else:
                # Local file path
                thumbnail_path = Path(thumbnail)
                if thumbnail_path.exists():
                    with open(thumbnail_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    img_src = f"data:image/png;base64,{img_data}"

            if img_src:
                # Status badge HTML
                status_badges = {
                    "published": '<span class="status-badge status-live">Published</span>',
                    "scheduled": '<span class="status-badge status-scheduled">Scheduled</span>',
                    "draft": '<span class="status-badge status-draft">Draft</span>'
                }

                # Check if this content is selected
                is_selected = content["name"] in st.session_state.selected_contents
                selected_style = "border: 2px solid rgba(168, 85, 247, 0.8); box-shadow: 0 0 15px rgba(168, 85, 247, 0.3);" if is_selected else ""

                st.markdown(f"""
                <div class="content-card" style="animation-delay: {idx * 0.05}s; {selected_style}">
                    <div class="quick-actions">
                        <span class="quick-action-btn" title="View">👁️</span>
                        <span class="quick-action-btn" title="Duplicate">📋</span>
                        <span class="quick-action-btn delete" title="Delete">🗑️</span>
                    </div>
                    <div class="insta-thumb">
                        <img src="{img_src}" alt="{content['display_name']}">
                    </div>
                    <div class="content-info">
                        <div class="content-meta">
                            <span class="content-title">{content['display_name']}</span>
                            {status_badges[content['status']]}
                        </div>
                        <div class="content-count">
                            {content['image_count']} slides
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Single invisible button for card click action
            if st.button(" ", key=f"card_{content['name']}", help="Click to view", use_container_width=True):
                st.session_state.selected_content = content["name"]
                st.session_state.page = "detail"
                st.rerun()


def render_create_content():
    """New Content Creation Page"""
    st.markdown("""
    <div class="main-header">
        <h1>Create Content</h1>
        <p>Enter a food topic to generate Instagram carousel content automatically</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🍎 Food Topic")

    col1, col2 = st.columns([3, 1])

    with col1:
        topic = st.text_input(
            "Topic",
            placeholder="e.g., tomato, egg, salmon...",
            label_visibility="collapsed"
        )

    with col2:
        generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)

    if generate_btn and topic:
        topic_clean = topic.strip().lower().replace(" ", "_")
        add_to_queue(topic_clean, "generate")

        st.success(f"✅ '{topic_clean}' added to queue!")

        st.markdown("---")

        st.markdown("### 📋 Run Command")
        st.code(f"python cli.py {topic_clean}", language="bash")

        st.info("""
        **Run in Claude Code:**
        1. Execute the command above in terminal
        2. Or ask Claude Code: "Generate banana content"
        """)

    # Manual Upload Section
    st.markdown("---")
    st.markdown("### 📤 Manual Upload")
    st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">Upload existing images to create a new content set manually.</p>', unsafe_allow_html=True)

    upload_col1, upload_col2 = st.columns([2, 1])

    with upload_col1:
        upload_name = st.text_input(
            "Content Name",
            placeholder="e.g., tomato, banana...",
            key="upload_content_name"
        )

    with upload_col2:
        # Number prefix (auto-increment)
        existing_contents = get_content_folders()
        next_num = len(existing_contents) + 1
        st.text_input("Number", value=f"{next_num:03d}", disabled=True, key="upload_num")

    # File uploader
    uploaded_files = st.file_uploader(
        "Drop images here or click to upload",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="image_uploader"
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} files selected:**")

        # Preview uploaded images
        preview_cols = st.columns(min(len(uploaded_files), 6))
        for i, file in enumerate(uploaded_files[:6]):
            with preview_cols[i]:
                st.image(file, use_container_width=True, caption=f"Slide {i+1}")

        if len(uploaded_files) > 6:
            st.caption(f"...and {len(uploaded_files) - 6} more")

        # Save button
        if st.button("💾 Save Content", type="primary", use_container_width=True, key="save_upload"):
            if upload_name:
                import shutil

                # Create folder
                folder_name = f"{next_num:03d}_{upload_name.strip().lower().replace(' ', '_')}"
                folder_path = IMAGES_DIR / folder_name
                folder_path.mkdir(parents=True, exist_ok=True)

                # Save files
                for i, file in enumerate(uploaded_files):
                    ext = Path(file.name).suffix or ".png"
                    file_path = folder_path / f"{folder_name}_{i:02d}{ext}"
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())

                st.session_state.toast_message = f"Created '{folder_name}' with {len(uploaded_files)} images!"
                st.session_state.toast_type = "success"
                st.rerun()
            else:
                st.error("Please enter a content name")

    # Work Queue
    st.markdown("---")
    st.markdown("### 📋 Work Queue")

    queue = load_queue()
    if queue:
        for idx, item in enumerate(queue):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{item['topic']}**")
            with col2:
                st.caption(f"📅 {item['created_at'][:16]}")
            with col3:
                if st.button("Remove", key=f"del_queue_{idx}"):
                    queue.pop(idx)
                    save_queue(queue)
                    st.rerun()
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.3);
                    background: rgba(255,255,255,0.02); border-radius: 12px;
                    border: 1px dashed rgba(255,255,255,0.08);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem; opacity: 0.5;">✨</div>
            <p style="margin: 0; font-size: 0.85rem;">No pending tasks</p>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; opacity: 0.7;">Enter a topic above to generate content</p>
        </div>
        """, unsafe_allow_html=True)


def render_content_detail():
    """Content Detail View"""
    content_name = st.session_state.get("selected_content")

    if not content_name:
        st.warning("No content selected")
        return

    if st.button("← Back"):
        st.session_state.page = "list"
        st.rerun()

    # Check local path first, then Cloudinary
    content_path = IMAGES_DIR / content_name
    use_cloudinary = False
    cloudinary_images = []

    if content_path.exists():
        # Local mode
        images = sorted(list(content_path.glob("*.png")) + list(content_path.glob("*.jpg")))
    elif CLOUDINARY_AVAILABLE:
        # Cloudinary mode
        use_cloudinary = True
        cloudinary_folders = get_cloudinary_content_folders()
        folder_data = next((f for f in cloudinary_folders if f["name"] == content_name), None)
        if folder_data and folder_data.get("images"):
            cloudinary_images = folder_data["images"]
            images = cloudinary_images  # Use URLs directly
        else:
            st.error("Content not found in Cloudinary")
            return
    else:
        st.error("Content not found")
        return

    if not images:
        st.error("No images found")
        return

    parts = content_name.split('_', 1)
    display_name = parts[1].upper() if len(parts) > 1 else content_name.upper()

    # Current status
    history = load_history()
    schedule = load_schedule()
    if content_name in history:
        current_status = "published"
    elif content_name in schedule:
        current_status = "scheduled"
    else:
        current_status = "draft"

    status_text = {"published": "✅ Published", "scheduled": "📅 Scheduled", "draft": "📝 Draft"}

    st.markdown(f"""
    <div class="main-header">
        <h1>{display_name}</h1>
        <p>{len(images)} slides • {content_name} • {status_text[current_status]}</p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🖼️ Preview", "✏️ Caption", "🏷️ Tags", "🔀 Reorder", "📅 Schedule", "⚡ Actions"])

    with tab1:
        if images:
            # Check if lightbox should be shown
            if st.session_state.get("lightbox_open") and st.session_state.get("lightbox_content") == content_name:
                render_lightbox()
            else:
                selected_idx = st.session_state.get(f"preview_idx_{content_name}", 0)
                if selected_idx >= len(images):
                    selected_idx = 0

                # Main preview with click to open lightbox
                col1, col2, col3 = st.columns([1, 5, 1])
                with col2:
                    # Large preview image - support both local files and URLs
                    current_img = images[selected_idx]
                    if use_cloudinary or (isinstance(current_img, str) and current_img.startswith('http')):
                        # Cloudinary URL
                        img_src = current_img
                    else:
                        # Local file
                        with open(current_img, "rb") as f:
                            img_data = base64.b64encode(f.read()).decode()
                        img_src = f"data:image/png;base64,{img_data}"

                    st.markdown(f"""
                    <div class="clickable-thumb" style="text-align: center;">
                        <img src="{img_src}"
                             style="max-width: 100%; border-radius: 12px; cursor: pointer;"
                             title="Click to open fullscreen">
                    </div>
                    """, unsafe_allow_html=True)

                    # Open lightbox button
                    if st.button("🔍 View Fullscreen", key="open_lightbox", use_container_width=True):
                        st.session_state.lightbox_open = True
                        st.session_state.lightbox_images = [str(img) for img in images]
                        st.session_state.lightbox_index = selected_idx
                        st.session_state.lightbox_content = content_name
                        st.rerun()

                    st.caption(f"📍 {selected_idx + 1} / {len(images)}")

                # Thumbnail grid with click to select
                st.markdown("#### All Slides")
                st.markdown('<p style="color: rgba(255,255,255,0.4); font-size: 0.8rem; margin-bottom: 1rem;">Click a thumbnail to preview, or use the fullscreen button above</p>', unsafe_allow_html=True)

                thumb_cols = st.columns(6)
                for i, img in enumerate(images):
                    with thumb_cols[i % 6]:
                        # Thumbnail with selection indicator
                        is_selected = i == selected_idx
                        border_style = "border: 2px solid #a855f7;" if is_selected else "border: 2px solid transparent;"

                        # Support both local files and URLs
                        if use_cloudinary or (isinstance(img, str) and img.startswith('http')):
                            thumb_src = img
                        else:
                            with open(img, "rb") as f:
                                thumb_data = base64.b64encode(f.read()).decode()
                            thumb_src = f"data:image/png;base64,{thumb_data}"

                        st.markdown(f"""
                        <div class="clickable-thumb" style="{border_style} border-radius: 8px; overflow: hidden;">
                            <img src="{thumb_src}" style="width: 100%; display: block;">
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button(f"#{i+1}", key=f"thumb_{i}", use_container_width=True):
                            st.session_state[f"preview_idx_{content_name}"] = i
                            st.rerun()

    with tab2:
        # Caption & Metadata Editor
        st.markdown("#### Caption & Metadata")
        st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.85rem; margin-bottom: 1rem;">Edit the caption, hashtags, and notes for this content.</p>', unsafe_allow_html=True)

        # Load current metadata
        current_meta = get_content_metadata(content_name)

        # Caption text area
        caption = st.text_area(
            "Caption",
            value=current_meta.get("caption", ""),
            height=150,
            placeholder="Write your Instagram caption here...",
            key=f"caption_{content_name}"
        )

        # Hashtags
        hashtags = st.text_area(
            "Hashtags",
            value=current_meta.get("hashtags", ""),
            height=80,
            placeholder="#강아지 #반려견 #dogfood #펫푸드...",
            key=f"hashtags_{content_name}"
        )

        # Character count
        caption_count = len(caption)
        hashtag_count = len(hashtags.split()) if hashtags.strip() else 0
        total_count = caption_count + len(hashtags) + 2  # +2 for newlines

        count_color = "#22c55e" if total_count <= 2200 else "#ef4444"
        st.markdown(f"""
        <div style="display: flex; gap: 1.5rem; margin-top: 0.5rem;">
            <span style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">
                📝 Caption: <span style="color: {count_color};">{caption_count}</span>/2,200
            </span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">
                #️⃣ Hashtags: {hashtag_count}/30
            </span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">
                📊 Total: <span style="color: {count_color};">{total_count}</span>/2,200
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Notes (internal)
        notes = st.text_area(
            "Internal Notes",
            value=current_meta.get("notes", ""),
            height=80,
            placeholder="Add internal notes (not published)...",
            key=f"notes_{content_name}"
        )

        # Alt text for accessibility
        alt_text = st.text_input(
            "Alt Text (Accessibility)",
            value=current_meta.get("alt_text", ""),
            placeholder="Describe the image for screen readers...",
            key=f"alt_text_{content_name}"
        )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Save button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💾 Save Metadata", type="primary", use_container_width=True):
                set_content_metadata(content_name, {
                    "caption": caption,
                    "hashtags": hashtags,
                    "notes": notes,
                    "alt_text": alt_text
                })
                st.session_state.toast_message = "Metadata saved!"
                st.session_state.toast_type = "success"
                st.rerun()

        # Quick insert suggestions
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("**Quick Hashtag Sets:**")
        qs_col1, qs_col2, qs_col3 = st.columns(3)

        with qs_col1:
            if st.button("🐕 Dog Food Basic", key="qs_dog_basic", use_container_width=True):
                base_hashtags = "#강아지 #반려견 #펫푸드 #강아지간식 #강아지음식 #dogfood #petfood #dogtreat #puppyfood #doglovers"
                current_hashtags = hashtags.strip()
                new_hashtags = f"{current_hashtags}\n{base_hashtags}" if current_hashtags else base_hashtags
                st.session_state[f"hashtags_{content_name}"] = new_hashtags
                st.rerun()

        with qs_col2:
            if st.button("🍎 Fruit Tags", key="qs_fruit", use_container_width=True):
                fruit_hashtags = "#과일 #강아지과일 #dogfruit #healthydog #naturaltreat #fruitfordogs"
                current_hashtags = hashtags.strip()
                new_hashtags = f"{current_hashtags}\n{fruit_hashtags}" if current_hashtags else fruit_hashtags
                st.session_state[f"hashtags_{content_name}"] = new_hashtags
                st.rerun()

        with qs_col3:
            if st.button("🥬 Vegetable Tags", key="qs_veg", use_container_width=True):
                veg_hashtags = "#야채 #강아지야채 #dogvegetables #healthypet #vegfordogs #petnutrition"
                current_hashtags = hashtags.strip()
                new_hashtags = f"{current_hashtags}\n{veg_hashtags}" if current_hashtags else veg_hashtags
                st.session_state[f"hashtags_{content_name}"] = new_hashtags
                st.rerun()

    with tab3:
        # Tags management
        st.markdown("#### Content Tags")
        st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.85rem; margin-bottom: 1rem;">Add tags to categorize and filter your content easily.</p>', unsafe_allow_html=True)

        current_tags = get_content_tags(content_name)

        # Display current tags
        if current_tags:
            st.markdown("**Current Tags:**")
            tag_cols = st.columns(len(current_tags) + 1)
            for i, tag in enumerate(current_tags):
                tag_info = AVAILABLE_TAGS.get(tag, {"label": tag, "icon": "🏷️", "color": "#6b7280"})
                with tag_cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: {tag_info['color']};
                        color: white;
                        padding: 0.5rem 1rem;
                        border-radius: 20px;
                        text-align: center;
                        font-size: 0.85rem;
                        font-weight: 500;
                    ">{tag_info['icon']} {tag_info['label']}</div>
                    """, unsafe_allow_html=True)
                    if st.button("✕", key=f"remove_tag_{tag}", help=f"Remove {tag_info['label']}"):
                        remove_content_tag(content_name, tag)
                        st.session_state.toast_message = f"Removed tag: {tag_info['label']}"
                        st.session_state.toast_type = "info"
                        st.rerun()
        else:
            st.info("No tags added yet. Add some tags below!")

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Add new tags
        st.markdown("**Add Tags:**")
        available_to_add = [t for t in AVAILABLE_TAGS.keys() if t not in current_tags]

        if available_to_add:
            # Display available tags as clickable pills
            add_cols = st.columns(min(len(available_to_add), 5))
            for i, tag_key in enumerate(available_to_add):
                tag_info = AVAILABLE_TAGS[tag_key]
                with add_cols[i % 5]:
                    st.markdown(f"""
                    <div style="
                        background: rgba(255,255,255,0.05);
                        border: 1px solid {tag_info['color']};
                        color: {tag_info['color']};
                        padding: 0.4rem 0.75rem;
                        border-radius: 16px;
                        text-align: center;
                        font-size: 0.8rem;
                        margin-bottom: 0.5rem;
                    ">{tag_info['icon']} {tag_info['label']}</div>
                    """, unsafe_allow_html=True)
                    if st.button("+ Add", key=f"add_tag_{tag_key}", use_container_width=True):
                        add_content_tag(content_name, tag_key)
                        st.session_state.toast_message = f"Added tag: {tag_info['label']}"
                        st.session_state.toast_type = "success"
                        st.rerun()
        else:
            st.success("All available tags have been added!")

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # Quick tag presets
        st.markdown("**Quick Presets:**")
        preset_col1, preset_col2, preset_col3 = st.columns(3)

        with preset_col1:
            if st.button("🍎 Fruit + Safe", key="preset_fruit_safe", use_container_width=True):
                set_content_tags(content_name, ["fruit", "safe"])
                st.session_state.toast_message = "Applied preset: Fruit + Safe"
                st.session_state.toast_type = "success"
                st.rerun()

        with preset_col2:
            if st.button("🥬 Vegetable + Safe", key="preset_veg_safe", use_container_width=True):
                set_content_tags(content_name, ["vegetable", "safe"])
                st.session_state.toast_message = "Applied preset: Vegetable + Safe"
                st.session_state.toast_type = "success"
                st.rerun()

        with preset_col3:
            if st.button("⚠️ Caution Food", key="preset_caution", use_container_width=True):
                set_content_tags(content_name, ["caution"])
                st.session_state.toast_message = "Applied preset: Caution"
                st.session_state.toast_type = "success"
                st.rerun()

    with tab4:
        # Reorder slides
        st.markdown("#### Reorder Slides")
        st.markdown('<p style="color: rgba(255,255,255,0.5); font-size: 0.85rem; margin-bottom: 1rem;">Use the buttons to move slides up or down. Changes are saved automatically.</p>', unsafe_allow_html=True)

        if images:
            # Initialize reorder state if needed
            reorder_key = f"reorder_{content_name}"
            if reorder_key not in st.session_state:
                st.session_state[reorder_key] = [str(img) for img in images]

            current_order = st.session_state[reorder_key]

            # Display slides with reorder controls
            for idx, img_path in enumerate(current_order):
                img = Path(img_path)
                if img.exists():
                    col1, col2, col3, col4 = st.columns([1, 4, 1, 1])

                    with col1:
                        st.markdown(f"""
                        <div style="
                            background: rgba(168, 85, 247, 0.2);
                            border: 1px solid rgba(168, 85, 247, 0.3);
                            border-radius: 8px;
                            padding: 0.5rem;
                            text-align: center;
                            font-weight: 600;
                            color: #c084fc;
                        ">{idx + 1}</div>
                        """, unsafe_allow_html=True)

                    with col2:
                        with open(img, "rb") as f:
                            thumb_data = base64.b64encode(f.read()).decode()
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <img src="data:image/png;base64,{thumb_data}"
                                 style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
                            <span style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">{img.name}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        # Move up button
                        if st.button("⬆️", key=f"up_{idx}", disabled=idx == 0, use_container_width=True):
                            # Swap with previous
                            current_order[idx], current_order[idx - 1] = current_order[idx - 1], current_order[idx]
                            st.session_state[reorder_key] = current_order
                            st.rerun()

                    with col4:
                        # Move down button
                        if st.button("⬇️", key=f"down_{idx}", disabled=idx == len(current_order) - 1, use_container_width=True):
                            # Swap with next
                            current_order[idx], current_order[idx + 1] = current_order[idx + 1], current_order[idx]
                            st.session_state[reorder_key] = current_order
                            st.rerun()

                    st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

            # Save and Reset buttons
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            bcol1, bcol2, bcol3 = st.columns([2, 1, 1])

            with bcol2:
                if st.button("🔄 Reset", key="reset_order", use_container_width=True):
                    st.session_state[reorder_key] = [str(img) for img in images]
                    st.rerun()

            with bcol3:
                if st.button("💾 Save Order", key="save_order", type="primary", use_container_width=True):
                    # Rename files to reflect new order
                    import shutil
                    temp_dir = content_path / "_temp_reorder"
                    temp_dir.mkdir(exist_ok=True)

                    try:
                        # Move to temp with new names
                        for new_idx, old_path in enumerate(current_order):
                            old_img = Path(old_path)
                            ext = old_img.suffix
                            new_name = f"{content_name}_{new_idx:02d}{ext}"
                            shutil.copy2(old_img, temp_dir / new_name)

                        # Remove old files
                        for img in images:
                            img.unlink()

                        # Move renamed files back
                        for temp_file in temp_dir.iterdir():
                            shutil.move(str(temp_file), content_path / temp_file.name)

                        # Cleanup
                        temp_dir.rmdir()

                        # Clear reorder state
                        del st.session_state[reorder_key]

                        st.session_state.toast_message = "Slide order saved!"
                        st.session_state.toast_type = "success"
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error saving order: {e}")
                        # Cleanup temp dir if exists
                        if temp_dir.exists():
                            shutil.rmtree(temp_dir)

    with tab5:
        current = schedule.get(content_name, {})

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Current Schedule")
            if current.get("scheduled_at"):
                st.success(f"📅 {current['scheduled_at']}")
                if st.button("Cancel Schedule"):
                    del schedule[content_name]
                    save_schedule(schedule)
                    st.rerun()
            else:
                st.info("Not scheduled")

        with col2:
            st.markdown("#### New Schedule")
            date = st.date_input("Date", datetime.now().date())
            time = st.time_input("Time", datetime.now().replace(hour=18, minute=0).time())
            if st.button("Save Schedule", type="primary"):
                dt = datetime.combine(date, time)
                schedule[content_name] = {"scheduled_at": dt.isoformat(), "status": "pending"}
                save_schedule(schedule)
                st.success(f"✅ Scheduled: {dt.strftime('%Y-%m-%d %H:%M')}")
                st.rerun()

    with tab6:
        st.markdown("#### Status")

        # 상태 변경 버튼
        col1, col2, col3 = st.columns(3)

        with col1:
            btn_type = "primary" if current_status == "draft" else "secondary"
            if st.button("📝 Draft", use_container_width=True, type=btn_type, key="btn_draft"):
                # Remove from history and schedule
                if content_name in history:
                    del history[content_name]
                    save_history(history)
                if content_name in schedule:
                    del schedule[content_name]
                    save_schedule(schedule)
                st.rerun()

        with col2:
            btn_type = "primary" if current_status == "scheduled" else "secondary"
            if st.button("📅 Scheduled", use_container_width=True, type=btn_type, key="btn_scheduled"):
                # Add to schedule, remove from history
                if content_name in history:
                    del history[content_name]
                    save_history(history)
                if content_name not in schedule:
                    schedule[content_name] = {"scheduled_at": datetime.now().isoformat(), "status": "pending"}
                    save_schedule(schedule)
                st.rerun()

        with col3:
            btn_type = "primary" if current_status == "published" else "secondary"
            if st.button("✅ Published", use_container_width=True, type=btn_type, key="btn_published"):
                # Add to history, remove from schedule
                if content_name in schedule:
                    del schedule[content_name]
                    save_schedule(schedule)
                if content_name not in history:
                    history[content_name] = {
                        "published_at": datetime.now().isoformat(),
                        "platform": "instagram",
                        "images": len(images)
                    }
                    save_history(history)
                st.rerun()

        st.markdown("---")

        # Instagram Direct Publish Section
        st.markdown("#### Publish to Instagram")

        if current_status == "published":
            hist = history.get(content_name, {})
            post_url = hist.get("url", "")
            post_id = hist.get("post_id", "")

            st.success("This content has been published!")
            if post_url:
                st.markdown(f"**Post URL:** [{post_url}]({post_url})")
            if post_id:
                st.caption(f"Post ID: {post_id}")
        else:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(225, 48, 108, 0.1), rgba(193, 53, 132, 0.1));
                border: 1px solid rgba(225, 48, 108, 0.3);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;">
                    📸 Ready to publish? Click the button below to upload this content directly to Instagram.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Check if publisher is available
            if not PUBLISHER_AVAILABLE:
                st.warning("Publisher agent is not available. Please check your configuration.")
            else:
                # Initialize publish confirmation state
                if "confirm_instagram_publish" not in st.session_state:
                    st.session_state.confirm_instagram_publish = None

                if st.session_state.confirm_instagram_publish == content_name:
                    # Show confirmation dialog
                    st.warning(f"Are you sure you want to publish '{display_name}' to Instagram?")
                    st.caption(f"This will upload {len(images)} images as a carousel post.")

                    conf_col1, conf_col2 = st.columns(2)
                    with conf_col1:
                        if st.button("✅ Yes, Publish Now", type="primary", use_container_width=True, key="confirm_publish"):
                            with st.spinner("Publishing to Instagram..."):
                                result = publish_content_to_instagram(content_name)

                            if result["success"]:
                                st.session_state.toast_message = f"Published to Instagram!"
                                st.session_state.toast_type = "success"
                                st.session_state.confirm_instagram_publish = None
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"Publish failed: {result['error']}")
                                st.session_state.confirm_instagram_publish = None

                    with conf_col2:
                        if st.button("❌ Cancel", use_container_width=True, key="cancel_publish"):
                            st.session_state.confirm_instagram_publish = None
                            st.rerun()
                else:
                    # Show publish button
                    if st.button("📤 Publish to Instagram", type="primary", use_container_width=True, key="publish_ig"):
                        st.session_state.confirm_instagram_publish = content_name
                        st.rerun()

        st.markdown("---")
        st.markdown("#### Quick Actions")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**CLI Command**")
            topic_name = parts[1] if len(parts) > 1 else content_name
            st.code(f"python cli.py {topic_name}", language="bash")

        with col2:
            st.markdown("**Regenerate**")
            if st.button("🔄 Regenerate Content", use_container_width=True):
                topic_name = parts[1] if len(parts) > 1 else content_name
                add_to_queue(topic_name, "regenerate")
                st.success(f"'{topic_name}' added to regeneration queue")

        st.markdown("---")
        st.markdown("#### Export")

        col1, col2 = st.columns(2)

        with col1:
            # Export as ZIP
            if st.button("📦 Download ZIP", use_container_width=True):
                zip_data = create_content_zip(content_name)
                if zip_data:
                    st.download_button(
                        label="💾 Save ZIP File",
                        data=zip_data,
                        file_name=f"{content_name}.zip",
                        mime="application/zip",
                        key="download_zip"
                    )

        with col2:
            # Copy to clipboard (folder path)
            st.markdown(f"**Folder Path**")
            st.code(str(content_path), language="text")


def render_schedule_view():
    """Schedule Overview with Calendar View"""
    st.markdown("""
    <div class="main-header">
        <h1>Schedule</h1>
        <p>Manage your scheduled content with calendar view</p>
    </div>
    """, unsafe_allow_html=True)

    schedule = load_schedule()
    history = load_history()

    # View toggle
    view_mode = st.radio("View", ["📅 Calendar", "📋 List"], horizontal=True, label_visibility="collapsed")

    if view_mode == "📅 Calendar":
        # Calendar View
        import calendar

        # Get current month/year or use session state
        if "cal_year" not in st.session_state:
            st.session_state.cal_year = datetime.now().year
        if "cal_month" not in st.session_state:
            st.session_state.cal_month = datetime.now().month

        year = st.session_state.cal_year
        month = st.session_state.cal_month

        # Navigation
        nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
        with nav_col1:
            if st.button("◀ Prev", use_container_width=True):
                if month == 1:
                    st.session_state.cal_month = 12
                    st.session_state.cal_year = year - 1
                else:
                    st.session_state.cal_month = month - 1
                st.rerun()
        with nav_col2:
            month_names = ["", "January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            st.markdown(f"<h3 style='text-align: center; margin: 0;'>{month_names[month]} {year}</h3>", unsafe_allow_html=True)
        with nav_col3:
            if st.button("Next ▶", use_container_width=True):
                if month == 12:
                    st.session_state.cal_month = 1
                    st.session_state.cal_year = year + 1
                else:
                    st.session_state.cal_month = month + 1
                st.rerun()

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Build calendar data
        cal = calendar.Calendar(firstweekday=6)  # Sunday start
        month_days = cal.monthdayscalendar(year, month)

        # Organize scheduled/published items by date
        items_by_date = {}
        for name, info in schedule.items():
            try:
                dt = datetime.fromisoformat(info.get("scheduled_at", ""))
                if dt.year == year and dt.month == month:
                    day = dt.day
                    if day not in items_by_date:
                        items_by_date[day] = []
                    parts = name.split('_', 1)
                    display = parts[1].upper() if len(parts) > 1 else name.upper()
                    items_by_date[day].append({"name": name, "display": display, "type": "scheduled"})
            except:
                pass

        for name, info in history.items():
            try:
                dt = datetime.fromisoformat(info.get("published_at", ""))
                if dt.year == year and dt.month == month:
                    day = dt.day
                    if day not in items_by_date:
                        items_by_date[day] = []
                    parts = name.split('_', 1)
                    display = parts[1].upper() if len(parts) > 1 else name.upper()
                    items_by_date[day].append({"name": name, "display": display, "type": "published"})
            except:
                pass

        # Day headers
        day_headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        header_cols = st.columns(7)
        for i, day_name in enumerate(day_headers):
            with header_cols[i]:
                st.markdown(f"<div style='text-align: center; font-size: 0.75rem; color: var(--text-tertiary); font-weight: 600;'>{day_name}</div>", unsafe_allow_html=True)

        # Calendar grid
        for week in month_days:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                    else:
                        is_today = (day == datetime.now().day and month == datetime.now().month and year == datetime.now().year)
                        today_style = "border: 2px solid #a855f7;" if is_today else ""
                        items = items_by_date.get(day, [])

                        items_html = ""
                        for item in items[:2]:  # Show max 2 items
                            if item["type"] == "scheduled":
                                items_html += f'<div style="font-size: 0.6rem; background: rgba(59, 130, 246, 0.2); color: #3b82f6; padding: 2px 4px; border-radius: 4px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">📅 {item["display"][:8]}</div>'
                            else:
                                items_html += f'<div style="font-size: 0.6rem; background: rgba(34, 197, 94, 0.2); color: #22c55e; padding: 2px 4px; border-radius: 4px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">✅ {item["display"][:8]}</div>'

                        if len(items) > 2:
                            items_html += f'<div style="font-size: 0.55rem; color: var(--text-tertiary); margin-top: 2px;">+{len(items) - 2} more</div>'

                        st.markdown(f"""
                        <div style="
                            background: var(--glass-bg);
                            border: 1px solid var(--glass-border);
                            border-radius: 8px;
                            padding: 6px;
                            min-height: 80px;
                            {today_style}
                        ">
                            <div style="font-size: 0.8rem; font-weight: 600; color: var(--text-primary);">{day}</div>
                            {items_html}
                        </div>
                        """, unsafe_allow_html=True)

    else:
        # List View
        if not schedule:
            render_empty_state(
                icon="📅",
                title="No scheduled content",
                description="Schedule your content for automatic publishing at the best times. Select a draft and set a publish date.",
                action_text="📋 View Content",
                action_page="list"
            )
            return

        for name, info in sorted(schedule.items(), key=lambda x: x[1].get("scheduled_at", "")):
            parts = name.split('_', 1)
            display = parts[1].upper() if len(parts) > 1 else name.upper()

            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"### {display}")
            with col2:
                scheduled_at = info.get('scheduled_at', '')
                try:
                    dt = datetime.fromisoformat(scheduled_at)
                    st.markdown(f"📅 {dt.strftime('%Y-%m-%d %H:%M')}")
                except:
                    st.markdown(f"📅 {scheduled_at}")
            with col3:
                if st.button("Cancel", key=f"cancel_{name}"):
                    del schedule[name]
                    save_schedule(schedule)
                    st.rerun()
            st.markdown("---")


def render_history_view():
    """Publishing History with Instagram Insights"""
    st.markdown("""
    <div class="main-header">
        <h1>History</h1>
        <p>Published content on Instagram with performance metrics</p>
    </div>
    """, unsafe_allow_html=True)

    history = load_history()
    if not history:
        render_empty_state(
            icon="📊",
            title="No publishing history",
            description="Your published content will appear here. Start by creating and publishing your first Instagram post.",
            action_text="➕ Create Content",
            action_page="create"
        )
        return

    # Load insights cache for performance data
    insights_cache = load_insights_cache()
    posts_insights = insights_cache.get("posts", {})

    # Refresh button
    col_header, col_refresh = st.columns([3, 1])
    with col_refresh:
        if st.button("🔄 Update Metrics", key="history_refresh_btn"):
            with st.spinner("Fetching latest metrics..."):
                result = refresh_insights_cache(force=True)
                if result["success"]:
                    st.success(f"✅ Updated {result['posts_updated']} posts")
                    st.rerun()
                else:
                    st.warning(f"⚠️ {result.get('error', 'Could not fetch metrics')}")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Table header
    st.markdown("""
    <div style="display: grid; grid-template-columns: 2fr 1.5fr 1fr 1fr 1fr 1fr 1fr 0.8fr;
                padding: 0.75rem 1rem; background: rgba(255,255,255,0.03);
                border-radius: 8px; margin-bottom: 0.5rem; font-size: 0.7rem;
                color: rgba(255,255,255,0.4); font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.05em;">
        <div>Content</div>
        <div>Published</div>
        <div style="text-align: center;">❤️ Likes</div>
        <div style="text-align: center;">💬 Comments</div>
        <div style="text-align: center;">🔖 Saves</div>
        <div style="text-align: center;">👁 Reach</div>
        <div style="text-align: center;">📈 Eng.</div>
        <div style="text-align: center;">Link</div>
    </div>
    """, unsafe_allow_html=True)

    for name, info in sorted(history.items(), key=lambda x: x[1].get("published_at", ""), reverse=True):
        parts = name.split('_', 1)
        display = parts[1].title() if len(parts) > 1 else name.title()

        # Get insights for this post
        post_id = info.get("post_id", "")
        post_insights = posts_insights.get(post_id, {}) if post_id else {}

        # Metrics with fallback
        likes = post_insights.get("likes", info.get("likes", "-"))
        comments = post_insights.get("comments", info.get("comments", "-"))
        saved = post_insights.get("saved", info.get("saved", "-"))
        reach = post_insights.get("reach", info.get("reach", "-"))
        engagement_rate = post_insights.get("engagement_rate", info.get("engagement_rate", "-"))

        # Format engagement rate color
        if isinstance(engagement_rate, (int, float)):
            rate_color = "#22c55e" if engagement_rate >= 5 else "#f59e0b" if engagement_rate >= 2 else "#ef4444"
            engagement_display = f"<span style='color: {rate_color}; font-weight: 600;'>{engagement_rate}%</span>"
        else:
            engagement_display = "<span style='color: rgba(255,255,255,0.3);'>-</span>"

        # Format numbers
        likes_display = f"{likes:,}" if isinstance(likes, int) else str(likes)
        comments_display = f"{comments:,}" if isinstance(comments, int) else str(comments)
        saved_display = f"{saved:,}" if isinstance(saved, int) else str(saved)
        reach_display = f"{reach:,}" if isinstance(reach, int) else str(reach)

        pub_date = info.get('published_at', 'N/A')[:10]
        url = info.get("url", "")

        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 2fr 1.5fr 1fr 1fr 1fr 1fr 1fr 0.8fr;
                    padding: 1rem; background: rgba(255,255,255,0.02);
                    border-radius: 12px; margin-bottom: 0.5rem;
                    border: 1px solid rgba(255,255,255,0.05); align-items: center;">
            <div>
                <span style="font-weight: 600; color: rgba(255,255,255,0.9); font-size: 0.95rem;">{display}</span>
            </div>
            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.5);">
                ✅ {pub_date}
            </div>
            <div style="text-align: center; font-weight: 500; color: rgba(255,255,255,0.7);">
                {likes_display}
            </div>
            <div style="text-align: center; font-weight: 500; color: rgba(255,255,255,0.7);">
                {comments_display}
            </div>
            <div style="text-align: center; font-weight: 500; color: rgba(255,255,255,0.7);">
                {saved_display}
            </div>
            <div style="text-align: center; font-weight: 500; color: rgba(255,255,255,0.7);">
                {reach_display}
            </div>
            <div style="text-align: center;">
                {engagement_display}
            </div>
            <div style="text-align: center;">
                {'<a href="' + url + '" target="_blank" style="color: #a855f7; text-decoration: none;">🔗</a>' if url else '<span style="color: rgba(255,255,255,0.2);">-</span>'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Summary stats at bottom
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Calculate totals from history with insights
    total_likes = 0
    total_comments = 0
    total_saved = 0
    total_reach = 0
    count_with_metrics = 0

    for name, info in history.items():
        post_id = info.get("post_id", "")
        post_insights = posts_insights.get(post_id, {}) if post_id else {}

        if post_insights:
            total_likes += post_insights.get("likes", 0)
            total_comments += post_insights.get("comments", 0)
            total_saved += post_insights.get("saved", 0)
            total_reach += post_insights.get("reach", 0)
            count_with_metrics += 1

    if count_with_metrics > 0:
        avg_engagement = (total_likes + total_comments + total_saved) / total_reach * 100 if total_reach > 0 else 0

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(99, 102, 241, 0.1));
                    border-radius: 16px; padding: 1.5rem; border: 1px solid rgba(168, 85, 247, 0.2);">
            <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
                        letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
                TOTAL PERFORMANCE ({count_with_metrics} posts with metrics)
            </div>
            <div style="display: flex; justify-content: space-around;">
                <div style="text-align: center;">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #ec4899;">{total_likes:,}</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Total Likes</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #8b5cf6;">{total_comments:,}</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Total Comments</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #06b6d4;">{total_saved:,}</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Total Saves</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #22c55e;">{total_reach:,}</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Total Reach</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.75rem; font-weight: 700; color: #f59e0b;">{avg_engagement:.2f}%</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Avg Eng. Rate</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_analytics_view():
    """Analytics Dashboard"""
    st.markdown("""
    <div class="main-header">
        <h1>Analytics</h1>
        <p>Track your content performance and audience engagement</p>
    </div>
    """, unsafe_allow_html=True)

    contents = get_content_folders()
    history = load_history()

    # Summary Stats
    total_content = len(contents)
    published_count = len(history)
    total_slides = sum(c["image_count"] for c in contents)
    avg_slides = total_slides / total_content if total_content > 0 else 0

    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        CONTENT OVERVIEW
    </p>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{total_content}</div>
            <div class="stat-label">Total Content</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #22c55e;">{published_count}</div>
            <div class="stat-label">Published</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #3b82f6;">{total_slides}</div>
            <div class="stat-label">Total Slides</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #f59e0b;">{avg_slides:.1f}</div>
            <div class="stat-label">Avg Slides</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Publishing Timeline
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        PUBLISHING TIMELINE
    </p>
    """, unsafe_allow_html=True)

    if history:
        # Create timeline data
        timeline_data = []
        for name, info in history.items():
            parts = name.split('_', 1)
            display = parts[1].title() if len(parts) > 1 else name.title()
            pub_date = info.get("published_at", "")[:10]
            timeline_data.append({"topic": display, "date": pub_date, "slides": info.get("images", 7)})

        # Sort by date
        timeline_data = sorted(timeline_data, key=lambda x: x["date"], reverse=True)

        for item in timeline_data[:10]:  # Show last 10
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.75rem 1rem;
                        background: rgba(255,255,255,0.03); border-radius: 8px;
                        margin-bottom: 0.5rem; border: 1px solid rgba(255,255,255,0.06);">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: rgba(255,255,255,0.9); font-size: 0.85rem;">{item['topic']}</div>
                    <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4);">{item['slides']} slides</div>
                </div>
                <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">{item['date']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: rgba(255,255,255,0.3);">
            <p style="margin: 0;">No publishing data yet</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Content by Status
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        CONTENT STATUS BREAKDOWN
    </p>
    """, unsafe_allow_html=True)

    published = sum(1 for c in contents if c["status"] == "published")
    scheduled = sum(1 for c in contents if c["status"] == "scheduled")
    draft = sum(1 for c in contents if c["status"] == "draft")

    if total_content > 0:
        pub_pct = (published / total_content) * 100
        sch_pct = (scheduled / total_content) * 100
        drf_pct = (draft / total_content) * 100

        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.5rem;
                    border: 1px solid rgba(255,255,255,0.06);">
            <div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 1rem;">
                <div style="width: {pub_pct}%; background: #22c55e;"></div>
                <div style="width: {sch_pct}%; background: #3b82f6;"></div>
                <div style="width: {drf_pct}%; background: rgba(255,255,255,0.2);"></div>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; color: #22c55e; font-weight: 600;">Published</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: rgba(255,255,255,0.9);">{published}</div>
                    <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">{pub_pct:.0f}%</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; color: #3b82f6; font-weight: 600;">Scheduled</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: rgba(255,255,255,0.9);">{scheduled}</div>
                    <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">{sch_pct:.0f}%</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; color: rgba(255,255,255,0.5); font-weight: 600;">Draft</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: rgba(255,255,255,0.9);">{draft}</div>
                    <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">{drf_pct:.0f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Recent Activity Feed
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        RECENT ACTIVITY
    </p>
    """, unsafe_allow_html=True)

    # Collect all activities
    activities = []

    # Add published events
    for name, info in history.items():
        parts = name.split('_', 1)
        display = parts[1].title() if len(parts) > 1 else name.title()
        pub_date = info.get("published_at", "")
        if pub_date:
            activities.append({
                "type": "published",
                "icon": "✅",
                "title": f"Published: {display}",
                "desc": f"{info.get('images', 7)} slides to Instagram",
                "time": pub_date,
                "color": "#22c55e"
            })

    # Add scheduled events
    schedule = load_schedule()
    for name, info in schedule.items():
        parts = name.split('_', 1)
        display = parts[1].title() if len(parts) > 1 else name.title()
        sch_date = info.get("scheduled_at", "")
        if sch_date:
            activities.append({
                "type": "scheduled",
                "icon": "📅",
                "title": f"Scheduled: {display}",
                "desc": f"Set for {sch_date[:10]}",
                "time": datetime.now().isoformat(),  # Use current time for sorting
                "color": "#3b82f6"
            })

    # Add created events (from folder creation time)
    for content in contents:
        activities.append({
            "type": "created",
            "icon": "➕",
            "title": f"Created: {content['display_name']}",
            "desc": f"{content['image_count']} slides generated",
            "time": content["created"].isoformat(),
            "color": "#a855f7"
        })

    # Sort by time and show recent 15
    activities = sorted(activities, key=lambda x: x["time"], reverse=True)[:15]

    if activities:
        for activity in activities:
            try:
                time_str = datetime.fromisoformat(activity["time"]).strftime("%Y-%m-%d %H:%M")
            except:
                time_str = activity["time"][:16]

            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; padding: 0.75rem 1rem;
                        background: rgba(255,255,255,0.02); border-radius: 8px;
                        margin-bottom: 0.5rem; border-left: 3px solid {activity['color']};">
                <div style="font-size: 1.25rem; margin-right: 1rem;">{activity['icon']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: rgba(255,255,255,0.9); font-size: 0.85rem;">{activity['title']}</div>
                    <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4);">{activity['desc']}</div>
                </div>
                <div style="font-size: 0.7rem; color: rgba(255,255,255,0.3);">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: rgba(255,255,255,0.3);">
            <p style="margin: 0;">No activity yet</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Tag Analytics
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        TAG DISTRIBUTION
    </p>
    """, unsafe_allow_html=True)

    # Count tags
    all_tags = load_tags()
    tag_counts = {}
    for content_tags in all_tags.values():
        for tag in content_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if tag_counts:
        # Sort by count
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        max_count = max(tag_counts.values()) if tag_counts else 1

        for tag_key, count in sorted_tags:
            tag_info = AVAILABLE_TAGS.get(tag_key, {"label": tag_key, "icon": "🏷️", "color": "#6b7280"})
            pct = (count / max_count) * 100

            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                <div style="width: 100px; font-size: 0.8rem;">
                    <span style="margin-right: 4px;">{tag_info['icon']}</span>
                    <span style="color: rgba(255,255,255,0.8);">{tag_info['label']}</span>
                </div>
                <div style="flex: 1; height: 24px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; margin: 0 1rem;">
                    <div style="height: 100%; width: {pct}%; background: {tag_info['color']}; border-radius: 4px;"></div>
                </div>
                <div style="width: 40px; text-align: right; font-size: 0.85rem; font-weight: 600; color: rgba(255,255,255,0.7);">
                    {count}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.3);">
            <p style="margin: 0;">No tags assigned yet</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Weekly Publishing Chart (simple text-based)
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        PUBLISHING FREQUENCY (LAST 4 WEEKS)
    </p>
    """, unsafe_allow_html=True)

    # Calculate weekly stats
    now = datetime.now()
    week_counts = [0, 0, 0, 0]  # [this week, last week, 2 weeks ago, 3 weeks ago]

    for name, info in history.items():
        try:
            pub_date = datetime.fromisoformat(info.get("published_at", "")[:19])
            days_ago = (now - pub_date).days
            if days_ago < 7:
                week_counts[0] += 1
            elif days_ago < 14:
                week_counts[1] += 1
            elif days_ago < 21:
                week_counts[2] += 1
            elif days_ago < 28:
                week_counts[3] += 1
        except:
            pass

    week_labels = ["This Week", "Last Week", "2 Weeks Ago", "3 Weeks Ago"]
    max_week = max(week_counts) if any(week_counts) else 1

    for i, (label, count) in enumerate(zip(week_labels, week_counts)):
        pct = (count / max_week) * 100 if max_week > 0 else 0
        color = "#22c55e" if i == 0 else "#3b82f6" if i == 1 else "rgba(255,255,255,0.3)"

        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <div style="width: 100px; font-size: 0.75rem; color: rgba(255,255,255,0.5);">{label}</div>
            <div style="flex: 1; height: 20px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; margin: 0 1rem;">
                <div style="height: 100%; width: {pct}%; background: {color}; border-radius: 4px;"></div>
            </div>
            <div style="width: 30px; text-align: right; font-size: 0.8rem; font-weight: 600; color: rgba(255,255,255,0.7);">
                {count}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # ============================================================
    # INSTAGRAM INSIGHTS SECTION
    # ============================================================
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        📊 INSTAGRAM INSIGHTS
    </p>
    """, unsafe_allow_html=True)

    # Refresh button
    col_refresh, col_status = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh Insights", key="refresh_insights_btn"):
            with st.spinner("Fetching Instagram Insights..."):
                result = refresh_insights_cache(force=True)
                if result["success"]:
                    st.success(f"✅ Updated {result['posts_updated']} posts")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', 'Unknown error')}")

    with col_status:
        cache = load_insights_cache()
        if cache.get("updated_at"):
            try:
                updated = datetime.fromisoformat(cache["updated_at"])
                time_ago = datetime.now() - updated
                if time_ago.total_seconds() < 3600:
                    mins = int(time_ago.total_seconds() / 60)
                    st.markdown(f"<span style='font-size: 0.75rem; color: rgba(255,255,255,0.4);'>Last updated: {mins} minutes ago</span>", unsafe_allow_html=True)
                else:
                    hours = int(time_ago.total_seconds() / 3600)
                    st.markdown(f"<span style='font-size: 0.75rem; color: rgba(255,255,255,0.4);'>Last updated: {hours} hours ago</span>", unsafe_allow_html=True)
            except:
                pass

    # Check for access token
    access_token, _ = get_instagram_credentials()
    if not access_token:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 12px; padding: 1.5rem; text-align: center; margin: 1rem 0;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔐</div>
            <div style="font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 0.5rem;">
                Instagram API Not Connected
            </div>
            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.5);">
                Add INSTAGRAM_ACCESS_TOKEN to your .env file to enable insights
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Account Insights
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        account_insights = fetch_account_insights("day")

        if account_insights:
            st.markdown("""
            <p style="font-size: 0.65rem; color: rgba(255,255,255,0.3); font-weight: 500;
                      letter-spacing: 0.05em; margin-bottom: 0.75rem;">
                ACCOUNT OVERVIEW
            </p>
            """, unsafe_allow_html=True)

            # Row 1: Basic stats
            acc_col1, acc_col2, acc_col3, acc_col4 = st.columns(4)

            with acc_col1:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(168, 85, 247, 0.05));">
                    <div class="stat-number" style="color: #a855f7;">{account_insights.get('followers_count', 0):,}</div>
                    <div class="stat-label">Followers</div>
                </div>
                """, unsafe_allow_html=True)

            with acc_col2:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05));">
                    <div class="stat-number" style="color: #3b82f6;">{account_insights.get('media_count', 0)}</div>
                    <div class="stat-label">Posts</div>
                </div>
                """, unsafe_allow_html=True)

            with acc_col3:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));">
                    <div class="stat-number" style="color: #22c55e;">{account_insights.get('reach', 0):,}</div>
                    <div class="stat-label">Reach (Today)</div>
                </div>
                """, unsafe_allow_html=True)

            with acc_col4:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05));">
                    <div class="stat-number" style="color: #f59e0b;">{account_insights.get('profile_views', 0):,}</div>
                    <div class="stat-label">Profile Views</div>
                </div>
                """, unsafe_allow_html=True)

            # Row 2: Engagement stats
            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
            eng_col1, eng_col2, eng_col3, eng_col4 = st.columns(4)

            with eng_col1:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.15), rgba(236, 72, 153, 0.05));">
                    <div class="stat-number" style="color: #ec4899;">{account_insights.get('accounts_engaged', 0):,}</div>
                    <div class="stat-label">Engaged Accounts</div>
                </div>
                """, unsafe_allow_html=True)

            with eng_col2:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(6, 182, 212, 0.05));">
                    <div class="stat-number" style="color: #06b6d4;">{account_insights.get('total_interactions', 0):,}</div>
                    <div class="stat-label">Total Interactions</div>
                </div>
                """, unsafe_allow_html=True)

            with eng_col3:
                # Calculate engagement rate
                reach = account_insights.get('reach', 0)
                interactions = account_insights.get('total_interactions', 0)
                eng_rate = (interactions / reach * 100) if reach > 0 else 0
                rate_color = "#22c55e" if eng_rate >= 5 else "#f59e0b" if eng_rate >= 2 else "#ef4444"
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));">
                    <div class="stat-number" style="color: {rate_color};">{eng_rate:.1f}%</div>
                    <div class="stat-label">Engagement Rate</div>
                </div>
                """, unsafe_allow_html=True)

            with eng_col4:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(139, 92, 246, 0.05));">
                    <div class="stat-number" style="color: #8b5cf6;">{account_insights.get('follows_count', 0)}</div>
                    <div class="stat-label">Following</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # Top Performing Posts
        st.markdown("""
        <p style="font-size: 0.65rem; color: rgba(255,255,255,0.3); font-weight: 500;
                  letter-spacing: 0.05em; margin-bottom: 0.75rem;">
            TOP PERFORMING POSTS
        </p>
        """, unsafe_allow_html=True)

        # Metric selector
        metric_options = {
            "engagement_rate": "Engagement Rate",
            "likes": "Likes",
            "reach": "Reach",
            "saved": "Saves"
        }
        selected_metric = st.selectbox(
            "Sort by",
            options=list(metric_options.keys()),
            format_func=lambda x: metric_options[x],
            key="top_posts_metric",
            label_visibility="collapsed"
        )

        top_posts = get_top_performing_posts(limit=5, metric=selected_metric)

        if top_posts:
            for i, post in enumerate(top_posts, 1):
                # Extract topic from caption
                caption = post.get("caption", "")[:100] + "..." if post.get("caption") else "No caption"
                topic = extract_topic_from_caption(post.get("caption", "")) or "Unknown"

                engagement_rate = post.get("engagement_rate", 0)
                rate_color = "#22c55e" if engagement_rate >= 5 else "#f59e0b" if engagement_rate >= 2 else "#ef4444"

                st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 1rem;
                            background: rgba(255,255,255,0.02); border-radius: 12px;
                            margin-bottom: 0.75rem; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="width: 32px; height: 32px; border-radius: 8px;
                                background: linear-gradient(135deg, #a855f7, #6366f1);
                                display: flex; align-items: center; justify-content: center;
                                font-weight: 700; font-size: 0.9rem; color: white; margin-right: 1rem;">
                        {i}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: rgba(255,255,255,0.9); font-size: 0.9rem; text-transform: capitalize;">
                            {topic}
                        </div>
                        <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 2px;">
                            {post.get('timestamp', '')[:10]}
                        </div>
                    </div>
                    <div style="display: flex; gap: 1.5rem; align-items: center;">
                        <div style="text-align: center;">
                            <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">Likes</div>
                            <div style="font-weight: 600; color: rgba(255,255,255,0.8);">{post.get('likes', 0):,}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">Comments</div>
                            <div style="font-weight: 600; color: rgba(255,255,255,0.8);">{post.get('comments', 0):,}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">Saves</div>
                            <div style="font-weight: 600; color: rgba(255,255,255,0.8);">{post.get('saved', 0):,}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">Reach</div>
                            <div style="font-weight: 600; color: rgba(255,255,255,0.8);">{post.get('reach', 0):,}</div>
                        </div>
                        <div style="text-align: center; min-width: 60px;">
                            <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4);">Eng. Rate</div>
                            <div style="font-weight: 700; color: {rate_color}; font-size: 1rem;">{engagement_rate}%</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Average metrics
            avg_metrics = calculate_average_metrics(top_posts)
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.02); border-radius: 12px; padding: 1rem;
                        border: 1px solid rgba(255,255,255,0.05);">
                <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4); margin-bottom: 0.75rem;">
                    AVERAGE METRICS (Top 5 Posts)
                </div>
                <div style="display: flex; justify-content: space-around;">
                    <div style="text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #ec4899;">{avg_metrics['avg_likes']}</div>
                        <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4);">Avg Likes</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #8b5cf6;">{avg_metrics['avg_comments']}</div>
                        <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4);">Avg Comments</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #06b6d4;">{avg_metrics['avg_saved']}</div>
                        <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4);">Avg Saves</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #22c55e;">{avg_metrics['avg_engagement_rate']}%</div>
                        <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4);">Avg Eng. Rate</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.3);">
                <p style="margin: 0;">No post insights available. Click "Refresh Insights" to fetch data.</p>
            </div>
            """, unsafe_allow_html=True)


def render_compare_view():
    """Content Comparison View"""
    st.markdown("""
    <div class="main-header">
        <h1>Compare Content</h1>
        <p>Side-by-side comparison of two content sets</p>
    </div>
    """, unsafe_allow_html=True)

    contents = get_content_folders()
    content_options = ["Select content..."] + [c["display_name"] for c in contents]
    content_map = {c["display_name"]: c for c in contents}

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Content A")
        content_a = st.selectbox("Select first content", content_options, key="compare_a", label_visibility="collapsed")

    with col2:
        st.markdown("#### Content B")
        content_b = st.selectbox("Select second content", content_options, key="compare_b", label_visibility="collapsed")

    if content_a != "Select content..." and content_b != "Select content...":
        if content_a == content_b:
            st.warning("Please select two different content sets to compare")
            return

        info_a = content_map[content_a]
        info_b = content_map[content_b]

        # Stats comparison
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
                  letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
            COMPARISON
        </p>
        """, unsafe_allow_html=True)

        # Stats table
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
            <div style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 1rem;">
                <div style="font-size: 0.7rem; color: var(--text-tertiary); margin-bottom: 0.5rem;">Slides</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary);">{info_a['image_count']}</span>
                    <span style="color: var(--text-tertiary);">vs</span>
                    <span style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary);">{info_b['image_count']}</span>
                </div>
            </div>
            <div style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 1rem;">
                <div style="font-size: 0.7rem; color: var(--text-tertiary); margin-bottom: 0.5rem;">Status</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: {'#22c55e' if info_a['status'] == 'published' else '#3b82f6' if info_a['status'] == 'scheduled' else 'var(--text-tertiary)'};">{info_a['status'].title()}</span>
                    <span style="color: var(--text-tertiary);">vs</span>
                    <span style="font-size: 0.85rem; color: {'#22c55e' if info_b['status'] == 'published' else '#3b82f6' if info_b['status'] == 'scheduled' else 'var(--text-tertiary)'};">{info_b['status'].title()}</span>
                </div>
            </div>
            <div style="background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 1rem;">
                <div style="font-size: 0.7rem; color: var(--text-tertiary); margin-bottom: 0.5rem;">Created</div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.75rem; color: var(--text-secondary);">{info_a['created'].strftime('%m/%d')}</span>
                    <span style="color: var(--text-tertiary);">vs</span>
                    <span style="font-size: 0.75rem; color: var(--text-secondary);">{info_b['created'].strftime('%m/%d')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Side by side image comparison
        st.markdown("""
        <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
                  letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
            SLIDE COMPARISON
        </p>
        """, unsafe_allow_html=True)

        # Slide selector
        max_slides = max(info_a['image_count'], info_b['image_count'])
        slide_num = st.slider("Slide", 1, max_slides, 1, key="compare_slide")

        img_col1, img_col2 = st.columns(2)

        with img_col1:
            st.markdown(f"<div style='text-align: center; margin-bottom: 0.5rem; font-weight: 600;'>{content_a}</div>", unsafe_allow_html=True)
            if slide_num <= info_a['image_count']:
                img_path = info_a['images'][slide_num - 1]
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode()
                st.markdown(f'<img src="data:image/png;base64,{img_data}" style="width: 100%; border-radius: 12px;">', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: var(--glass-bg); border: 1px dashed var(--glass-border);
                            border-radius: 12px; padding: 3rem; text-align: center; color: var(--text-tertiary);">
                    No slide {slide_num}
                </div>
                """, unsafe_allow_html=True)

        with img_col2:
            st.markdown(f"<div style='text-align: center; margin-bottom: 0.5rem; font-weight: 600;'>{content_b}</div>", unsafe_allow_html=True)
            if slide_num <= info_b['image_count']:
                img_path = info_b['images'][slide_num - 1]
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode()
                st.markdown(f'<img src="data:image/png;base64,{img_data}" style="width: 100%; border-radius: 12px;">', unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: var(--glass-bg); border: 1px dashed var(--glass-border);
                            border-radius: 12px; padding: 3rem; text-align: center; color: var(--text-tertiary);">
                    No slide {slide_num}
                </div>
                """, unsafe_allow_html=True)

    else:
        render_empty_state(
            icon="🔍",
            title="Select two content sets",
            description="Choose two different content sets from the dropdowns above to compare them side by side.",
            action_text=None,
            action_page=None
        )


def render_settings_view():
    """Settings Page"""
    st.markdown("""
    <div class="main-header">
        <h1>Settings</h1>
        <p>Configure your dashboard preferences</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize settings in session state
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "theme": "dark",
            "language": "en",
            "grid_columns": 6,
            "auto_sync": False,
            "notifications": True,
            "compact_mode": False
        }

    settings = st.session_state.settings

    # Appearance Section
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        APPEARANCE
    </p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: var(--glass-bg); border-radius: 12px; padding: 1.25rem;
                    border: 1px solid var(--glass-border); margin-bottom: 1rem;">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Theme</div>
            <div style="font-size: 0.75rem; color: var(--text-tertiary);">Choose your preferred color scheme</div>
        </div>
        """, unsafe_allow_html=True)

        # Get current theme index
        theme_options = ["dark", "light", "system"]
        theme_display = ["🌙 Dark", "☀️ Light", "💻 System"]
        current_theme = settings.get("theme", "dark")
        theme_index = theme_options.index(current_theme) if current_theme in theme_options else 0

        theme = st.selectbox("Theme", theme_display, index=theme_index, label_visibility="collapsed", key="theme_select")

        # Update theme in settings
        selected_theme = theme_options[theme_display.index(theme)]
        if selected_theme != settings.get("theme"):
            st.session_state.settings["theme"] = selected_theme
            st.session_state.toast_message = f"Theme changed to {theme}"
            st.session_state.toast_type = "success"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background: var(--glass-bg); border-radius: 12px; padding: 1.25rem;
                    border: 1px solid var(--glass-border); margin-bottom: 1rem;">
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Language</div>
            <div style="font-size: 0.75rem; color: var(--text-tertiary);">Select interface language</div>
        </div>
        """, unsafe_allow_html=True)

        lang_options = ["en", "ko", "ja"]
        lang_display = ["🇺🇸 English", "🇰🇷 한국어", "🇯🇵 日本語"]
        current_lang = settings.get("language", "en")
        lang_index = lang_options.index(current_lang) if current_lang in lang_options else 0

        language = st.selectbox("Language", lang_display, index=lang_index, label_visibility="collapsed", key="lang_select")

        # Update language in settings
        selected_lang = lang_options[lang_display.index(language)]
        if selected_lang != settings.get("language"):
            st.session_state.settings["language"] = selected_lang
            st.session_state.toast_message = f"Language changed to {language}"
            st.session_state.toast_type = "success"
            st.rerun()

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Display Section
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        DISPLAY
    </p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.25rem;
                    border: 1px solid rgba(255,255,255,0.06); margin-bottom: 1rem;">
            <div style="font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 0.5rem;">Grid Columns</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">Number of columns in content grid</div>
        </div>
        """, unsafe_allow_html=True)
        grid_cols = st.select_slider("Columns", options=[4, 5, 6, 7, 8], value=6, label_visibility="collapsed")

    with col2:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.25rem;
                    border: 1px solid rgba(255,255,255,0.06); margin-bottom: 1rem;">
            <div style="font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 0.5rem;">Compact Mode</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">Reduce spacing for more content</div>
        </div>
        """, unsafe_allow_html=True)
        compact = st.toggle("Compact", value=False, label_visibility="collapsed")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Sync & Notifications Section
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        SYNC & NOTIFICATIONS
    </p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.25rem;
                    border: 1px solid rgba(255,255,255,0.06); margin-bottom: 1rem;">
            <div style="font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 0.5rem;">Auto Sync</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">Automatically sync with Instagram</div>
        </div>
        """, unsafe_allow_html=True)
        auto_sync = st.toggle("Auto Sync", value=False, label_visibility="collapsed")

    with col2:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.25rem;
                    border: 1px solid rgba(255,255,255,0.06); margin-bottom: 1rem;">
            <div style="font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 0.5rem;">Notifications</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">Show toast notifications</div>
        </div>
        """, unsafe_allow_html=True)
        notifications = st.toggle("Notifications", value=True, label_visibility="collapsed")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # API Configuration Section
    st.markdown("""
    <p style="font-size: 0.7rem; color: rgba(255,255,255,0.4); font-weight: 600;
              letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;">
        API CONFIGURATION
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.25rem;
                border: 1px solid rgba(255,255,255,0.06);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <div style="font-weight: 600; color: rgba(255,255,255,0.9);">Instagram API</div>
                <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">Graph API connection status</div>
            </div>
            <div style="background: rgba(34, 197, 94, 0.15); color: #22c55e; padding: 0.25rem 0.75rem;
                        border-radius: 100px; font-size: 0.7rem; font-weight: 600;">Connected</div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <div style="font-weight: 600; color: rgba(255,255,255,0.9);">Cloudinary</div>
                <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">Image hosting service</div>
            </div>
            <div style="background: rgba(34, 197, 94, 0.15); color: #22c55e; padding: 0.25rem 0.75rem;
                        border-radius: 100px; font-size: 0.7rem; font-weight: 600;">Connected</div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-weight: 600; color: rgba(255,255,255,0.9);">FAL.ai</div>
                <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">Image generation API</div>
            </div>
            <div style="background: rgba(34, 197, 94, 0.15); color: #22c55e; padding: 0.25rem 0.75rem;
                        border-radius: 100px; font-size: 0.7rem; font-weight: 600;">Connected</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Save button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.session_state.settings["grid_columns"] = grid_cols
            st.session_state.settings["auto_sync"] = auto_sync
            st.session_state.settings["notifications"] = notifications
            st.session_state.settings["compact_mode"] = compact
            st.session_state.toast_message = "Settings saved!"
            st.session_state.toast_type = "success"
            st.rerun()


# ============================================================
# MAIN APP
# ============================================================
def main():
    if "page" not in st.session_state:
        st.session_state.page = "list"

    # Apply dynamic theme CSS
    theme_css = get_theme_css()
    st.markdown(f"""
    <style>
        :root {{
            {theme_css}
        }}
    </style>
    """, unsafe_allow_html=True)

    render_sidebar()

    # Keyboard shortcuts help
    render_keyboard_shortcuts_help()

    # Show toast notifications from session state
    if st.session_state.get("toast_message"):
        show_toast(
            st.session_state.toast_message,
            st.session_state.get("toast_type", "info")
        )
        # Clear after showing
        st.session_state.toast_message = None
        st.session_state.toast_type = None

    page = st.session_state.get("page", "list")

    if page == "list":
        render_content_list()
    elif page == "detail":
        render_content_detail()
    elif page == "create":
        render_create_content()
    elif page == "schedule":
        render_schedule_view()
    elif page == "history":
        render_history_view()
    elif page == "analytics":
        render_analytics_view()
    elif page == "settings":
        render_settings_view()
    elif page == "compare":
        render_compare_view()


if __name__ == "__main__":
    main()
