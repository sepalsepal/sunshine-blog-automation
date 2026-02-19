#!/usr/bin/env python3
"""037 콜리플라워 검수"""
import json
from pathlib import Path

FOLDER = Path("01_contents/037_Cauliflower")
FOOD_DATA = Path("config/food_data.json")

print("=" * 60)
print("037 콜리플라워 검수 보고서")
print("=" * 60)

# 1. food_data.json 확인
with open(FOOD_DATA, "r") as f:
    food_data = json.load(f)

food_37 = food_data.get("37", {})
name = food_37.get("name", "Unknown")
safety = food_37.get("safety", "Unknown")

print(f"\n[1] 기본 정보")
print(f"  한글명: {name}")
print(f"  안전도: {safety}")

# 2. 이미지 확인
print(f"\n[2] 이미지 현황")

common_dir = FOLDER / "00_Common"
blog_dir = FOLDER / "blog"
old_blog_dir = FOLDER / "02_Blog"

images_found = []

if common_dir.exists():
    for f in sorted(common_dir.iterdir()):
        if f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            images_found.append(("Common", f.name))
            print(f"  V Common: {f.name}")

for blog_path in [blog_dir, old_blog_dir]:
    if blog_path.exists():
        for f in sorted(blog_path.iterdir()):
            if f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                images_found.append(("Blog", f.name))
                print(f"  V Blog: {f.name}")

# 3. 캡션 확인
print(f"\n[3] 캡션 현황")

insta_dir = FOLDER / "insta"
thread_dir = FOLDER / "thread"
old_insta_dir = FOLDER / "01_Insta&Thread"

captions = {}

for p, name_key in [(insta_dir / "caption.txt", "insta_new"), (thread_dir / "caption.txt", "thread_new"), (blog_dir / "caption.txt", "blog_new")]:
    if p.exists():
        with open(p, "r") as f:
            captions[name_key] = f.read()

if old_insta_dir.exists():
    for f in old_insta_dir.iterdir():
        if "Insta_Caption" in f.name:
            with open(f, "r") as file:
                captions["insta_old"] = file.read()
        if "Threads_Caption" in f.name:
            with open(f, "r") as file:
                captions["thread_old"] = file.read()

if old_blog_dir.exists():
    for f in old_blog_dir.iterdir():
        if "Blog_Caption" in f.name:
            with open(f, "r") as file:
                captions["blog_old"] = file.read()

for key, content in captions.items():
    print(f"  V {key}: {len(content)}자")

# 4. 검증기 결과
print(f"\n[4] 검증기 PASS 확인")
with open("caption_verify_result.json", "r") as f:
    verify = json.load(f)

insta_fails = {f['num'] for f in verify['insta']['fails']}
blog_fails = {f['num'] for f in verify['blog']['fails']}
thread_fails = {f['num'] for f in verify['thread']['fails']}

print(f"  인스타: {'X FAIL' if 37 in insta_fails else 'V PASS'}")
print(f"  블로그: {'X FAIL' if 37 in blog_fails else 'V PASS'}")
print(f"  쓰레드: {'X FAIL' if 37 in thread_fails else 'V PASS'}")

# 5. Safety 정합성
print(f"\n[5] Safety 정합성 확인")
insta_caption = captions.get("insta_old") or captions.get("insta_new", "")

if "검색해본 적" in insta_caption or "좋은 보호자" in insta_caption:
    detected = "SAFE"
elif "한 번 더 확인" in insta_caption or "사랑하니까" in insta_caption:
    detected = "CAUTION"
elif "알고 있는 것과 모르는 것" in insta_caption:
    detected = "DANGER"
elif "몰랐다면 괜찮아요" in insta_caption:
    detected = "FORBIDDEN"
else:
    detected = "UNKNOWN"

match = "V 일치" if detected == safety else f"X 불일치 (detected={detected})"
print(f"  food_data: {safety}")
print(f"  캡션 후킹: {detected}")
print(f"  결과: {match}")

# 6. 요약
print(f"\n{'='*60}")
print("검수 결과 요약")
print("="*60)

total_pass = True
checks = [
    ("food_data 존재", bool(food_37)),
    ("이미지 5장 이상", len(images_found) >= 5),
    ("인스타 캡션", "insta" in str(captions.keys())),
    ("블로그 캡션", "blog" in str(captions.keys())),
    ("쓰레드 캡션", "thread" in str(captions.keys())),
    ("인스타 검증 PASS", 37 not in insta_fails),
    ("블로그 검증 PASS", 37 not in blog_fails),
    ("쓰레드 검증 PASS", 37 not in thread_fails),
    ("Safety 정합성", detected == safety),
]

for name, passed in checks:
    status = "V" if passed else "X"
    print(f"  {status} {name}")
    if not passed:
        total_pass = False

print()
if total_pass:
    print("V 전체 검수 PASS")
else:
    print("X 일부 검수 FAIL - 수정 필요")
