import os
import shutil
import csv
from pathlib import Path
from PIL import Image, ImageFile
import torch
from transformers import CLIPProcessor, CLIPModel
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- Configurations ---
SOURCE_DIR = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/01_haetsali_best'
OUTPUT_BABY = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/photos/00_haetsali_baby'
CSV_REPORT = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/media_bank/puppy_classification_report.csv'

# Threshold for being a puppy
PUPPY_THRESHOLD = 0.6  # Puppy 점수가 60% 이상이면 아기로 분류

def setup_model():
    logging.info("🔄 Puppy Detection 모델 로딩 중... (CLIP ViT-B/32)")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

def classify_age(image, model, processor):
    prompts = [
        "a tiny golden retriever puppy with fluffy fur",
        "a baby golden retriever dog",
        "an adult golden retriever dog with long hair",
        "a full grown golden retriever"
    ]
    
    try:
        inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0]
            
        # Puppy scores indices: 0, 1
        # Adult scores indices: 2, 3
        puppy_score = probs[0].item() + probs[1].item()
        adult_score = probs[2].item() + probs[3].item()
        
        return puppy_score, adult_score
    except Exception as e:
        logging.error(f"Error during classification: {e}")
        return 0.0, 0.0

def main():
    if not os.path.exists(SOURCE_DIR):
        logging.error(f"Source directory {SOURCE_DIR} not found.")
        return

    model, processor = setup_model()
    
    os.makedirs(OUTPUT_BABY, exist_ok=True)
    
    results = []
    processed_count = 0
    baby_count = 0
    
    # Walk through all subfolders in 01_haetsali_best
    for root, dirs, files in os.walk(SOURCE_DIR):
        category = os.path.basename(root)
        if category == '01_haetsali_best': continue
        
        logging.info(f"🔍 카테고리 검사 중: {category}")
        
        for filename in files:
            if filename.startswith('.') or not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            
            file_path = Path(root) / filename
            try:
                image = Image.open(file_path).convert('RGB')
                puppy_score, adult_score = classify_age(image, model, processor)
                
                is_baby = puppy_score > PUPPY_THRESHOLD
                status = "BABY" if is_baby else "ADULT"
                
                if is_baby:
                    # Create corresponding subfolder in baby directory
                    target_dir = Path(OUTPUT_BABY) / category
                    os.makedirs(target_dir, exist_ok=True)
                    # Move (not copy) because baby photos don't belong in 'Adult' best folders
                    shutil.move(file_path, target_dir / filename)
                    baby_count += 1
                
                results.append([filename, category, status, f"{puppy_score:.4f}", f"{adult_score:.4f}"])
                processed_count += 1
                
                if processed_count % 50 == 0:
                    logging.info(f"Progress: {processed_count} files processed. Found {baby_count} baby photos.")
                    
            except Exception as e:
                logging.error(f"Error processing {filename}: {e}")

    # Write Report
    with open(CSV_REPORT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'original_category', 'classification', 'puppy_score', 'adult_score'])
        writer.writerows(results)
        
    logging.info(f"✅ 분류 완료! 총 {processed_count}개 중 {baby_count}개의 아기 사진을 {OUTPUT_BABY}로 이동했습니다.")

if __name__ == "__main__":
    main()
