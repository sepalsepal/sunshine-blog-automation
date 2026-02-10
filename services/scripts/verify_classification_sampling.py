import os
import random

base_path = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/haetsali_photos"
categories = ["01_happy", "02_curious", "03_eating", "04_with_human", "05_profile", "06_outdoor", "99_unusable"]

print("📋 Classification Sampling Verification Result\n")
for cat in categories:
    path = os.path.join(base_path, cat)
    if os.path.exists(path):
        files = [f for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            print(f"## 📂 {cat}: Empty")
            continue
            
        sample = random.sample(files, min(10, len(files)))
        print(f"## 📂 {cat} (Sample {len(sample)}/{len(files)})")
        for s in sample:
            print(f"- {s}")
        print("")
    else:
        print(f"## 📂 {cat}: Not Found")
