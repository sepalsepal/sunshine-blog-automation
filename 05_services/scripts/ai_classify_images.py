#!/usr/bin/env python3
"""
Project Sunshine - AI 이미지 자동 분류 스크립트
CLIP 모델을 사용하여 haetsali/special 폴더의 이미지를 자동 분류
"""

import os
import shutil
import csv
from pathlib import Path
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

# 설정
SOURCE_DIR = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/photo_sunshine_master/haetsali/special'
OUTPUT_DIR = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/photo_sunshine_master/haetsali'
CSV_OUTPUT = '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/classification_results.csv'

# 분류 카테고리 및 CLIP 프롬프트
CATEGORIES = {
    'happy': [
        'a happy smiling golden retriever dog',
        'a joyful dog with bright expression',
        'a dog smiling with tongue out'
    ],
    'curious': [
        'a curious dog tilting head',
        'a dog looking with curious expression',
        'a dog with head tilted sideways'
    ],
    'eating': [
        'a dog eating food',
        'a dog with food in front',
        'a dog licking or chewing'
    ],
    'with_human': [
        'a dog with a person',
        'a dog being petted by human hand',
        'a dog and human together'
    ],
    'profile': [
        'a professional dog portrait photo',
        'a side profile of a golden retriever',
        'a beautiful dog profile shot'
    ],
    'outdoor': [
        'a dog in outdoor park or garden',
        'a dog on grass outside',
        'a dog in nature outdoor setting'
    ],
    'unusable': [
        'a blurry unfocused photo',
        'a dark underexposed image',
        'a photo with no clear subject'
    ]
}

def load_model():
    """CLIP 모델 로드"""
    print("🔄 CLIP 모델 로딩 중...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    print("✅ 모델 로딩 완료!")
    return model, processor

def classify_image(image_path, model, processor):
    """단일 이미지 분류"""
    try:
        image = Image.open(image_path).convert('RGB')
    except Exception as e:
        return 'unusable', 0.0, str(e)
    
    # 모든 카테고리의 프롬프트 준비
    all_prompts = []
    prompt_to_category = {}
    
    for category, prompts in CATEGORIES.items():
        for prompt in prompts:
            all_prompts.append(prompt)
            prompt_to_category[prompt] = category
    
    # CLIP 분석
    inputs = processor(
        text=all_prompts,
        images=image,
        return_tensors="pt",
        padding=True
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
    
    # 가장 높은 확률의 프롬프트 찾기
    best_idx = probs.argmax().item()
    best_prompt = all_prompts[best_idx]
    best_category = prompt_to_category[best_prompt]
    best_score = probs[0][best_idx].item()
    
    return best_category, best_score, best_prompt

def classify_all_images():
    """모든 이미지 분류"""
    model, processor = load_model()
    
    source_path = Path(SOURCE_DIR)
    images = list(source_path.glob('*'))
    total = len(images)
    
    print(f"\n📷 총 {total}개 이미지 분류 시작!\n")
    
    results = []
    category_counts = {cat: 0 for cat in CATEGORIES.keys()}
    
    for idx, img_path in enumerate(images, 1):
        if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.heic', '.webp']:
            continue
        
        # 분류
        category, score, prompt = classify_image(img_path, model, processor)
        
        # 결과 저장
        results.append({
            'filename': img_path.name,
            'category': category,
            'score': score,
            'prompt': prompt
        })
        
        category_counts[category] += 1
        
        # 파일 이동
        dest_dir = Path(OUTPUT_DIR) / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        new_filename = f"{category}_{category_counts[category]:04d}{img_path.suffix.lower()}"
        dest_path = dest_dir / new_filename
        
        try:
            shutil.move(str(img_path), str(dest_path))
            status = "✅"
        except Exception as e:
            status = "❌"
        
        # 진행 상황 출력 (매 50개마다)
        if idx % 50 == 0 or idx == total:
            print(f"[{idx}/{total}] {status} {img_path.name} → {category} ({score:.2%})")
    
    # CSV 저장
    with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'category', 'score', 'prompt'])
        writer.writeheader()
        writer.writerows(results)
    
    # 최종 요약
    print("\n" + "="*60)
    print("📊 AI 분류 완료 요약")
    print("="*60)
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}개")
    print(f"\n  총 {sum(category_counts.values())}개 파일 분류 완료!")
    print(f"  📄 결과 CSV: {CSV_OUTPUT}")
    
    return results

if __name__ == '__main__':
    classify_all_images()
