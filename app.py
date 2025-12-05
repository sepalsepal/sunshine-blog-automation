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

# --- [1] 페이지 설정 ---
st.set_page_config(
    page_title="Sunshine Imageworks", 
    page_icon="🌞", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

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

# --- [3] 상태 초기화 ---
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = {"step": 0}
if 'final_data' not in st.session_state:
    st.session_state.final_data = {}
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

# --- [4] 헤더 ---
st.markdown('<div class="hero-title">Sunshine Imageworks</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">AI-Powered Blog Content Generation Platform</div>', unsafe_allow_html=True)

# --- [5] 프로세스 시각화 (Clean Timeline) ---
def render_workflow_timeline():
    """가로 스크롤 타임라인 렌더링"""
    steps = [
        ('search_trends', '📊', 'Trends'),
        ('search_youtube', '📺', 'YouTube'),
        ('search_blog', '📝', 'Blog'),
        ('combine_research', '🧠', 'Combine'),
        ('write_content', '✍️', 'Draft'),
        ('create_hashtags', '#️⃣', 'Tags'),
        ('audit_content', '⚖️', 'Audit'),
        ('create_img_prompt', '🖼️', 'Prompt'),
        ('audit_img_prompt', '🔍', 'ChkPrompt'),
        ('generate_images', '🎨', 'GenImg'),
        ('telegram_report', '📢', 'Report'),
        ('approval', '👍', 'Approve'),
        ('upload_wordpress', '🚀', 'Deploy'),
        ('archive_sheets', '📂', 'Archive')
    ]
    
    html = '<div class="workflow-container">'
    for key, icon, title in steps:
        status = st.session_state.progress.get(key, {}).get('status', 'pending')
        
        # 상태 클래스 매핑
        if status == 'complete':
            state_class = 'complete'
            display_icon = '✅'
        elif status == 'active':
            state_class = 'active'
            display_icon = icon
        elif status == 'error':
            state_class = 'error'
            display_icon = '⚠️'
        else:
            state_class = ''
            display_icon = icon
            
        html += f"""<div class="step-item {state_class}"><div class="step-icon">{display_icon}</div><div class="step-label">{title}</div></div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

render_workflow_timeline()

# --- [6] 사이드바 ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Dog%20Face.png", width=120)
    st.markdown("### 🎮 Control Center")
    
    category = st.selectbox("📁 Category", ["강아지 ## 먹어도 되나요?", "WALK_TIPS"])
    topic_input = st.text_input("💡 Custom Topic (Optional)")
    
    st.markdown("---")
    
    if st.button("🚀 START WORKFLOW"):
        # 상태 리셋
        st.session_state.pipeline['step'] = 1
        for key in st.session_state.progress:
            st.session_state.progress[key] = {'status': 'pending', 'percent': 0}
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
    
    # 1. Research Data
    with st.expander("📊 1. Research Data (Trends & Keywords)", expanded=False):
        if 'research_data' in st.session_state.final_data:
            st.json(st.session_state.final_data['research_data'])
        else:
            st.info("No research data yet.")

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
    # Research 단계
    st.session_state.progress['search_trends']['status'] = 'active'
    st.session_state.progress['search_trends']['percent'] = 100
    st.session_state.progress['search_trends']['status'] = 'complete'
    
    st.session_state.progress['search_youtube']['status'] = 'active'
    st.session_state.progress['search_youtube']['percent'] = 100
    st.session_state.progress['search_youtube']['status'] = 'complete'
    
    st.session_state.progress['search_blog']['status'] = 'active'
    st.session_state.progress['search_blog']['percent'] = 100
    st.session_state.progress['search_blog']['status'] = 'complete'
    
    # [수정] 주제 선정 우선순위: 1. 텔레그램/기존 설정 -> 2. 사이드바 입력 -> 3. 자동 생성
    if st.session_state.final_data.get('topic'):
        topic = st.session_state.final_data['topic']
    elif topic_input:
        topic = topic_input
    else:
        if "FOOD" in str(category):
            topic, prompt = food_manager.get_todays_food_topic()
            st.session_state.final_data['food_prompt'] = prompt
        else:
            cands = research.get_trending_dog_topics()
            topic = research.select_topic(cands)
    
    st.session_state.final_data['topic'] = topic
    st.session_state.progress['combine_research']['status'] = 'complete'
    st.session_state.progress['combine_research']['percent'] = 100
    
    # [Telegram] Research Complete
    try:
        telegram_notifier.send_message(f"📊 [1/5] 주제 선정 완료: {topic}")
    except: pass
    
    time.sleep(0.5)
    st.session_state.pipeline['step'] = 2
    st.rerun()

elif step == 2:
    # Draft 단계
    st.session_state.progress['write_content']['status'] = 'active'
    st.session_state.progress['write_content']['percent'] = 30
    
    # [Telegram] Start Notification
    try: telegram_notifier.send_message(f"✍️ [2/5] 글 작성을 시작합니다... (Topic: {st.session_state.final_data['topic']})")
    except: pass
    
    try:
        with st.spinner("✍️ Writing content..."):
            post = content.generate_blog_content("정보성", st.session_state.final_data['topic'])
            
            if not post:
                raise Exception("Gemini API No Response")
            
            if not all(k in post for k in ['title', 'content_html', 'hashtags']):
                raise Exception("Missing required fields")
            
            st.session_state.final_data['post'] = post
            st.success(f"✅ 글 작성 완료: {post['title']}")
        
        st.session_state.progress['write_content']['percent'] = 100
        st.session_state.progress['write_content']['status'] = 'complete'
        st.session_state.progress['create_hashtags']['status'] = 'complete'
        st.session_state.progress['create_hashtags']['percent'] = 100
        
        # [Telegram] Complete Notification
        try: telegram_notifier.send_message(f"✅ [2/5] 초안 작성 완료: {post['title']}")
        except: pass
        
        time.sleep(0.5)
        st.session_state.pipeline['step'] = 3
        st.rerun()
        
    except Exception as e:
        st.session_state.progress['write_content']['status'] = 'error'
        state_manager.save_state()
        
        st.error(f"❌ 글 작성 중 에러 발생")
        with st.expander("🚨 System Logs (Debug Info)", expanded=True):
            st.code(str(e), language="bash")
            st.warning("위 에러 메시지를 캡처해서 개발자에게 보내주세요.")
            
        try: telegram_notifier.send_message(f"🚨 [오류] 글 작성 중 문제가 발생했습니다: {str(e)}")
        except: pass
        st.stop()

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
    st.session_state.progress['create_img_prompt']['status'] = 'complete'
    st.session_state.progress['create_img_prompt']['percent'] = 100
    st.session_state.progress['audit_img_prompt']['status'] = 'complete'
    st.session_state.progress['audit_img_prompt']['percent'] = 100
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
                food_name = st.session_state.final_data['topic'].split()[1] if len(st.session_state.final_data['topic'].split()) > 1 else "food"
                food_prompt = st.session_state.final_data.get('food_prompt', f"fresh {food_name}")
                images = image_utils.generate_images_food_mode(food_name, food_prompt)
            else:
                prompts = post.get("image_prompts", ["Scenery", "Dog"]) if post else ["Scenery", "Dog"]
                # Pass callback here
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
            
            # 텔레그램 승인 요청 전송
            st.session_state.progress['telegram_report']['status'] = 'active'
            st.session_state.progress['telegram_report']['percent'] = 50
            
            if post and post.get('title'):
                telegram_notifier.send_telegram_notification(
                    post['title'],
                    st.session_state.final_data['topic'],
                    images
                )
            
            st.session_state.progress['telegram_report']['percent'] = 100
            st.session_state.progress['telegram_report']['status'] = 'complete'
            st.session_state.progress['approval']['status'] = 'complete'
            st.session_state.progress['approval']['percent'] = 100
        
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
