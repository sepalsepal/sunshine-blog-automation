import feedparser
from pytrends.request import TrendReq
import random

def search_google_trends(keywords=["강아지", "반려견", "애견"]):
    """
    Google Trends에서 관련 검색어 수집
    Returns: dict with 'top_queries' and 'rising_queries'
    """
    result = {
        "source": "Google Trends",
        "keywords_searched": keywords,
        "top_queries": [],
        "rising_queries": [],
        "status": "pending"
    }
    
    try:
        pytrends = TrendReq(hl='ko-KR', tz=540)
        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='KR', gprop='')
        related_queries = pytrends.related_queries()
        
        for kw in keywords:
            if related_queries[kw]['top'] is not None:
                top = related_queries[kw]['top']['query'].tolist()[:5]
                result['top_queries'].extend(top)
            
            if related_queries[kw]['rising'] is not None:
                rising = related_queries[kw]['rising']['query'].tolist()[:5]
                result['rising_queries'].extend(rising)
        
        result['status'] = "complete"
        print(f"✅ [Trends] Found {len(result['top_queries'])} top, {len(result['rising_queries'])} rising")
        
    except Exception as e:
        result['status'] = "error"
        result['error'] = str(e)
        print(f"❌ [Trends] Failed: {e}")
    
    return result


def search_youtube(query):
    """
    YouTube 검색 시뮬레이션 (실제 API는 별도 필요)
    Returns: dict with search results
    """
    result = {
        "source": "YouTube",
        "query": query,
        "suggested_videos": [
            f"[영상] {query} 완벽 가이드",
            f"[영상] 수의사가 알려주는 {query}",
            f"[영상] {query} 먹방 리뷰"
        ],
        "status": "complete"
    }
    print(f"✅ [YouTube] Simulated search: {query}")
    return result


def search_naver_blog(query):
    """
    네이버 블로그 RSS 검색
    Returns: dict with blog titles
    """
    result = {
        "source": "Naver Blog",
        "query": query,
        "blog_titles": [],
        "status": "pending"
    }
    
    try:
        naver_url = f"https://search.naver.com/search.naver?where=rss&query={query}"
        naver_feed = feedparser.parse(naver_url)
        
        for entry in naver_feed.entries[:5]:
            result['blog_titles'].append(entry.title)
        
        result['status'] = "complete"
        print(f"✅ [Naver] Found {len(result['blog_titles'])} blogs")
        
    except Exception as e:
        result['status'] = "error"
        result['error'] = str(e)
        print(f"❌ [Naver] Failed: {e}")
    
    return result


def combine_research(trends_data, youtube_data, blog_data):
    """
    모든 리서치 결과를 종합
    Returns: dict with combined keywords and selected topic
    """
    all_keywords = []
    
    # Collect from all sources
    all_keywords.extend(trends_data.get('top_queries', []))
    all_keywords.extend(trends_data.get('rising_queries', []))
    all_keywords.extend(blog_data.get('blog_titles', []))
    
    # Deduplicate
    unique_keywords = list(set(all_keywords))[:10]
    
    result = {
        "source": "Combined",
        "total_keywords": len(unique_keywords),
        "selected_keywords": unique_keywords,
        "status": "complete"
    }
    
    print(f"✅ [Combine] Total {len(unique_keywords)} unique keywords")
    return result


def get_trending_dog_topics():
    """
    Fetches trending dog-related topics using Google Trends and Google News.
    Returns a list of topic strings. (Legacy function for backward compatibility)
    """
    trends = search_google_trends()
    blog = search_naver_blog("강아지")
    
    topics = []
    topics.extend(trends.get('top_queries', []))
    topics.extend(trends.get('rising_queries', []))
    topics.extend(blog.get('blog_titles', []))
    
    unique_topics = list(set(topics))
    
    if not unique_topics:
        unique_topics = [
            "강아지 산책 꿀팁",
            "반려견 건강 관리",
            "강아지 간식 만들기",
            "반려견 훈련 방법",
            "강아지 분리불안 해결"
        ]
        
    print(f"Found topics: {unique_topics}")
    return unique_topics

def select_topic(topics):
    """Selects a random topic from the list."""
    if not topics:
        return "강아지 행복하게 해주는 방법"
    return random.choice(topics)

if __name__ == "__main__":
    topics = get_trending_dog_topics()
    print(f"Selected Topic: {select_topic(topics)}")
