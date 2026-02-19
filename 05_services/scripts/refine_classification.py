import os
import shutil
import csv
import time
from pathlib import Path
from PIL import Image, ImageFile, ImageOps
import torch
from transformers import CLIPProcessor, CLIPModel
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- Configurations ---
SOURCE_DIR = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/02_haetsali_curated_strict'
OUTPUT_BASE = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/03_haetsali_perfect'
REJECT_BASE = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/99_rejected_by_qa'
CSV_REPORT = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/refine_report.csv'

# "Negative Prompt" Thresholds
# If probability of NEGATIVE concept > THRESHOLD, reject firmly.
STRICT_THRESHOLD = 0.15  # 15% 이상이면 의심 (매우 엄격)

# Define Logic: Category -> [Positive Prompts], [Negative Prompts]
VALIDATION_RULES = {
    '01_face_closeup': {
        'positive': ['extreme close up of dog face', 'dog headshot only'],
        'negative': ['full body of dog', 'dog paws visible', 'dog tail visible', 'human body', 'person']
    },
    '02_sitting_pose': {
        'positive': ['dog sitting upright on floor', 'golden retriever sitting posture'],
        'negative': ['dog lying down', 'dog sleeping', 'dog standing on four legs', 'dog running', 'belly up']
    },
    '03_standing_pose': {
        'positive': ['dog standing on four legs', 'golden retriever standing side view'],
        'negative': ['dog sitting', 'dog lying down', 'dog sleeping']
    },
    '04_lying_down_sleep': {
        'positive': ['dog lying down', 'dog sleeping'],
        'negative': ['dog standing', 'dog running', 'dog sitting upright']
    },
    '05_lying_down_belly': {
        'positive': ['dog lying on back belly up', 'upside down dog'],
        'negative': ['dog standing', 'dog sitting', 'dog running']
    },
    '06_action_running': {
        'positive': ['dog running fast', 'dog jumping'],
        'negative': ['dog sitting', 'dog lying down', 'dog sleeping', 'blurry photo']
    },
    '08_with_human': {
        'positive': ['dog with human', 'person petting dog'],
        'negative': ['dog alone', 'no human']
    },
    '09_tilted_head_curious': {
        'positive': ['dog tilting head', 'curious face'],
        'negative': ['dog sleeping', 'dog running', 'dog looking away']
    }
}

def setup_model():
    print("🔄 QA 검수 모델 로딩 중... (CLIP ViT-B/32)")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

def check_image_quality(image, model, processor, category):
    # Rule check
    if category not in VALIDATION_RULES:
        return True, "No rules", 0.0

    rule = VALIDATION_RULES[category]
    pos_prompts = rule['positive']
    neg_prompts = rule['negative']
    
    all_prompts = pos_prompts + neg_prompts
    
    try:
        inputs = processor(text=all_prompts, images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0] # shape: [num_prompts]
            
        # Check Negative Scores
        # Neg indices start after Pos indices
        neg_start_idx = len(pos_prompts)
        max_neg_score = 0
        max_neg_prompt = ""
        
        for i in range(len(neg_prompts)):
            score = probs[neg_start_idx + i].item()
            if score > max_neg_score:
                max_neg_score = score
                max_neg_prompt = neg_prompts[i]
        
        if max_neg_score > STRICT_THRESHOLD:
            return False, f"Rejected: {max_neg_prompt} ({max_neg_score:.2f})", max_neg_score
            
        return True, "Passed", max_neg_score
        
    except Exception as e:
        return False, f"Error: {e}", 0.0

def main():
    print("🚀 초정밀 필터링(Hyper-Refine) 시작")
    print(f"👉 기준: Negative Filtering (Threshold: {STRICT_THRESHOLD})")
    print(f"📂 입력: {SOURCE_DIR}")
    print(f"📂 합격: {OUTPUT_BASE}")
    print(f"📂 탈락: {REJECT_BASE}")
    
    model, processor = setup_model()
    
    csv_data = []
    
    # Iterate Categories
    for cat in os.listdir(SOURCE_DIR):
        cat_dir = Path(SOURCE_DIR) / cat
        if not cat_dir.is_dir() or cat.startswith('99'): continue # Skip existing rejects
        
        print(f"🔍 검수 중: {cat} ...")
        
        target_pass = Path(OUTPUT_BASE) / cat
        target_fail = Path(REJECT_BASE) / cat
        target_pass.mkdir(parents=True, exist_ok=True)
        target_fail.mkdir(parents=True, exist_ok=True)
        
        files = list(cat_dir.glob('*'))
        for img_path in files:
            if img_path.name.startswith('.'): continue
            
            try:
                image = Image.open(img_path).convert('RGB')
                passed, reason, score = check_image_quality(image, model, processor, cat)
                
                if passed:
                    shutil.copy2(img_path, target_pass / img_path.name)
                    status = "PASS"
                else:
                    shutil.copy2(img_path, target_fail / img_path.name)
                    status = "FAIL"
                    
                csv_data.append([img_path.name, cat, status, reason, score])
                
            except Exception as e:
                print(f"Error processing {img_path.name}: {e}")
                
    # Save Report
    with open(CSV_REPORT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'category', 'status', 'reason', 'negative_score'])
        writer.writerows(csv_data)
        
    print(f"\n✅ 초정밀 검수 완료! 합격본은 {OUTPUT_BASE} 확인.")

if __name__ == "__main__":
    main()
