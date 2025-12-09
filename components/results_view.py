import streamlit as st

def show_research_results(final_data):
    """Step 1: 리서치 결과 표시"""
    if not final_data.get('research_data'):
        return

    with st.expander("📊 Step 1: Research Results", expanded=False):
        tabs = st.tabs(["Trends", "YouTube", "Blog", "Combined"])
        
        data = final_data['research_data']
        
        with tabs[0]:
            st.json(data.get('trends', {}))
        with tabs[1]:
            st.json(data.get('youtube', {}))
        with tabs[2]:
            st.json(data.get('blog', {}))
        with tabs[3]:
            st.markdown(data.get('combined', ''))

def show_draft_preview(final_data):
    """Step 2: 초안 및 감수 결과 표시"""
    post = final_data.get('post')
    if not post:
        return

    with st.expander("✍️ Step 2 & 3: Draft & Audit", expanded=False):
        st.subheader(post.get('title', 'No Title'))
        st.markdown(f"**Tags:** {post.get('hashtags', '')}")
        st.markdown("---")
        st.markdown(post.get('content_html', ''), unsafe_allow_html=True)

def show_image_prompts(final_data):
    """Step 4: 이미지 프롬프트 표시"""
    prompts = final_data.get('audited_prompts') or final_data.get('post', {}).get('image_prompts', [])
    if not prompts:
        return

    with st.expander("🖼️ Step 4: Image Prompts", expanded=False):
        for i, prompt in enumerate(prompts):
            st.markdown(f"**{i+1}.** {prompt}")

def show_image_gallery(final_data):
    """Step 4: 이미지 생성 결과 표시"""
    images = final_data.get('images', [])
    if not images:
        return

    with st.expander("🎨 Step 4: Generated Images", expanded=True):
        cols = st.columns(len(images))
        for idx, (col, img_path) in enumerate(zip(cols, images)):
            with col:
                st.image(img_path, caption=f"Image {idx+1}", use_container_width=True)
