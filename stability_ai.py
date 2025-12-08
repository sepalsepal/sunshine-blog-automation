"""
Stability AI (Stable Diffusion 3.5) 이미지 생성
무료로 고품질 이미지 생성 가능
"""
import os
import time
import requests
from datetime import datetime
import random
import base64
from dotenv import load_dotenv
from retry_utils import retry

load_dotenv()

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
BASE_URL = "https://api.stability.ai/v2beta"


@retry(max_attempts=3, delay=3)
def generate_stable_diffusion(prompt, width=1024, height=768, model="sd3.5-large"):
    """
    Stable Diffusion 3.5로 이미지 생성
    
    Args:
        prompt: 이미지 프롬프트
        width: 이미지 너비 (기본 1024)
        height: 이미지 높이 (기본 768)
        model: 모델 (sd3.5-large, sd3.5-medium, sd3.5-large-turbo)
    
    Models:
        - sd3.5-large: 고품질, 느림
        - sd3.5-medium: 균형
        - sd3.5-large-turbo: 빠름, 4 steps
    
    Returns:
        저장된 이미지 파일 경로 또는 None
    """
    if not STABILITY_API_KEY:
        print("❌ [Stability] API 키가 없습니다. .env에 STABILITY_API_KEY 추가 필요")
        return None
    
    try:
        print(f"🎨 [Stable Diffusion] 이미지 생성 중: {prompt[:50]}...")
        
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*"  # 바이너리 이미지 직접 반환
        }
        
        # Multipart form data
        data = {
            "prompt": prompt,
            "output_format": "png",
            "model": model,
            "aspect_ratio": "16:9"  # 또는 "4:3", "1:1", "3:2" 등
        }
        
        response = requests.post(
            f"{BASE_URL}/stable-image/generate/sd3",
            headers=headers,
            files={"none": ""},  # multipart 강제
            data=data
        )
        
        if response.status_code == 200:
            # 이미지 저장
            if not os.path.exists("images"):
                os.makedirs("images")
            
            filename = f"images/sd3_{datetime.now().strftime('%H%M%S')}_{random.randint(1,99)}.png"
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"   ✅ [Stable Diffusion] 저장 완료: {filename}")
            return filename
        else:
            error_msg = response.text[:100] if response.text else response.status_code
            print(f"   ❌ [Stability] API 오류: {error_msg}")
            raise Exception(f"API error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ [Stable Diffusion] 실패: {e}")
        raise  # retry 데코레이터가 처리


def get_account_balance():
    """Stability AI 계정 크레딧 잔액 확인"""
    if not STABILITY_API_KEY:
        return None
    
    try:
        response = requests.get(
            "https://api.stability.ai/v1/user/balance",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}"}
        )
        
        if response.status_code == 200:
            return response.json().get("credits", 0)
    except:
        pass
    
    return None


# 모델 옵션
MODELS = {
    "FAST": "sd3.5-large-turbo",   # 빠름, 4 steps
    "BALANCED": "sd3.5-medium",     # 균형
    "QUALITY": "sd3.5-large"        # 고품질
}
