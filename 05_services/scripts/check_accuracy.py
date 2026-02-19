import os
import random

base_path = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/haetsali_photos"

categories = ["01_happy", "02_curious", "03_eating", "04_with_human", "05_profile", "06_outdoor", "99_unusable"]

print("📋 분류 정확도 샘플링 검수 파일 목록")
print("=" * 50)

for category in categories:
    folder_path = os.path.join(base_path, category)
    if not os.path.exists(folder_path):
        continue
    
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    sample_size = min(10, len(files))
    if sample_size == 0:
        continue
        
    samples = random.sample(files, sample_size)
    samples.sort()
    
    print(f"\n📂 {category} (샘플 {sample_size}장):")
    for f in samples:
        print(f"  - {f}")

print("\n" + "=" * 50)
print("👆 위 파일들을 열어서 분류가 맞는지 확인하세요!")
