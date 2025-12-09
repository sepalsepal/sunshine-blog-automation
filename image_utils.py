import os
import time
from datetime import datetime
import replicate
from dotenv import load_dotenv
import requests
import weather_utils
import random
import base64
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import firebase_uploader # [NEW] Firebase 업로더 추가
from retry_utils import retry  # [NEW] 재시도 유틸
import leonardo_ai  # [NEW] Leonardo AI 연동
import stability_ai  # [NEW] Stable Diffusion 3.5 연동

# .env 로드
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# =========================================================
# [1] 기초 부품 함수 (먼저 정의해야 함!)
# =========================================================

# ===== Imagen 초사실적 프리셋 =====
IMAGEN_PHOTOREALISTIC_PRESET = {
    "quality_core": [
        "professional photography",
        "award-winning photograph", 
        "national geographic quality",
        "ultra high definition 8k",
        "extremely detailed and sharp",
        "perfect focus throughout",
        "RAW photograph quality",
        "professional color grading"
    ],
    
    "scene_presets": {
        "food": [
            "professional food photography",
            "appetizing and fresh ingredients",
            "perfect lighting from multiple angles",
            "beautiful plating and presentation",
            "visible texture and moisture",
            "shallow depth of field",
            "natural food colors",
            "editorial quality"
        ],
        "landscape": [
            "breathtaking landscape photography",
            "vivid natural colors",
            "perfect atmospheric perspective",
            "golden hour natural lighting",
            "dramatic clouds and sky",
            "crisp details from foreground to background",
            "professional composition"
        ],
        "object": [
            "professional product photography",
            "studio lighting setup",
            "clean and minimalist background",
            "perfect shadows and highlights",
            "visible material texture and details",
            "commercial photography quality"
        ],
        "product_white_bg": [
            "clean product photography on pure white background",
            "soft natural window light from side",
            "medium distance framing showing full product",
            "moderate depth of field",
            "subtle shadows for depth",
            "muted desaturated colors",
            "seamless white backdrop",
            "blog-style minimalist composition"
        ]
    }
}


def enhance_imagen_prompt(base_prompt, scene_type="object"):
    """
    Imagen용 프롬프트를 초사실적으로 개선
    
    Args:
        base_prompt: 기본 설명
        scene_type: "food", "landscape", "object"
    
    Returns:
        enhanced_prompt: 개선된 프롬프트
    """
    preset = IMAGEN_PHOTOREALISTIC_PRESET
    
    # 핵심 품질 키워드 (랜덤 선택)
    import random
    quality = random.sample(preset["quality_core"], 4)
    
    # 장면별 키워드
    scene_keys = preset["scene_presets"].get(scene_type, preset["scene_presets"]["object"])
    scene_selected = random.sample(scene_keys, min(4, len(scene_keys)))
    
    # 프롬프트 조합  
    enhanced = (
        f"{base_prompt}, "
        f"{', '.join(quality)}, "
        f"{', '.join(scene_selected)}"
    )
    
    return enhanced


@retry(max_attempts=3, delay=2)
def generate_imagen_photorealistic(base_prompt, scene_type="object"):
    """
    [Imagen] 초사실적 이미지 생성 (프리셋 자동 적용)
    
    Args:
        base_prompt: 기본 설명 (예: "fresh ripe peach on wooden table")
        scene_type: "food", "landscape", "object"
    
    Returns:
        이미지 파일 경로
    """
    # 프롬프트 자동 개선
    enhanced_prompt = enhance_imagen_prompt(base_prompt, scene_type)
    
    print(f"📸 [Imagen Photorealistic] Scene: {scene_type}")
    print(f"   Enhanced: {enhanced_prompt[:80]}...")
    
    return generate_imagen_landscape(enhanced_prompt)


@retry(max_attempts=3, delay=2)
def generate_imagen_landscape(prompt):
    """[구글] 풍경/사물 생성"""
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        images = model.generate_images(prompt=prompt, number_of_images=1, aspect_ratio="16:9", safety_filter_level="block_some", person_generation="allow_adult")
        if not os.path.exists("images"): os.makedirs("images")
        filename = f"images/google_{datetime.now().strftime('%H%M%S')}_{random.randint(1,99)}.png"
        images[0].save(location=filename, include_generation_parameters=False)
        print(f"   ✅ [구글] 저장 완료: {filename}")
        
        # [NEW] Firebase 업로드
        firebase_uploader.upload_file(filename, f"google/{os.path.basename(filename)}")
        
        return filename
    except Exception as e:
        print(f"   ❌ [구글] 실패: {e}")
        return None

@retry(max_attempts=3, delay=2)
def generate_haetsal_lora(prompt):
    """[FLUX] 햇살이 생성"""
    try:
        output = replicate.run(
            "sepalsepal/sunshine-flux:f150cae9b2097ee80e480b5304f1218545f5b3dfabf0bc0a6988d81e2fd63c54",
            input={"prompt": prompt, "model": "dev", "lora_scale": 0.7, "aspect_ratio": "4:3", "output_format": "png", "output_quality": 100, "guidance_scale": 2.0, "num_inference_steps": 35, "disable_safety_checker": True}
        )
        resp = requests.get(output[0])
        if resp.status_code == 200:
            if not os.path.exists("images"): os.makedirs("images")
            filename = f"images/haetsal_{datetime.now().strftime('%H%M%S')}_{random.randint(1,99)}.png"
            with open(filename, "wb") as f: f.write(resp.content)
            print(f"   ✅ [햇살이] 저장 완료: {filename}")
            
            # [NEW] Firebase 업로드
            firebase_uploader.upload_file(filename, f"flux/{os.path.basename(filename)}")
            
            return filename
    except Exception as e:
        print(f"   ❌ [FLUX] 실패: {e}")
        raise  # retry 데코레이터가 처리

@retry(max_attempts=3, delay=3)
def generate_leonardo(prompt):
    """[Leonardo AI] 고품질 일관된 스타일 이미지 생성"""
    try:
        result = leonardo_ai.generate_leonardo_image(prompt)
        if result:
            # Firebase 업로드
            firebase_uploader.upload_file(result, f"leonardo/{os.path.basename(result)}")
        return result
    except Exception as e:
        print(f"   ❌ [Leonardo] 실패: {e}")
        raise

@retry(max_attempts=3, delay=3)
def generate_sd3(prompt, model="sd3.5-large"):
    """[Stable Diffusion 3.5] 무료 고품질 이미지 생성"""
    try:
        result = stability_ai.generate_stable_diffusion(prompt, model=model)
        if result:
            # Firebase 업로드
            firebase_uploader.upload_file(result, f"sd3/{os.path.basename(result)}")
        return result
    except Exception as e:
        print(f"   ❌ [SD3] 실패: {e}")
        raise

# =========================================================
# [2] 템플릿 기반 이미지 생성 (안정적인 고정 프롬프트)
# =========================================================

def load_image_templates():
    """config/image_templates.json에서 고정 프롬프트 로드"""
    import json
    template_path = os.path.join(os.path.dirname(__file__), "config", "image_templates.json")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ [Warning] image_templates.json not found. Using fallback prompts.")
        return None

def generate_images_from_template(food_name, callback=None):
    """
    템플릿 기반 이미지 생성 (일관된 품질 보장)
    - config/image_templates.json의 고정 프롬프트 사용
    - {food} 자리를 food_name으로 치환
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    templates = load_image_templates()
    if not templates:
        # Fallback to basic prompts if template not found
        templates = {
            "food_mode": {
                "hero": "A senior Golden Retriever looking at {food}. Home kitchen, natural light.",
                "detail": "Close-up of {food} on wooden table. Dog paw visible.",
                "reaction": "Golden Retriever happily eating {food}.",
                "info": "Dog bowl next to {food} portion.",
                "summary": "Golden Retriever with owner enjoying {food} snack time."
            },
            "negative_prompts": {"global": "-illustration -cartoon"},
            "model_config": {
                "hero": {"model": "flux-1.1-pro", "quality": 90},
                "detail": {"model": "imagen", "quality": 90},
                "reaction": {"model": "flux-1.1-pro", "quality": 90},
                "info": {"model": "imagen", "quality": 90},
                "summary": {"model": "imagen", "quality": 90}
            }
        }
    
    food_templates = templates["food_mode"]
    negative = templates.get("negative_prompts", {}).get("global", "")
    model_config = templates.get("model_config", {})
    
    # 프롬프트 생성 (템플릿에서 {food} 치환)
    prompts = [
        ("hero", food_templates["hero"].replace("{food}", food_name) + " " + negative),
        ("detail", food_templates["detail"].replace("{food}", food_name) + " " + negative),
        ("reaction", food_templates["reaction"].replace("{food}", food_name) + " " + negative),
        ("info", food_templates["info"].replace("{food}", food_name) + " " + negative),
        ("summary", food_templates["summary"].replace("{food}", food_name) + " " + negative),
    ]
    
    print(f"🎨 [Template Engine] Generating {len(prompts)} images for '{food_name}'...")
    generated_files = [None] * len(prompts)
    completed_count = 0
    
    def process_image(index, prompt_type, prompt):
        print(f"   📸 [{index+1}/5] Generating {prompt_type}...")
        
        config = model_config.get(prompt_type, {"model": "imagen", "quality": 90})
        use_flux = config["model"] == "flux-1.1-pro"
        
        filename = None
        
        if use_flux:
            print(f"      ✨ Using FLUX 1.1 Pro")
            try:
                output = replicate.run(
                    "black-forest-labs/flux-1.1-pro",
                    input={
                        "prompt": prompt,
                        "aspect_ratio": "16:9",
                        "output_format": "jpg",
                        "output_quality": config["quality"],
                        "safety_tolerance": 2
                    }
                )
                image_url = str(output)
                resp = requests.get(image_url)
                if resp.status_code == 200:
                    if not os.path.exists("images"): os.makedirs("images")
                    filename = f"images/flux_{prompt_type}_{datetime.now().strftime('%H%M%S')}_{random.randint(1,999)}.jpg"
                    with open(filename, "wb") as f: f.write(resp.content)
                    firebase_uploader.upload_file(filename, f"flux/{os.path.basename(filename)}")
            except Exception as e:
                print(f"      ❌ Flux failed: {e}. Fallback to Imagen.")
                filename = generate_imagen_landscape(prompt)
        else:
            print(f"      🔹 Using Google Imagen 3")
            filename = generate_imagen_landscape(prompt)
        
        return index, filename
    
    # 병렬 실행
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_image, i, p_type, p) for i, (p_type, p) in enumerate(prompts)]
        
        for future in as_completed(futures):
            idx, fname = future.result()
            if fname:
                generated_files[idx] = fname
            completed_count += 1
            if callback:
                callback(completed_count, len(prompts))
    
    return [f for f in generated_files if f]

# Legacy function (backward compatibility)
def generate_images_food_mode(food_name, food_detail_prompt):
    """음식 모드 (레거시 - generate_images_from_template 사용 권장)"""
    return generate_images_from_template(food_name)

def generate_images_hybrid(prompts, callback=None):
    """
    High-Quality Strategy (Flux 1.1 Pro for Hero/Reaction, Imagen 3 for others)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"🎨 [High-Quality Engine] Generating {len(prompts)} images in PARALLEL...")
    generated_files = [None] * len(prompts) # Pre-allocate to maintain order
    completed_count = 0
    
    def process_single_image(index, prompt_detail):
        print(f"   📸 Starting Image {index+1}/{len(prompts)}...")
        
        # Clean prompt
        clean_prompt = prompt_detail.split('.', 1)[-1].strip() if '.' in prompt_detail[:3] else prompt_detail
        
        # Determine Model based on type
        is_hero = "Hero" in prompt_detail or index == 0
        is_reaction = "Reaction" in prompt_detail or "햇살이" in prompt_detail
        
        filename = None
        
        if is_hero or is_reaction:
            # Use FLUX 1.1 Pro (Best Quality)
            print(f"      ✨ [Img {index+1}] Using FLUX 1.1 Pro")
            full_prompt = f"A high-end commercial photography of {clean_prompt}. 8k resolution, highly detailed, professional lighting, shot on Phase One XF IQ4 150MP. -fake -illustration"
            
            try:
                output = replicate.run(
                    "black-forest-labs/flux-1.1-pro",
                    input={
                        "prompt": full_prompt,
                        "aspect_ratio": "16:9",
                        "output_format": "jpg",
                        "output_quality": 90,
                        "safety_tolerance": 2
                    }
                )
                image_url = str(output)
                resp = requests.get(image_url)
                if resp.status_code == 200:
                    if not os.path.exists("images"): os.makedirs("images")
                    filename = f"images/flux_{datetime.now().strftime('%H%M%S')}_{random.randint(1,999)}.jpg"
                    with open(filename, "wb") as f: f.write(resp.content)
                    
                    # Firebase Upload
                    firebase_uploader.upload_file(filename, f"flux/{os.path.basename(filename)}")
            except Exception as e:
                print(f"      ❌ [Img {index+1}] Flux failed: {e}")
                # Fallback to Imagen
                filename = generate_imagen_landscape(clean_prompt)

        else:
            # Use Google Imagen 3 (Standard Quality)
            print(f"      🔹 [Img {index+1}] Using Google Imagen 3")
            full_prompt = f"A high-quality photography of {clean_prompt}. Realistic, detailed, natural light. -text -watermark"
            filename = generate_imagen_landscape(full_prompt)
            
        return index, filename

    # Run in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_image, i, p) for i, p in enumerate(prompts)]
        
        for future in as_completed(futures):
            idx, fname = future.result()
            if fname:
                generated_files[idx] = fname
            
            completed_count += 1
            if callback:
                callback(completed_count, len(prompts))
                
    # Filter out Nones just in case
    return [f for f in generated_files if f]

