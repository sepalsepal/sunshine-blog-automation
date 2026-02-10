"""
이미지 갤러리 뷰 모듈 v1.0

기능:
- CTA/표지 이미지 썸네일 그리드
- 이미지 필터링 (표정, 등급별)
- 이미지 상세 뷰
- 선택 및 일괄 작업
"""

import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import os

# 경로 설정
ROOT = Path(__file__).parent.parent.parent.parent
SUNSHINE_DIR = ROOT / "content/images/sunshine"
CTA_CROPPED_DIR = SUNSHINE_DIR / "cta_source/cropped"
BEST_CTA_DIR = SUNSHINE_DIR / "cta_source/best_cta"
GRADE_A_DIR = SUNSHINE_DIR / "01_usable/grade_A/expression"
GRADE_B_DIR = SUNSHINE_DIR / "01_usable/grade_B"
THUMB_DIR = Path(__file__).parent.parent / ".thumbs"


def get_thumbnail_path(image_path: Path, size: Tuple[int, int] = (200, 200)) -> Path:
    """썸네일 경로 생성"""
    THUMB_DIR.mkdir(exist_ok=True)
    thumb_name = f"{image_path.stem}_{size[0]}x{size[1]}.jpg"
    return THUMB_DIR / thumb_name


def create_thumbnail(image_path: Path, size: Tuple[int, int] = (200, 200)) -> Optional[Path]:
    """썸네일 생성"""
    thumb_path = get_thumbnail_path(image_path, size)

    if thumb_path.exists():
        return thumb_path

    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.LANCZOS)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(thumb_path, 'JPEG', quality=80)
        return thumb_path
    except Exception as e:
        st.warning(f"썸네일 생성 실패: {image_path.name} - {e}")
        return None


def get_images_by_category(category: str) -> List[Path]:
    """카테고리별 이미지 목록 조회"""
    images = []

    if category == "best_cta":
        if BEST_CTA_DIR.exists():
            images = list(BEST_CTA_DIR.glob("*.jpg"))
    elif category == "cta":
        if CTA_CROPPED_DIR.exists():
            images = list(CTA_CROPPED_DIR.glob("*.jpg"))
    elif category == "grade_a_happy":
        dir_path = GRADE_A_DIR / "happy"
        if dir_path.exists():
            images = list(dir_path.glob("*.jpg"))
    elif category == "grade_a_curious":
        dir_path = GRADE_A_DIR / "curious"
        if dir_path.exists():
            images = list(dir_path.glob("*.jpg"))
    elif category == "grade_a_calm":
        dir_path = GRADE_A_DIR / "calm"
        if dir_path.exists():
            images = list(dir_path.glob("*.jpg"))
    elif category == "grade_b":
        if GRADE_B_DIR.exists():
            for subdir in GRADE_B_DIR.iterdir():
                if subdir.is_dir():
                    images.extend(list(subdir.glob("*.jpg")))

    return sorted(images, key=lambda x: x.name)


def render_gallery_grid(
    images: List[Path],
    cols: int = 5,
    show_names: bool = True,
    selectable: bool = False,
    page: int = 0,
    per_page: int = 50
) -> List[Path]:
    """갤러리 그리드 렌더링

    Args:
        images: 이미지 경로 목록
        cols: 열 개수
        show_names: 파일명 표시 여부
        selectable: 선택 가능 여부
        page: 현재 페이지
        per_page: 페이지당 이미지 수

    Returns:
        선택된 이미지 목록 (selectable=True일 때)
    """
    selected = []

    # 페이지네이션
    total_pages = (len(images) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(images))
    page_images = images[start_idx:end_idx]

    # 이미지 수 표시
    st.caption(f"총 {len(images)}개 이미지 (페이지 {page + 1}/{total_pages})")

    # 그리드 렌더링
    rows = (len(page_images) + cols - 1) // cols

    for row in range(rows):
        columns = st.columns(cols)
        for col in range(cols):
            idx = row * cols + col
            if idx < len(page_images):
                img_path = page_images[idx]

                with columns[col]:
                    # 썸네일 생성 및 표시
                    thumb_path = create_thumbnail(img_path)
                    if thumb_path and thumb_path.exists():
                        st.image(str(thumb_path), use_container_width=True)
                    else:
                        st.image(str(img_path), use_container_width=True)

                    if show_names:
                        st.caption(img_path.stem[:20] + "..." if len(img_path.stem) > 20 else img_path.stem)

                    if selectable:
                        if st.checkbox("선택", key=f"sel_{img_path.name}", label_visibility="collapsed"):
                            selected.append(img_path)

    return selected


def render_image_detail(image_path: Path):
    """이미지 상세 뷰"""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.image(str(image_path), use_container_width=True)

    with col2:
        st.subheader("이미지 정보")

        # 파일 정보
        stat = image_path.stat()
        st.write(f"**파일명:** {image_path.name}")
        st.write(f"**크기:** {stat.st_size / 1024:.1f} KB")

        # 이미지 정보
        try:
            with Image.open(image_path) as img:
                st.write(f"**해상도:** {img.width} x {img.height}")
                st.write(f"**포맷:** {img.format}")
                st.write(f"**모드:** {img.mode}")
        except Exception as e:
            st.error(f"이미지 정보 로드 실패: {e}")

        # 경로 정보
        st.write(f"**경로:** `{image_path.parent.name}/`")


def render_gallery_page():
    """갤러리 페이지 렌더링"""
    st.header("🖼️ 이미지 갤러리")

    # 사이드바 필터
    with st.sidebar:
        st.subheader("필터")

        category = st.selectbox(
            "카테고리",
            options=[
                ("best_cta", "⭐ Best CTA (TOP 50)"),
                ("cta", "CTA 소스 (크롭)"),
                ("grade_a_happy", "Grade A - Happy"),
                ("grade_a_curious", "Grade A - Curious"),
                ("grade_a_calm", "Grade A - Calm"),
                ("grade_b", "Grade B"),
            ],
            format_func=lambda x: x[1]
        )[0]

        cols = st.slider("열 개수", 3, 8, 5)
        per_page = st.slider("페이지당 이미지", 20, 100, 50)
        show_names = st.checkbox("파일명 표시", value=True)
        selectable = st.checkbox("선택 모드", value=False)

    # 이미지 로드
    images = get_images_by_category(category)

    if not images:
        st.info(f"'{category}' 카테고리에 이미지가 없습니다.")
        return

    # 페이지 선택
    total_pages = (len(images) + per_page - 1) // per_page
    page = st.number_input("페이지", 1, total_pages, 1) - 1

    # 그리드 렌더링
    selected = render_gallery_grid(
        images=images,
        cols=cols,
        show_names=show_names,
        selectable=selectable,
        page=page,
        per_page=per_page
    )

    # 선택된 이미지 처리
    if selectable and selected:
        st.divider()
        st.subheader(f"선택된 이미지: {len(selected)}개")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗑️ 삭제", type="secondary"):
                st.warning("삭제 기능은 준비 중입니다.")
        with col2:
            if st.button("📁 이동", type="secondary"):
                st.warning("이동 기능은 준비 중입니다.")
        with col3:
            if st.button("⭐ 즐겨찾기", type="secondary"):
                st.warning("즐겨찾기 기능은 준비 중입니다.")


# 단독 실행 시
if __name__ == "__main__":
    st.set_page_config(
        page_title="이미지 갤러리",
        page_icon="🖼️",
        layout="wide"
    )
    render_gallery_page()
