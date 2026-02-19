import os
import shutil
import csv
import time
from pathlib import Path
from PIL import Image, ImageFile
import torch
from transformers import CLIPProcessor, CLIPModel
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 이미지 로딩 설정
ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- 설정 ---
# 이미 media_bank/photos/01_haetsali_raw 로 이동된 상태라고 가정
SOURCE_DIR = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/01_haetsali_raw'
# 새로운 분류 결과 저장소
OUTPUT_BASE = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/02_haetsali_deep_sorted'
CSV_REPORT = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/deep_classification_report.csv'

# 심층 분류 카테고리 정의
DEEP_CATEGORIES = {
    '01_smile_face': [
        'close up photo of a golden retriever face smiling',
        'dog face closeup happy expression',
        'golden retriever headshot smiling'
    ],
    '02_smile_body_sit': [
        'golden retriever sitting and smiling',
        'dog sitting on floor happy',
        'full body shot of dog sitting'
    ],
    '03_smile_body_stand': [
        'golden retriever standing and smiling',
        'dog standing up happy'
    ],
    '04_action_run': [
        'dog running fast',
        'golden retriever jumping or running',
        'action shot of dog moving'
    ],
    '05_sleeping': [
        'dog sleeping with eyes closed',
        'golden retriever lying down sleeping',
        'sleeping dog on floor',
        'peaceful dog resting eyes shut'
    ],
    '06_curious_tilt': [
        'dog tilting head sideways',
        'curious dog looking at camera',
        'golden retriever head tilt'
    ],
    '07_eating': [
        'dog eating food from bowl',
        'dog chewing on a treat',
        'golden retriever eating'
    ],
    '08_with_human': [
        'dog together with a human',
        'person petting golden retriever',
        'dog being hugged by human',
        'human hand touching dog'
    ],
    '09_profile_side': [
        'side profile view of golden retriever',
        'dog looking to the side'
    ],
    '10_back_view': [
        'back of the dog',
        'dog looking away from camera',
        'rear view of golden retriever'
    ],
    '11_outdoor_scenery': [
        'dog in a beautiful outdoor landscape',
        'dog on grass field far away',
        'scenic photo with dog'
    ],
    '99_low_quality': [
        'blurry blurry photo',
        'very dark image',
        'out of focus dog',
        'bad quality noise'
    ]
}

def setup_model():
    print("🔄 모델 로딩 중... (CLIP ViT-B/32)")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    print("✅ 모델 로딩 완료.")
    return model, processor

def classify_single(image_path, model, processor):
    try:
        image = Image.open(image_path).convert('RGB')
    except Exception as e:
        return '99_error', 0.0

    flat_prompts = []
    prompt_to_cat = {}
    for cat, prompts in DEEP_CATEGORIES.items():
        for p in prompts:
            flat_prompts.append(p)
            prompt_to_cat[p] = cat
            
    inputs = processor(text=flat_prompts, images=image, return_tensors="pt", padding=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
        
    best_idx = probs.argmax().item()
    best_prompt = flat_prompts[best_idx]
    category = prompt_to_cat[best_prompt]
    score = probs[0][best_idx].item()
    
    # 임계값 적용 (너무 낮으면 기타로 분류 가능하지만, 일단 가장 높은 것 선택)
    return category, score

def main():
    print("🚀 심층 분류(Deep Classification) 시작")
    print(f"📂 원본 소스: {SOURCE_DIR}")
    print(f"📂 저장 위치: {OUTPUT_BASE}")
    
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    model, processor = setup_model()
    
    # 소스 폴더 내의 모든 이미지 재귀 탐색
    all_images = []
    source_path = Path(SOURCE_DIR)
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.heic', '*.JPG', '*.JPEG', '*.PNG']:
        all_images.extend(list(source_path.rglob(ext)))
        
    total = len(all_images)
    print(f"📸 총 분류 대상: {total}장")
    
    csv_data = []
    start_time = time.time()
    
    for i, img_path in enumerate(all_images, 1):
        filename = img_path.name
        
        # 분류 실행
        cat, score = classify_single(img_path, model, processor)
        
        # 결과 폴더로 복사 (이동 아님, 안전하게 복사)
        # 파일명 충돌 방지: 원래 폴더명_파일명
        parent_folder = img_path.parent.name
        new_filename = f"{parent_folder}_{filename}" if parent_folder != '01_haetsali_raw' else filename
        # 또는 그냥 고유하게 유지. 일단 덮어쓰기 방지용 prefix
        
        target_dir = Path(OUTPUT_BASE) / cat
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / filename
        
        if not target_file.exists():
            try:
                shutil.copy2(img_path, target_file)
            except Exception as e:
                print(f"Copy Error: {e}")
        
        csv_data.append([filename, cat, score, str(img_path)])
        
        if i % 20 == 0:
            elapsed = time.time() - start_time
            print(f"[{i}/{total}] 분류중... ({cat})")
            
    # 리포트 저장
    with open(CSV_REPORT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'deep_category', 'score', 'original_path'])
        writer.writerows(csv_data)
        
    print(f"\n✅ 심층 분류 완료! 결과: {OUTPUT_BASE}")
    print(f"📄 리포트: {CSV_REPORT}")

if __name__ == "__main__":
    main()
