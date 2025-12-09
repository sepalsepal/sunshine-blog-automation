import streamlit as st

def render_workflow_timeline():
    """4개 그룹으로 나뉜 워크플로우 타임라인"""
    
    # 그룹 정의
    groups = [
        {
            "title": "1️⃣ 키워드 설정",
            "color": "#2383E2",
            "steps": [
                ('search_trends', '📊', 'Trends'),
                ('search_youtube', '📺', 'YouTube'),
                ('search_blog', '📝', 'Blog'),
                ('combine_research', '🧠', 'Combine'),
            ]
        },
        {
            "title": "2️⃣ 글 작성",
            "color": "#00875A",
            "steps": [
                ('write_content', '✍️', 'Draft'),
                ('create_hashtags', '#️⃣', 'Tags'),
                ('audit_content', '⚖️', 'Audit'),
            ]
        },
        {
            "title": "3️⃣ 이미지 제작",
            "color": "#FF7452",
            "steps": [
                ('create_img_prompt', '🖼️', 'Prompt'),
                ('audit_img_prompt', '🔍', 'Audit'),
                ('generate_images', '🎨', 'Generate'),
            ]
        },
        {
            "title": "4️⃣ 업로드",
            "color": "#6554C0",
            "steps": [
                ('telegram_report', '📢', 'Report'),
                ('approval', '👍', 'Approve'),
                ('upload_wordpress', '🚀', 'Deploy'),
                ('archive_sheets', '📂', 'Archive'),
            ]
        }
    ]
    
    def get_status_display(key):
        status = st.session_state.progress.get(key, {}).get('status', 'pending')
        if status == 'complete':
            return 'complete', '✅'
        elif status == 'active':
            return 'active', '🔄'
        elif status == 'error':
            return 'error', '⚠️'
        else:
            return 'pending', '⬜'
    
    for group in groups:
        # 그룹 전체 진행률 계산
        total = len(group['steps'])
        completed = sum(1 for key, _, _ in group['steps'] 
                       if st.session_state.progress.get(key, {}).get('status') == 'complete')
        active = any(st.session_state.progress.get(key, {}).get('status') == 'active' 
                    for key, _, _ in group['steps'])
        
        # 그룹 상태 표시
        if completed == total:
            group_status = "✅ 완료"
            bg_color = "#E3FCEF"
        elif active:
            group_status = f"🔄 진행중 ({completed}/{total})"
            bg_color = "#E6F3F7"
        elif completed > 0:
            group_status = f"⏸️ 일시정지 ({completed}/{total})"
            bg_color = "#FFF8C5"
        else:
            group_status = "⏳ 대기중"
            bg_color = "#F7F7F5"
        
        # HTML 구성 (들여쓰기 제거하여 코드 블록 인식 방지)
        html = f"""
<div style="background: {bg_color}; border-radius: 12px; padding: 16px; margin-bottom: 16px; border-left: 4px solid {group['color']};">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
<span style="font-weight: 600; font-size: 1.1rem; color: {group['color']};">{group['title']}</span>
<span style="font-size: 0.85rem; color: #666;">{group_status}</span>
</div>
<div style="display: flex; gap: 12px; flex-wrap: wrap;">
"""
        
        for key, icon, title in group['steps']:
            state_class, display_icon = get_status_display(key)
            
            # Audit 단계는 빨간색 테마
            is_audit = 'audit' in key.lower()
            audit_color = "#DE350B"  # Red
            
            if state_class == 'complete':
                if is_audit:
                    item_style = f"background: {audit_color}; color: white;"
                else:
                    item_style = "background: #00875A; color: white;"
            elif state_class == 'active':
                if is_audit:
                    item_style = f"background: {audit_color}; color: white; animation: pulse 1s infinite;"
                else:
                    item_style = f"background: {group['color']}; color: white; animation: pulse 1s infinite;"
            elif state_class == 'error':
                item_style = "background: #DE350B; color: white;"
            else:
                if is_audit:
                    item_style = f"background: #FFEBE6; color: {audit_color}; border: 1px solid {audit_color};"
                else:
                    item_style = "background: #E0E0E0; color: #666;"
            
            html += f"""
<div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; {item_style}">
<span>{display_icon}</span>
<span>{title}</span>
</div>
"""
        
        html += '</div></div>'
        st.markdown(html, unsafe_allow_html=True)
