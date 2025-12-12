import streamlit as st
import os
import glob
import datetime
from PIL import Image

def render():
    """
    Render the Generation History (Gallery) page.
    Displays images grouped by date in a tight grid.
    """
    st.markdown('<div class="hero-title">Generation History</div>', unsafe_allow_html=True)
    
    # 이미지 파일 검색
    image_files = glob.glob("generated_images/*.png") + glob.glob("generated_images/*.jpg") + glob.glob("generated_images/*.webp")
    
    if not image_files:
        st.info("🖼️ No images generated yet.")
        return

    # 메타데이터 추출 및 정렬
    images_with_meta = []
    for img_path in image_files:
        mod_time = os.path.getmtime(img_path)
        dt = datetime.datetime.fromtimestamp(mod_time)
        images_with_meta.append({
            "path": img_path,
            "time": mod_time,
            "date_str": dt.strftime("%A, %B %d, %Y") # e.g., Friday, December 12, 2025
        })
    
    # 최신순 정렬
    images_with_meta.sort(key=lambda x: x["time"], reverse=True)
    
    # 날짜별 그룹화
    grouped_images = {}
    for img in images_with_meta:
        date_key = img["date_str"]
        if date_key not in grouped_images:
            grouped_images[date_key] = []
        grouped_images[date_key].append(img)
    
    # 렌더링
    for date_str, images in grouped_images.items():
        st.markdown(f"### {date_str}")
        
        # 4열 그리드 (Tight Layout)
        cols = st.columns(4)
        for idx, img_data in enumerate(images):
            with cols[idx % 4]:
                try:
                    img_path = img_data["path"]
                    img = Image.open(img_path)
                    
                    # 이미지 표시 (CSS 클래스 적용)
                    st.image(img, use_container_width=True)
                    
                    # 오버레이 버튼 (다운로드) - Streamlit 한계로 아래에 작게 표시
                    filename = os.path.basename(img_path)
                    with open(img_path, "rb") as file:
                        st.download_button(
                            label="⬇️",
                            data=file,
                            file_name=filename,
                            mime="image/png",
                            key=f"dl_{filename}",
                            help=f"Download {filename}"
                        )
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.markdown("---")
