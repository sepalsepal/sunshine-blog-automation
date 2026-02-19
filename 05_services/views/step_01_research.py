import streamlit as st
import research
import food_manager
import time

def render(wm, topic_input=None, category=None):
    """
    Render Step 1: Research.
    Executes research logic and updates state.
    """
    st.header("📊 Step 1: Research")
    
    # 1-1. Trends 검색
    wm.update_progress('search_trends', 'active')
    wm.save_state()
    
    with st.spinner("📊 Google Trends 검색 중..."):
        trends_data = research.search_google_trends()
    st.session_state.final_data['trends_data'] = trends_data
    wm.update_progress('search_trends', 'complete', 100)
    wm.save_state()
    
    # 1-2. YouTube 검색
    wm.update_progress('search_youtube', 'active')
    wm.save_state()
    
    # 먼저 주제 결정
    if topic_input:
        topic = topic_input
    elif category and "FOOD" in str(category):
        topic, prompt = food_manager.get_todays_food_topic()
        st.session_state.final_data['food_prompt'] = prompt
    else:
        # Trends에서 선택
        all_topics = trends_data.get('top_queries', []) + trends_data.get('rising_queries', [])
        topic = research.select_topic(all_topics) if all_topics else "강아지 건강"
    
    with st.spinner(f"📺 YouTube 검색 중: {topic}..."):
        youtube_data = research.search_youtube(topic)
    st.session_state.final_data['youtube_data'] = youtube_data
    wm.update_progress('search_youtube', 'complete', 100)
    wm.save_state()
    
    # 1-3. 네이버 블로그 검색
    wm.update_progress('search_blog', 'active')
    wm.save_state()
    
    with st.spinner(f"📝 네이버 블로그 검색 중: {topic}..."):
        blog_data = research.search_naver_blog(topic)
    st.session_state.final_data['blog_data'] = blog_data
    wm.update_progress('search_blog', 'complete', 100)
    wm.save_state()
    
    # 1-4. 결과 종합
    wm.update_progress('combine_research', 'active')
    wm.save_state()
    
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
    
    wm.update_progress('combine_research', 'complete', 100)
    wm.save_state()
    
    # [Telegram] Research Complete
    # Note: Telegram notification logic is currently in app.py, 
    # ideally should be moved to a service or here. 
    # For now, we'll leave it to the caller or move it later.
    
    time.sleep(0.3)
    wm.set_step(2)
    wm.rerun()
