import json
import os
from datetime import datetime
import research
import content
import blogger
import image_utils

class ContentManager:
    def __init__(self):
        self.pending_file = "pending_posts.json"
        
    def generate_content(self, topic=None, category=None):
        """Generate a new blog post content."""
        print("[ContentManager] Generating new content...")
        
        # 1. Research topic (if not provided and not category-specific)
        if not topic and not category:
            topics = research.get_trending_dog_topics()
            topic = research.select_topic(topics)
        
        print(f"[ContentManager] Selected topic: {topic}, Category: {category}")
        
        # 2. Generate content with Gemini
        post_json = content.generate_blog_post(topic, category)
        
        if not post_json:
            return None
            
        try:
            post_data = json.loads(post_json)
            post_data['topic'] = topic
            post_data['created_at'] = datetime.now().isoformat()
            post_data['id'] = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            
            return post_data
        except json.JSONDecodeError:
            print("[ContentManager] Failed to parse JSON from Gemini")
            return None
    
    def save_pending(self, post_data):
        """Save post to pending list."""
        pending = self.load_pending()
        pending[post_data['id']] = post_data
        
        with open(self.pending_file, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=2)
        
        print(f"[ContentManager] Saved pending post: {post_data['id']}")
        return post_data['id']
    
    def load_pending(self):
        """Load pending posts."""
        if os.path.exists(self.pending_file):
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_pending(self, post_id):
        """Get a specific pending post."""
        pending = self.load_pending()
        return pending.get(post_id)
    
    def remove_pending(self, post_id):
        """Remove a pending post."""
        pending = self.load_pending()
        if post_id in pending:
            del pending[post_id]
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                json.dump(pending, f, ensure_ascii=False, indent=2)
            print(f"[ContentManager] Removed pending post: {post_id}")
            return True
        return False
    
    def publish_post(self, post_id):
        """Publish a pending post to Blogger."""
        post_data = self.get_pending(post_id)
        if not post_data:
            print(f"[ContentManager] Post {post_id} not found")
            return None
        
        print(f"[ContentManager] Publishing post: {post_data['title']}")
        
        # Publish to Blogger
        service = blogger.get_service()
        blog_id = blogger.get_blog_id(service)
        
        if not blog_id:
            print("[ContentManager] No blog found")
            return None
            
        print(f"[ContentManager] Blog ID: {blog_id}")
        
        # footer = "<br><hr><p><i>이 글은 AI에 의해 자동으로 작성되었습니다.</i></p>"
        footer = ""
        
        # Embed AI-generated images
        final_content = post_data['content']
        # Use ai_image_urls if available, otherwise fallback to single url
        image_urls = post_data.get('ai_image_urls') or post_data.get('ai_image_url')
        if image_urls:
            final_content = image_utils.embed_image_in_content(final_content, image_urls)
        
        final_content = final_content + footer
        
        result = blogger.create_post(
            service, 
            blog_id, 
            post_data['title'], 
            final_content, 
            post_data.get('tags', [])
        )
        
        if result:
            self.remove_pending(post_id)
            print(f"[ContentManager] Successfully published: {result['url']}")
            return result['url']
        else:
            print(f"[ContentManager] Failed to publish post {post_id}. Result was None.")
        
        return None

if __name__ == "__main__":
    manager = ContentManager()
    post = manager.generate_content()
    if post:
        post_id = manager.save_pending(post)
        print(f"Saved as: {post_id}")
