import streamlit as st
import os
import sys

# 프로젝트 경로 추가
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "04_pipeline"))
sys.path.insert(0, os.path.join(_ROOT, "05_services"))

import content
import telegram_notifier
import time

def render(wm):
    """
    Render Step 2: Draft & Editor.
    Handles content generation and the human-in-the-loop editor.
    """
    # Draft 생성 로직 (없을 때만 실행)
    if not st.session_state.final_data.get('post'):
        try:
            wm.update_progress('write_content', 'active', 30)
            
            # [Telegram] Start Notification
            try: telegram_notifier.send_message(f"✍️ [2/5] 글 작성을 시작합니다... (Topic: {st.session_state.final_data['topic']})")
            except: pass
            
            with st.spinner("✍️ Writing content..."):
                post = content.generate_blog_content("정보성", st.session_state.final_data['topic'])
                
                if not post:
                    raise Exception("Gemini API No Response")
                
                if not all(k in post for k in ['title', 'content_html', 'hashtags']):
                    raise Exception("Missing required fields")
                
                st.session_state.final_data['post'] = post
                st.success(f"✅ 글 작성 완료: {post['title']}")
                wm.save_state()
                wm.rerun() # 생성 후 리런하여 에디터 진입
                
        except Exception as e:
            wm.update_progress('write_content', 'error')
            wm.save_state()
            st.error(f"❌ 글 작성 중 에러 발생: {str(e)}")
            st.stop()

    # --- [NEW] Content Command Center: Phase 1 (Draft Editor) ---
    if st.session_state.final_data.get('post'):
        # 상태 동기화 (복구 시 Pending으로 뜨는 문제 해결)
        if st.session_state.progress['write_content']['status'] != 'active':
            wm.update_progress('write_content', 'active')
        
        st.markdown("### 📝 Draft Editor (Human-in-the-Loop)")
        st.info("AI가 작성한 초안입니다. 내용을 확인하고 수정해주세요. 완료되면 'Save & Continue'를 눌러주세요.")

        try:
            # 데이터 무결성 체크
            current_post = st.session_state.final_data['post']
            if 'title' not in current_post or 'content_html' not in current_post:
                raise ValueError("Corrupted post data")

            # 에디터 UI (Tabs)
            tab1, tab2 = st.tabs(["📝 Edit (HTML)", "👁️ Preview"])
            
            with tab1:
                edited_title = st.text_input("제목 (Title)", value=current_post['title'])
                edited_content = st.text_area("본문 (Content HTML)", value=current_post['content_html'], height=600)
            
            with tab2:
                st.markdown(f"### {current_post['title']}")
                st.markdown(current_post['content_html'], unsafe_allow_html=True)

        except Exception as e:
            st.error(f"⚠️ 데이터 오류 발생: {e}")
            if st.button("🗑️ 데이터 초기화 및 재생성"):
                del st.session_state.final_data['post']
                wm.update_progress('write_content', 'pending')
                wm.save_state()
                wm.rerun()
            st.stop()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save & Continue (Next Step)", type="primary", use_container_width=True):
                # 수정 사항 저장
                st.session_state.final_data['post']['title'] = edited_title
                st.session_state.final_data['post']['content_html'] = edited_content
                
                # 상태 업데이트 및 다음 단계로 이동
                wm.update_progress('write_content', 'complete', 100)
                wm.update_progress('create_hashtags', 'complete', 100)
                
                # [Telegram] Complete Notification
                try: telegram_notifier.send_message(f"✅ [2/5] 초안 컨펌 완료: {edited_title}")
                except: pass
                
                wm.save_state()
                time.sleep(0.5)
                wm.set_step(3)
                wm.rerun()
                
        with col2:
            if st.button("🔄 Regenerate Draft (다시 쓰기)", use_container_width=True):
                # 재확인 없이 바로 삭제 후 리런
                del st.session_state.final_data['post']
                wm.update_progress('write_content', 'pending')
                wm.save_state()
                wm.rerun()
