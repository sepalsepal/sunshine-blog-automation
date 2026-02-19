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

ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- 설정 ---
SOURCE_DIR = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/01_haetsali_raw'
# "Curated"라는 이름으로 변경하여 수동 분류급 퀄리티 지향
OUTPUT_BASE = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/02_haetsali_curated_strict'
CSV_REPORT = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/strict_classification_report.csv'

# 임계값 (이 점수보다 낮으면 99_unsure로 보냄)
# CLIP 점수는 상대적이므로 softmax 후 확률값 기준. 항목이 13개이므로 평균 0.07. 
# 0.2 이상이면 꽤 확실한 편. 사용자가 엄격함을 원하므로 0.25 설정.
CONFIDENCE_THRESHOLD = 0.25

# 심층 분류 카테고리 정의 (상호 배타적 묘사 강화)
DEEP_CATEGORIES = {
    '01_face_closeup': [
        'extreme close up photo of a golden retriever face only',
        'dog face filling the frame, no body visible',
        'headshot of a golden retriever'
    ],
    '02_sitting_pose': [
        'golden retriever dog sitting on the floor upright',
        'dog sitting body posture, not lying down',
        'full body of a sitting dog'
    ],
    '03_standing_pose': [
        'golden retriever dog standing on four legs',
        'side view of a standing dog',
        'dog standing up'
    ],
    '04_lying_down_sleep': [
        'golden retriever lying down on floor',
        'dog sleeping on the ground',
        'dog resting head on paws on floor'
    ],
    '05_lying_down_belly': [
        'dog lying on back showing belly',
        'golden retriever rolling on floor belly up',
        'upside down dog face'
    ],
    '06_action_running': [
        'dog running fast in outdoor',
        'action shot of golden retriever jumping',
        'blur motion of running dog'
    ],
    '07_eating': [
        'dog eating food from a bowl',
        'dog chewing a treat or snack',
        'close up of dog mouth eating'
    ],
    '08_with_human': [
        'human hand petting a dog',
        'dog together with a person',
        'selfie with a dog'
    ],
    '09_tilted_head_curious': [
        'dog tilting head to the side questioning',
        'golden retriever with head tilt curious expression'
    ],
    '10_back_view': [
        'back of the dog head and body',
        'dog looking away from camera',
        'rear view of golden retriever'
    ],
    '99_low_quality': [
        'extremely blurry photo',
        'too dark image, black screen',
        'no dog visible in photo'
    ]
}

def setup_model():
    print("🔄 엄격 모드 모델 로딩 중... (CLIP ViT-B/32)")
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
            
    # CLIP Inference
    inputs = processor(text=flat_prompts, images=image, return_tensors="pt", padding=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
        # softmax로 확률 변환
        probs = outputs.logits_per_image.softmax(dim=1)
        
    best_idx = probs.argmax().item()
    best_prompt = flat_prompts[best_idx]
    category = prompt_to_cat[best_prompt]
    score = probs[0][best_idx].item()
    
    return category, score

def main():
    print("🚀 사진 정밀 분류(Strict Mode) 시작")
    print("👉 기준: 자세(앉기/눕기)와 앵글(얼굴/전신)을 엄격히 구분")
    print(f"📂 원본 소스: {SOURCE_DIR}")
    print(f"📂 저장 위치: {OUTPUT_BASE}")
    
    if os.path.exists(OUTPUT_BASE):
        print("⚠️ 기존 결과 폴더가 있어 덮어쓰거나 추가합니다.")
    
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    model, processor = setup_model()
    
    # 소스 폴더 탐색
    all_images = []
    source_path = Path(SOURCE_DIR)
    # 재귀적으로 탐색하되, 이미 분류된 폴더 말고 원본(raw)이나 합쳐진 곳을 봐야함.
    # 하지만 사용자가 'media_bank/photos/01_haetsali_raw'로 다 옮기라고 했었음.
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.heic', '*.JPG', '*.JPEG', '*.PNG']:
        all_images.extend(list(source_path.rglob(ext)))
        
    total = len(all_images)
    print(f"📸 총 처리 대상: {total}장")
    
    csv_data = []
    start_time = time.time()
    
    count_dict = {k:0 for k in DEEP_CATEGORIES.keys()}
    count_dict['99_unsure'] = 0
    count_dict['99_error'] = 0
    
    for i, img_path in enumerate(all_images, 1):
        filename = img_path.name
        
        # 분류 실행
        cat, score = classify_single(img_path, model, processor)
        
        # 임계값 적용: 점수가 낮으면 '99_unsure'로 보내서 사용자가 직접 보게 함
        if score < CONFIDENCE_THRESHOLD and cat != '99_low_quality':
            final_cat = '99_unsure_mixed'
        else:
            final_cat = cat
            
        # 결과 복사
        target_dir = Path(OUTPUT_BASE) / final_cat
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / filename
        
        # 중복 방지를 위해 없으면 복사
        if not target_file.exists():
            try:
                shutil.copy2(img_path, target_file)
            except Exception as e:
                print(f"Copy Error: {e}")
        
        # 통계
        if final_cat in count_dict:
            count_dict[final_cat] += 1
        else:
            count_dict[final_cat] = 1 # unsure 등
            
        csv_data.append([filename, final_cat, score, str(img_path)])
        
        if i % 20 == 0:
            elapsed = time.time() - start_time
            print(f"[{i}/{total}] 처리중... ({final_cat}, {score:.2f})")
            
    # 리포트 저장
    with open(CSV_REPORT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'strict_category', 'score', 'original_path'])
        writer.writerows(csv_data)
        
    print(f"\n✅ 정밀 분류 완료!")
    print("📊 결과 요약:")
    for k, v in count_dict.items():
        print(f"  {k}: {v}장")
    print(f"📂 결과 폴더: {OUTPUT_BASE}")

if __name__ == "__main__":
    main()
