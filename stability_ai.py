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

# ===== 초사실적 이미지 프리셋 =====
PHOTOREALISTIC_PRESET = {
    "quality_boosters": [
        "shot on Canon EOS R5",
        "85mm f/1.4 lens",
        "professional photography",
        "award-winning photograph",
        "national geographic style",
        "8k ultra HD resolution",
        "extremely detailed",
        "sharp focus throughout",
        "perfect exposure",
        "natural color grading",
        "RAW image quality"
    ],
    
    "lighting": [
        "natural lighting",
        "golden hour soft light",
        "professional studio lighting",
        "volumetric lighting",
        "realistic shadows and highlights",
        "ambient occlusion"
    ],
    
    "texture_detail": [
        "ultra-realistic skin texture",
        "visible pores and fine details",
        "realistic fur texture with individual hairs",
        "fabric weave visible",
        "natural surface imperfections",
        "micro-details visible",
        "lifelike material properties"
    ],
    
    "negative_prompts": [
        "illustration", "cartoon", "anime", "drawing", "painting",
        "3d render", "cgi", "artificial", "fake", "unrealistic",
        "low quality", "blurry", "grainy", "pixelated", "compressed",
        "oversaturated", "overexposed", "underexposed",
        "amateur", "poorly lit", "out of focus",
        "distorted", "deformed", "ugly", "bad anatomy"
    ]
}


def enhance_prompt_photorealistic(base_prompt, scene_type="general"):
    """
    프롬프트를 초사실적으로 개선
    
    Args:
        base_prompt: 기본 프롬프트
        scene_type: 장면 타입 ("landscape", "portrait", "food", "general")
    
    Returns:
        enhanced_prompt: 개선된 프롬프트
        negative_prompt: 네거티브 프롬프트
    """
    preset = PHOTOREALISTIC_PRESET
    
    # 장면별 추가 키워드
    scene_keywords = {
        "landscape": [
            "landscape photography", "wide angle", "depth of field",
            "atmospheric perspective", "natural colors"
        ],
        "portrait": [
            "portrait photography", "bokeh background", "shallow depth of field",
            "catch light in eyes", "skin tone accuracy"
        ],
        "food": [
            "food photography", "macro lens", "appetizing presentation",
            "fresh ingredients", "professional food styling"
        ],
        "pet": [
            "pet photography", "shallow depth of field", "eye-level perspective",
            "natural animal behavior", "detailed fur texture"
        ]
    }
    
    # 품질 부스터 (랜덤 3개 선택)
    import random
    quality = random.sample(preset["quality_boosters"], 3)
    lighting = random.sample(preset["lighting"], 2)
    texture = random.sample(preset["texture_detail"], 2)
    
    # 장면별 키워드
    scene_keys = scene_keywords.get(scene_type, ["professional photography"])
    
    # 프롬프트 조합
    enhanced = (
        f"{base_prompt}, "
        f"{', '.join(scene_keys)}, "
        f"{', '.join(quality)}, "
        f"{', '.join(lighting)}, "  
        f"{', '.join(texture)}"
    )
    
    # 네거티브 프롬프트
    negative = ", ".join(preset["negative_prompts"])
    
    return enhanced, negative


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


def generate_photorealistic(base_prompt, scene_type="general", model="sd3.5-large"):
    """
    초사실적 이미지 생성 (프리셋 자동 적용)
    
    Args:
        base_prompt: 기본 설명
        scene_type: "landscape", "portrait", "food", "pet", "general"
        model: SD3.5 모델
    
    Returns:
        이미지 파일 경로
    
    Example:
        >>> generate_photorealistic("golden retriever looking at peach", scene_type="pet")
    """
    # 프롬프트 자동 개선
    enhanced_prompt, negative = enhance_prompt_photorealistic(base_prompt, scene_type)
    
    print(f"📸 [Photorealistic Mode] Scene: {scene_type}")
    print(f"   Enhanced: {enhanced_prompt[:80]}...")
    
    # 생성 (네거티브 프롬프트는 SD3.5 API에서 직접 지원 안함, 프롬프트에 통합)
    full_prompt = f"{enhanced_prompt}. NOT: {negative}"
    
    return generate_stable_diffusion(full_prompt, model=model)


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
