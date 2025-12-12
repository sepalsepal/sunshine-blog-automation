import streamlit as st
import time

# --- [1] Configuration (Lightweight) ---
st.set_page_config(
    page_title="Sunshine Studio", 
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
    
    # 3. Empty State
    st.markdown("""
    <div style="display:flex; justify-content:center; align-items:center; height:60vh; flex-direction:column; color:#8B949E;">
        <div style="font-size:3rem; margin-bottom:1rem;">🎨</div>
        <div style="font-size:1.2rem;">Start creating by describing your idea below.</div>
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
            
        # --- LAZY LOGIC EXECUTION ---
        if start_btn and topic_input:
            st.info("🚀 Starting workflow... (Loading modules)")
            
            # [CRITICAL] Lazy Import Here!
            # Only import heavy modules when the user actually clicks the button
            import workflow_manager
            
            # Initialize Manager
            wm = workflow_manager.WorkflowManager()
            st.session_state.final_data = {'topic': topic_input}
            wm.set_step(1)
            wm.rerun()

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
