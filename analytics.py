import os
from datetime import datetime, timedelta
import blogger

def get_blog_stats(days=1):
    """Get blog statistics for the last N days."""
    try:
        service = blogger.get_service()
        blog_id = blogger.get_blog_id(service)
        
        if not blog_id:
            return None
        
        # Get recent posts
        posts = service.posts().list(
            blogId=blog_id,
            maxResults=10,
            orderBy='published',
            status='live'
        ).execute()
        
        if 'items' not in posts:
            return {
                'total_posts': 0,
                'recent_posts': [],
                'message': '발행된 포스트가 없습니다.'
            }
        
        # Calculate stats
        recent_posts = []
        for post in posts['items'][:days]:
            post_info = {
                'title': post['title'],
                'url': post['url'],
                'published': post['published'],
                # Note: Blogger API doesn't provide view counts directly
                # You would need Google Analytics integration for detailed stats
            }
            recent_posts.append(post_info)
        
        stats = {
            'total_posts': len(posts['items']),
            'recent_posts': recent_posts,
            'blog_url': f"https://dogisourfriends.blogspot.com",
            'generated_at': datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        print(f"[Analytics] Error getting stats: {e}")
        return None

def format_stats_message(stats):
    """Format stats into a readable message."""
    if not stats:
        return "📊 통계를 가져올 수 없습니다."
    
    message = f"📊 **일일 블로그 리포트**\n\n"
    message += f"🕐 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    if stats.get('recent_posts'):
        message += f"📝 **최근 발행 포스트** ({len(stats['recent_posts'])}개):\n\n"
        for i, post in enumerate(stats['recent_posts'], 1):
            pub_date = datetime.fromisoformat(post['published'].replace('Z', '+00:00'))
            message += f"{i}. {post['title']}\n"
            message += f"   🔗 {post['url']}\n"
            message += f"   📅 {pub_date.strftime('%Y-%m-%d %H:%M')}\n\n"
    else:
        message += stats.get('message', '포스트가 없습니다.')
    
    message += f"\n🌐 블로그: {stats.get('blog_url', 'N/A')}"
    
    return message

if __name__ == "__main__":
    stats = get_blog_stats()
    print(format_stats_message(stats))
