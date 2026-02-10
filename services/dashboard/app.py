#!/usr/bin/env python3
"""
Project Sunshine - 통합 대시보드 v5.0
웹에서 직접 파이프라인 실행 + 실시간 로그

실행: streamlit run services/dashboard/app.py

Modules:
    - 대시보드: 프로젝트 현황 요약
    - 콘텐츠 허브: 콘텐츠 관리 및 갤러리
    - 제작: 파이프라인 실행 및 모니터링
    - API 비용: 사용량 추적
    - 설정: 프로젝트 설정 관리
"""

from __future__ import annotations

import streamlit as st
from pathlib import Path
import sys
import json
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from PIL import Image
import base64
import subprocess
import time
import logging
import signal
import re  # P0 fix: topic 검증용

# ============================================
# 상수 정의
# ============================================
VERSION = "5.2"
INSTAGRAM_HANDLE = "@sunshinedogfood"

# 썸네일 설정
THUMB_SIZE: Tuple[int, int] = (200, 200)
THUMB_QUALITY: int = 80

# 이미지 설정
TARGET_IMAGE_SIZE: Tuple[int, int] = (1080, 1080)

# 로그 설정
LOG_MAX_FILES: int = 20
LOG_MAX_DAYS: int = 7
LOG_TAIL_CHARS: int = 5000
LOG_TAIL_LINES: int = 30

# 캐시 TTL (초)
CACHE_TTL: int = 300

# 자동 새로고침 간격 (초)
AUTO_REFRESH_INTERVAL: int = 3
LOG_REFRESH_INTERVAL: int = 5

# 간소화된 파이프라인 단계 (UI 표시용 - 7단계)
SIMPLIFIED_STEPS: List[Dict[str, Any]] = [
    {"id": 0, "emoji": "👔", "role": "지시", "status": "pending"},
    {"id": 1, "emoji": "✍️", "role": "기획", "status": "pending"},
    {"id": 2, "emoji": "🔬", "role": "검증", "status": "pending"},
    {"id": 3, "emoji": "🎨", "role": "이미지", "status": "pending"},
    {"id": 4, "emoji": "✏️", "role": "합성", "status": "pending"},
    {"id": 5, "emoji": "📤", "role": "업로드", "status": "pending"},
    {"id": 6, "emoji": "📸", "role": "게시", "status": "pending"},
]

# ============================================
# 로깅 설정
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# 경로 설정
# ============================================
ROOT = Path(__file__).parent.parent.parent.resolve()  # P0 fix: 절대 경로로 변환
# P0 fix: 경로 검증 - project_sunshine 디렉토리인지 확인
if not (ROOT / "CLAUDE.md").exists():
    raise RuntimeError(f"Invalid ROOT path: {ROOT}")
sys.path.insert(0, str(ROOT))

# P0 fix: topic 화이트리스트 (subprocess 인젝션 방지)
VALID_TOPIC_PATTERN = r'^[a-z][a-z0-9_]{0,29}$'  # 소문자, 숫자, 언더스코어만 허용

THUMB_DIR = Path(__file__).parent / ".thumbs"
THUMB_DIR.mkdir(exist_ok=True)


def get_thumbnail(image_path: str) -> str:
    """썸네일 생성 및 캐싱.

    이미지 파일의 썸네일을 생성하고 캐시 디렉토리에 저장합니다.
    이미 캐시된 썸네일이 있으면 캐시된 경로를 반환합니다.

    Args:
        image_path: 원본 이미지 파일 경로

    Returns:
        썸네일 파일 경로. 생성 실패 시 원본 경로 반환.

    Note:
        캐시 키는 파일명과 수정 시간으로 생성됩니다.
    """
    src = Path(image_path)
    if not src.exists():
        return image_path

    # 캐시 키 생성 (파일명 + 수정시간)
    cache_key = f"{src.name}_{src.stat().st_mtime_ns}"
    thumb_name = hashlib.md5(cache_key.encode()).hexdigest() + ".jpg"
    thumb_path = THUMB_DIR / thumb_name

    if thumb_path.exists():
        return str(thumb_path)

    try:
        img = Image.open(src)
        img.thumbnail(THUMB_SIZE, Image.LANCZOS)
        img = img.convert("RGB")
        img.save(thumb_path, "JPEG", quality=THUMB_QUALITY)
        logger.debug(f"Thumbnail created: {thumb_path.name}")
        return str(thumb_path)
    except (IOError, OSError) as e:
        logger.warning(f"Thumbnail generation failed for {src}: {e}")
        return image_path


def img_to_b64(path: str) -> str:
    """이미지를 base64 문자열로 변환.

    썸네일을 생성한 후 base64로 인코딩하여 HTML img 태그에서
    직접 사용할 수 있는 형태로 반환합니다.

    Args:
        path: 이미지 파일 경로

    Returns:
        base64 인코딩된 문자열. 실패 시 빈 문자열.
    """
    try:
        thumb = get_thumbnail(path)
        with open(thumb, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except (IOError, OSError) as e:
        logger.warning(f"Base64 encoding failed for {path}: {e}")
        return ""


def resize_with_padding(
    img: Image.Image,
    target_size: Tuple[int, int] = TARGET_IMAGE_SIZE
) -> Image.Image:
    """비율 유지하며 패딩을 추가하여 리사이즈 (Letterbox).

    이미지의 가로세로 비율을 유지하면서 목표 크기에 맞게 리사이즈하고,
    남는 영역은 배경색으로 채웁니다. RGBA 이미지의 투명도를 보존합니다.

    Args:
        img: PIL Image 객체
        target_size: 목표 크기 (width, height). 기본값 1080x1080.

    Returns:
        리사이즈된 PIL Image 객체

    Example:
        >>> img = Image.open("photo.png")
        >>> resized = resize_with_padding(img, (1080, 1080))
    """
    target_w, target_h = target_size

    # 투명도 모드 처리
    has_alpha = img.mode in ('RGBA', 'LA', 'P')
    if has_alpha:
        img = img.convert('RGBA')
        background_color: Tuple[int, ...] = (255, 255, 255, 0)
    else:
        img = img.convert('RGB')
        background_color = (255, 255, 255)

    # 비율 계산 (작은 쪽에 맞춤)
    orig_w, orig_h = img.size
    scale_ratio = min(target_w / orig_w, target_h / orig_h)
    new_w = int(orig_w * scale_ratio)
    new_h = int(orig_h * scale_ratio)

    # 고품질 리사이즈
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 새 캔버스에 중앙 배치
    new_img = Image.new(img.mode, target_size, background_color)
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2

    # RGBA는 알파 채널을 마스크로 사용
    if img.mode == 'RGBA':
        new_img.paste(img, (paste_x, paste_y), img)
    else:
        new_img.paste(img, (paste_x, paste_y))

    return new_img


def cleanup_old_logs(
    max_files: int = LOG_MAX_FILES,
    max_days: int = LOG_MAX_DAYS
) -> int:
    """오래된 로그 파일 정리.

    두 가지 기준으로 로그 파일을 정리합니다:
    1. 최대 파일 수 초과분 삭제
    2. 지정된 일수보다 오래된 파일 삭제

    Args:
        max_files: 보관할 최대 로그 파일 수. 기본값 20.
        max_days: 보관할 최대 일수. 기본값 7.

    Returns:
        삭제된 파일 수
    """
    logs_dir = ROOT / "config" / "logs"
    if not logs_dir.exists():
        return 0

    deleted_count = 0
    log_files = sorted(
        logs_dir.glob("pipeline_*.log"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    # 최대 파일 수 초과분 삭제
    for old_file in log_files[max_files:]:
        try:
            old_file.unlink()
            logger.info(f"Deleted excess log: {old_file.name}")
            deleted_count += 1
        except OSError as e:
            logger.debug(f"Failed to delete {old_file.name}: {e}")

    # 오래된 파일 삭제
    seconds_per_day = 86400
    cutoff = datetime.now().timestamp() - (max_days * seconds_per_day)
    for log_file in log_files[:max_files]:
        try:
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                logger.info(f"Deleted old log: {log_file.name}")
                deleted_count += 1
        except OSError as e:
            logger.debug(f"Failed to delete {log_file.name}: {e}")

    return deleted_count


# 페이지 설정
st.set_page_config(
    page_title="Project Sunshine",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# CSS v5.0 - 통합 대시보드 스타일
# ============================================
st.markdown("""
<style>
/* === 기본 === */
@import url('https://fastly.jsdelivr.net/gh/nickcee/LINESeedKR@latest/LINESeedKR-Bd.woff2');
* { font-family: 'LINESeedKR', -apple-system, sans-serif !important; }
.stApp { background: linear-gradient(180deg, #08080c 0%, #0d0d14 100%); color: #c8c8d8; }
[data-testid="stSidebar"] { background: #0a0a10; border-right: 1px solid rgba(255,255,255,0.03); }
#MainMenu, footer { visibility: hidden; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

/* === 사이드바 === */
.sidebar-brand {
    font-size: 1.4rem; font-weight: 800;
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    padding: 0.8rem 0 1.2rem;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(139,92,246,0.08) !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 10px !important;
}

/* === 헤더 === */
.page-header { padding: 0.8rem 0 1.2rem; }
.page-title {
    font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(135deg, #f0f0f8 0%, #a0a0b8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.page-subtitle { color: #8a8aa0; font-size: 0.85rem; margin-top: 0.2rem; }

/* === 통계 카드 === */
.stat-grid { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.stat-card {
    flex: 1; background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 16px; padding: 1.2rem; text-align: center;
    position: relative; overflow: hidden;
    transition: all 0.3s ease;
}
.stat-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.08); }
.stat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.stat-card.published::before { background: linear-gradient(90deg, #10b981, #34d399); }
.stat-card.ready::before { background: linear-gradient(90deg, #06b6d4, #22d3ee); }
.stat-card.cover::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.stat-card.total::before { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.stat-value { font-size: 2.2rem; font-weight: 800; line-height: 1; }
.stat-label { color: #8a8aa0; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; margin-top: 0.4rem; }

/* === 섹션 === */
.section-title {
    font-size: 0.75rem; font-weight: 700; color: #8a8aa0;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 1.5rem 0 1rem; display: flex; align-items: center; gap: 0.6rem;
}
.section-title::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.04); }

/* === 콘텐츠 카드 === */
.content-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 12px; overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 0.5rem;
}
.content-card:hover {
    transform: translateY(-4px);
    border-color: rgba(139,92,246,0.3);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}
.card-img { width: 100%; aspect-ratio: 1; object-fit: cover; display: block; }
.card-body { padding: 0.7rem; }
.card-title { font-size: 0.75rem; font-weight: 700; color: #e0e0ec; margin-bottom: 0.3rem; }
.card-meta { display: flex; justify-content: space-between; align-items: center; }
.card-count { font-size: 0.6rem; color: #8a8aa0; }
.badge {
    font-size: 0.5rem; font-weight: 700; padding: 0.2rem 0.5rem;
    border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em;
}
.badge-published { background: rgba(16,185,129,0.15); color: #34d399; }
.badge-ready { background: rgba(6,182,212,0.15); color: #22d3ee; }
.badge-cover { background: rgba(245,158,11,0.15); color: #fbbf24; }

/* === 파이프라인 === */
.pipeline-container {
    background: rgba(255,255,255,0.01);
    border-radius: 16px; padding: 1.2rem;
    border: 1px solid rgba(255,255,255,0.03);
}
.pipeline-row { display: flex; justify-content: center; gap: 0.3rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.pipe-step {
    display: flex; flex-direction: column; align-items: center;
    padding: 0.4rem 0.6rem; min-width: 60px;
}
.pipe-icon {
    width: 42px; height: 42px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; border: 2px solid transparent;
    transition: all 0.3s ease;
}
.pipe-icon.pending { background: #1a1a24; border-color: #2a2a3e; }
.pipe-icon.running {
    background: linear-gradient(135deg, #f59e0b, #fbbf24);
    border-color: #fbbf24;
    box-shadow: 0 0 20px rgba(245,158,11,0.4);
    animation: pulse 1.5s infinite;
}
.pipe-icon.done {
    background: linear-gradient(135deg, #10b981, #34d399);
    border-color: #34d399;
    box-shadow: 0 0 12px rgba(16,185,129,0.3);
}
.pipe-icon.error {
    background: linear-gradient(135deg, #ef4444, #f87171);
    border-color: #f87171;
    box-shadow: 0 0 12px rgba(239,68,68,0.4);
}
.pipe-icon.gate { border-radius: 8px; }
.pipe-label { font-size: 0.55rem; color: #9a9ab0; margin-top: 0.3rem; text-align: center; }
.pipe-arrow { color: #2a2a3e; font-size: 0.8rem; display: flex; align-items: center; }
.pipe-arrow.done { color: #34d399; }

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.08); opacity: 0.9; }
}

/* === 타임라인 === */
.timeline { padding: 0.5rem 0; }
.timeline-item {
    display: flex; gap: 1rem; padding: 0.8rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
}
.timeline-icon {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; flex-shrink: 0;
}
.timeline-icon.success { background: rgba(16,185,129,0.15); }
.timeline-icon.info { background: rgba(59,130,246,0.15); }
.timeline-icon.warning { background: rgba(245,158,11,0.15); }
.timeline-content { flex: 1; }
.timeline-title { font-size: 0.8rem; font-weight: 600; color: #e0e0ec; }
.timeline-desc { font-size: 0.7rem; color: #9a9ab0; margin-top: 0.2rem; }
.timeline-time { font-size: 0.6rem; color: #8a8aa0; }

/* === 검색바 === */
.search-container {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 12px; padding: 1rem;
    margin-bottom: 1rem;
}

/* === 갤러리 모달 === */
.gallery-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
}
.gallery-item {
    aspect-ratio: 1;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.2s;
}
.gallery-item:hover { transform: scale(1.02); }
.gallery-item img { width: 100%; height: 100%; object-fit: cover; }

/* === 버튼 === */
.stButton > button {
    border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.03); color: #a0a0b4;
    font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover {
    border-color: rgba(139,92,246,0.3); background: rgba(139,92,246,0.08);
    color: #c4b5fd;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #6366f1);
    border: none; color: #fff;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 8px 24px rgba(124,58,237,0.4);
    transform: translateY(-1px);
}

/* === 진행바 === */
.progress-bar {
    height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px;
    overflow: hidden; margin-top: 0.5rem;
}
.progress-fill {
    height: 100%; border-radius: 2px;
    background: linear-gradient(90deg, #7c3aed, #6366f1);
    transition: width 0.5s ease;
}

/* === 실행 로그 === */
.log-container {
    background: #0a0a0f;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 1rem;
    max-height: 300px;
    overflow-y: auto;
    font-family: 'Monaco', 'Menlo', monospace !important;
    font-size: 0.75rem;
    line-height: 1.5;
}
.log-line { color: #9a9ab0; }
.log-line.info { color: #3b82f6; }
.log-line.success { color: #10b981; }
.log-line.error { color: #ef4444; }
.log-line.warning { color: #f59e0b; }

/* === 기타 === */
hr { border-color: rgba(255,255,255,0.03) !important; margin: 1.5rem 0 !important; }
.stSelectbox label { font-size: 0.7rem !important; color: #8a8aa0 !important; text-transform: uppercase; letter-spacing: 0.08em; }
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    color: #c8c8d8 !important;
}

/* === 접근성 개선 - 색상 대비 강화 (WCAG AA 준수) === */
/* 중복 선언 정리: 기존 선언과 병합 */

/* === 로딩 스피너 === */
.loading-spinner {
    display: inline-block;
    width: 20px; height: 20px;
    border: 2px solid rgba(255,255,255,0.1);
    border-top-color: #fbbf24;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

/* === 토스트 알림 === */
.toast {
    position: fixed; bottom: 2rem; right: 2rem;
    background: rgba(16,185,129,0.95); color: #fff;
    padding: 1rem 1.5rem; border-radius: 8px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease;
    z-index: 9999;
}
.toast.error { background: rgba(239,68,68,0.95); }
@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* === 반응형 - 모바일 === */
@media (max-width: 768px) {
    .stat-grid { flex-wrap: wrap; }
    .stat-card { min-width: 45%; flex: 1 1 45%; }
    .stat-value { font-size: 1.6rem; }
    .page-title { font-size: 1.4rem; }
    .pipeline-row { gap: 0.2rem; }
    .pipe-step { min-width: 45px; padding: 0.3rem; }
    .pipe-icon { width: 32px; height: 32px; font-size: 0.9rem; }
    .pipe-label { font-size: 0.5rem; }
    .content-card { margin-bottom: 0.8rem; }
    .card-title { font-size: 0.7rem; }
    .gallery-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
    .stat-card { min-width: 100%; }
    .pipe-step { min-width: 40px; }
    .pipe-icon { width: 28px; height: 28px; font-size: 0.8rem; }
    .gallery-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ============================================
# 데이터 로딩
# ============================================

# 음식 영문-한글 매핑
FOOD_NAME_KR: Dict[str, str] = {
    "pumpkin": "호박", "carrot": "당근", "blueberry": "블루베리",
    "cherry": "체리", "cherries": "체리",
    "sweet_potato": "고구마", "apple": "사과", "pineapple": "파인애플", "banana": "바나나",
    "broccoli": "브로콜리", "watermelon": "수박", "strawberry": "딸기", "mango": "망고",
    "orange": "오렌지", "pear": "배", "kiwi": "키위", "papaya": "파파야", "peach": "복숭아",
    "grape": "포도", "melon": "멜론", "avocado": "아보카도", "cucumber": "오이",
    "spinach": "시금치", "potato": "감자", "tomato": "토마토",
}


@st.cache_data(ttl=CACHE_TTL)
def load_content_data() -> List[Dict[str, Any]]:
    """콘텐츠 데이터 로드.

    content/images 디렉토리에서 콘텐츠 정보를 수집합니다.
    게시됨(published), 준비됨(ready), 커버만(cover_ready) 상태를 구분합니다.

    Returns:
        콘텐츠 정보 딕셔너리 리스트
    """
    content_dir = ROOT / "content" / "images"
    cover_ref_dir = ROOT / "content" / "images" / "000_cover"

    def _find_cover(images):
        for img in images:
            if "00" in img.name or "cover" in img.name.lower():
                return img
        return images[0] if images else None

    all_contents = []
    published_topics = set()
    ready_topics = set()

    if not content_dir.exists():
        return all_contents

    # PUBLISHED
    for folder in content_dir.iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if folder.name in ["reference", "temp", "sunshine"]:
            continue
        if "_published" not in folder.name:
            continue

        parts = folder.name.replace("_published", "").split("_", 1)
        topic = parts[1] if len(parts) > 1 else parts[0]
        published_topics.add(topic.lower())

        images = sorted(folder.glob("*.png")) + sorted(folder.glob("*.jpg"))
        cover_img = _find_cover(images)

        # 폴더 수정 시간으로 날짜 추정
        try:
            mtime = folder.stat().st_mtime
            created = datetime.fromtimestamp(mtime)
        except OSError:
            created = datetime.now()

        all_contents.append({
            "topic": topic, "topic_kr": FOOD_NAME_KR.get(topic.lower(), topic),
            "folder_name": folder.name,  # 폴더명 전체 저장
            "status": "published", "slides": len(images),
            "cover": str(cover_img) if cover_img else None,
            "thumb_b64": img_to_b64(str(cover_img)) if cover_img else "",
            "all_images": [str(img) for img in images],
            "folder": str(folder),
            "created": created,
        })

    # READY
    for folder in content_dir.iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if folder.name in ["reference", "temp", "sunshine"]:
            continue
        if "_published" in folder.name:
            continue

        parts = folder.name.split("_", 1)
        topic = parts[1] if len(parts) > 1 else parts[0]
        if topic.lower() in published_topics:
            continue

        images = sorted(folder.glob("*.png")) + sorted(folder.glob("*.jpg"))
        if len(images) < 3:
            continue

        ready_topics.add(topic.lower())
        cover_img = _find_cover(images)

        try:
            mtime = folder.stat().st_mtime
            created = datetime.fromtimestamp(mtime)
        except OSError:
            created = datetime.now()

        all_contents.append({
            "topic": topic, "topic_kr": FOOD_NAME_KR.get(topic.lower(), topic),
            "folder_name": folder.name,  # 폴더명 전체 저장
            "status": "ready", "slides": len(images),
            "cover": str(cover_img) if cover_img else None,
            "thumb_b64": img_to_b64(str(cover_img)) if cover_img else "",
            "all_images": [str(img) for img in images],
            "folder": str(folder),
            "created": created,
        })

    # COVER READY
    if cover_ref_dir.exists():
        ref_images = sorted(cover_ref_dir.glob("*.png")) + sorted(cover_ref_dir.glob("*.jpg"))
        ref_categories = {}
        for img in ref_images:
            # hf_ 접두사 (Hugging Face 임시 파일) 및 UUID 형식 파일 제외
            if img.stem.startswith("hf_") or "-" in img.stem and len(img.stem) > 30:
                continue
            parts = img.stem.split("_")
            category = parts[3].lower().replace("danger", "").strip() if len(parts) >= 4 else "other"
            if category:
                ref_categories.setdefault(category, []).append(img)

        for category, imgs in ref_categories.items():
            if category.lower() in published_topics or category.lower() in ready_topics:
                continue
            all_contents.append({
                "topic": category.upper(), "topic_kr": FOOD_NAME_KR.get(category.lower(), category),
                "folder_name": f"000_cover/{category}",  # 커버 폴더명
                "status": "cover_ready", "slides": len(imgs),
                "cover": str(imgs[0]) if imgs else None,
                "thumb_b64": img_to_b64(str(imgs[0])) if imgs else "",
                "all_images": [str(img) for img in imgs],
                "folder": str(cover_ref_dir),
                "created": datetime.now(),
            })

    return all_contents


def load_pipeline_status() -> Dict[str, Any]:
    """파이프라인 상태 로드.

    status.json 파일에서 현재 파이프라인 실행 상태를 읽어옵니다.
    파일이 없거나 읽기 실패 시 기본 상태를 반환합니다.

    Returns:
        파이프라인 상태 딕셔너리 (topic, steps, progress 등)
    """
    status_file = ROOT / "services" / "dashboard" / "status.json"

    default = {
        "topic": None, "current_step": -1, "total_progress": 0,
        "steps": [s.copy() for s in SIMPLIFIED_STEPS],  # 복사본 사용
        "errors": [],
        "last_updated": None,
    }
    if status_file.exists():
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                raw_status = json.load(f)

            # 14단계 → 7단계 간소화 매핑
            raw_steps = raw_status.get("steps", [])
            if len(raw_steps) > 7:
                # 상세 단계 → 간소화 단계 매핑
                step_mapping = {
                    0: [0],           # 지시 → 지시
                    1: [1, 2, 4],     # 기획 ← 주제탐색, 주제검증, 기획/글
                    2: [3],           # 검증 ← 팩트체크
                    3: [6],           # 이미지 ← 이미지
                    4: [8],           # 합성 ← 합성
                    5: [11],          # 업로드 ← 업로드
                    6: [12, 13],      # 게시 ← 인스타, 웹
                }

                simplified = []
                for simp_id in range(len(SIMPLIFIED_STEPS)):
                    raw_ids = step_mapping.get(simp_id, [])
                    base = SIMPLIFIED_STEPS[simp_id].copy()
                    # 매핑된 단계 중 하나라도 done이면 done, running이면 running
                    statuses = [raw_steps[i].get("status", "pending") for i in raw_ids if i < len(raw_steps)]
                    if "running" in statuses:
                        base["status"] = "running"
                    elif all(s == "done" for s in statuses):
                        base["status"] = "done"
                    elif "error" in statuses:
                        base["status"] = "error"
                    simplified.append(base)

                raw_status["steps"] = simplified

            return raw_status
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load pipeline status: {e}")
    return default


def load_recent_activities() -> List[Dict[str, Any]]:
    """최근 활동 로드.

    작업 보고서와 콘텐츠 폴더 변경 내역을 수집하여
    시간순으로 정렬된 활동 목록을 반환합니다.

    Returns:
        활동 딕셔너리 리스트 (최대 10개)
    """
    activities: List[Dict[str, Any]] = []

    # 로그 파일에서 최근 활동 수집
    logs_dir = ROOT / "config" / "logs"
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("work_report_*.md"), reverse=True)[:5]
        for log_file in log_files:
            try:
                mtime = log_file.stat().st_mtime
                activities.append({
                    "type": "report",
                    "icon": "📝",
                    "title": "작업 보고서 생성",
                    "desc": log_file.name,
                    "time": datetime.fromtimestamp(mtime),
                })
            except OSError:
                continue

    # 콘텐츠 폴더에서 최근 활동
    content_dir = ROOT / "content" / "images"
    if content_dir.exists():
        folders = sorted(
            [f for f in content_dir.iterdir() if f.is_dir() and not f.name.startswith(".")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:5]

        for folder in folders:
            if folder.name in ["reference", "temp", "sunshine"]:
                continue
            try:
                mtime = folder.stat().st_mtime
                is_published = "_published" in folder.name
                activities.append({
                    "type": "content",
                    "icon": "✅" if is_published else "📦",
                    "title": f"{'게시 완료' if is_published else '제작 완료'}: {folder.name}",
                    "desc": f"{len(list(folder.glob('*.png')))}장 이미지",
                    "time": datetime.fromtimestamp(mtime),
                })
            except OSError:
                continue

    # 시간순 정렬
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:10]


def load_instagram_stats() -> Dict[str, Any]:
    """Instagram 성과 통계 로드.

    config/data/instagram_stats.json 파일에서 통계 데이터를 로드합니다.

    Returns:
        Instagram 통계 딕셔너리 (posts, daily_summary, last_updated)
    """
    stats_file = ROOT / "config" / "data" / "instagram_stats.json"

    if stats_file.exists():
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"posts": {}, "daily_summary": [], "last_updated": None}

    return {"posts": {}, "daily_summary": [], "last_updated": None}


# ============================================
# 메인 앱
# ============================================
def main() -> None:
    """대시보드 메인 엔트리포인트."""
    if "page" not in st.session_state:
        st.session_state.page = "🏠 대시보드"
    if "detail_topic" not in st.session_state:
        st.session_state.detail_topic = None
    if "gallery_images" not in st.session_state:
        st.session_state.gallery_images = None

    # 사이드바
    st.sidebar.markdown('<div class="sidebar-brand">🌞 Project Sunshine</div>', unsafe_allow_html=True)

    nav_options = ["🏠 대시보드", "📁 콘텐츠", "🖼️ 갤러리", "📅 캘린더", "🎬 제작", "📊 성과", "💰 API 비용", "⚙️ 설정"]
    current_idx = nav_options.index(st.session_state.page) if st.session_state.page in nav_options else 0

    page = st.sidebar.selectbox("", nav_options, index=current_idx, label_visibility="collapsed")

    if page != st.session_state.page:
        st.session_state.page = page
        st.session_state.detail_topic = None
        st.rerun()

    st.sidebar.markdown("---")

    if st.sidebar.button("🚀 새 콘텐츠 제작", use_container_width=True, type="primary"):
        st.session_state.page = "🎬 제작"
        st.session_state.detail_topic = None
        st.rerun()

    # 파이프라인 상태 미니뷰
    status = load_pipeline_status()
    if status.get("topic"):
        progress = status.get("total_progress", 0)
        st.sidebar.markdown(f"""
        <div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:0.8rem; margin-top:1rem;">
            <div style="font-size:0.65rem; color:#9a9ab0; text-transform:uppercase;">Running</div>
            <div style="font-size:0.85rem; font-weight:700; color:#e0e0ec;">{status['topic'].upper()}</div>
            <div class="progress-bar" style="margin-top:0.5rem;"><div class="progress-fill" style="width:{progress}%;"></div></div>
            <div style="font-size:0.65rem; color:#9a9ab0; margin-top:0.3rem;">{progress}% 완료</div>
        </div>
        """, unsafe_allow_html=True)

    st.sidebar.markdown(f"<div style='text-align:center; color:#3a3a4e; font-size:0.6rem; margin-top:2rem;'>v{VERSION} · {INSTAGRAM_HANDLE}</div>", unsafe_allow_html=True)

    # 페이지 라우팅
    if page == "🏠 대시보드":
        show_dashboard()
    elif page == "📁 콘텐츠":
        show_content_hub()
    elif page == "🖼️ 갤러리":
        show_gallery()
    elif page == "📅 캘린더":
        show_calendar()
    elif page == "🎬 제작":
        show_production()
    elif page == "📊 성과":
        show_analytics()
    elif page == "💰 API 비용":
        show_api_costs()
    elif page == "⚙️ 설정":
        show_settings()


# ============================================
# 갤러리 페이지 (신규 v5.1)
# ============================================
def show_gallery() -> None:
    """이미지 갤러리 페이지 렌더링."""
    try:
        from _modules.gallery_view import render_gallery_page
        render_gallery_page()
    except ImportError:
        st.header("🖼️ 이미지 갤러리")
        st.info("갤러리 모듈을 로드하는 중...")

        # 간단한 갤러리 (모듈 로드 실패 시 대체)
        sunshine_dir = ROOT / "content/images/sunshine"
        cta_dir = sunshine_dir / "cta_source/cropped"

        if cta_dir.exists():
            images = list(cta_dir.glob("*.jpg"))[:50]
            if images:
                st.subheader(f"CTA 소스 이미지 ({len(images)}개)")
                cols = st.columns(5)
                for i, img in enumerate(images):
                    with cols[i % 5]:
                        st.image(str(img), use_container_width=True)
                        st.caption(img.stem[:15])
            else:
                st.warning("CTA 이미지가 없습니다.")
        else:
            st.warning("CTA 폴더를 찾을 수 없습니다.")


# ============================================
# 캘린더 페이지 (신규 v5.1)
# ============================================
def show_calendar() -> None:
    """게시 스케줄 캘린더 페이지 렌더링."""
    try:
        from _modules.calendar_view import render_calendar_page
        render_calendar_page()
    except ImportError:
        st.header("📅 게시 스케줄")

        # 간단한 스케줄 뷰 (모듈 로드 실패 시 대체)
        schedule_file = ROOT / "config/settings/publish_schedule.json"

        if schedule_file.exists():
            with open(schedule_file, 'r', encoding='utf-8') as f:
                schedule = json.load(f)

            # 예정된 게시
            scheduled = schedule.get("scheduled", [])
            if scheduled:
                st.subheader("📋 예정된 게시")
                for item in sorted(scheduled, key=lambda x: x.get("scheduled_date", "")):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{item.get('topic_kr', item.get('topic', 'Unknown'))}**")
                    with col2:
                        st.write(item.get("scheduled_date", "-"))
                    with col3:
                        st.write(item.get("scheduled_time", "18:00"))
            else:
                st.info("예정된 게시가 없습니다.")

            # 완료된 게시
            completed = schedule.get("completed", [])
            if completed:
                st.subheader("✅ 완료된 게시")
                for item in completed[-5:]:
                    st.write(f"- {item.get('topic_kr', item.get('topic'))} ({item.get('scheduled_date', '')})")
        else:
            st.warning("스케줄 파일을 찾을 수 없습니다.")
            if st.button("스케줄 파일 생성"):
                schedule_file.parent.mkdir(parents=True, exist_ok=True)
                # P0 fix: atomic write - 임시 파일 후 rename으로 race condition 방지
                import tempfile
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=schedule_file.parent, suffix='.tmp'
                )
                try:
                    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                        json.dump({"scheduled": [], "completed": [], "failed": [], "settings": {}}, f)
                    os.replace(temp_path, schedule_file)  # atomic on POSIX
                except Exception:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
                st.success("스케줄 파일이 생성되었습니다.")
                st.rerun()


# ============================================
# 성과 분석 페이지 (신규)
# ============================================
def show_analytics() -> None:
    """Instagram 성과 분석 페이지 렌더링."""
    try:
        from _modules.analytics_charts import render_analytics_page
        render_analytics_page()
    except ImportError as e:
        st.header("📊 성과 분석")
        st.error(f"모듈 로드 실패: {e}")

        # 간단한 대체 뷰
        stats_file = ROOT / "config/data/instagram_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)

            summary = stats.get("summary", {})
            st.metric("총 좋아요", summary.get("total_likes", 0))
            st.metric("총 댓글", summary.get("total_comments", 0))
            st.metric("평균 좋아요", summary.get("avg_likes", 0))
        else:
            st.info("Instagram 통계 데이터가 없습니다.")


# ============================================
# 대시보드 (신규)
# ============================================
def show_dashboard() -> None:
    """대시보드 페이지 렌더링.

    프로젝트 현황 요약을 표시합니다:
    - 콘텐츠 통계 (게시됨/준비됨/커버만)
    - 파이프라인 실행 상태
    - 최근 콘텐츠 미리보기
    - 최근 활동 타임라인
    """
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">프로젝트 현황을 한눈에 확인하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 로딩 피드백 개선
    loading_placeholder = st.empty()
    with loading_placeholder:
        with st.spinner("📊 데이터 로딩 중..."):
            all_contents = load_content_data()
    loading_placeholder.empty()

    # 통계
    published = len([c for c in all_contents if c["status"] == "published"])
    ready = len([c for c in all_contents if c["status"] == "ready"])
    cover_ready = len([c for c in all_contents if c["status"] == "cover_ready"])
    total = len(all_contents)

    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-card total">
            <div class="stat-value" style="color:#a78bfa;">{total}</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat-card published">
            <div class="stat-value" style="color:#34d399;">{published}</div>
            <div class="stat-label">Published</div>
        </div>
        <div class="stat-card ready">
            <div class="stat-value" style="color:#22d3ee;">{ready}</div>
            <div class="stat-label">Ready</div>
        </div>
        <div class="stat-card cover">
            <div class="stat-value" style="color:#fbbf24;">{cover_ready}</div>
            <div class="stat-label">Cover Ready</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2열 레이아웃
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # 파이프라인 상태
        st.markdown('<div class="section-title">파이프라인 상태</div>', unsafe_allow_html=True)

        status = load_pipeline_status()
        steps = status.get("steps", [])
        topic = status.get("topic")
        progress = status.get("total_progress", 0)

        if topic:
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                <div>
                    <span style="font-size:0.7rem; color:#5a5a70;">TOPIC</span>
                    <div style="font-size:1rem; font-weight:700; color:#e0e0ec;">{topic.upper()}</div>
                </div>
                <div style="font-size:1.2rem; font-weight:800; color:{'#34d399' if progress == 100 else '#fbbf24'};">{progress}%</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="pipeline-container">', unsafe_allow_html=True)
            render_pipeline_row(steps)  # 7단계 한 줄
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("현재 실행 중인 파이프라인이 없습니다.")

        # 최근 콘텐츠
        st.markdown('<div class="section-title">최근 콘텐츠</div>', unsafe_allow_html=True)

        recent = sorted(all_contents, key=lambda x: x.get("created", datetime.min), reverse=True)[:6]
        if recent:
            cols = st.columns(6)
            for i, content in enumerate(recent):
                with cols[i]:
                    render_mini_card(content)
        else:
            st.info("콘텐츠가 없습니다.")

    with col_right:
        # 최근 활동
        st.markdown('<div class="section-title">최근 활동</div>', unsafe_allow_html=True)

        activities = load_recent_activities()

        if activities:
            st.markdown('<div class="timeline">', unsafe_allow_html=True)
            for activity in activities[:5]:
                time_str = activity["time"].strftime("%m/%d %H:%M")
                icon_class = "success" if activity["icon"] in ["✅", "📝"] else "info"
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-icon {icon_class}">{activity['icon']}</div>
                    <div class="timeline-content">
                        <div class="timeline-title">{activity['title']}</div>
                        <div class="timeline-desc">{activity['desc']}</div>
                        <div class="timeline-time">{time_str}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("최근 활동이 없습니다.")

        # 빠른 액션
        st.markdown('<div class="section-title">빠른 액션</div>', unsafe_allow_html=True)

        if st.button("🚀 새 콘텐츠 제작", use_container_width=True, type="primary", key="dash_create"):
            st.session_state.page = "🎬 제작"
            st.rerun()

        if st.button("📁 콘텐츠 관리", use_container_width=True, key="dash_content"):
            st.session_state.page = "📁 콘텐츠"
            st.rerun()

        # Instagram 성과 통계
        st.markdown('<div class="section-title">Instagram 성과</div>', unsafe_allow_html=True)

        insta_stats = load_instagram_stats()
        posts = insta_stats.get("posts", {})
        summary = insta_stats.get("summary", {})

        if posts:
            # summary가 있으면 사용, 없으면 계산 (새/구 형식 모두 지원)
            if summary:
                total_likes = summary.get("total_likes", 0)
                total_comments = summary.get("total_comments", 0)
                post_count = summary.get("total_posts", len(posts))
            else:
                total_likes = sum(p.get("likes", p.get("stats", {}).get("likes", 0)) for p in posts.values())
                total_comments = sum(p.get("comments", p.get("stats", {}).get("comments", 0)) for p in posts.values())
                post_count = len(posts)

            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border-radius:12px; padding:1rem; margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between; margin-bottom:0.8rem;">
                    <div style="text-align:center; flex:1;">
                        <div style="font-size:1.3rem; font-weight:700; color:#f472b6;">{post_count}</div>
                        <div style="font-size:0.6rem; color:#9a9ab0;">게시물</div>
                    </div>
                    <div style="text-align:center; flex:1;">
                        <div style="font-size:1.3rem; font-weight:700; color:#fb7185;">{total_likes:,}</div>
                        <div style="font-size:0.6rem; color:#9a9ab0;">좋아요</div>
                    </div>
                    <div style="text-align:center; flex:1;">
                        <div style="font-size:1.3rem; font-weight:700; color:#34d399;">{total_comments:,}</div>
                        <div style="font-size:0.6rem; color:#9a9ab0;">댓글</div>
                    </div>
                </div>
                <div style="font-size:0.55rem; color:#5a5a70; text-align:center;">
                    마지막 업데이트: {insta_stats.get('last_updated', '-')[:10] if insta_stats.get('last_updated') else '-'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Instagram 통계 데이터가 없습니다.")


def render_mini_card(content: Dict[str, Any]) -> None:
    """미니 카드 렌더링.

    Args:
        content: 콘텐츠 정보 딕셔너리
    """
    thumb = content.get("thumb_b64", "")
    # 음식명만 표시: 영어_한국어 (번호, _published 제외)
    topic = content.get("topic", "")
    topic_kr = content.get("topic_kr", "")
    display_name = f"{topic}_{topic_kr}" if topic_kr and topic_kr != topic else topic

    if thumb:
        img_html = f'<img src="data:image/jpeg;base64,{thumb}" style="width:100%; aspect-ratio:1; object-fit:cover; border-radius:8px; display:block;" />'
    else:
        img_html = '<div style="width:100%; aspect-ratio:1; background:#16161f; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#3a3a4e; font-size:0.6rem;">No Image</div>'

    st.markdown(f"""
    <div style="margin-bottom:0.3rem;">
        {img_html}
        <div style="font-size:0.6rem; font-weight:500; color:#c8c8d8; margin-top:0.3rem; text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="{display_name}">{display_name}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# 콘텐츠 허브
# ============================================
def show_content_hub() -> None:
    """콘텐츠 허브 페이지 렌더링."""
    with st.spinner("콘텐츠 로딩 중..."):
        all_contents = load_content_data()

    # 상세보기
    if st.session_state.detail_topic:
        content = next((c for c in all_contents if c["topic"].lower() == st.session_state.detail_topic.lower()), None)
        if content:
            render_detail_view(content)
            return

    # 갤러리 모달
    if st.session_state.gallery_images:
        render_gallery_modal()
        return

    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Content Hub</h1>
        <p class="page-subtitle">모든 콘텐츠를 관리하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 검색 & 필터
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search = st.text_input("🔍 검색", placeholder="주제명 검색...", label_visibility="collapsed")
    with col2:
        status_filter = st.selectbox("상태", ["전체", "PUBLISHED", "READY", "COVER READY"], label_visibility="collapsed")
    with col3:
        sort_by = st.selectbox("정렬", ["최신순", "이름순", "슬라이드 많은순"], label_visibility="collapsed")

    # 필터링
    filtered = all_contents.copy()

    if search:
        search_lower = search.lower()
        filtered = [c for c in filtered if search_lower in c["topic"].lower() or search_lower in c["topic_kr"]]

    if status_filter == "PUBLISHED":
        filtered = [c for c in filtered if c["status"] == "published"]
    elif status_filter == "READY":
        filtered = [c for c in filtered if c["status"] == "ready"]
    elif status_filter == "COVER READY":
        filtered = [c for c in filtered if c["status"] == "cover_ready"]

    # 정렬
    if sort_by == "이름순":
        filtered = sorted(filtered, key=lambda x: x["topic"])
    elif sort_by == "슬라이드 많은순":
        filtered = sorted(filtered, key=lambda x: x["slides"], reverse=True)
    else:
        filtered = sorted(filtered, key=lambda x: x.get("created", datetime.min), reverse=True)

    # 통계
    st.markdown(f'<div class="section-title">콘텐츠 ({len(filtered)})</div>', unsafe_allow_html=True)

    # 그리드
    if filtered:
        cols = st.columns(6)
        for i, content in enumerate(filtered):
            with cols[i % 6]:
                render_content_card(content)
    else:
        # 빈 상태 UI 개선
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02); border:1px dashed rgba(255,255,255,0.1);
             border-radius:16px; padding:3rem; text-align:center; margin-top:2rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">🔍</div>
            <div style="font-size:1.1rem; font-weight:600; color:#c8c8d8; margin-bottom:0.5rem;">
                검색 결과가 없습니다
            </div>
            <div style="font-size:0.85rem; color:#6a6a80;">
                다른 검색어를 시도하거나 필터를 변경해보세요
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_content_card(content: Dict[str, Any]) -> None:
    """콘텐츠 카드 렌더링.

    Args:
        content: 콘텐츠 정보 딕셔너리
    """
    status = content["status"]
    badge_class = "badge-published" if status == "published" else ("badge-ready" if status == "ready" else "badge-cover")
    badge_text = "PUBLISHED" if status == "published" else ("READY" if status == "ready" else "COVER")

    thumb = content.get("thumb_b64", "")
    if thumb:
        img_html = f'<img src="data:image/jpeg;base64,{thumb}" class="card-img" />'
    else:
        img_html = '<div style="width:100%; aspect-ratio:1; background:#16161f; display:flex; align-items:center; justify-content:center; color:#3a3a4e; font-size:0.7rem;">No Image</div>'

    st.markdown(f"""
    <div class="content-card">
        {img_html}
        <div class="card-body">
            <div class="card-title">{content['topic'].upper()}</div>
            <div class="card-meta">
                <span class="card-count">{content['slides']}장</span>
                <span class="badge {badge_class}">{badge_text}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️", key=f"v_{content['topic']}", use_container_width=True):
            st.session_state.detail_topic = content["topic"]
            st.rerun()
    with col2:
        if st.button("🖼️", key=f"g_{content['topic']}", use_container_width=True):
            st.session_state.gallery_images = content.get("all_images", [])
            st.session_state.gallery_topic = content["topic"]
            st.rerun()


def render_detail_view(content: Dict[str, Any]) -> None:
    """콘텐츠 상세보기 렌더링.

    Args:
        content: 콘텐츠 정보 딕셔너리
    """
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("← 뒤로", use_container_width=True):
            st.session_state.detail_topic = None
            st.rerun()

    with col1:
        status_colors = {"published": "#34d399", "ready": "#22d3ee", "cover_ready": "#fbbf24"}
        status_texts = {"published": "PUBLISHED", "ready": "READY", "cover_ready": "COVER READY"}
        color = status_colors.get(content["status"], "#888")
        text = status_texts.get(content["status"], "UNKNOWN")

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.5rem;">
            <h1 style="margin:0; font-size:2rem; font-weight:800;">{content['topic'].upper()}</h1>
            <span style="color:{color}; font-size:0.75rem; font-weight:700; padding:0.3rem 0.8rem; background:rgba(255,255,255,0.05); border-radius:6px;">{text}</span>
        </div>
        <p style="color:#6a6a80; margin:0 0 1.5rem 0;">{content['topic_kr']} · {content['slides']}장</p>
        """, unsafe_allow_html=True)

    # 이미지 갤러리
    col_main, col_side = st.columns([2, 1])

    with col_main:
        if content["cover"] and Path(content["cover"]).exists():
            st.image(content["cover"], use_container_width=True)

    with col_side:
        st.markdown("**미리보기**")
        images = content.get("all_images", [])
        if images:
            thumb_cols = st.columns(2)
            for i, img in enumerate(images[:6]):
                with thumb_cols[i % 2]:
                    if Path(img).exists():
                        st.image(get_thumbnail(img), use_container_width=True)

        if len(images) > 6:
            if st.button(f"🖼️ 전체 보기 ({len(images)}장)", use_container_width=True):
                st.session_state.gallery_images = images
                st.session_state.gallery_topic = content["topic"]
                st.rerun()

    st.markdown("---")

    # 정보 & 액션
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 정보")
        st.markdown(f"""
        - **폴더:** `{Path(content['folder']).name}`
        - **이미지 수:** {content['slides']}장
        - **상태:** {text}
        """)

    with col2:
        st.markdown("### 액션")

        if content["status"] == "cover_ready":
            if st.button("🚀 제작 시작", type="primary", use_container_width=True):
                st.session_state.selected_topic = content["topic"].lower()
                st.session_state.page = "🎬 제작"
                st.session_state.detail_topic = None
                st.rerun()

        elif content["status"] == "ready":
            if st.button("📤 게시하기", type="primary", use_container_width=True):
                st.code(f"python cli.py {content['topic'].lower()}", language="bash")

        if st.button("📁 폴더 경로 복사", use_container_width=True):
            st.code(content["folder"])


def render_gallery_modal() -> None:
    """갤러리 모달 렌더링."""
    images = st.session_state.gallery_images
    topic = st.session_state.get("gallery_topic", "Gallery")

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"## 🖼️ {topic.upper()} 갤러리 ({len(images)}장)")
    with col2:
        if st.button("✕ 닫기", use_container_width=True):
            st.session_state.gallery_images = None
            st.session_state.gallery_topic = None
            st.rerun()

    st.markdown("---")

    # 그리드로 이미지 표시
    with st.spinner("이미지 로딩 중..."):
        cols = st.columns(4)
        for i, img_path in enumerate(images):
            with cols[i % 4]:
                if Path(img_path).exists():
                    st.image(img_path, use_container_width=True)
                    st.caption(f"슬라이드 {i+1}")


# ============================================
# 제작 페이지 헬퍼 함수
# ============================================
def load_available_covers(cover_dir: Path) -> List[Dict[str, Any]]:
    """기제작 표지 목록 로드.

    Args:
        cover_dir: 표지 이미지 디렉토리 경로

    Returns:
        표지 정보 딕셔너리 리스트
    """
    covers: List[Dict[str, Any]] = []

    if not cover_dir.exists():
        return covers

    # 이미 게시된 주제 확인
    content_dir = ROOT / "content" / "images"
    published_topics = set()
    if content_dir.exists():
        for folder in content_dir.iterdir():
            if folder.is_dir() and "_published" in folder.name:
                parts = folder.name.replace("_published", "").split("_", 1)
                topic = parts[1] if len(parts) > 1 else parts[0]
                published_topics.add(topic.lower())

    # 표지 이미지 수집
    cover_images = sorted(cover_dir.glob("*.png")) + sorted(cover_dir.glob("*.jpg"))

    # 주제별 그룹화 (가장 최신 파일만)
    topic_covers: Dict[str, Path] = {}
    for img in cover_images:
        # 파일명에서 주제 추출: cover_ref_XX_topic.png
        parts = img.stem.split("_")
        if len(parts) >= 4:
            topic = parts[3].lower().replace("danger", "").strip()
            if topic and topic not in published_topics:
                # 같은 주제면 가장 최신 파일 사용
                if topic not in topic_covers:
                    topic_covers[topic] = img

    # 딕셔너리로 변환
    for topic, img_path in sorted(topic_covers.items()):
        covers.append({
            "topic": topic,
            "topic_kr": FOOD_NAME_KR.get(topic.lower(), topic),
            "cover_path": str(img_path),
            "thumb_b64": img_to_b64(str(img_path)),
        })

    return covers


def _render_cover_card(cover: Dict[str, Any], large: bool = False) -> None:
    """표지 카드 렌더링.

    Args:
        cover: 표지 정보 딕셔너리
        large: True면 큰 카드 (3열), False면 작은 카드 (5열)
    """
    thumb = cover.get("thumb_b64", "")
    topic = cover["topic"]
    topic_kr = cover["topic_kr"]

    # 큰 카드: 더 선명한 이미지와 큰 텍스트
    if large:
        if thumb:
            img_html = f'<img src="data:image/jpeg;base64,{thumb}" style="width:100%; aspect-ratio:1; object-fit:cover; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.3);" />'
        else:
            img_html = '<div style="width:100%; aspect-ratio:1; background:#16161f; border-radius:12px; display:flex; align-items:center; justify-content:center; color:#3a3a4e; font-size:1rem;">No Image</div>'

        st.markdown(f"""
        <div style="margin-bottom:0.8rem; transition:transform 0.2s;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
            {img_html}
            <div style="margin-top:0.6rem; text-align:center;">
                <div style="font-size:1rem; font-weight:700; color:#e0e0ec;">{topic.upper()}</div>
                <div style="font-size:0.85rem; color:#fbbf24; font-weight:500;">{topic_kr}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if thumb:
            img_html = f'<img src="data:image/jpeg;base64,{thumb}" style="width:100%; aspect-ratio:1; object-fit:cover; border-radius:8px;" />'
        else:
            img_html = '<div style="width:100%; aspect-ratio:1; background:#16161f; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#3a3a4e;">No Image</div>'

        st.markdown(f"""
        <div style="margin-bottom:0.5rem;">
            {img_html}
            <div style="font-size:0.75rem; font-weight:600; color:#c8c8d8; margin-top:0.4rem; text-align:center;">{topic.upper()}</div>
            <div style="font-size:0.7rem; color:#fbbf24; text-align:center;">{topic_kr}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🚀 선택", key=f"sel_{topic}", use_container_width=True):
        st.session_state.selected_topic = topic
        st.session_state.selected_cover = cover["cover_path"]
        st.rerun()


def _start_pipeline(topic: str) -> None:
    """파이프라인 실행.

    백그라운드에서 파이프라인 프로세스를 시작하고
    실시간 로그 모니터링을 활성화합니다.

    Args:
        topic: 주제명 (영문)

    Raises:
        표시만 되고 예외는 발생하지 않음 (에러는 UI에 표시)
    """
    # P0 fix: topic 입력 검증 (명령어 인젝션 방지)
    if not re.match(VALID_TOPIC_PATTERN, topic):
        st.error(f"❌ 유효하지 않은 주제명: {topic}")
        st.warning("주제명은 소문자, 숫자, 언더스코어만 사용 가능합니다 (최대 30자)")
        return

    st.session_state.pipeline_running = True
    st.session_state.pipeline_topic = topic
    st.session_state.pipeline_start_time = datetime.now().isoformat()

    # 오래된 로그 정리
    cleanup_old_logs()

    # 명령어 구성
    cmd_parts = ["python", str(ROOT / "cli.py"), topic, "--v5"]

    # 로그 파일 경로
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = ROOT / "config" / "logs" / f"pipeline_{topic}_{timestamp}.log"
    log_file.parent.mkdir(exist_ok=True)

    # 로딩 피드백 개선
    with st.spinner(f"🚀 {topic.upper()} 파이프라인 초기화 중..."):
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                # 초기 로그 헤더 작성
                f.write(f"=== Pipeline Start: {topic} ===\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(f"Command: {' '.join(cmd_parts)}\n")
                f.write("=" * 40 + "\n\n")

                process = subprocess.Popen(
                    cmd_parts,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(ROOT),
                    text=True,
                    bufsize=1  # 라인 버퍼링으로 실시간 로그
                )

            st.session_state.pipeline_pid = process.pid
            st.session_state.pipeline_log = str(log_file)

            st.success(f"✅ 파이프라인 시작됨 (PID: {process.pid})")
            st.info("💡 아래 '자동 로그 새로고침'을 켜면 실시간으로 진행 상황을 확인할 수 있습니다.")
            time.sleep(0.5)  # 상태 저장 대기
            st.rerun()

        except FileNotFoundError:
            st.error("❌ Python 또는 CLI 파일을 찾을 수 없습니다.")
            st.session_state.pipeline_running = False
        except PermissionError:
            st.error("❌ 로그 파일 작성 권한이 없습니다.")
            st.session_state.pipeline_running = False
        except subprocess.SubprocessError as e:
            st.error(f"❌ 프로세스 시작 실패: {e}")
            st.session_state.pipeline_running = False


# ============================================
# 제작 페이지
# ============================================
def show_production() -> None:
    """제작 페이지 렌더링."""
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Production</h1>
        <p class="page-subtitle">파이프라인 실행 및 콘텐츠 제작</p>
    </div>
    """, unsafe_allow_html=True)

    # 파이프라인 상태
    status = load_pipeline_status()
    steps = status.get("steps", [])
    topic = status.get("topic", "대기 중")
    progress = status.get("total_progress", 0)
    errors = status.get("errors", [])

    topic_display = topic.upper() if topic else "대기 중"

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <div>
            <span style="font-size:0.7rem; color:#5a5a70; text-transform:uppercase; letter-spacing:0.1em;">Current Topic</span>
            <div style="font-size:1.2rem; font-weight:700; color:#e0e0ec;">{topic_display}</div>
        </div>
        <div style="text-align:right;">
            <span style="font-size:0.7rem; color:#5a5a70; text-transform:uppercase; letter-spacing:0.1em;">Progress</span>
            <div style="font-size:1.2rem; font-weight:800; color:{'#34d399' if progress == 100 else '#fbbf24'};">{progress}%</div>
        </div>
    </div>
    <div class="progress-bar"><div class="progress-fill" style="width:{progress}%;"></div></div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 파이프라인 시각화 (한 줄)
    st.markdown('<div class="pipeline-container">', unsafe_allow_html=True)
    render_pipeline_row(steps)  # 7단계 한 줄
    st.markdown('</div>', unsafe_allow_html=True)

    # 상태 범례 및 완료 표시
    if progress == 100:
        st.success("✅ 파이프라인이 성공적으로 완료되었습니다!")
    st.caption("🟢 완료 · 🟡 진행중 · 🔴 에러 · ⚫ 대기")

    # 에러 표시
    if errors:
        st.markdown('<div class="section-title">에러 로그</div>', unsafe_allow_html=True)
        for err in errors[-3:]:
            st.error(err)

    # 자동 새로고침
    col1, col2 = st.columns([1, 3])
    with col1:
        auto_refresh = st.checkbox("🔄 자동 새로고침", value=False)

    if auto_refresh:
        time.sleep(AUTO_REFRESH_INTERVAL)
        st.rerun()

    st.markdown("---")

    # 탭으로 구분 (표지 선택이 메인 워크플로우)
    tab1, tab2 = st.tabs(["📸 표지 선택 → 제작", "➕ 새 표지 추가"])

    with tab1:
        # 기제작 표지에서 선택
        st.markdown("### 📸 기제작 표지 선택")
        st.caption("PD님이 제작한 표지 중 하나를 선택하여 콘텐츠 제작을 시작하세요.")

        # 기제작 표지 로드
        cover_ref_dir = ROOT / "content" / "images" / "000_cover"
        available_covers = load_available_covers(cover_ref_dir)

        # 선택된 주제 확인
        selected_topic = st.session_state.get("selected_topic", "")
        selected_cover = st.session_state.get("selected_cover", "")

        if selected_topic and selected_cover:
            # 선택된 표지 표시 (영어 + 한국어)
            topic_kr = FOOD_NAME_KR.get(selected_topic.lower(), selected_topic)
            st.success(f"✅ 선택된 주제: **{selected_topic.upper()}** ({topic_kr})")

            col_img, col_action = st.columns([1, 2])
            with col_img:
                if Path(selected_cover).exists():
                    st.image(selected_cover, width=250)  # 더 크게

            with col_action:
                st.markdown(f"""
                ### 🎬 {selected_topic.upper()}
                **{topic_kr}** 콘텐츠를 제작합니다.
                """)

                if st.button("🚀 제작 시작", type="primary", use_container_width=True):
                    # 파이프라인 실행
                    _start_pipeline(selected_topic)

                if st.button("❌ 다른 표지 선택", use_container_width=True):
                    del st.session_state.selected_topic
                    del st.session_state.selected_cover
                    st.rerun()
        else:
            # 표지 그리드 표시
            if available_covers:
                # 검색 필터
                search_query = st.text_input(
                    "🔍 검색",
                    placeholder="주제명으로 검색 (예: strawberry, 딸기)",
                    key="cover_search"
                )

                # 필터링
                filtered_covers = available_covers
                if search_query:
                    query_lower = search_query.lower()
                    filtered_covers = [
                        c for c in available_covers
                        if query_lower in c["topic"].lower() or query_lower in c["topic_kr"]
                    ]

                st.markdown(f'<div class="section-title">📸 사용 가능한 표지 ({len(filtered_covers)}개)</div>', unsafe_allow_html=True)

                # 콘텐츠 허브와 동일한 6열 그리드
                cols = st.columns(6)
                for i, cover in enumerate(filtered_covers):
                    with cols[i % 6]:
                        _render_cover_card(cover, large=False)
            else:
                st.markdown("""
                <div style="background:rgba(245,158,11,0.08); border:1px dashed rgba(245,158,11,0.3);
                     border-radius:16px; padding:2.5rem; text-align:center; margin-top:1rem;">
                    <div style="font-size:2.5rem; margin-bottom:0.8rem;">📭</div>
                    <div style="font-size:1rem; font-weight:600; color:#fbbf24; margin-bottom:0.5rem;">
                        기제작 표지가 없습니다
                    </div>
                    <div style="font-size:0.85rem; color:#9a9ab0;">
                        '➕ 새 표지 추가' 탭에서 PD님 표지를 업로드하세요
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 실행 중인 파이프라인 로그 표시
        if st.session_state.get("pipeline_running") and st.session_state.get("pipeline_log"):
            st.markdown("---")
            st.markdown("### 📜 실시간 로그")

            log_path = Path(st.session_state.pipeline_log)
            if log_path.exists():
                try:
                    log_content = log_path.read_text()[-LOG_TAIL_CHARS:]
                    lines = log_content.split("\n")[-LOG_TAIL_LINES:]

                    # 로그 스타일링
                    log_html = ['<div class="log-container">']
                    for line in lines:
                        if not line.strip():
                            continue
                        line_class = "log-line"
                        if "error" in line.lower() or "❌" in line:
                            line_class += " error"
                        elif "success" in line.lower() or "✅" in line or "완료" in line:
                            line_class += " success"
                        elif "warning" in line.lower() or "⚠️" in line:
                            line_class += " warning"
                        elif "info" in line.lower() or "📊" in line or "🎬" in line:
                            line_class += " info"
                        log_html.append(f'<div class="{line_class}">{line}</div>')
                    log_html.append('</div>')

                    st.markdown(''.join(log_html), unsafe_allow_html=True)
                except (IOError, UnicodeDecodeError) as e:
                    st.warning(f"로그를 읽을 수 없습니다: {e}")

            # 중지 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🛑 파이프라인 중지", use_container_width=True):
                    pid = st.session_state.get("pipeline_pid")
                    if pid:
                        try:
                            # P0 fix: PID 검증 - 프로세스 존재 및 소유권 확인
                            # os.kill(pid, 0)은 프로세스 존재 여부만 확인 (신호 전송 안함)
                            os.kill(pid, 0)
                            # SIGTERM으로 정상 종료 요청
                            os.kill(pid, signal.SIGTERM)
                            st.warning("파이프라인이 중지되었습니다.")
                        except ProcessLookupError:
                            st.info("프로세스가 이미 종료되었습니다.")
                        except PermissionError:
                            # P0 fix: 권한 없음 = 다른 사용자의 프로세스
                            st.error("프로세스 종료 권한이 없습니다. (다른 사용자의 프로세스일 수 있음)")
                            logger.warning(f"PID {pid} 종료 시도 실패: 권한 없음")
                    st.session_state.pipeline_running = False
                    st.rerun()
            with col2:
                if st.button("🔄 로그 새로고침", use_container_width=True):
                    st.rerun()

            # 자동 새로고침
            auto_log_refresh = st.checkbox(
                f"자동 로그 새로고침 ({LOG_REFRESH_INTERVAL}초)",
                value=True,
                key="auto_log"
            )
            if auto_log_refresh:
                time.sleep(LOG_REFRESH_INTERVAL)
                st.rerun()

    with tab2:
        st.markdown("### ➕ 새 표지 추가")
        st.caption("PD님이 제작한 새 표지 이미지를 업로드하세요.")

        upload_topic = st.text_input(
            "주제명 (영문)",
            placeholder="예: strawberry",
            key="upload_topic"
        )

        uploaded_file = st.file_uploader(
            "표지 이미지 드래그 & 드롭",
            type=["png", "jpg", "jpeg"],
            help="1080x1080 권장"
        )

        if uploaded_file and upload_topic:
            st.image(uploaded_file, width=300, caption="업로드된 이미지")

            if st.button("💾 표지 저장", type="primary", key="save_cover"):
                cover_ref_dir = ROOT / "content" / "images" / "000_cover"
                cover_ref_dir.mkdir(parents=True, exist_ok=True)

                # 파일명 생성 (기존 파일 수 + 1)
                existing = list(cover_ref_dir.glob(f"*_{upload_topic}*.png"))
                next_num = len(existing) + 1
                cover_filename = f"cover_ref_{next_num:02d}_{upload_topic}.png"
                cover_path = cover_ref_dir / cover_filename

                try:
                    with st.spinner("이미지 처리 중..."):
                        img = Image.open(uploaded_file)
                        img = resize_with_padding(img, TARGET_IMAGE_SIZE)
                        img.save(cover_path, "PNG")

                    st.success(f"✅ 저장 완료!")
                    st.info(f"📁 {cover_filename}")
                    st.balloons()
                    st.cache_data.clear()
                except (IOError, OSError) as e:
                    st.error(f"저장 실패: {e}")
        elif uploaded_file and not upload_topic:
            st.warning("주제명을 입력해주세요.")


def render_pipeline_row(steps: List[Dict[str, Any]]) -> None:
    """파이프라인 단계를 가로 행으로 렌더링 (한 줄).

    Args:
        steps: 파이프라인 단계 딕셔너리 리스트 (최대 7개)
    """
    html_parts = ['<div class="pipeline-row" style="justify-content:space-between; padding:0 1rem;">']

    for i, step in enumerate(steps):
        status = step.get("status", "pending")
        emoji = step.get("emoji", "❓")
        role = step.get("role", "?")

        icon_class = f"pipe-icon {status}"

        html_parts.append(f'''
        <div class="pipe-step" style="min-width:70px;">
            <div class="{icon_class}">{emoji}</div>
            <div class="pipe-label">{role}</div>
        </div>
        ''')

        if i < len(steps) - 1:
            arrow_class = "pipe-arrow done" if status == "done" else "pipe-arrow"
            html_parts.append(f'<div class="{arrow_class}">→</div>')

    html_parts.append('</div>')
    st.markdown(''.join(html_parts), unsafe_allow_html=True)


# ============================================
# API 비용 페이지
# ============================================
def show_api_costs() -> None:
    """API 비용 페이지 렌더링.

    fal.ai 스타일의 Usage & Billing 대시보드.
    크레딧 잔액, 총 사용량, 모델별 breakdown 표시.
    """
    import pandas as pd
    from datetime import datetime, timedelta

    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Usage & Billing</h1>
        <p class="page-subtitle">Track your usage, credit balance, and costs</p>
    </div>
    """, unsafe_allow_html=True)

    # api_usage.json에서 직접 데이터 로드
    usage_file = ROOT / "config" / "data" / "api_usage.json"
    usage_data = {}
    if usage_file.exists():
        try:
            with open(usage_file, 'r', encoding='utf-8') as f:
                usage_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load api_usage.json: {e}")

    total_cost = usage_data.get("total_cost", 0)
    credit_balance = usage_data.get("credit_balance", 0)
    model_breakdown = usage_data.get("model_breakdown", {})
    daily_data = usage_data.get("daily_summary", {})

    # 상단 카드: 잔액 & 총 사용량 (fal.ai 스타일)
    st.markdown("""
    <style>
    .billing-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .billing-label {
        font-size: 0.75rem;
        color: #9a9ab0;
        margin-bottom: 0.3rem;
    }
    .billing-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
    }
    .billing-value.balance { color: #10b981; }
    .billing-value.spent { color: #f472b6; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="billing-card">
            <div class="billing-label">Current credit balance</div>
            <div class="billing-value balance">${credit_balance:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="billing-card">
            <div class="billing-label">Total cost (This month)</div>
            <div class="billing-value spent">${total_cost:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    # 트래커 미설정 안내
    if not usage_data:
        st.info("""
        📊 **API 사용량 데이터가 없습니다.**

        `config/data/api_usage.json` 파일을 확인하세요.
        파이프라인 실행 시 자동으로 기록됩니다.
        """)

    # 기간 선택 탭
    period_tab = st.tabs(["📅 30일", "📆 이번달", "📊 전체"])

    # 날짜 계산
    today = datetime.now().strftime("%Y-%m-%d")
    days_30_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    month_start = datetime.now().strftime("%Y-%m-01")

    def calc_period_cost(start_date: str, end_date: str = None) -> tuple:
        """기간별 비용 계산"""
        period_cost = 0.0
        period_count = 0
        period_days = []
        for date_str, day_data in sorted(daily_data.items()):
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            day_cost = sum(v.get("cost", 0) for v in day_data.values())
            day_count = sum(v.get("count", 0) for v in day_data.values())
            period_cost += day_cost
            period_count += day_count
            period_days.append({"날짜": date_str[-5:], "비용($)": day_cost, "횟수": day_count})
        return period_cost, period_count, period_days

    # 30일 탭
    with period_tab[0]:
        cost_30, count_30, days_30 = calc_period_cost(days_30_ago)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("30일 비용", f"${cost_30:,.2f}")
        with col2:
            st.metric("API 호출", f"{count_30:,}회")
        with col3:
            avg_daily = cost_30 / 30 if cost_30 > 0 else 0
            st.metric("일 평균", f"${avg_daily:.2f}")

        if days_30:
            st.markdown("#### 📈 일별 추이 (최근 30일)")
            df_30 = pd.DataFrame(days_30)
            st.bar_chart(df_30.set_index("날짜")["비용($)"])
            st.dataframe(df_30, use_container_width=True, hide_index=True)
        else:
            st.info("최근 30일간 사용 기록이 없습니다.")

    # 1달 탭
    with period_tab[1]:
        month_cost_calc, month_count, month_days = calc_period_cost(month_start)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("이번 달 비용", f"${month_cost_calc:,.2f}")
        with col2:
            st.metric("API 호출", f"{month_count:,}회")
        with col3:
            st.metric("원화 환산", f"₩{month_cost_calc * 1450:,.0f}")

        if month_days:
            st.markdown("#### 📈 일별 추이")
            df_month = pd.DataFrame(month_days)
            st.bar_chart(df_month.set_index("날짜")["비용($)"])
            st.dataframe(df_month, use_container_width=True, hide_index=True)
        else:
            st.info("이번 달 사용 기록이 없습니다.")

    # 전체 탭
    with period_tab[2]:
        all_cost, all_count, all_days = calc_period_cost(None)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 비용", f"${total_cost:,.2f}")
        with col2:
            st.metric("총 API 호출", f"{all_count:,}회")
        with col3:
            st.metric("원화 환산", f"₩{total_cost * 1450:,.0f}")

        st.markdown("---")

        # 모델별 사용량 (fal.ai 스타일)
        st.markdown("### Usage per model")
        st.caption("Top models ranked by total spend")

        table_data = []
        for model_id, data in model_breakdown.items():
            table_data.append({
                "Model endpoint": model_id,
                "Quantity": f"{data.get('quantity', 0):,.2f}",
                "Unit": data.get("unit", "-"),
                "Unit Price": f"${data.get('unit_price', 0):.3f}",
                "Usage Cost": f"${data.get('cost', 0):,.2f}"
            })

        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("📋 사용 기록이 없습니다.")

        # 전체 일별 데이터
        if all_days:
            st.markdown("### 📊 전체 일별 기록")
            df_all = pd.DataFrame(all_days)
            st.bar_chart(df_all.set_index("날짜")["비용($)"])
            with st.expander("상세 데이터 보기"):
                st.dataframe(df_all, use_container_width=True, hide_index=True)


# ============================================
# 설정 페이지
# ============================================
def show_settings() -> None:
    """설정 페이지 렌더링."""
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">프로젝트 설정을 관리하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # API 연결 상태
    st.markdown('<div class="section-title">API Connections</div>', unsafe_allow_html=True)

    apis = [
        ("FAL_KEY", "fal.ai", "이미지 생성"),
        ("CLOUDINARY_CLOUD_NAME", "Cloudinary", "이미지 호스팅"),
        ("INSTAGRAM_ACCESS_TOKEN", "Instagram", "게시"),
        ("ANTHROPIC_API_KEY", "Anthropic", "AI 텍스트"),
    ]

    for key, name, desc in apis:
        value = os.environ.get(key, "")
        cols = st.columns([0.5, 2, 2, 1])
        with cols[0]:
            st.markdown("🟢" if value else "🔴")
        with cols[1]:
            st.markdown(f"**{name}**")
        with cols[2]:
            st.caption(desc)
        with cols[3]:
            st.markdown("Connected" if value else "—")

    st.markdown("---")

    # 캐시 관리
    st.markdown('<div class="section-title">캐시 관리</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        thumb_count = len(list(THUMB_DIR.glob("*.jpg")))
        st.metric("썸네일 캐시", f"{thumb_count}개")
    with col2:
        logs_dir = ROOT / "config" / "logs"
        log_count = len(list(logs_dir.glob("pipeline_*.log"))) if logs_dir.exists() else 0
        st.metric("로그 파일", f"{log_count}개")
    with col3:
        if st.button("🗑️ 캐시 정리", use_container_width=True):
            # 썸네일 삭제
            for f in THUMB_DIR.glob("*.jpg"):
                f.unlink()
            # 오래된 로그 정리
            cleanup_old_logs(max_files=10, max_days=7)
            st.success("캐시 및 로그가 정리되었습니다.")
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    # 프로젝트 정보
    st.markdown('<div class="section-title">Project Info</div>', unsafe_allow_html=True)

    info = [
        ("Project", "Project Sunshine"),
        ("Instagram", INSTAGRAM_HANDLE),
        ("Pipeline", f"v{VERSION} — 14 Steps"),
        ("Image Gen", "fal.ai FLUX 2 Pro"),
        ("Dashboard", f"v{VERSION}"),
    ]

    for label, value in info:
        cols = st.columns([1, 3])
        with cols[0]:
            st.caption(label)
        with cols[1]:
            st.markdown(f"**{value}**")


if __name__ == "__main__":
    main()
