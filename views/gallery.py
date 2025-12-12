import streamlit as st
import os
import glob
from PIL import Image

def render():
    """
    Render the Image Gallery page.
    Displays all images found in the 'generated_images' directory.
    """
    st.header("🖼️ Image Gallery")
    st.caption("📂 Local Directory: `generated_images/`")
    
    # 이미지 파일 검색
    image_files = glob.glob("generated_images/*.png") + glob.glob("generated_images/*.jpg") + glob.glob("generated_images/*.webp")
    image_files.sort(key=os.path.getmtime, reverse=True) # 최신순 정렬
    
    if not image_files:
        st.info("🖼️ 아직 생성된 이미지가 없습니다.")
        return

    # 갤러리 그리드 표시
    cols = st.columns(4) # 4열 그리드
    for idx, img_path in enumerate(image_files):
        with cols[idx % 4]:
            try:
                # 이미지 로드 및 표시
                img = Image.open(img_path)
                st.image(img, use_container_width=True)
                
                # 파일명 표시 (확장자 제외)
                filename = os.path.basename(img_path).split('.')[0]
                st.caption(f"📄 {filename}")
                
                # 다운로드 버튼
                with open(img_path, "rb") as file:
                    btn = st.download_button(
                        label="⬇️ Download",
                        data=file,
                        file_name=os.path.basename(img_path),
                        mime="image/png",
                        key=f"dl_{idx}"
                    )
            except Exception as e:
                st.error(f"Error loading {os.path.basename(img_path)}")
