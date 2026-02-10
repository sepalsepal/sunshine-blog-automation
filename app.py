import streamlit as st
import time

# --- [1] Configuration (Lightweight) ---
st.set_page_config(
    page_title="Sunshine Studio v2.4", 
    page_icon="🎨", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- [2] CSS Styling (Pure Design) ---
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
        
        /* Inputs */
        .stTextInput > div > div > input {
            background-color: #0D1117;
            color: white;
            border-color: #30363D;
        }

        /* Bento Grid */
        .bento-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(2, 1fr);
            gap: 1.5rem;
            padding: 2rem 5%;
            max-width: 1200px;
            margin: 0 auto;
            height: 60vh;
        }
        
        .bento-card {
            background: rgba(22, 27, 34, 0.6);
            border: 1px solid #30363D;
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
            position: relative;
            overflow: hidden;
        }
        
        .bento-card:hover {
            border-color: #58A6FF;
            background: rgba(22, 27, 34, 0.8);
            transform: translateY(-2px);
        }
        
        .card-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            background: rgba(255,255,255,0.05);
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
        }
        
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #FFFFFF;
            margin-bottom: 0.5rem;
        }
        
        .card-desc {
            font-size: 0.9rem;
            color: #8B949E;
            line-height: 1.4;
        }
        
        .card-visuals {
            grid-column: span 2;
            grid-row: span 2;
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.8) 0%, rgba(35, 134, 54, 0.1) 100%);
        }
        
        .step-badge {
            display: inline-block;
            padding: 2px 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            font-size: 0.7rem;
            color: #8B949E;
            margin-right: 5px;
            margin-bottom: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- [3] State Management (Minimal) ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'workflow'

# --- [4] Sidebar Navigation ---
with st.sidebar:
    st.markdown("### Manager")
    st.caption("Admin Dashboard")
    
    view_options = ["Go to Studio", "Generation History", "API Management"]
    view_map = {"workflow": 0, "gallery": 1, "api_management": 2}
    reverse_map = {0: "workflow", 1: "gallery", 2: "api_management"}
    
    current_index = view_map.get(st.session_state.view_mode, 0)
    
    nav_index = st.radio(
        "Navigation", 
        range(len(view_options)),
        format_func=lambda x: view_options[x],
        index=current_index,
        label_visibility="collapsed"
    )
    
    new_view_mode = reverse_map[nav_index]
    if st.session_state.view_mode != new_view_mode:
        st.session_state.view_mode = new_view_mode
        st.rerun()
        
    st.markdown("---")
    st.caption("v2.3 (Lazy Load Architecture)")

# --- [5] Main Content Routing ---

# A. Studio (Workflow) Mode
if st.session_state.view_mode == 'workflow':
    # Initialize step
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = {'step': 0}
    step = st.session_state.pipeline['step']

    # 1. Background
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
    
    # 3. Main Content Area (Bento Grid Dashboard)
    if step == 0:
        st.markdown("""
        <div class="bento-container">
            <div class="bento-card">
                <div><div class="card-icon">🔍</div><div class="card-title">Research</div><div class="card-desc">Analyze Google Trends and YouTube for high-traffic keywords.</div></div>
                <div style="margin-top:1rem;"><span class="step-badge">Trend Analysis</span><span class="step-badge">Keyword Mining</span></div>
            </div>
            <div class="bento-card">
                <div><div class="card-icon">✍️</div><div class="card-title">Content Engine</div><div class="card-desc">Generate SEO-optimized drafts with structured headings.</div></div>
                <div style="margin-top:1rem;"><span class="step-badge">Gemini 2.0</span><span class="step-badge">Markdown</span></div>
            </div>
            <div class="bento-card card-visuals">
                <div><div class="card-icon">🎨</div><div class="card-title">Visual Studio</div><div class="card-desc">Create stunning, high-fidelity images using Imagen 3 and Nano Banana Pro models. Supports 2K/4K upscaling.</div></div>
                <div style="margin-top:auto; text-align:right;"><div style="font-size:4rem; opacity:0.1;">🖼️</div></div>
            </div>
            <div class="bento-card">
                <div><div class="card-icon">🚀</div><div class="card-title">Publishing</div><div class="card-desc">Automated upload to WordPress and Google Sheets archiving.</div></div>
                <div style="margin-top:1rem;"><span class="step-badge">WordPress</span><span class="step-badge">Sheets</span></div>
            </div>
            <div class="bento-card">
                <div><div class="card-icon">📊</div><div class="card-title">Analytics</div><div class="card-desc">Track performance and engagement metrics.</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 4. Floating Bottom Bar
    with st.container():
        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
        st.markdown("---")
        
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
            
        # --- n8n WEBHOOK INTEGRATION ---
        if start_btn and topic_input:
            try:
                with st.spinner("🚀 Sending job to n8n automation engine..."):
                    import requests
                    
                    # n8n Webhook URL (Test Mode)
                    N8N_WEBHOOK_URL = "http://localhost:5678/webhook-test/3b7f98ba-fdd1-45f2-b0f6-429a1a9febac"
                    
                    payload = {
                        "topic": topic_input,
                        "timestamp": time.time(),
                        "source": "Sunshine Studio v2.4"
                    }
                    
                    response = requests.post(N8N_WEBHOOK_URL, json=payload)
                    
                    if response.status_code == 200:
                        st.success(f"✅ Job sent successfully! Check your n8n dashboard.")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed to send to n8n. Status: {response.status_code}")
                        st.write(response.text)
                        
            except Exception as e:
                st.error(f"❌ Connection Error: {str(e)}")
                st.exception(e)

# B. Gallery Mode
elif st.session_state.view_mode == 'gallery':
    # Lazy import view
    from views import gallery
    gallery.render()

# C. API Management Mode
elif st.session_state.view_mode == 'api_management':
    # Lazy import view
    from views import api_management
    api_management.render()
