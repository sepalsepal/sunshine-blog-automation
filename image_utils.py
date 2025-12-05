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
        return None

# =========================================================
# [2] 조립 함수 (메인 로직)
# =========================================================

def generate_images_food_mode(food_name, food_detail_prompt):
    """음식 모드 (구글 2장 + 햇살이 1장)"""
    print(f"🎨 [Food Engine] 가동: {food_name}")
    generated_files = []
    
    # 1. 구글 (음식 클로즈업)
    p1 = f"A candid smartphone food photography of {food_detail_prompt}. Focus on texture. Natural light. -fake"
    f1 = generate_imagen_landscape(p1) # 위에서 정의했으므로 에러 안 남
    if f1: generated_files.append(f1)
    time.sleep(2)

    # 2. 구글 (테이블 샷)
    p2 = f"A candid smartphone photography of {food_detail_prompt} on a wooden table, home kitchen context. -fake"
    f2 = generate_imagen_landscape(p2)
    if f2: generated_files.append(f2)
    time.sleep(2)

    # 3. FLUX (햇살이)
    flux_prompt = f"A detailed macro photograph of TOK dog, senior Golden Retriever, looking at {food_name} with curious eyes. soft lighting. -plastic"
    f3 = generate_haetsal_lora(flux_prompt) # 위에서 정의했으므로 에러 안 남
    if f3: generated_files.append(f3)
    
    return generated_files

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

