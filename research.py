import feedparser
from pytrends.request import TrendReq
import random

def get_trending_dog_topics():
    """
    Fetches trending dog-related topics using Google Trends and Google News.
    Returns a list of topic strings.
    """
    topics = []
    
    # 1. Google Trends (Broad search)
    try:
        pytrends = TrendReq(hl='ko-KR', tz=540) # Korea timezone
        kw_list = ["강아지", "반려견", "애견"]
        pytrends.build_payload(kw_list, cat=0, timeframe='now 7-d', geo='KR', gprop='')
        related_queries = pytrends.related_queries()
        
        for kw in kw_list:
            if related_queries[kw]['top'] is not None:
                top_queries = related_queries[kw]['top']['query'].tolist()
                topics.extend(top_queries[:3]) # Take top 3 from each
            
            if related_queries[kw]['rising'] is not None:
                rising_queries = related_queries[kw]['rising']['query'].tolist()
                topics.extend(rising_queries[:3])
                
    except Exception as e:
        print(f"Warning: Google Trends API failed: {e}")

    # 2. Google News RSS (Fallback/Supplement)
    try:
        # Search for "반려견" in Google News Korea
        rss_url = "https://news.google.com/rss/search?q=반려견+when:7d&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries[:5]:
            topics.append(entry.title)
            
    except Exception as e:
        print(f"Warning: Google News RSS failed: {e}")
    
    # 3. Naver Blog Search (Third source)
    try:
        # Naver Blog RSS for dog-related content
        naver_url = "https://search.naver.com/search.naver?where=rss&query=강가지"
        naver_feed = feedparser.parse(naver_url)
        
        for entry in naver_feed.entries[:5]:
            topics.append(entry.title)
            
    except Exception as e:
        print(f"Warning: Naver Blog RSS failed: {e}")
        
    # Deduplicate and clean
    unique_topics = list(set(topics))
    
    # If nothing found, provide fallbacks
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
