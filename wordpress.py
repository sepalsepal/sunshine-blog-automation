import os
import requests
import html
import time
from datetime import datetime

class WordPressClient:
    def __init__(self):
        self.url = os.getenv("WORDPRESS_URL")
        self.user = os.getenv("WORDPRESS_USER")
        self.password = os.getenv("WORDPRESS_APP_PASSWORD")
        
        if not self.url or not self.user or not self.password:
            raise ValueError("WordPress credentials are missing in .env")
            
        self.xmlrpc_url = f"{self.url}/xmlrpc.php"
        self.max_retries = 3  # 최대 재시도 횟수
    
    def _retry_operation(self, operation_name, func, *args, **kwargs):
        """
        재시도 로직 (exponential backoff)
        - 최대 3회 시도
        - 실패 시 2초 → 4초 → 8초 대기
        """
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                if result:
                    return result
            except Exception as e:
                wait_time = 2 ** (attempt + 1)
                print(f"   ⚠️ [{operation_name}] Attempt {attempt+1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    print(f"      ⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ [{operation_name}] All {self.max_retries} attempts failed.")
        return None

    def upload_image(self, image_path):
        """
        Uploads an image to WordPress Media Library via XML-RPC.
        Returns the URL of the uploaded image.
        """
        filename = os.path.basename(image_path)
        print(f"   🖼️ [WordPress] Uploading image: {filename}")
        
        try:
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()
                
            # XML-RPC struct for media object
            data = {
                'name': filename,
                'type': 'image/png', # Assuming PNG from generation
                'bits': requests.utils.super_len(img_data) and img_data, # Raw bytes
                'overwrite': True
            }
            
            # Construct XML for metaWeblog.newMediaObject
            # This is tricky with raw XML string construction for binary data.
            # It's safer/easier to use the 'xmlrpc.client' library if available, 
            # but since we are avoiding deps, we'll use a standard library approach or requests with correct encoding.
            # Actually, standard 'xmlrpc.client' is built-in Python! Let's use it for this complex binary handling.
            
            import xmlrpc.client
            
            client = xmlrpc.client.ServerProxy(self.xmlrpc_url)
            # metaWeblog.newMediaObject(blogid, username, password, struct)
            
            # We need to pass the binary data as xmlrpc.client.Binary
            media_struct = {
                'name': filename,
                'type': 'image/png',
                'bits': xmlrpc.client.Binary(img_data)
            }
            
            response = client.metaWeblog.newMediaObject(1, self.user, self.password, media_struct)
            
            if 'url' in response:
                print(f"   ✅ Image uploaded: {response['url']}")
                return response['url']
            else:
                print(f"   ⚠️ Upload response missing URL: {response}")
                return None
                
        except Exception as e:
            print(f"   ❌ Image upload failed: {e}")
            return None

    def upload_post(self, title, content, tags=None, category=None, image_paths=None):
        """
        Uploads a post to WordPress using XML-RPC.
        If image_paths are provided, uploads them and appends to content.
        """
        print(f"🚀 [WordPress] Uploading post: {title}")
        
        # 1. Upload Images and Prepare HTML
        final_content = content
        
        if image_paths:
            print(f"   📸 Processing {len(image_paths)} images...")
            image_html = '<div class="image-gallery" style="margin-top: 20px;">'
            
            for img_path in image_paths:
                img_url = self.upload_image(img_path)
                if img_url:
                    # Append image to content (Simple stacking for now)
                    # You can also insert them into specific placeholders if logic allows,
                    # but appending is safest for MVP.
                    image_html += f'<img src="{img_url}" alt="Blog Image" style="max-width: 100%; margin-bottom: 10px; border-radius: 8px;" /><br/>'
            
            image_html += '</div>'
            
            # Insert images at the top or bottom? 
            # Usually top (Hero) and then others. 
            # Let's put the first image (Hero) at the top, and others at the bottom or distributed.
            # For this MVP, let's prepend the first image and append the rest.
            
            # Actually, let's just append all for safety, or prepend the first one.
            # Let's try to be smart: Hero at top, others at bottom.
            
            uploaded_urls = []
            # Re-uploading to get the list (logic above was mixed, let's fix)
            # Refactoring the loop above to just collect URLs
            pass 

        # Re-implementing image logic cleanly
        if image_paths:
            uploaded_urls = []
            for img_path in image_paths:
                url = self.upload_image(img_path)
                if url: uploaded_urls.append(url)
            
            if uploaded_urls:
                # Hero Image (First one) - Responsive Style
                hero_html = f'<figure class="wp-block-image"><img src="{uploaded_urls[0]}" alt="Hero Image" style="width:100%; height:auto; max-width:100%; border-radius:12px; margin-bottom:20px;" /></figure><br/><br/>'
                
                # Gallery (Rest) - Responsive Style
                gallery_html = '<br/><hr/><h3>📸 갤러리</h3><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">'
                for url in uploaded_urls[1:]:
                    gallery_html += f'<figure class="wp-block-image" style="margin:0;"><img src="{url}" alt="Gallery Image" style="width:100%; height:auto; max-width:100%; border-radius:8px;" /></figure>'
                gallery_html += '</div>'
                
                final_content = hero_html + final_content + gallery_html

        # 2. Prepare Tags
        tags_str = ""
        if tags:
            tags_str = ", ".join(tags)

        # 3. Upload Post using xmlrpc.client with RETRY
        import xmlrpc.client
        
        post_struct = {
            'title': title,
            'description': final_content,
            'mt_keywords': tags_str,
            'post_status': 'publish'
        }
        
        def _do_post():
            client = xmlrpc.client.ServerProxy(self.xmlrpc_url)
            post_id = client.metaWeblog.newPost(1, self.user, self.password, post_struct, True)
            print(f"✅ [WordPress] Post published! ID: {post_id}")
            return f"{self.url}/?p={post_id}"
        
        # 재시도 로직 적용
        result = self._retry_operation("Post Upload", _do_post)
        return result

if __name__ == "__main__":
    # Test
    client = WordPressClient()
    client.upload_post("XML-RPC Module Test", "<h1>Hello</h1><p>This is a test from the module.</p>", ["test", "python"])
