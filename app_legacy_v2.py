import streamlit as st
import time
import os
import glob
from PIL import Image

# 모듈 연결 - LAZY LOADED to prevent blocking on startup
# These will be imported only when needed
# import content
# import image_utils
# import weather_utils
# import wordpress 
# import food_manager
# import research
# import auditor
# import g_sheet_archiver
# import telegram_notifier
# import email_notifier
import state_manager
from components.timeline import render_workflow_timeline
from components import results_view
# import bot_listener  # DISABLED - causing infinite loading

# [NEW] Modular Architecture Imports
from workflow_manager import WorkflowManager
from views import step_01_research
from views import step_02_draft
from views import gallery
from views import api_management

# --- [1] 페이지 설정 ---
st.set_page_config(
    page_title="Sunshine v2.2", 
    page_icon="🌞", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- [NEW] Workflow Manager 초기화 ---
wm = WorkflowManager()

# --- [6] 사이드바 (Moved to Top) ---
with st.sidebar:
    st.markdown("### Manager")
    st.caption("Admin Dashboard")
    
    # Initialize view_mode if not set (default to 'workflow')
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'workflow'
    
    # Map view_mode to index for radio button
    view_options = ["Go to Studio", "Generation History", "API Management"]
    view_map = {"workflow": 0, "gallery": 1, "api_management": 2}
    reverse_map = {0: "workflow", 1: "gallery", 2: "api_management"}
    
    # Get current index
    current_index = view_map.get(st.session_state.view_mode, 0)
    
    # Navigation (use index to avoid constant reruns)
    nav_index = st.radio(
        "Navigation", 
        range(len(view_options)),
        format_func=lambda x: view_options[x],
        index=current_index,
        label_visibility="collapsed"
    )
    
    # Only update if changed
    new_view_mode = reverse_map[nav_index]
    if st.session_state.view_mode != new_view_mode:
        st.session_state.view_mode = new_view_mode
        st.rerun()

    st.markdown("---")
    st.caption("🎛️ Studio controls are in the main area")


# --- [NEW] 텔레그램 봇 명령 감지 ---
# TEMPORARILY DISABLED - causing infinite loading
# bot_cmd = bot_listener.check_for_commands()
# if bot_cmd:
#     wm.rerun()

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
        
        /* Global Dark Theme */
        * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; color: #E6E6E6; }
        .stApp { background-color: #0E1117; }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #161B22;
            border-right: 1px solid #30363D;
        }
        
        /* Main Title */
        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        
        .hero-subtitle {
            color: #8B949E;
            font-size: 1.1rem;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        /* Notion Card (Dark Mode) */
        .notion-card {
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        
        .section-header {
            font-size: 1.2rem;
            font-weight: 600;
            color: #FFFFFF;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #238636; /* GitHub Green */
            color: white !important;
            border: 1px solid rgba(240, 246, 252, 0.1);
            border-radius: 6px;
            font-weight: 500;
        }
        .stButton > button:hover {
            background-color: #2EA043;
        }
        
        /* Inputs */
        .stTextInput > div > div > input, .stSelectbox > div > div > div {
            background-color: #0D1117;
            color: white;
            border-color: #30363D;
        }
        
        /* Gallery Grid */
        .gallery-img {
            border-radius: 8px;
            border: 1px solid #30363D;
        }

        /* --- STUDIO UI --- */
        
        /* Grid Background */
        .studio-grid-bg {
            background-color: #0E1117;
            background-image: linear-gradient(#161B22 1px, transparent 1px), linear-gradient(90deg, #161B22 1px, transparent 1px);
            background-size: 40px 40px;
            height: 100vh;
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            z-index: -1;
        }
        
        /* Top Bar */
        .top-bar {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.5rem 1rem;
            background: #0E1117;
            border-bottom: 1px solid #30363D;
            margin-bottom: 2rem;
        }
        
        .model-badge {
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 20px;
            padding: 0.2rem 0.8rem;
            font-size: 0.8rem;
            color: #8B949E;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .model-badge.active {
            border-color: #2383E2;
            color: #2383E2;
            background: rgba(35, 131, 226, 0.1);
        }
        
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #238636;
        }
        
        /* Floating Bottom Bar */
        .bottom-bar-container {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            width: 80%;
            max-width: 900px;
            background: rgba(22, 27, 34, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid #30363D;
            border-radius: 16px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            z-index: 1000;
        }
        
        .bottom-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 0.5rem;
        }
        
        .control-group {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        /* Custom Input for Bottom Bar */
        .studio-input textarea {
            background: transparent !important;
            border: none !important;
            color: white !important;
            font-size: 1rem !important;
            resize: none;
        }
        
        .studio-input textarea:focus {
            box-shadow: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- [NEW] 저장된 상태 불러오기 (앱 재시작 시 복구)
if wm.load_state():
    pass # Toast is handled in load_state

# --- [ROUTING] View Mode Routing (Before Header/Timeline) ---
if st.session_state.get('view_mode') == 'gallery':
    gallery.render()
    st.stop()
elif st.session_state.get('view_mode') == 'api_management':
    api_management.render()
    st.stop()
elif st.session_state.get('view_mode') == 'workflow':
    # Workflow (Studio) mode - skip header/timeline, render Studio UI directly
    pass
else:
    # For placeholder views, show header
    st.markdown('<div class="hero-title">Sunshine Imageworks (v2.2)</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">AI-Powered Blog Content Generation Platform</div>', unsafe_allow_html=True)
    render_workflow_timeline()
    st.info("🚧 This page is under construction.")
    st.stop()

# --- [4] 헤더 --- (Only for non-workflow modes now handled above)
# Removed from here to avoid showing in Studio mode

# --- [5] 타임라인 --- (Only for non-workflow modes now handled above)
# Removed from here to avoid showing in Studio mode

# --- [6] 메인 로직 (Step-by-Step) ---

step = st.session_state.pipeline['step']
final_data = st.session_state.final_data

# [STUDIO UI] Render Studio Interface if in Workflow mode
if st.session_state.get('view_mode') == 'workflow':
    # 1. Grid Background
    st.markdown('<div class="studio-grid-bg"></div>', unsafe_allow_html=True)
    
    # 2. Top Bar
    st.markdown("""
    <div class="top-bar">
        <div class="model-badge active"><div class="dot"></div>Gemini 2.0 Flash Exp</div>
        <div class="model-badge"><div class="dot" style="background:#8B949E"></div>Nano Banana Pro</div>
        <div style="flex-grow:1"></div>
        <div class="model-badge">2K</div>
        <div class="model-badge">4K</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Main Content Area (Empty State or Results)
    if step == 0:
        st.markdown("""
        <div style="display:flex; justify-content:center; align-items:center; height:60vh; flex-direction:column; color:#8B949E;">
            <div style="font-size:3rem; margin-bottom:1rem;">🎨</div>
            <div style="font-size:1.2rem;">Start creating by describing your idea below.</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 4. Floating Bottom Bar (Input & Controls)
    # We use a container to mimic the floating bar
    with st.container():
        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True) # Spacer
        
        # Using columns to center the input area if needed, but CSS handles fixed pos.
        # Streamlit widgets can't be easily put inside custom HTML fixed divs.
        # So we use a trick: Place widgets at the bottom and use CSS to style the container?
        # No, Streamlit widgets are hard to float.
        # Alternative: Use standard Streamlit widgets at the bottom of the page, styled to look like a floating bar?
        # Or just put them in a container at the bottom.
        
        st.markdown("---") # Visual separator
        
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            topic_input = st.text_input("Topic", placeholder="이미지를 설명하세요... (예: 눈 내리는 마을의 크리스마스)", label_visibility="collapsed")
        with col_btn:
            start_btn = st.button("✨ Generate", type="primary", use_container_width=True)
            
        # Options
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            st.toggle("Step-by-Step", value=True)
        with c2:
            st.selectbox("Ratio", ["1:1", "16:9", "9:16"], label_visibility="collapsed")
            
        if start_btn and topic_input:
            st.session_state.final_data['topic'] = topic_input
            wm.set_step(1)
            wm.rerun()

# [Legacy Logic for Steps 1-5] - Only show if step > 0
if step >= 1:
    # Hide the empty state if step > 0 (handled above)
    pass

if step >= 2:
    results_view.show_research_results(final_data)

if step >= 3:
    results_view.show_draft_preview(final_data)

if step >= 4:
    results_view.show_image_prompts(final_data)

if step == 0:
    # 0. 시작 대기
    with st.sidebar:
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

# --- [6] 사이드바 (Moved to Top) ---
# Sidebar must be defined before st.stop() calls
with st.sidebar:
    st.markdown("### Manager")
    st.caption("Admin Dashboard")
    
    # Navigation
    nav_selection = st.radio(
        "Navigation", 
        ["Generation History", "Knowledge Base", "API Management", "User Management", "---", "Go to Studio"],
        label_visibility="collapsed"
    )
    
    # Routing Logic
    if nav_selection == "Generation History":
        st.session_state.view_mode = 'gallery'
    elif nav_selection == "API Management":
        st.session_state.view_mode = 'api_management'
    elif nav_selection == "Go to Studio":
        st.session_state.view_mode = 'workflow'
    else:
        st.session_state.view_mode = 'placeholder'

    st.markdown("---")
    
    # Studio Controls (Only visible in Studio Mode)
    if st.session_state.get('view_mode') == 'workflow':
        st.markdown("### 🎮 Studio Controls")
        category = st.selectbox("📁 Category", ["강아지 ## 먹어도 되나요?", "WALK_TIPS"])
        topic_input = st.text_input("💡 Custom Topic")
        
        if st.button("🚀 START WORKFLOW"):
            # 상태 리셋
            st.session_state.pipeline['step'] = 1
            st.session_state.final_data = {} 
            for key in st.session_state.progress:
                st.session_state.progress[key] = {'status': 'pending', 'percent': 0}
            state_manager.clear_state()
            st.rerun()

# [Telegram Bot Listener]
import bot_listener
command = bot_listener.check_for_commands()
if command == "START_WORKFLOW":
    try: telegram_notifier.send_message(f"🚀 웹 앱에서 작업을 시작했습니다! (주제: {st.session_state.final_data['topic']})")
    except: pass
    state_manager.save_state()
    st.rerun()
elif command == "APPROVE_UPLOAD":
    st.rerun()
    st.balloons()
    
    # 완료 후 리셋 버튼
    if st.button("🔄 새로운 글 작성하기"):
        state_manager.clear_state()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        wm.rerun()

# 봇 리스너 주기적 체크 (마지막 안전장치)
# TEMPORARILY DISABLED - causing infinite loading every 3 seconds
# bot_listener.auto_refresh_if_idle()
