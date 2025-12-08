"""
Leonardo AI 이미지 생성
더 일관된 스타일의 고품질 이미지 생성
"""
import os
import time
import requests
from datetime import datetime
import random
from dotenv import load_dotenv
from retry_utils import retry

load_dotenv()

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"


def _get_headers():
    """API 헤더 생성"""
    return {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }


@retry(max_attempts=3, delay=3)
def generate_leonardo_image(prompt, model_id="6bef9f1b-29cb-40c7-b9df-32b51c1f67d3", width=1024, height=768):
    """
    Leonardo AI로 이미지 생성
    
    Args:
        prompt: 이미지 프롬프트
        model_id: 모델 ID (기본: Leonardo Diffusion XL)
        width: 이미지 너비
        height: 이미지 높이
    
    Returns:
        저장된 이미지 파일 경로 또는 None
    """
    if not LEONARDO_API_KEY:
        print("❌ [Leonardo] API 키가 없습니다. .env에 LEONARDO_API_KEY 추가 필요")
        return None
    
    try:
        # 1. 이미지 생성 요청
        print(f"🎨 [Leonardo] 이미지 생성 중: {prompt[:50]}...")
        
        payload = {
            "prompt": prompt,
            "modelId": model_id,
            "width": width,
            "height": height,
            "num_images": 1,
            "promptMagic": True,
            "public": False
        }
        
        response = requests.post(
            f"{BASE_URL}/generations",
            headers=_get_headers(),
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ [Leonardo] API 오류: {response.status_code} - {response.text[:100]}")
            raise Exception(f"API error: {response.status_code}")
        
        data = response.json()
        generation_id = data["sdGenerationJob"]["generationId"]
        print(f"   ⏳ 생성 ID: {generation_id}")
        
        # 2. 생성 완료 대기 (최대 60초)
        for _ in range(20):
            time.sleep(3)
            
            status_response = requests.get(
                f"{BASE_URL}/generations/{generation_id}",
                headers=_get_headers()
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                generation = status_data.get("generations_by_pk")
                
                if generation and generation.get("status") == "COMPLETE":
                    images = generation.get("generated_images", [])
                    if images:
                        image_url = images[0]["url"]
                        
                        # 3. 이미지 다운로드
                        img_response = requests.get(image_url)
                        if img_response.status_code == 200:
                            if not os.path.exists("images"):
                                os.makedirs("images")
                            
                            filename = f"images/leonardo_{datetime.now().strftime('%H%M%S')}_{random.randint(1,99)}.png"
                            with open(filename, "wb") as f:
                                f.write(img_response.content)
                            
                            print(f"   ✅ [Leonardo] 저장 완료: {filename}")
                            return filename
        
        print("❌ [Leonardo] 생성 시간 초과")
        return None
        
    except Exception as e:
        print(f"❌ [Leonardo] 실패: {e}")
        raise  # retry를 위해 예외 다시 발생


def get_available_models():
    """사용 가능한 모델 목록 조회"""
    if not LEONARDO_API_KEY:
        return []
    
    try:
        response = requests.get(
            f"{BASE_URL}/platformModels",
            headers=_get_headers()
        )
        
        if response.status_code == 200:
            return response.json().get("custom_models", [])
    except:
        pass
    
    return []


# 인기 모델 ID 상수
MODELS = {
    "DIFFUSION_XL": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Diffusion XL
    "VISION_XL": "5c232a9e-9061-4777-980a-ddc8e65647c6",    # Leonardo Vision XL
    "ANIME_XL": "e71a1c2f-4f80-4800-934f-2c68979d8cc8",     # Anime XL
}
