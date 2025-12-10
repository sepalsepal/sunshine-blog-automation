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
import email_notifier  # [NEW] Gmail 승인 시스템
import state_manager
from components.timeline import render_workflow_timeline  # [Fix] Import early for button handler
from components import results_view  # [NEW] 결과물 표시 컴포넌트
import bot_listener  # [NEW] 텔레그램 봇 리스너

# --- [1] 페이지 설정 ---
st.set_page_config(
    page_title="Sunshine Imageworks", 
    page_icon="🌞", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- [NEW] 텔레그램 봇 명령 감지 ---
bot_cmd = bot_listener.check_for_commands()
if bot_cmd:
    st.rerun()

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
        st.session_state.pipeline['step'] = 1
        st.query_params.clear()
        st.rerun()

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

# --- [3] Session State 초기화 ---
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = {'step': 0, 'status': 'idle'}

if 'progress' not in st.session_state:
    st.session_state.progress = {
        'search_trends': {'status': 'pending', 'percent': 0},
        'search_youtube': {'status': 'pending', 'percent': 0},
        'search_blog': {'status': 'pending', 'percent': 0},
        'combine_research': {'status': 'pending', 'percent': 0},
        'write_content': {'status': 'pending', 'percent': 0},
        'create_hashtags': {'status': 'pending', 'percent': 0},
        'audit_content': {'status': 'pending', 'percent': 0},
        'create_img_prompt': {'status': 'pending', 'percent': 0},
        'audit_img_prompt': {'status': 'pending', 'percent': 0},
        'generate_images': {'status': 'pending', 'percent': 0},
        'telegram_report': {'status': 'pending', 'percent': 0},
        'approval': {'status': 'pending', 'percent': 0},
        'upload_wordpress': {'status': 'pending', 'percent': 0},
        'archive_sheets': {'status': 'pending', 'percent': 0}
    }

if 'final_data' not in st.session_state:
    st.session_state.final_data = {}

# [NEW] 저장된 상태 불러오기 (앱 재시작 시 복구)
if state_manager.load_state():
    st.toast("💾 이전 작업 상태를 복구했습니다.")

# --- [4] 헤더 ---
st.markdown('<div class="hero-title">Sunshine Imageworks (v2.1)</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">AI-Powered Blog Content Generation Platform</div>', unsafe_allow_html=True)

# --- [5] 타임라인 ---
render_workflow_timeline()

# --- [6] 메인 로직 (Step-by-Step) ---
step = st.session_state.pipeline['step']
final_data = st.session_state.final_data

# [Auto-Recovery] 진행 상태와 Step이 맞지 않을 경우 자동 보정
if step == 1 and st.session_state.progress['combine_research']['status'] == 'complete':
    st.session_state.pipeline['step'] = 2
    state_manager.save_state()  # [FIX] 무한 루프 방지: 변경된 상태 저장
    st.rerun()
elif step == 2 and st.session_state.progress['write_content']['status'] == 'complete':
    st.session_state.pipeline['step'] = 3
    state_manager.save_state()  # [FIX] 무한 루프 방지: 변경된 상태 저장
    st.rerun()

if step >= 2:
    results_view.show_research_results(final_data)

if step >= 3: # 초안 작성 완료 후
    results_view.show_draft_preview(final_data)

if step >= 4: # 프롬프트 생성 완료 후
    results_view.show_image_prompts(final_data)

if step >= 5: # 이미지 생성 완료 후 (Step 4는 생성 중)
    results_view.show_image_gallery(final_data)

# --- [6] 사이드바 ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Dog%20Face.png", width=120)
    st.markdown("### 🎮 Control Center")
    
    category = st.selectbox("📁 Category", ["강아지 ## 먹어도 되나요?", "WALK_TIPS"])
    topic_input = st.text_input("💡 Custom Topic (Optional)")
    
    # 자동 승인 옵션
    auto_approve = st.checkbox("⚡ 자동 승인 (검토 없이 바로 업로드)", value=False)
    if auto_approve:
        st.caption("⚠️ 텔레그램 승인 없이 자동으로 워드프레스에 업로드됩니다.")
    
    st.markdown("---")
    
    if st.button("🚀 START WORKFLOW"):
        # 상태 리셋
        st.session_state.pipeline['step'] = 1
        st.session_state.final_data = {} # [Fix] Clear previous data
        for key in st.session_state.progress:
            st.session_state.progress[key] = {'status': 'pending', 'percent': 0}
        
        # [Critical] DELETE state file to kill zombie completely
        state_manager.clear_state()
        st.rerun()

    # [Telegram Bot Listener]
    import bot_listener
    command = bot_listener.check_for_commands()
    if command == "START_WORKFLOW":
        # [Telegram] Immediate Ack
        try: telegram_notifier.send_message(f"🚀 웹 앱에서 작업을 시작했습니다! (주제: {st.session_state.final_data['topic']})")
        except: pass
        
        # 상태 저장
        state_manager.save_state()
        st.rerun()
    elif command == "APPROVE_UPLOAD":
        st.rerun()
    
    # --- [NEW] 통계 대시보드 ---
    st.markdown("---")
    st.markdown("### 📊 Statistics")
    
    try:
        stats = g_sheet_archiver.get_statistics()
        
        # 핵심 지표 (3열)
        col1, col2, col3 = st.columns(3)
        col1.metric("📝 전체", stats['total_posts'])
        col2.metric("📅 이번 달", stats['posts_this_month'])
        col3.metric("📆 이번 주", stats['posts_this_week'])
        
        # 데이터 출처 표시
        if stats['source'] == 'sheets':
            st.caption("📗 Google Sheets 연동")
        elif stats['source'] == 'backup':
            st.caption("💾 로컬 백업 데이터")
        else:
            st.caption("⚠️ 아직 발행 기록 없음")
        
        # 최근 글 목록
        if stats['recent_posts']:
            with st.expander("📋 최근 발행 글", expanded=False):
                for post in stats['recent_posts']:
                    title = post.get('Title') or post.get('title', '제목 없음')
                    date = post.get('Date') or post.get('date', '')
                    link = post.get('Link') or post.get('link', '')
                    if link:
                        st.markdown(f"• [{title[:30]}...]({link}) ({date[:10]})")
                    else:
                        st.markdown(f"• {title[:30]}... ({date[:10]})")
    except Exception as e:
        st.caption(f"⚠️ 통계 로드 실패: {str(e)[:30]}")
            
    # [Auto-Refresh for Bot]
    bot_listener.auto_refresh_if_idle()

# --- [7] 실행 로직 (진행률 추가) ---
step = st.session_state.pipeline['step']

# --- [State Management] ---
import state_manager

# 앱 시작 시 상태 로드 (다른 세션/기기 동기화)
if 'loaded' not in st.session_state:
    if state_manager.load_state():
        st.toast("🔄 이전 작업 상태를 불러왔습니다.")
    st.session_state.loaded = True

def update_progress(key, percent, status='active', do_rerun=True):
    """진행률 업데이트 헬퍼 함수"""
    st.session_state.progress[key]['percent'] = percent
    st.session_state.progress[key]['status'] = status
    
    # 상태 저장 (동기화)
    state_manager.save_state()
    
    if do_rerun:
        st.rerun()

    # --- [5.5] 상세 산출물 확인 (Mobile Friendly) ---
    st.markdown("### 📑 Process Details")
    
    # 1. Research Data (Detailed Breakdown)
    with st.expander("📊 1. Research Data (실시간 검색 결과)", expanded=True):
        research_data = st.session_state.final_data.get('research_data', {})
        
        if research_data:
            # Trends
            trends = research_data.get('trends', {})
            if trends:
                st.markdown("**📈 Google Trends**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("*인기 검색어:*")
                    for q in trends.get('top_queries', [])[:5]:
                        st.write(f"• {q}")
                with col2:
                    st.markdown("*급상승 검색어:*")
                    for q in trends.get('rising_queries', [])[:5]:
                        st.write(f"🔥 {q}")
                st.markdown("---")
            
            # YouTube (Real API)
            youtube = research_data.get('youtube', {})
            if youtube:
                st.markdown(f"**📺 YouTube** (검색어: `{youtube.get('query', '')}`)")
                videos = youtube.get('videos', [])
                if videos:
                    for v in videos:
                        video_url = f"https://youtube.com/watch?v={v.get('video_id', '')}"
                        st.markdown(f"• [{v.get('title', '')}]({video_url})")
                        st.caption(f"  📺 {v.get('channel', '')}")
                else:
                    # Fallback for old format
                    for v in youtube.get('suggested_videos', []):
                        st.write(f"• {v}")
                st.markdown("---")
            
            # Blog (Real API)
            blog = research_data.get('blog', {})
            if blog:
                st.markdown(f"**📝 네이버 블로그** (검색어: `{blog.get('query', '')}`)")
                blog_posts = blog.get('blog_posts', [])
                if blog_posts:
                    for b in blog_posts:
                        if b.get('link'):
                            st.markdown(f"• [{b.get('title', '')}]({b.get('link', '')})")
                            st.caption(f"  ✍️ {b.get('blogger', '')}")
                        else:
                            st.write(f"• {b.get('title', '')}")
                else:
                    # Fallback for old format
                    for b in blog.get('blog_titles', []):
                        st.write(f"• {b}")
                st.markdown("---")
            
            # Combined
            combined = research_data.get('combined', {})
            if combined:
                st.markdown("**🧠 최종 선정 키워드**")
                st.write(", ".join(combined.get('selected_keywords', [])))
        else:
            st.info("⏳ 리서치가 시작되면 여기에 실시간으로 결과가 표시됩니다.")

    # 2. Draft Content
    with st.expander("✍️ 2. Draft Content", expanded=False):
        if 'post' in st.session_state.final_data and 'content_html' in st.session_state.final_data['post']:
            st.markdown(st.session_state.final_data['post']['content_html'], unsafe_allow_html=True)
        elif 'content' in st.session_state.final_data: # Fallback for older state structure
             st.markdown(st.session_state.final_data['content'], unsafe_allow_html=True)
        else:
            st.info("No content generated yet.")

    # 3. Audit Report
    with st.expander("⚖️ 3. Audit Report", expanded=False):
        if 'audit_report' in st.session_state.final_data:
            st.markdown(st.session_state.final_data['audit_report'])
        else:
            st.info("No audit report yet.")
            
    # 4. Image Prompts
    with st.expander("🖼️ 4. Image Prompts", expanded=False):
        if 'post' in st.session_state.final_data and 'image_prompts' in st.session_state.final_data['post']:
            st.json(st.session_state.final_data['post']['image_prompts'])
        else:
            st.info("No image prompts yet.")

# --- [Process Visualization] ---
# 현재 단계 이전의 완료된 작업들을 "Notion Card" 형태로 보여줍니다.

if step >= 2:
    st.markdown("""
    <div class="notion-card">
        <div class="section-header">📊 Step 1: Research</div>
        <div style="color: #666; font-size: 0.9rem;">
            Selected Topic: <b>{}</b>
        </div>
    </div>
    """.format(st.session_state.final_data.get('topic', 'Unknown')), unsafe_allow_html=True)

if step >= 3:
    post = st.session_state.final_data.get('post', {})
    st.markdown("""
    <div class="notion-card">
        <div class="section-header">✍️ Step 2: Draft</div>
        <div style="color: #666; font-size: 0.9rem;">
            Title: <b>{}</b><br>
            <span style="font-size: 0.8rem; color: #999;">Generated {} characters</span>
        </div>
    </div>
    """.format(post.get('title', 'Untitled'), len(post.get('content_html', ''))), unsafe_allow_html=True)

if step >= 4:
    st.markdown("""
    <div class="notion-card">
        <div class="section-header">⚖️ Step 3: Audit</div>
        <div style="color: #666; font-size: 0.9rem;">
            ✅ Content audited and improved by AI Editor.
        </div>
    </div>
    """, unsafe_allow_html=True)

if step >= 6: # 이미지 생성 완료 후
    images = st.session_state.final_data.get('images', [])
    img_html = ""
    # 간단한 이미지 프리뷰 HTML 생성 (가로 스크롤)
    if images:
        img_html = '<div style="display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px;">'
        for img in images:
            # 로컬 경로를 웹에서 바로 보여주기 위해 base64 인코딩하거나, Streamlit static serving 필요.
            # 여기서는 간단히 갯수만 표시하거나, st.image를 쓰는게 나음. HTML로는 복잡함.
            pass 
        img_html += '</div>'
    
    st.markdown(f"""
    <div class="notion-card">
        <div class="section-header">🎨 Step 4: Visuals</div>
        <div style="color: #666; font-size: 0.9rem;">
            ✅ Generated {len(images)} images.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 이미지는 st.image로 별도 표시 (HTML 카드 안에 넣기 힘듦)
    if images:
        with st.expander("📸 View Generated Images", expanded=False):
            cols = st.columns(len(images))
            for idx, (col, img_path) in enumerate(zip(cols, images)):
                with col:
                    st.image(img_path, use_container_width=True)

if step == 1:
    # 1-1. Trends 검색
    st.session_state.progress['search_trends']['status'] = 'active'
    state_manager.save_state()
    
    with st.spinner("📊 Google Trends 검색 중..."):
        trends_data = research.search_google_trends()
    st.session_state.final_data['trends_data'] = trends_data
    st.session_state.progress['search_trends']['percent'] = 100
    st.session_state.progress['search_trends']['status'] = 'complete'
    state_manager.save_state()
    
    # 1-2. YouTube 검색
    st.session_state.progress['search_youtube']['status'] = 'active'
    state_manager.save_state()
    
    # 먼저 주제 결정
    if topic_input:
        topic = topic_input
    elif "FOOD" in str(category):
        topic, prompt = food_manager.get_todays_food_topic()
        st.session_state.final_data['food_prompt'] = prompt
    else:
        # Trends에서 선택
        all_topics = trends_data.get('top_queries', []) + trends_data.get('rising_queries', [])
        topic = research.select_topic(all_topics) if all_topics else "강아지 건강"
    
    with st.spinner(f"📺 YouTube 검색 중: {topic}..."):
        youtube_data = research.search_youtube(topic)
    st.session_state.final_data['youtube_data'] = youtube_data
    st.session_state.progress['search_youtube']['percent'] = 100
    st.session_state.progress['search_youtube']['status'] = 'complete'
    state_manager.save_state()
    
    # 1-3. 네이버 블로그 검색
    st.session_state.progress['search_blog']['status'] = 'active'
    state_manager.save_state()
    
    with st.spinner(f"📝 네이버 블로그 검색 중: {topic}..."):
        blog_data = research.search_naver_blog(topic)
    st.session_state.final_data['blog_data'] = blog_data
    st.session_state.progress['search_blog']['percent'] = 100
    st.session_state.progress['search_blog']['status'] = 'complete'
    state_manager.save_state()
    
    # 1-4. 결과 종합
    st.session_state.progress['combine_research']['status'] = 'active'
    state_manager.save_state()
    
    with st.spinner("🧠 리서치 결과 종합 중..."):
        combined_data = research.combine_research(trends_data, youtube_data, blog_data)
    
    st.session_state.final_data['topic'] = topic
    st.session_state.final_data['combined_data'] = combined_data
    
    # 통합 research_data (Process Details용)
    st.session_state.final_data['research_data'] = {
        "trends": trends_data,
        "youtube": youtube_data,
        "blog": blog_data,
        "combined": combined_data
    }
    
    st.session_state.progress['combine_research']['status'] = 'complete'
    st.session_state.progress['combine_research']['percent'] = 100
    state_manager.save_state()
    
    # [Telegram] Research Complete
    try:
        telegram_notifier.send_message(f"📊 [1/5] 주제 선정 완료: {topic}")
    except: pass
    
    time.sleep(0.3)
    st.session_state.pipeline['step'] = 2
    st.rerun()

elif step == 2:
    # Draft 생성 로직 (없을 때만 실행)
    if not st.session_state.final_data.get('post'):
        try:
            st.session_state.progress['write_content']['status'] = 'active'
            st.session_state.progress['write_content']['percent'] = 30
            
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
                state_manager.save_state()
                st.rerun() # 생성 후 리런하여 에디터 진입
                
        except Exception as e:
            st.session_state.progress['write_content']['status'] = 'error'
            state_manager.save_state()
            st.error(f"❌ 글 작성 중 에러 발생: {str(e)}")
            st.stop()

    # --- [NEW] Content Command Center: Phase 1 (Draft Editor) ---
    if st.session_state.final_data.get('post'):
        # 상태 동기화 (복구 시 Pending으로 뜨는 문제 해결)
        if st.session_state.progress['write_content']['status'] != 'active':
            st.session_state.progress['write_content']['status'] = 'active'
        
        st.markdown("### 📝 Draft Editor (Human-in-the-Loop)")
        st.info("AI가 작성한 초안입니다. 내용을 확인하고 수정해주세요. 완료되면 'Save & Continue'를 눌러주세요.")

        try:
            # 데이터 무결성 체크
            current_post = st.session_state.final_data['post']
            if 'title' not in current_post or 'content_html' not in current_post:
                raise ValueError("Corrupted post data")

            # 에디터 UI
            edited_title = st.text_input("제목 (Title)", value=current_post['title'])
            edited_content = st.text_area("본문 (Content HTML)", value=current_post['content_html'], height=600)
        except Exception as e:
            st.error(f"⚠️ 데이터 오류 발생: {e}")
            if st.button("🗑️ 데이터 초기화 및 재생성"):
                del st.session_state.final_data['post']
                st.rerun()
            st.stop()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save & Continue (Next Step)", type="primary", use_container_width=True):
                # 수정 사항 저장
                st.session_state.final_data['post']['title'] = edited_title
                st.session_state.final_data['post']['content_html'] = edited_content
                
                # 상태 업데이트 및 다음 단계로 이동
                st.session_state.progress['write_content']['percent'] = 100
                st.session_state.progress['write_content']['status'] = 'complete'
                st.session_state.progress['create_hashtags']['status'] = 'complete'
                st.session_state.progress['create_hashtags']['percent'] = 100
                
                # [Telegram] Complete Notification
                try: telegram_notifier.send_message(f"✅ [2/5] 초안 컨펌 완료: {edited_title}")
                except: pass
                
                state_manager.save_state()
                time.sleep(0.5)
                st.session_state.pipeline['step'] = 3
                st.rerun()
                
        with col2:
            if st.button("🔄 Regenerate Draft (다시 쓰기)", use_container_width=True):
                # 재확인 없이 바로 삭제 후 리런 (버튼 중첩 문제 해결)
                del st.session_state.final_data['post']
                st.rerun()

elif step == 3:
    # Audit 단계
    st.session_state.progress['audit_content']['status'] = 'active'
    st.session_state.progress['audit_content']['percent'] = 50
    
    # [Telegram] Start Notification
    try: telegram_notifier.send_message("⚖️ [3/5] 감수 및 윤문을 시작합니다...")
    except: pass
    
    try:
        with st.spinner("⚖️ Auditing content..."):
            if st.session_state.final_data.get('post'):
                improved = auditor.audit_and_improve(
                    st.session_state.final_data['topic'], 
                    st.session_state.final_data['post']['content_html']
                )
                if improved:
                    st.session_state.final_data['post']['content_html'] = improved
                    st.success("✅ 감수 완료")
            
            st.session_state.progress['audit_content']['percent'] = 100
            st.session_state.progress['audit_content']['status'] = 'complete'
            
            # [Telegram] Complete Notification
            try: telegram_notifier.send_message("✅ [3/5] 감수 완료")
            except: pass
        
        time.sleep(0.5)
        st.session_state.pipeline['step'] = 4
        st.rerun()
        
    except Exception as e:
        st.warning(f"⚠️ 감수 중 에러 (계속 진행): {str(e)}")
        try: telegram_notifier.send_message(f"⚠️ [주의] 감수 중 오류가 발생했으나 계속 진행합니다: {str(e)}")
        except: pass
        st.session_state.progress['audit_content']['status'] = 'complete'
        st.session_state.pipeline['step'] = 4
        time.sleep(0.5)
        st.rerun()

elif step == 4:
    # Image Rendering 단계
    post = st.session_state.final_data.get('post')
    topic = st.session_state.final_data.get('topic', '')
    
    # 4-1. Prompt 생성/확인
    st.session_state.progress['create_img_prompt']['status'] = 'active'
    state_manager.save_state()
    
    if post and 'image_prompts' in post:
        image_prompts = post['image_prompts']
        st.session_state.progress['create_img_prompt']['percent'] = 100
        st.session_state.progress['create_img_prompt']['status'] = 'complete'
    else:
        st.warning("⚠️ 이미지 프롬프트가 없습니다. 기본값 사용.")
        image_prompts = [f"Golden Retriever with {topic}", f"Close-up of {topic}"]
        st.session_state.progress['create_img_prompt']['status'] = 'complete'
    
    # 4-2. Prompt 검수 (최대 2회 재시도)
    st.session_state.progress['audit_img_prompt']['status'] = 'active'
    state_manager.save_state()
    
    max_audit_retries = 2
    audit_passed = False
    
    for audit_attempt in range(max_audit_retries + 1):
        with st.spinner(f"🔍 이미지 프롬프트 검수 중... (시도 {audit_attempt + 1}/{max_audit_retries + 1})"):
            content_html = post.get('content_html', '') if post else ''
            audit_result = auditor.audit_image_prompts(topic, content_html, image_prompts)
        
        if audit_result.get('approved'):
            st.success(f"✅ 프롬프트 검수 통과: {audit_result.get('reason', '')}")
            image_prompts = audit_result.get('improved_prompts', image_prompts)
            audit_passed = True
            break
        else:
            st.warning(f"⚠️ 검수 실패 (시도 {audit_attempt + 1}): {audit_result.get('reason', '')}")
            # 수정된 프롬프트로 재시도
            image_prompts = audit_result.get('improved_prompts', image_prompts)
            st.info(f"📝 프롬프트 수정됨: {len(image_prompts)}개")
    
    if not audit_passed:
        st.warning("⚠️ 검수를 통과하지 못했지만, 수정된 프롬프트로 진행합니다.")
    
    # 검수 완료된 프롬프트 저장
    st.session_state.final_data['audited_prompts'] = image_prompts
    st.session_state.progress['audit_img_prompt']['percent'] = 100
    st.session_state.progress['audit_img_prompt']['status'] = 'complete'
    state_manager.save_state()
    
    # 4-3. 이미지 생성
    st.session_state.progress['generate_images']['status'] = 'active'
    st.session_state.progress['generate_images']['percent'] = 30
    
    # [Telegram] Start Notification
    try: telegram_notifier.send_message("🎨 [4/5] 이미지 생성을 시작합니다 (예상 소요시간: 2~3분)...")
    except: pass
    
    try:
        # [UI] Status Container 사용
        with st.status("🎨 Generating images...", expanded=True) as status:
            post = st.session_state.final_data.get('post')
            
            # Progress Callback Definition
            def image_progress_callback(current, total):
                status.update(label=f"🎨 Generating images... ({current}/{total})")
                st.write(f"✅ Image {current}/{total} generated.")
                # 텔레그램 중간 알림 (너무 자주 보내면 시끄러울 수 있으니 2장마다 or 마지막에?)
                # 사용자 요청: "불안하지 않게" -> 매장마다 보내자.
                try: telegram_notifier.send_message(f"🎨 이미지 생성 중... ({current}/{total})")
                except: pass

            if "FOOD" in str(category):
                # FOOD 모드: 템플릿 기반 생성
                images = image_utils.generate_images_from_template(topic, callback=image_progress_callback)
            else:
                # 검수된 프롬프트 사용
                prompts = st.session_state.final_data.get('audited_prompts', image_prompts)
                images = image_utils.generate_images_hybrid(prompts, callback=image_progress_callback)
            
            if not images or len(images) == 0:
                raise Exception("No images generated")
            
            status.update(label="✅ All images generated!", state="complete", expanded=False)
            
            st.session_state.final_data['images'] = images
            st.success(f"✅ 이미지 {len(images)}장 생성 완료")
            st.session_state.progress['generate_images']['percent'] = 100
            st.session_state.progress['generate_images']['status'] = 'complete'
            
            # [Telegram] Complete Notification
            try: telegram_notifier.send_message(f"✅ [4/5] 이미지 {len(images)}장 생성 완료")
            except: pass
            
            # 자동 승인 모드 vs 수동 승인 모드
            if auto_approve:
                # 자동 승인: 텔레그램 승인 없이 바로 업로드
                st.info("⚡ 자동 승인 모드 - 승인 없이 바로 업로드합니다")
                st.session_state.progress['telegram_report']['status'] = 'complete'
                st.session_state.progress['telegram_report']['percent'] = 100
                st.session_state.progress['approval']['status'] = 'complete'
                st.session_state.progress['approval']['percent'] = 100
                try: telegram_notifier.send_message("⚡ [자동 승인] 검토 없이 자동 업로드를 진행합니다...")
                except: pass
            else:
                # 수동 승인: 이메일 + 텔레그램 승인 요청 전송
                st.session_state.progress['telegram_report']['status'] = 'active'
                st.session_state.progress['telegram_report']['percent'] = 50
                
                if post and post.get('title'):
                    # 1. 이메일 승인 요청 (새로 추가)
                    app_url = os.getenv("STREAMLIT_APP_URL", "https://sunshine-blog.streamlit.app")
                    email_notifier.send_approval_email(
                        title=post['title'],
                        topic=st.session_state.final_data['topic'],
                        preview_html=post.get('content_html', '')[:500],
                        images=images[:3],
                        app_url=app_url
                    )
                    st.info("📧 승인 요청 이메일을 발송했습니다. 이메일을 확인해주세요!")
                    
                    # 2. 텔레그램도 함께 전송 (기존 유지)
                    telegram_notifier.send_telegram_notification(
                        post['title'],
                        st.session_state.final_data['topic'],
                        images
                    )
                
                st.session_state.progress['telegram_report']['percent'] = 100
                st.session_state.progress['telegram_report']['status'] = 'complete'
                st.session_state.progress['approval']['status'] = 'active'
                st.session_state.progress['approval']['percent'] = 50
                
                # 이메일 승인 대기 (Step 5로 이동하지 않고 대기)
                st.warning("⏳ 이메일 또는 텔레그램에서 승인을 기다리는 중...")
                st.session_state.pipeline['step'] = 5  # 승인 대기 상태로 변경
                state_manager.save_state()
                time.sleep(1)
                st.rerun()
        
        time.sleep(0.5)
        st.session_state.pipeline['step'] = 6
        st.rerun()
        
    except Exception as e:
        st.session_state.progress['generate_images']['status'] = 'error'
        state_manager.save_state()
        
        st.error(f"❌ 이미지 생성 중 에러 발생")
        with st.expander("🚨 System Logs (Debug Info)", expanded=True):
            st.code(str(e), language="bash")
            st.warning("위 에러 메시지를 캡처해서 개발자에게 보내주세요.")

        try: telegram_notifier.send_message(f"🚨 [오류] 이미지 생성 실패: {str(e)}")
        except: pass
        st.stop()

elif step == 5:
    # 승인 대기 중
    st.markdown("### ⏳ 승인 대기 중...")
    st.info("📧 이메일 또는 📱 텔레그램에서 [승인] 버튼을 클릭해주세요.")
    
    # 이메일 승인 확인
    if st.session_state.get('email_approved'):
        st.success("✅ 이메일에서 승인되었습니다! 업로드를 진행합니다...")
        st.session_state.progress['approval']['status'] = 'complete'
        st.session_state.progress['approval']['percent'] = 100
        st.session_state.email_approved = False  # 리셋
        st.session_state.pipeline['step'] = 6
        state_manager.save_state()
        time.sleep(1)
        st.rerun()
    
    # 이메일 거절 확인
    if st.session_state.get('email_rejected'):
        st.error("❌ 이메일에서 거절되었습니다. 워크플로우를 종료합니다.")
        st.session_state.email_rejected = False
        st.session_state.pipeline['step'] = 0
        state_manager.save_state()
        st.stop()
    
    # 텔레그램 승인 확인 (기존 로직)
    if st.session_state.get('auto_upload_triggered'):
        st.success("✅ 텔레그램에서 승인되었습니다!")
        st.session_state.progress['approval']['status'] = 'complete'
        st.session_state.progress['approval']['percent'] = 100
        st.session_state.pipeline['step'] = 6
        state_manager.save_state()
        time.sleep(1)
        st.rerun()
    
    # [NEW] 웹에서 바로 승인 버튼
    if st.button("✅ 웹에서 바로 승인 (Direct Approve)", type="primary", use_container_width=True):
        st.success("✅ 웹에서 승인되었습니다! 업로드를 진행합니다...")
        st.session_state.auto_upload_triggered = True
        state_manager.save_state()
        time.sleep(0.5)
        st.rerun()

    # 수동 확인 버튼
    if st.button("🔄 승인 상태 확인 (텔레그램/이메일)"):
        st.rerun()
    
    # 자동 새로고침 (bot_listener가 처리하므로 여기서는 짧게 대기)
    time.sleep(2)
    st.rerun()

# --- [8] 결과 화면 ---
if step >= 6:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎨 Generated Content</div>', unsafe_allow_html=True)
    
    # ======= 추가: 워크플로우 산출물 표시 =======
    with st.expander("🔍 Step 1: Research Outputs", expanded=False):
        if st.session_state.final_data.get('topic'):
            st.success(f"**선정된 주제**: {st.session_state.final_data['topic']}")
        if st.session_state.final_data.get('food_prompt'):
            st.info(f"**음식 프롬프트**: {st.session_state.final_data['food_prompt']}")
    
    with st.expander("✍️ Step 2: Content Generation Details", expanded=False):
        post = st.session_state.final_data.get('post')
        if post and isinstance(post, dict):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Content Length", f"{len(post.get('content_html', ''))} chars")
            with col2:
                st.metric("Keywords", len(post.get('hashtags', [])))
            
            st.write("**Hashtags**:")
            st.write(", ".join(post.get('hashtags', [])))
            
            if post.get('image_prompts'):
                st.write("**Image Prompts**:")
                for idx, prompt in enumerate(post['image_prompts'], 1):
                    st.text(f"{idx}. {prompt}")
    
    with st.expander("🎨 Step 4: Image Generation", expanded=False):
        images = st.session_state.final_data.get('images', [])
        if images:
            st.success(f"**생성된 이미지**: {len(images)}장")
            for idx, img_path in enumerate(images, 1):
                st.text(f"{idx}. {os.path.basename(img_path)}")
        else:
            st.warning("이미지 미생성")
    # ======= 산출물 표시 끝 =======
    
    images = st.session_state.final_data.get('images', [])
    if images:
        cols = st.columns(len(images))
        for idx, (col, img_path) in enumerate(zip(cols, images)):
            with col:
                try:
                    img = Image.open(img_path)
                    st.image(img, use_container_width=True)
                except:
                    st.error(f"이미지 로드 실패: {img_path}")
    
    post = st.session_state.final_data.get('post')
    if post and isinstance(post, dict):
        st.markdown(f"### {post.get('title', 'Untitled')}")
        
        # 전체 텍스트 표시
        content_html = post.get('content_html', '')
        if content_html:
            st.markdown("**📝 Generated Content:**")
            # HTML 태그 제거하고 텍스트만 표시
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content_html, 'html.parser')
            text_content = soup.get_text()
            st.text_area("Content Preview", text_content, height=300)
            
            with st.expander("📄 View Full HTML Source"):
                st.code(content_html, language='html')
            
            st.info(f"📊 Content Length: {len(text_content)} characters | {len(content_html)} bytes")
    else:
        st.warning("⚠️ 콘텐츠 데이터가 없습니다. 워크플로우를 다시 실행해주세요.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 배포 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📡 DEPLOY TO WORDPRESS") and post and isinstance(post, dict):
            update_progress('upload_wordpress', 50, 'active', do_rerun=False)
            
            with st.spinner("Deploying to WordPress..."):
                try:
                    wp_client = wordpress.WordPressClient()
                    post_url = wp_client.upload_post(
                        post['title'], 
                        post['content_html'], 
                        post['hashtags'],
                        image_paths=st.session_state.final_data.get('images', [])
                    )
                    
                    if post_url:
                        update_progress('upload_wordpress', 100, 'complete', do_rerun=False)
                        st.balloons()
                        st.success(f"✅ Successfully deployed to WordPress! [View Post]({post_url})")
                        
                        # 구글 시트 아카이빙
                        update_progress('archive_sheets', 50, 'active', do_rerun=False)
                        
                        try:
                            success = g_sheet_archiver.archive_post(
                                post['title'], 
                                post['content_html'], 
                                post_url, 
                                st.session_state.final_data['topic']
                            )
                            
                            if success:
                                update_progress('archive_sheets', 100, 'complete', do_rerun=False)
                                st.success("✅ Archived to Google Sheets!")
                            else:
                                st.error("❌ Google Sheets archiving failed. Check logs.")
                                
                        except Exception as e:
                            st.warning(f"⚠️ Google Sheets archiving failed: {e}")
                        
                        st.session_state.pipeline['step'] = 7
                    else:
                        st.error("❌ WordPress deployment failed. Check logs.")
                except Exception as e:
                    st.error(f"❌ Deployment Error: {e}")
    
    with col2:
        if st.button("🔄 RESET"):
            st.session_state.pipeline['step'] = 0
            for key in st.session_state.progress:
                st.session_state.progress[key] = {'status': 'pending', 'percent': 0}
            st.rerun()

# --- [9] 갤러리 ---
st.markdown('<div class="section-title">🖼️ Recent Gallery</div>', unsafe_allow_html=True)
files = glob.glob("images/*.png")
files.sort(key=os.path.getmtime, reverse=True)
cols = st.columns(6)
for i, f in enumerate(files[:12]):
    with cols[i % 6]:
        st.markdown('<div class="gallery-item">', unsafe_allow_html=True)
        st.image(f, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [NEW] 자동 새로고침 (봇 명령 감지용) ---
bot_listener.auto_refresh_if_idle()

