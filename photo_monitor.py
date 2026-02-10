import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

class PhotoMonitor:
    def __init__(self, photo_folder="~/Pictures"):
        """Initialize photo monitor for iCloud Photos."""
        self.photo_folder = Path(photo_folder).expanduser()
        self.processed_file = "processed_photos.json"
        
    def get_todays_photos(self):
        """Get all photos added today from iCloud Photos folder."""
        today = datetime.now().date()
        photos = []
        
        # Common photo locations
        search_paths = [
            self.photo_folder,
            Path.home() / "Downloads",
            Path.home() / "Desktop" / "햇살이산책",
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            # Find image files modified today
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.heic']:
                for photo_path in search_path.rglob(ext):
                    # Check if modified today
                    mod_time = datetime.fromtimestamp(photo_path.stat().st_mtime)
                    if mod_time.date() == today:
                        photos.append(str(photo_path))
        
        print(f"[PhotoMonitor] Found {len(photos)} photos from today")
        return photos
    
    def is_dog_photo(self, image_path):
        """Use Gemini Vision to check if photo contains a dog."""
        try:
            # Load image
            img = Image.open(image_path)
            
            # Use Gemini Vision
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = """
            Analyze this image and answer with ONLY 'YES' or 'NO':
            Does this image contain a dog (especially a Golden Retriever)?
            
            Answer: 
            """
            
            response = model.generate_content([prompt, img])
            answer = response.text.strip().upper()
            
            is_dog = 'YES' in answer
            print(f"[PhotoMonitor] {image_path}: Dog detected = {is_dog}")
            
            return is_dog
            
        except Exception as e:
            print(f"[PhotoMonitor] Error analyzing {image_path}: {e}")
            return False
    
    def analyze_photos_with_gemini(self, photo_paths):
        """Analyze multiple photos and generate a natural blog post."""
        try:
            # Filter only dog photos
            dog_photos = []
            for photo_path in photo_paths[:10]:  # Limit to 10 photos
                if self.is_dog_photo(photo_path):
                    dog_photos.append(photo_path)
            
            if not dog_photos:
                print("[PhotoMonitor] No dog photos found")
                return None
            
            print(f"[PhotoMonitor] Analyzing {len(dog_photos)} dog photos...")
            
            # Load images
            images = []
            for photo_path in dog_photos[:5]:  # Use max 5 photos for analysis
                try:
                    img = Image.open(photo_path)
                    images.append(img)
                except Exception as e:
                    print(f"[PhotoMonitor] Could not load {photo_path}: {e}")
            
            if not images:
                return None
            
            # Use Gemini Vision to analyze
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = """
            이 사진들은 오늘 오후 펫시터가 햇살이(10살 골든리트리버)를 산책시키면서 찍은 사진들입니다.
            
            사진들을 보고 자연스러운 블로그 포스팅을 작성해주세요.
            
            **중요:**
            - '햇살이 엄마' 페르소나로 작성 (30대 후반 여성)
            - 펫시터가 보내준 사진을 보고 쓰는 것처럼
            - 사진 속 햇살이의 모습, 표정, 행동을 구체적으로 묘사
            - 날씨, 장소(한강공원 등) 언급
            - AI 같은 느낌 절대 금지
            - 자연스럽고 따뜻한 톤
            
            JSON 형식으로 출력:
            {
                "title": "자연스러운 제목 (예: 오늘 햇살이 산책 일기)",
                "content": "HTML 포맷 본문 (사진 묘사 포함)",
                "tags": ["햇살이", "골든리트리버", "산책", "일상", "반려견"],
                "mood": "사진에서 느껴지는 햇살이의 기분",
                "weather": "사진으로 추정되는 날씨"
            }
            """
            
            # Combine prompt with images
            content = [prompt] + images
            response = model.generate_content(content)
            
            text = response.text.replace('```json', '').replace('```', '').strip()
            
            try:
                post_data = json.loads(text)
                post_data['photos'] = dog_photos  # Add photo paths
                post_data['created_at'] = datetime.now().isoformat()
                
                print(f"[PhotoMonitor] Generated post: {post_data['title']}")
                return post_data
                
            except json.JSONDecodeError as e:
                print(f"[PhotoMonitor] JSON parse error: {e}")
                return None
                
        except Exception as e:
            print(f"[PhotoMonitor] Error analyzing photos: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_processed(self):
        """Load list of processed photos."""
        if os.path.exists(self.processed_file):
            with open(self.processed_file, 'r') as f:
                return json.load(f)
        return []
    
    def mark_processed(self, photo_paths):
        """Mark photos as processed."""
        processed = self.load_processed()
        processed.extend(photo_paths)
        
        with open(self.processed_file, 'w') as f:
            json.dump(processed, f)
    
    def get_new_photos(self):
        """Get today's photos that haven't been processed yet."""
        all_photos = self.get_todays_photos()
        processed = self.load_processed()
        
        new_photos = [p for p in all_photos if p not in processed]
        print(f"[PhotoMonitor] {len(new_photos)} new photos to process")
        
        return new_photos

if __name__ == "__main__":
    monitor = PhotoMonitor()
    new_photos = monitor.get_new_photos()
    
    if new_photos:
        post_data = monitor.analyze_photos_with_gemini(new_photos)
        if post_data:
            print(json.dumps(post_data, ensure_ascii=False, indent=2))
            monitor.mark_processed(new_photos)
    else:
        print("No new photos to process")
