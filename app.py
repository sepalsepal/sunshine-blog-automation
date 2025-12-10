import streamlit as st
import time
import os
import glob
from PIL import Image

# 모듈 연결
import content
import image_utils
import weather_utils
import wordpress 
import food_manager
import research
import auditor
import g_sheet_archiver
import telegram_notifier
import email_notifier
import state_manager
from components.timeline import render_workflow_timeline
from components import results_view
import bot_listener

# [NEW] Modular Architecture Imports
from workflow_manager import WorkflowManager
from views import step_01_research
from views import step_02_draft

# --- [1] 페이지 설정 ---
st.set_page_config(
    page_title="Sunshine v2.2", 
    page_icon="🌞", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- [NEW] Workflow Manager 초기화 ---
wm = WorkflowManager()

# --- [NEW] 텔레그램 봇 명령 감지 ---
bot_cmd = bot_listener.check_for_commands()
if bot_cmd:
    wm.rerun()

# --- [NEW] URL 파라미터 처리 (이메일/텔레그램/스케줄러 통합) ---
params = st.query_params

# 텔레그램 또는 스케줄러에서 시작 요청
if params.get("action") == "start":
    topic = params.get("topic", "")
    
    # 자동 주제 선정 (스케줄러에서 topic=auto로 호출)
    if topic == "auto":
        st.info("⏰ 스케줄러 자동 실행! 트렌드 주제 선정 중...")
        try:
            trends = research.get_google_trends("강아지")
            if trends.get('top_queries'):
                topic = trends['top_queries'][0]  # 상위 1개 선택
                st.success(f"📈 트렌드 주제 선정: **{topic}**")
            else:
                topic = "복숭아"  # 기본값
                st.warning(f"⚠️ 트렌드 없음, 기본 주제 사용: {topic}")
        except:
            topic = "사과"  # 폴백
            st.warning(f"⚠️ 트렌드 조회 실패, 기본 주제 사용: {topic}")
    
    if topic:
        st.success(f"🚀 워크플로우 시작! 주제: **{topic}**")
        st.session_state.final_data['topic'] = topic
        wm.set_step(1)
        st.query_params.clear()
        wm.rerun()

# 이메일 승인
elif params.get("action") == "approve":
    st.success("✅ 이메일 승인 확인! 워드프레스 업로드를 시작합니다...")
    st.session_state.email_approved = True
    st.query_params.clear()

# 이메일 거절
elif params.get("action") == "reject":
    st.warning("❌ 이메일에서 거절되었습니다. 워크플로우를 종료합니다.")
    st.session_state.email_rejected = True
    st.query_params.clear()

# --- [2] Notion Style CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global */
        * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; color: #37352f; }
        .stApp { background-color: #FFFFFF; }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #F7F7F5;
            border-right: 1px solid #E0E0E0;
        }
        
        /* Main Title */
        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            color: #37352f;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        
        .hero-subtitle {
            color: #787774;
            font-size: 1.1rem;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        /* Notion Card (Callout) */
        .notion-card {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        
        .notion-card:hover {
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-color: #D0D0D0;
        }
        
        /* Section Headers */
        .section-header {
            font-size: 1.2rem;
            font-weight: 600;
            color: #37352f;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Workflow Container (Mobile Scroll) */
        .workflow-container {
            display: flex;
            justify-content: flex-start; /* Left align for scrolling */
            align-items: center;
            margin: 2rem 0;
            padding: 1rem 0;
            overflow-x: auto; /* Enable horizontal scroll */
            white-space: nowrap; /* Prevent wrapping */
            -webkit-overflow-scrolling: touch; /* Smooth scroll on iOS */
            gap: 1rem; /* Space between items */
        }
        
        /* Hide scrollbar for clean look */
        .workflow-container::-webkit-scrollbar {
            display: none;
        }

        .step-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 80px;
            gap: 0.5rem;
            opacity: 0.4;
            transition: all 0.3s ease;
        }
        
        .step-item.active { opacity: 1; transform: scale(1.05); }
        .step-item.complete { opacity: 1; color: #2EAADC; }
        
        .step-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            background: #F0F0F0;
            border: 1px solid #E0E0E0;
        }
        
        .step-item.active .step-icon {
            background: #2383E2;
            color: white;
            border-color: #2383E2;
            box-shadow: 0 0 0 4px rgba(35, 131, 226, 0.2);
        }
        
        .step-item.complete .step-icon {
            background: #E3FCEF;
            color: #00703C;
            border-color: #E3FCEF;
        }
        
        .step-item.error { opacity: 1; color: #D70022; }
        .step-item.error .step-icon {
            background: #FFEBE6;
            color: #D70022;
            border-color: #FFBDAD;
            box-shadow: 0 0 0 4px rgba(215, 0, 34, 0.2);
            animation: shake 0.5s;
        }
        
        @keyframes shake {
            0% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            50% { transform: translateX(5px); }
            75% { transform: translateX(-5px); }
            100% { transform: translateX(0); }
        }
        
        .step-label {
            font-size: 0.75rem;
            font-weight: 500;
            text-align: center;
        }
        
        /* Buttons */
        .stButton > button {
            width: 100%;
            background-color: #2383E2;
            color: white !important;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background 0.2s;
        }
        .stButton > button:hover {
            background-color: #1A6FB0;
        }
        
        /* Status Messages */
        .stSuccess { background-color: #E3FCEF; color: #00703C; border: none; }
        .stInfo { background-color: #E6F3F7; color: #005A87; border: none; }
        .stWarning { background-color: #FFF8C5; color: #5C4B00; border: none; }
        .stError { background-color: #FFEBE6; color: #BF2600; border: none; }
        
        /* Gallery */
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 1rem;
        }
        .gallery-img {
            border-radius: 8px;
            border: 1px solid #E0E0E0;
            width: 100%;
            height: auto;
        }
    </style>
""", unsafe_allow_html=True)

# [NEW] 저장된 상태 불러오기 (앱 재시작 시 복구)
if wm.load_state():
    pass # Toast is handled in load_state

# --- [4] 헤더 ---
st.markdown('<div class="hero-title">Sunshine Imageworks (v2.2)</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">AI-Powered Blog Content Generation Platform</div>', unsafe_allow_html=True)

# --- [5] 타임라인 ---
render_workflow_timeline()

# --- [6] 메인 로직 (Step-by-Step) ---
step = wm.get_current_step()
final_data = st.session_state.final_data

# [Auto-Recovery] 진행 상태와 Step이 맞지 않을 경우 자동 보정 (WorkflowManager 내부로 이동됨)
# wm._auto_recover() is called in load_state()

if step >= 2:
    results_view.show_research_results(final_data)

if step >= 3:
    results_view.show_draft_preview(final_data)

if step >= 4:
    results_view.show_image_prompts(final_data)

if step == 0:
    # 0. 시작 대기
    with st.sidebar:
        st.header("🎮 Control Center")
        
        category = st.selectbox("📂 Category", ["강아지 건강", "강아지 훈련", "강아지 영양", "강아지 행동", "FOOD (오늘 뭐 먹지?)"])
        topic_input = st.text_input("💡 Custom Topic (Optional)", placeholder="Enter specific topic...")
        
        auto_approve = st.checkbox("⚡ 자동 승인 (검토 없이 바로 업로드)", value=False)
        st.session_state.auto_approve = auto_approve
        
        if st.button("🚀 START WORKFLOW", type="primary"):
            wm.set_step(1)
            wm.rerun()

elif step == 1:
    # 1. Research (Modularized)
    step_01_research.render(wm, topic_input if 'topic_input' in locals() else None, category if 'category' in locals() else None)

elif step == 2:
    # 2. Draft & Editor (Modularized)
    step_02_draft.render(wm)

elif step == 3:
    # 3. Audit
    st.header("🧐 Step 3: Content Audit")
    
    # 3-1. 해시태그 생성
    wm.update_progress('create_hashtags', 'active')
    wm.save_state()
    
    with st.spinner("🏷️ 해시태그 생성 중..."):
        hashtags = content.generate_hashtags(st.session_state.final_data['post']['content_html'])
    
    st.session_state.final_data['post']['hashtags'] = hashtags
    wm.update_progress('create_hashtags', 'complete', 100)
    wm.save_state()
    
    # 3-2. 콘텐츠 검수
    wm.update_progress('audit_content', 'active')
    wm.save_state()
    
    with st.spinner("🧐 콘텐츠 검수 중..."):
        audit_result = auditor.audit_content(st.session_state.final_data['post'])
    
    st.session_state.final_data['audit_result'] = audit_result
    wm.update_progress('audit_content', 'complete', 100)
    wm.save_state()
    
    # Audit 결과 표시
    st.success(f"✅ 검수 완료! 점수: {audit_result['score']}/100")
    with st.expander("상세 검수 결과"):
        st.json(audit_result)
        
    time.sleep(0.5)
    wm.set_step(4)
    wm.rerun()

elif step == 4:
    # 4. Visuals
    st.header("🎨 Step 4: Visuals")
    
    # 4-1. 이미지 프롬프트 생성
    wm.update_progress('create_img_prompt', 'active')
    wm.save_state()
    
    with st.spinner("🎨 이미지 프롬프트 생성 중..."):
        image_prompts = image_utils.generate_image_prompts(st.session_state.final_data['post'])
    
    st.session_state.final_data['image_prompts'] = image_prompts
    wm.update_progress('create_img_prompt', 'complete', 100)
    wm.save_state()
    
    # 4-2. 이미지 생성
    wm.update_progress('generate_images', 'active')
    wm.save_state()
    
    generated_images = []
    with st.spinner("🖼️ 이미지 생성 중 (Imagen 3)..."):
        for i, prompt in enumerate(image_prompts):
            st.write(f"Generating image {i+1}/{len(image_prompts)}...")
            img_path = image_utils.generate_imagen_image(prompt, i)
            if img_path:
                generated_images.append(img_path)
    
    st.session_state.final_data['images'] = generated_images
    wm.update_progress('generate_images', 'complete', 100)
    wm.save_state()
    
    time.sleep(0.5)
    wm.set_step(5)
    wm.rerun()

elif step == 5:
    # 5. Approval & Upload
    st.header("🚀 Step 5: Approval & Upload")
    
    # 5-1. 텔레그램 보고
    if st.session_state.progress['telegram_report']['status'] != 'complete':
        wm.update_progress('telegram_report', 'active')
        wm.save_state()
        
        with st.spinner("📱 텔레그램 보고서 전송 중..."):
            telegram_notifier.send_final_report(st.session_state.final_data)
        
        wm.update_progress('telegram_report', 'complete', 100)
        wm.save_state()
    
    # 5-2. 승인 대기
    wm.update_progress('approval', 'active')
    wm.save_state()
    
    st.info("⏳ 사용자 승인 대기 중... (텔레그램 또는 아래 버튼을 확인하세요)")
    
    # [NEW] Manual Check Button
    if st.button("🔄 승인 상태 확인 (Check Status)"):
        wm.load_state() # 파일에서 최신 상태 다시 로드
        if st.session_state.get('telegram_approved'):
             st.success("✅ 텔레그램 승인 확인됨!")
             time.sleep(1)
             wm.rerun()
        else:
             st.warning("아직 승인되지 않았습니다.")

    # [NEW] Web Direct Approve Button
    if st.button("✅ 웹에서 바로 승인 (Direct Approve)", type="primary"):
        st.session_state.telegram_approved = True
        wm.save_state()
        st.success("✅ 승인되었습니다! 업로드를 시작합니다.")
        time.sleep(1)
        wm.rerun()

    # 승인 체크
    if st.session_state.get('auto_approve') or st.session_state.get('telegram_approved') or st.session_state.get('email_approved'):
        wm.update_progress('approval', 'complete', 100)
        wm.save_state()
        
        # 5-3. 워드프레스 업로드
        wm.update_progress('upload_wordpress', 'active')
        wm.save_state()
        
        with st.spinner("🌐 워드프레스 업로드 중..."):
            post_url = wordpress.upload_post(st.session_state.final_data)
        
        st.session_state.final_data['post_url'] = post_url
        wm.update_progress('upload_wordpress', 'complete', 100)
        wm.save_state()
        
        # 5-4. 구글 시트 아카이빙
        wm.update_progress('archive_sheets', 'active')
        wm.save_state()
        
        with st.spinner("📊 구글 시트 기록 중..."):
            g_sheet_archiver.archive_post(st.session_state.final_data)
            
        wm.update_progress('archive_sheets', 'complete', 100)
        wm.save_state()
        
        st.success(f"✨ 모든 작업 완료! [포스트 보러가기]({post_url})")
        st.balloons()
        
        # 완료 후 리셋 버튼
        if st.button("🔄 새로운 글 작성하기"):
            state_manager.clear_state()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            wm.rerun()

# 봇 리스너 주기적 체크 (마지막 안전장치)
bot_listener.auto_refresh_if_idle()
