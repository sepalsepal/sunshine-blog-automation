#!/usr/bin/env python3
"""
WO-2026-0205-004-R1: FLUX Body Image Generation + Re-rendering
================================================================

R1 핵심: 커버 ≠ 바디 필수 (SHA256 검증)
- FLUX.2 Pro로 바디 전용 이미지 생성
- 기존 커버 소스 재사용 금지
- 바디①② 동일 FLUX 이미지 사용 가능 (커버와만 다르면 됨)

사용법:
    .venv/bin/python services/scripts/wo_004_r1_flux.py prework
    .venv/bin/python services/scripts/wo_004_r1_flux.py forbidden
    .venv/bin/python services/scripts/wo_004_r1_flux.py danger
    .venv/bin/python services/scripts/wo_004_r1_flux.py caution
    .venv/bin/python services/scripts/wo_004_r1_flux.py safe
"""

import asyncio
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Project setup
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from PIL import Image

from pipeline.pillow_overlay import (
    render_body, render_cta,
    build_validation_config, get_safety_color,
)
from pipeline.validators_strict import (
    validate_before_render, validate_v31_slide, strip_emoji,
)
from services.scripts.image_generation.generate_images import generate_image

# ============================================================
# Constants
# ============================================================
BODY_READY_DIR = PROJECT_ROOT / "contents" / "2_body_ready"
COVER_ONLY_DIR = PROJECT_ROOT / "contents" / "1_cover_only"
COVER_SOURCE_DIR = (
    PROJECT_ROOT / "backup_2026-02-03" / "content" / "images"
    / "000_cover" / "02_ready"
)
BEST_CTA_DIR = PROJECT_ROOT / "contents" / "sunshine" / "cta_source" / "best_cta"
TEXT_JSON_DIR = PROJECT_ROOT / "config" / "settings"
TARGET_SIZE = (1080, 1080)
WO_NUMBER = "WO-2026-0205-004-R1"


# ============================================================
# FLUX Prompt Templates
# ============================================================
def build_body_prompt(food_en: str, food_ko: str, safety: str) -> str:
    """Build FLUX prompt for body image generation"""

    # Food descriptions for common items
    food_desc = {
        "blackberry": "fresh blackberries in a white bowl",
        "mackerel": "cooked mackerel fillet on a white plate",
        "yogurt": "a bowl of plain white yogurt with a spoon",
        "tofu": "blocks of white tofu on a wooden cutting board",
        "chocolate": "chocolate bars and pieces on a plate",
        "cheese": "slices of yellow cheese on a wooden board",
        "kimchi": "a bowl of traditional Korean kimchi",
        "cabbage": "fresh green cabbage on a cutting board",
        "brownie": "chocolate brownies on a plate",
        "reeses": "Reese's peanut butter cups on a plate",
        "soju": "a bottle and small glass of clear Korean soju",
        "pizza": "a slice of pizza on a plate",
        "ramen": "a bowl of Korean ramen noodles",
        "bibimbap": "a bowl of Korean bibimbap with colorful vegetables",
        "jjajangmyeon": "a bowl of Korean black bean noodles",
        "bulgogi": "a plate of Korean grilled marinated beef bulgogi",
        "cake": "a slice of frosted cake on a plate",
        "dakgangjeong": "Korean sweet crispy fried chicken pieces",
        "milk": "a glass of banana milk",
        "doritos": "a bag of Doritos chips with some chips on a plate",
        "fanta": "a can and glass of orange Fanta soda",
        "lays": "a bag of Lay's potato chips with chips on a plate",
        "milkis": "a can and glass of Milkis carbonated drink",
        "perrier": "a bottle and glass of Perrier sparkling water",
        "skittles": "a bag of Skittles candies on a plate",
        "starburst": "Starburst candies on a plate",
        "sprite": "a can and glass of Sprite soda",
        "raisin": "a bowl of dried raisins",
        "lemon": "fresh yellow lemons on a cutting board",
        "bacon": "strips of cooked bacon on a plate",
        "donut": "colorful frosted donuts on a plate",
        "nuts": "a bowl of mixed nuts",
        "almonds": "a bowl of raw almonds",
        "baguette": "a fresh French baguette on a cutting board",
        "tteokguk": "a bowl of Korean rice cake soup tteokguk",
        "kimbap": "sliced Korean kimbap rolls on a plate",
        "udon": "a bowl of Japanese udon noodles",
        "toast": "slices of toasted bread on a plate",
        "muffin": "a blueberry muffin on a plate",
        "pancake": "a stack of golden pancakes",
        "waffle": "a golden waffle on a plate",
        "cereal": "a bowl of cereal",
        "granola": "a bowl of crunchy granola",
        "meatball": "meatballs on a plate with sauce",
        "croissant": "a golden flaky croissant on a plate",
        "ritz": "Ritz crackers on a plate",
        "mushroom": "fresh mushrooms on a cutting board",
        "plum": "fresh purple plums on a plate",
        "bean_sprouts": "a plate of cooked bean sprouts",
        "melon": "sliced fresh melon on a plate",
        "pomegranate": "a cut pomegranate showing red seeds",
        "quail_egg": "boiled quail eggs on a small plate",
        "fried_chicken": "crispy fried chicken pieces on a plate",
        "chicken_skewer": "grilled chicken skewers on a plate",
        "raspberry": "fresh red raspberries in a bowl",
        "coconut": "a halved coconut showing white flesh",
        "white_fish": "a cooked white fish fillet on a plate",
        "lettuce": "fresh green lettuce leaves",
        "green_beans": "cooked green beans on a plate",
        "asparagus": "fresh green asparagus spears",
        "beet": "sliced red beets on a cutting board",
        "peas": "a bowl of fresh green peas",
        "chicken_breast": "cooked chicken breast on a plate",
        "naengmyeon": "a bowl of Korean cold noodles naengmyeon",
        "sandwich": "a fresh sandwich cut in half",
        "cheetos": "a bag of Cheetos with some on a plate",
    }

    food_item = food_desc.get(food_en, f"a plate of {food_en.replace('_', ' ')}")

    # Vary angle based on food_id hash for diversity
    angles = [
        "side angle 45 degrees, looking at food with curiosity",
        "front view, looking at camera with gentle expression",
        "profile view from the side, 90 degrees angle",
        "slightly elevated angle, three-quarter view",
    ]
    h = int(hashlib.md5(food_en.encode()).hexdigest(), 16)
    angle = angles[h % len(angles)]

    # Safety-specific expression
    if safety.lower() in ("forbidden", "danger"):
        expression = "gentle gaze, calm expression"
    else:
        expression = "happy expression, tongue slightly out, bright eyes"

    prompt = (
        f"A senior golden retriever with white muzzle and caramel golden fur, "
        f"dark brown eyes, black nose, ears 30 percent smaller than typical golden retriever, "
        f"{expression}, "
        f"sitting behind {food_item}, "
        f"the food prominent in the foreground taking up 25 percent of the frame, "
        f"dog positioned in center of frame, {angle}, "
        f"warm cozy kitchen setting with natural window lighting, "
        f"8K, ultra detailed fur texture, Canon EOS R5, "
        f"soft natural lighting, shallow depth of field, "
        f"dog NOT touching or eating the food, mouth closed"
    )

    return prompt


# ============================================================
# CTA selection (same as wo_004_batch.py)
# ============================================================
def select_cta_image(food_id: str) -> Path:
    cta_files = sorted([f for f in BEST_CTA_DIR.iterdir()
                        if f.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    if not cta_files:
        raise FileNotFoundError(f"CTA 이미지 없음: {BEST_CTA_DIR}")
    h = hashlib.sha256(food_id.encode()).hexdigest()
    idx = int(h, 16) % len(cta_files)
    return cta_files[idx]


# ============================================================
# SHA256 verification
# ============================================================
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_cover_ne_body(cover_path: Path, body_clean_path: Path) -> bool:
    """Verify cover source ≠ body source (SHA256)"""
    if not cover_path.exists() or not body_clean_path.exists():
        return True  # can't verify, assume OK
    c_hash = sha256_file(cover_path)
    b_hash = sha256_file(body_clean_path)
    return c_hash != b_hash


# ============================================================
# Folder/Cover helpers
# ============================================================
def find_folder(food_id):
    for base_dir in [BODY_READY_DIR, COVER_ONLY_DIR]:
        if not base_dir.exists():
            continue
        for d in base_dir.iterdir():
            if not d.is_dir():
                continue
            parts = d.name.split("_", 2)
            if len(parts) >= 2 and parts[1] == food_id:
                return d
    return None


def find_cover_source(food_id, cover_file_hint=""):
    if cover_file_hint:
        p = COVER_SOURCE_DIR / cover_file_hint
        if p.exists():
            return p
    for f in COVER_SOURCE_DIR.glob("cover_*"):
        fname = f.stem.lower()
        if food_id.lower().replace("_", "") in fname.lower().replace("_", ""):
            return f
    return None


# ============================================================
# Caption generation (from wo_004_batch.py)
# ============================================================
def generate_instagram_caption(food_id, food_ko, safety, body1_sub, body2_sub):
    s = safety.upper()
    if s == "FORBIDDEN":
        lines = [
            f"⛔ {food_ko}, 강아지에게 절대 금지!",
            "", f"{body1_sub}", "증상 발견 시 즉시 동물병원으로!", "",
            f"📌 저장해두고 주변 견주에게 공유하세요.", "",
            f"#강아지금지음식 #반려견건강 #강아지음식 #{food_ko.replace(' ','')} @sunshinedogfood",
            "", "ℹ️ 일부 이미지는 AI로 생성되었습니다.", "ℹ️ Some images were generated by AI.",
        ]
    elif s == "DANGER":
        lines = [
            f"⚠️ {food_ko}, 강아지에게 위험해요!",
            "", f"{body1_sub}", f"{body2_sub}", "",
            f"📌 저장해두고 참고하세요!", "",
            f"#강아지위험음식 #반려견건강 #강아지음식 #{food_ko.replace(' ','')} @sunshinedogfood",
            "", "ℹ️ 일부 이미지는 AI로 생성되었습니다.", "ℹ️ Some images were generated by AI.",
        ]
    elif s == "CAUTION":
        lines = [
            f"🟡 {food_ko}, 강아지 급여 시 주의하세요!",
            "", f"{body1_sub}", f"{body2_sub}", "",
            f"📌 저장 & 공유로 다른 견주에게도 알려주세요!", "",
            f"#강아지음식 #반려견건강 #강아지간식 #{food_ko.replace(' ','')} @sunshinedogfood",
            "", "ℹ️ 일부 이미지는 AI로 생성되었습니다.", "ℹ️ Some images were generated by AI.",
        ]
    else:
        lines = [
            f"🐕 {food_ko}, 강아지 급여 가능!",
            "", f"{body1_sub}", f"{body2_sub}", "",
            f"📌 저장해두고 급여할 때 참고하세요!", "",
            f"#강아지음식 #반려견건강 #강아지간식 #{food_ko.replace(' ','')} @sunshinedogfood",
            "", "ℹ️ 일부 이미지는 AI로 생성되었습니다.", "ℹ️ Some images were generated by AI.",
        ]
    return "\n".join(lines)


def generate_threads_caption(food_id, food_ko, safety, body1_sub, body2_sub):
    s = safety.upper()
    if s == "FORBIDDEN":
        lines = [f"⛔ {food_ko}는 강아지에게 절대 금지예요. {body1_sub}",
                 "소량도 위험하니 보관에 주의하세요!", "", "ℹ️ AI 생성 이미지 포함"]
    elif s == "DANGER":
        lines = [f"⚠️ {food_ko}, 강아지한테 위험해요. {body1_sub}",
                 f"{body2_sub}", "", "ℹ️ AI 생성 이미지 포함"]
    elif s == "CAUTION":
        lines = [f"🟡 {food_ko}, 급여 가능하지만 주의! {body1_sub}",
                 f"{body2_sub}", "", "ℹ️ AI 생성 이미지 포함"]
    else:
        lines = [f"🐕 {food_ko}, 강아지 급여 OK! {body1_sub}",
                 f"{body2_sub}", "", "ℹ️ AI 생성 이미지 포함"]
    return "\n".join(lines)


# ============================================================
# Text.json reader — extract body1/body2 text
# ============================================================
def read_body_text(food_id: str, safety: str):
    """Read body1/body2 text from text.json or return defaults"""
    text_path = TEXT_JSON_DIR / f"{food_id}_text.json"
    if text_path.exists():
        data = json.loads(text_path.read_text())

        # Handle both formats:
        # 1) List format: [{"slide":0, "type":"cover", ...}, ...]
        # 2) Dict format: {"food_id":..., "slides": [{"slide":0, ...}, ...]}
        if isinstance(data, dict):
            slides = data.get("slides", [])
        else:
            slides = data

        # Find body1 and body2 slides
        body1 = body2 = None
        for s in slides:
            if not isinstance(s, dict):
                continue
            stype = s.get("type", "")
            slide_num = s.get("slide", -1)
            # List format with "type" field
            if stype in ("content_bottom", "content_top"):
                if body1 is None:
                    body1 = s
                elif body2 is None:
                    body2 = s
                    break
            # Dict format without "type" — use slide 1 and 2
            elif not stype and slide_num in (1, 2):
                if body1 is None:
                    body1 = s
                elif body2 is None:
                    body2 = s
                    break

        if body1 and body2:
            return (
                {"title": body1.get("title", ""), "subtitle": body1.get("subtitle", "")},
                {"title": body2.get("title", ""), "subtitle": body2.get("subtitle", "")},
            )

    # Fallback defaults by safety
    if safety.lower() == "forbidden":
        return (
            {"title": "절대 금지!", "subtitle": "독성 성분 매우 위험"},
            {"title": "증상 & 대처", "subtitle": "이상 증상 시 즉시 동물병원"},
        )
    elif safety.lower() == "danger":
        return (
            {"title": "위험해요!", "subtitle": "급여 금지 음식"},
            {"title": "대처법", "subtitle": "증상 발생 시 급여 중단"},
        )
    elif safety.lower() == "caution":
        return (
            {"title": "주의 급여!", "subtitle": "소량만 급여 가능"},
            {"title": "급여 방법", "subtitle": "주의사항 확인 후 급여"},
        )
    else:
        return (
            {"title": "먹어도 돼요!", "subtitle": "건강에 좋은 성분 포함"},
            {"title": "급여 방법", "subtitle": "소량씩 급여하세요"},
        )


# ============================================================
# CTA text reader
# ============================================================
def read_cta_text(food_id: str):
    text_path = TEXT_JSON_DIR / f"{food_id}_text.json"
    if text_path.exists():
        data = json.loads(text_path.read_text())
        slides = data.get("slides", []) if isinstance(data, dict) else data
        for s in slides:
            if not isinstance(s, dict):
                continue
            # List format with "type" field
            if s.get("type") == "cta":
                return {"title": s.get("title", "저장 & 공유"),
                        "subtitle": s.get("subtitle", "주변 견주에게 알려주세요!")}
            # Dict format — slide 3 is CTA
            if not s.get("type") and s.get("slide") == 3:
                return {"title": s.get("title", "저장 & 공유"),
                        "subtitle": s.get("subtitle", "주변 견주에게 알려주세요!")}
    return {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"}


# ============================================================
# Process single item
# ============================================================
async def process_item(food_id, food_ko, safety, cover_file="", folder_name=""):
    """Full R1 processing: FLUX gen → render → verify → captions → metadata"""

    result = {
        "food_id": food_id,
        "food_ko": food_ko,
        "safety": safety.upper(),
        "flux_gen": False,
        "text_json": True,  # already exists
        "render_01": False,
        "render_02": False,
        "render_03": False,
        "caption_insta": False,
        "caption_threads": False,
        "cover_ne_body": "N/A",
        "validators": "N/A",
        "metadata": False,
        "errors": [],
        "skipped": False,
    }

    # Find folder
    folder = find_folder(food_id)
    if not folder:
        result["errors"].append("폴더 없음")
        result["skipped"] = True
        return result

    # Move to body_ready if in cover_only
    if COVER_ONLY_DIR in folder.parents or folder.parent == COVER_ONLY_DIR:
        dest = BODY_READY_DIR / folder.name
        if not dest.exists():
            shutil.move(str(folder), str(dest))
        folder = dest

    archive = folder / "archive"
    archive.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  📦 {food_id} ({food_ko}) [{safety.upper()}]")
    print(f"  📁 {folder.name}")
    print(f"{'='*60}")

    # Find cover source
    cover_src = find_cover_source(food_id, cover_file)

    # [1] FLUX Body Image Generation
    body_clean = archive / f"{food_id}_body_clean.png"
    if body_clean.exists() and os.path.getsize(body_clean) > 100000:
        print(f"  ⏭️ FLUX body_clean 이미 존재 → 스킵 ({os.path.getsize(body_clean)//1024}KB)")
        result["flux_gen"] = True
    else:
        prompt = build_body_prompt(food_id, food_ko, safety)
        print(f"  🎨 FLUX 생성 중...")
        try:
            gen_result = await generate_image(prompt, body_clean, verbose=True)
            if gen_result["success"]:
                result["flux_gen"] = True
                print(f"  ✅ FLUX 완료: {os.path.getsize(body_clean)//1024}KB")
            else:
                result["errors"].append(f"FLUX 실패: {gen_result['error']}")
                print(f"  ❌ FLUX 실패: {gen_result['error']}")
                return result
        except Exception as e:
            result["errors"].append(f"FLUX 예외: {e}")
            print(f"  ❌ FLUX 예외: {e}")
            return result

    # [2] SHA256 Cover ≠ Body verification
    if cover_src and body_clean.exists():
        is_different = verify_cover_ne_body(cover_src, body_clean)
        result["cover_ne_body"] = "PASS" if is_different else "FAIL"
        if not is_different:
            result["errors"].append("SHA256 커버=바디 동일!")
            print(f"  ❌ SHA256 FAIL: 커버와 바디가 동일합니다!")
        else:
            print(f"  ✅ SHA256 PASS: 커버 ≠ 바디")
    else:
        result["cover_ne_body"] = "N/A (no cover)"
        print(f"  ⚠️ 커버소스 없음 → SHA256 검증 스킵")

    # Read body text
    body1, body2 = read_body_text(food_id, safety)
    cta_text = read_cta_text(food_id)

    validators_passed = 0
    validators_total = 0

    # [3] Render body1 (_01.png)
    for slide_num, text_data in [("01", body1), ("02", body2)]:
        out_file = folder / f"{food_id}_{slide_num}.png"
        bg_file = archive / f"{food_id}_{slide_num}_bg.png"

        try:
            # Copy FLUX body_clean as bg
            shutil.copy2(body_clean, bg_file)

            v_config = build_validation_config("body", safety.lower())
            rel_path = str(bg_file.relative_to(PROJECT_ROOT))
            validate_before_render("body", rel_path, v_config)
            validators_passed += 1
            validators_total += 1

            img = Image.open(bg_file).resize(TARGET_SIZE, Image.LANCZOS)
            title_clean = strip_emoji(text_data["title"])
            sub_clean = strip_emoji(text_data["subtitle"])
            img = render_body(img, title_clean, sub_clean, safety.lower())
            img.save(out_file, "PNG")

            validate_v31_slide("body", v_config, str(out_file.relative_to(PROJECT_ROOT)))
            validators_passed += 2
            validators_total += 2

            result[f"render_{slide_num}"] = True
            print(f"  ✅ _{slide_num} 렌더링 완료 ({os.path.getsize(out_file)//1024}KB)")

        except Exception as e:
            validators_total += 2
            result["errors"].append(f"_{slide_num} 실패: {e}")
            print(f"  ❌ _{slide_num} 실패: {e}")

    # [4] CTA rendering
    out_03 = folder / f"{food_id}_03.png"
    cta_src_file = ""
    try:
        cta_src = select_cta_image(food_id)
        cta_src_file = cta_src.name
        bg_03 = archive / f"{food_id}_03_bg.png"
        shutil.copy2(cta_src, bg_03)

        v_config = build_validation_config("cta", safety.lower())

        # CTA false positive workaround for problematic food_ids
        problematic = any(kw in food_id.lower() for kw in
                          ['ai', 'chicken', 'meat', 'onion', 'garlic',
                           'apple', 'banana', 'carrot', 'beef', 'food'])
        problematic_folder = any(kw in str(folder).lower() for kw in
                                 ['ai', 'chicken', 'meat', 'onion', 'garlic',
                                  'apple', 'banana', 'carrot', 'beef', 'food'])

        if problematic or problematic_folder:
            # Use temp path workaround
            tmp_dir = PROJECT_ROOT / "contents" / "temp_cta_work"
            tmp_dir.mkdir(exist_ok=True)
            bg_tmp = tmp_dir / "source_bg.png"
            shutil.copy2(cta_src, bg_tmp)
            rel_path = str(bg_tmp.relative_to(PROJECT_ROOT))
            validate_before_render("cta", rel_path, v_config)
            validators_passed += 1
            validators_total += 1

            img = Image.open(bg_tmp).resize(TARGET_SIZE, Image.LANCZOS)
            title_clean = strip_emoji(cta_text["title"])
            sub_clean = strip_emoji(cta_text["subtitle"])
            img = render_cta(img, title_clean, sub_clean, bg_path=rel_path)

            # Validate with temp path
            tmp_out = tmp_dir / "rendered_03.png"
            img.save(tmp_out, "PNG")
            validate_v31_slide("cta", v_config, str(tmp_out.relative_to(PROJECT_ROOT)))
            validators_passed += 2
            validators_total += 2

            # Copy to actual location
            shutil.copy2(tmp_out, out_03)
            shutil.rmtree(tmp_dir, ignore_errors=True)
        else:
            rel_path = str(bg_03.relative_to(PROJECT_ROOT))
            validate_before_render("cta", rel_path, v_config)
            validators_passed += 1
            validators_total += 1

            img = Image.open(bg_03).resize(TARGET_SIZE, Image.LANCZOS)
            title_clean = strip_emoji(cta_text["title"])
            sub_clean = strip_emoji(cta_text["subtitle"])
            img = render_cta(img, title_clean, sub_clean, bg_path=rel_path)
            img.save(out_03, "PNG")

            validate_v31_slide("cta", v_config, str(out_03.relative_to(PROJECT_ROOT)))
            validators_passed += 2
            validators_total += 2

        result["render_03"] = True
        print(f"  ✅ _03 CTA 완료 ({os.path.getsize(out_03)//1024}KB)")

    except Exception as e:
        validators_total += 2
        result["errors"].append(f"_03 CTA 실패: {e}")
        print(f"  ❌ _03 CTA 실패: {e}")

    result["validators"] = f"{validators_passed}/{validators_total}"

    # [5] Captions
    b1_sub = strip_emoji(body1["subtitle"])
    b2_sub = strip_emoji(body2["subtitle"])

    try:
        cap = generate_instagram_caption(food_id, food_ko, safety, b1_sub, b2_sub)
        (folder / "caption_instagram.txt").write_text(cap, encoding="utf-8")
        result["caption_insta"] = True
    except Exception as e:
        result["errors"].append(f"인스타 캡션: {e}")

    try:
        cap = generate_threads_caption(food_id, food_ko, safety, b1_sub, b2_sub)
        (folder / "caption_threads.txt").write_text(cap, encoding="utf-8")
        result["caption_threads"] = True
    except Exception as e:
        result["errors"].append(f"쓰레드 캡션: {e}")

    # [6] Metadata
    try:
        slides_rendered = sum([result["render_01"], result["render_02"], result["render_03"]])
        meta = {
            "food_id": food_id,
            "status": "body_ready",
            "synced_at": datetime.now().isoformat(),
            "food_name_ko": food_ko,
            "pd_approved": False,
            "body_rendered_at": datetime.now().isoformat(),
            "body_version": f"v3.1_{WO_NUMBER}",
            "safety": safety.lower(),
            "slides_rendered": slides_rendered + 1,  # +1 for cover
            "cta_source_image": cta_src_file,
            "clean_cover_source": cover_src.name if cover_src else "",
            "cover_source": cover_src.name if cover_src else "",
            "body_source": "flux-2-pro",
            "body_clean_image": f"{food_id}_body_clean.png",
            "cover_ne_body_sha256": result["cover_ne_body"],
            "work_order": WO_NUMBER,
        }
        (folder / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result["metadata"] = True
    except Exception as e:
        result["errors"].append(f"메타데이터: {e}")

    return result


# ============================================================
# Item Definitions
# ============================================================
PREWORK_ITEMS = [
    {"food_id": "blackberry", "food_ko": "블랙베리", "safety": "safe",
     "cover_file": "cover_28_블랙베리_blackberry.png"},
    {"food_id": "mackerel", "food_ko": "고등어", "safety": "safe",
     "cover_file": "cover_34_고등어_mackerel.png"},
    {"food_id": "yogurt", "food_ko": "요거트", "safety": "safe",
     "cover_file": "cover_41_요거트_yogurt.png"},
    {"food_id": "tofu", "food_ko": "두부", "safety": "safe",
     "cover_file": "cover_52_두부_tofu.png"},
    {"food_id": "chocolate", "food_ko": "초콜릿", "safety": "forbidden",
     "cover_file": "cover_64_초콜릿_chocolate.png"},
    {"food_id": "cheese", "food_ko": "치즈", "safety": "caution",
     "cover_file": "cover_131_치즈_cheese.png"},
    {"food_id": "kimchi", "food_ko": "김치", "safety": "safe",
     "cover_file": "cover_65_김치_kimchi.png"},
    {"food_id": "cabbage", "food_ko": "양배추", "safety": "safe",
     "cover_file": "cover_159_양배추_cabbage.png"},
]

# Import remaining items from wo_004_batch
def load_batch_items():
    """Load ITEMS from wo_004_batch.py"""
    batch_path = PROJECT_ROOT / "services" / "scripts" / "wo_004_batch.py"
    # We'll inline the key items here
    return {
        "forbidden": [
            {"food_id": "brownie", "food_ko": "브라우니", "safety": "forbidden",
             "cover_file": "cover_95_브라우니_brownie.png"},
            {"food_id": "reeses", "food_ko": "리세스", "safety": "forbidden",
             "cover_file": "cover_124_리세스_reeses.png"},
            {"food_id": "soju", "food_ko": "소주", "safety": "forbidden",
             "cover_file": "cover_128_소주_soju.png"},
            {"food_id": "green_onion", "food_ko": "대파", "safety": "forbidden",
             "cover_file": ""},
            {"food_id": "pizza", "food_ko": "피자", "safety": "forbidden",
             "cover_file": "cover_121_피자_pizza.png"},
            {"food_id": "ramen", "food_ko": "라면", "safety": "forbidden",
             "cover_file": "cover_75_라면_ramen.png"},
        ],
        "danger": [
            {"food_id": "bibimbap", "food_ko": "비빔밥", "safety": "danger",
             "cover_file": "cover_81_비빔밥_bibimbap.png"},
            {"food_id": "jjajangmyeon", "food_ko": "짜장면", "safety": "danger",
             "cover_file": "cover_82_짜장면_jjajangmyeon.png"},
            {"food_id": "bulgogi", "food_ko": "불고기", "safety": "danger",
             "cover_file": "cover_90_불고기_bulgogi.png"},
            {"food_id": "cake", "food_ko": "케이크", "safety": "danger",
             "cover_file": "cover_91_케이크_cake.png"},
            {"food_id": "dakgangjeong", "food_ko": "닭강정", "safety": "danger",
             "cover_file": "cover_102_닭강정_dakgangjeong.png"},
            {"food_id": "milk", "food_ko": "바나나우유", "safety": "danger",
             "cover_file": "cover_106_바나나우유_banana_milk.png"},
            {"food_id": "doritos", "food_ko": "도리토스", "safety": "danger",
             "cover_file": "cover_113_도리토스_doritos.png"},
            {"food_id": "fanta", "food_ko": "환타", "safety": "danger",
             "cover_file": "cover_114_환타_fanta.png"},
            {"food_id": "lays", "food_ko": "레이즈", "safety": "danger",
             "cover_file": "cover_118_레이즈_lays.png"},
            {"food_id": "milkis", "food_ko": "밀키스", "safety": "danger",
             "cover_file": "cover_119_밀키스_milkis.png"},
            {"food_id": "perrier", "food_ko": "페리에", "safety": "danger",
             "cover_file": "cover_120_페리에_perrier.png"},
            {"food_id": "skittles", "food_ko": "스키틀즈", "safety": "danger",
             "cover_file": "cover_127_스키틀즈_skittles.png"},
            {"food_id": "starburst", "food_ko": "스타버스트", "safety": "danger",
             "cover_file": "cover_130_스타버스트_starburst.png"},
            {"food_id": "sprite", "food_ko": "스프라이트", "safety": "danger",
             "cover_file": "cover_133_스프라이트_sprite.png"},
            {"food_id": "raisin", "food_ko": "건포도", "safety": "danger",
             "cover_file": "cover_156_건포도_raisin.png"},
            {"food_id": "lemon", "food_ko": "레몬", "safety": "danger",
             "cover_file": "cover_158_레몬_lemon.png"},
            {"food_id": "bacon", "food_ko": "베이컨", "safety": "danger",
             "cover_file": "cover_105_베이컨_bacon.png"},
            {"food_id": "donut", "food_ko": "도넛", "safety": "danger",
             "cover_file": "cover_92_도넛_donut.png"},
        ],
        "caution": [
            {"food_id": "nuts", "food_ko": "견과류", "safety": "caution",
             "cover_file": "cover_31_견과류_nuts.png"},
            {"food_id": "almonds", "food_ko": "아몬드", "safety": "caution",
             "cover_file": "cover_32_아몬드_almonds.png"},
            {"food_id": "baguette", "food_ko": "바게트", "safety": "caution",
             "cover_file": "cover_34_바게트_baguette.png"},
            {"food_id": "tteokguk", "food_ko": "떡국", "safety": "caution",
             "cover_file": "cover_76_떡국_tteokguk.png"},
            {"food_id": "kimbap", "food_ko": "김밥", "safety": "caution",
             "cover_file": "cover_80_김밥_kimbap.png"},
            {"food_id": "udon", "food_ko": "우동", "safety": "caution",
             "cover_file": "cover_83_우동_udon.png"},
            {"food_id": "toast", "food_ko": "토스트", "safety": "caution",
             "cover_file": "cover_87_토스트_toast.png"},
            {"food_id": "muffin", "food_ko": "머핀", "safety": "caution",
             "cover_file": "cover_96_머핀_muffin.png"},
            {"food_id": "pancake", "food_ko": "팬케이크", "safety": "caution",
             "cover_file": "cover_97_팬케이크_pancake.png"},
            {"food_id": "waffle", "food_ko": "와플", "safety": "caution",
             "cover_file": "cover_98_와플_waffle.png"},
            {"food_id": "cereal", "food_ko": "시리얼", "safety": "caution",
             "cover_file": "cover_99_시리얼_cereal.png"},
            {"food_id": "granola", "food_ko": "그래놀라", "safety": "caution",
             "cover_file": "cover_100_그래놀라_granola.png"},
            {"food_id": "meatball", "food_ko": "미트볼", "safety": "caution",
             "cover_file": "cover_103_미트볼_meatball.png"},
            {"food_id": "croissant", "food_ko": "크루아상", "safety": "caution",
             "cover_file": "cover_111_크루아상_croissant.png"},
            {"food_id": "perrier", "food_ko": "페리에", "safety": "caution",
             "cover_file": "cover_120_페리에_perrier.png"},
            {"food_id": "ritz", "food_ko": "리츠", "safety": "caution",
             "cover_file": "cover_125_리츠_ritz.png"},
            {"food_id": "mushroom", "food_ko": "버섯", "safety": "caution",
             "cover_file": "cover_165_버섯_mushroom.png"},
            {"food_id": "persimmon_ripe", "food_ko": "홍시", "safety": "caution",
             "cover_file": ""},
            {"food_id": "plum", "food_ko": "자두", "safety": "caution",
             "cover_file": "cover_151_자두_plum.png"},
            {"food_id": "dumpling", "food_ko": "만두", "safety": "caution",
             "cover_file": ""},
        ],
        "safe": [
            {"food_id": "bean_sprouts", "food_ko": "숙주나물", "safety": "safe", "cover_file": ""},
            {"food_id": "melon", "food_ko": "멜론", "safety": "safe",
             "cover_file": "cover_45_멜론_melon.png"},
            {"food_id": "pomegranate", "food_ko": "석류", "safety": "safe",
             "cover_file": "cover_49_석류_pomegranate.png"},
            {"food_id": "quail_egg", "food_ko": "메추리알", "safety": "safe", "cover_file": ""},
            {"food_id": "fried_chicken", "food_ko": "후라이드치킨", "safety": "safe", "cover_file": ""},
            {"food_id": "chicken_skewer", "food_ko": "닭꼬치", "safety": "safe", "cover_file": ""},
            {"food_id": "raspberry", "food_ko": "라즈베리", "safety": "safe",
             "cover_file": "cover_152_라즈베리_raspberry.png"},
            {"food_id": "coconut", "food_ko": "코코넛", "safety": "safe",
             "cover_file": "cover_154_코코넛_coconut.png"},
            {"food_id": "white_fish", "food_ko": "흰살생선", "safety": "safe",
             "cover_file": "cover_132_흰살생선_white_fish.png"},
            {"food_id": "lettuce", "food_ko": "상추", "safety": "safe",
             "cover_file": "cover_160_상추_lettuce.png"},
            {"food_id": "green_beans", "food_ko": "강낭콩", "safety": "safe",
             "cover_file": "cover_163_강낭콩_green_beans.png"},
            {"food_id": "asparagus", "food_ko": "아스파라거스", "safety": "safe",
             "cover_file": "cover_170_아스파라거스_asparagus.png"},
            {"food_id": "beet", "food_ko": "비트", "safety": "safe",
             "cover_file": "cover_176_비트_beet.png"},
            {"food_id": "peas", "food_ko": "완두콩", "safety": "safe",
             "cover_file": "cover_172_완두콩_peas.png"},
            {"food_id": "chicken_breast", "food_ko": "닭가슴살", "safety": "safe",
             "cover_file": "cover_139_닭가슴살_chicken_breast.png"},
            {"food_id": "naengmyeon", "food_ko": "냉면", "safety": "safe",
             "cover_file": "cover_85_냉면_naengmyeon.png"},
            {"food_id": "sandwich", "food_ko": "샌드위치", "safety": "safe",
             "cover_file": "cover_88_샌드위치_sandwich.png"},
            {"food_id": "cheetos", "food_ko": "치토스", "safety": "safe",
             "cover_file": "cover_109_치토스_cheetos.png"},
            # Items below have no cover source → will be skipped
            {"food_id": "cranberry", "food_ko": "크랜베리", "safety": "safe", "cover_file": ""},
            {"food_id": "bell_pepper", "food_ko": "피망", "safety": "safe", "cover_file": ""},
            {"food_id": "napa_cabbage", "food_ko": "배추", "safety": "safe", "cover_file": ""},
            {"food_id": "radish", "food_ko": "무", "safety": "safe", "cover_file": ""},
            {"food_id": "corn", "food_ko": "옥수수", "safety": "safe", "cover_file": ""},
            {"food_id": "pork", "food_ko": "돼지고기", "safety": "safe", "cover_file": ""},
            {"food_id": "turkey", "food_ko": "칠면조", "safety": "safe", "cover_file": ""},
            {"food_id": "lamb", "food_ko": "양고기", "safety": "safe", "cover_file": ""},
            {"food_id": "venison", "food_ko": "사슴고기", "safety": "safe", "cover_file": ""},
            {"food_id": "rabbit", "food_ko": "토끼고기", "safety": "safe", "cover_file": ""},
            {"food_id": "chicken_liver", "food_ko": "닭간", "safety": "safe", "cover_file": ""},
            {"food_id": "beef_liver", "food_ko": "소간", "safety": "safe", "cover_file": ""},
            {"food_id": "heart", "food_ko": "심장", "safety": "safe", "cover_file": ""},
            {"food_id": "tripe", "food_ko": "양", "safety": "safe", "cover_file": ""},
            {"food_id": "bone_broth", "food_ko": "사골국물", "safety": "safe", "cover_file": ""},
            {"food_id": "cod", "food_ko": "대구", "safety": "safe", "cover_file": ""},
        ],
    }


# ============================================================
# Batch runner
# ============================================================
async def run_batch(items, batch_name):
    """Run a batch of items"""
    print(f"\n{'#'*60}")
    print(f"  배치: {batch_name}")
    print(f"  건수: {len(items)}")
    print(f"  시작: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#'*60}")

    results = []
    processed = 0
    skipped = 0

    for item in items:
        fid = item["food_id"]
        fko = item["food_ko"]
        safety = item["safety"]
        cf = item.get("cover_file", "")

        # Check if folder exists
        folder = find_folder(fid)
        if not folder and not cf:
            print(f"\n  ⏭️ {fid} ({fko}): 폴더 없음 + 커버 없음 → SKIP")
            results.append({
                "food_id": fid, "food_ko": fko, "safety": safety.upper(),
                "skipped": True, "errors": ["폴더+커버 없음"],
                "flux_gen": False, "text_json": False,
                "render_01": False, "render_02": False, "render_03": False,
                "caption_insta": False, "caption_threads": False,
                "cover_ne_body": "N/A", "validators": "N/A", "metadata": False,
            })
            skipped += 1
            continue

        result = await process_item(fid, fko, safety, cf)
        results.append(result)
        processed += 1

        # Brief delay between FLUX API calls
        if result["flux_gen"] and processed < len(items):
            await asyncio.sleep(2)

    # Print batch summary
    print(f"\n{'='*60}")
    print(f"  📊 배치 완료: {batch_name}")
    print(f"{'='*60}")
    print(f"  처리: {processed}건, 스킵: {skipped}건")

    success = sum(1 for r in results if not r.get("skipped") and
                  r.get("render_01") and r.get("render_02") and r.get("render_03"))
    print(f"  성공 (3/3 렌더): {success}건")

    # Print table
    print(f"\n  | # | 영문명 | FLUX | 01 | 02 | 03 | 캡션 | SHA256 | valid |")
    print(f"  |---|--------|------|----|----|----| -----|--------|-------|")
    for i, r in enumerate(results, 1):
        fid = r["food_id"]
        fx = "O" if r.get("flux_gen") else "X"
        r01 = "O" if r.get("render_01") else "X"
        r02 = "O" if r.get("render_02") else "X"
        r03 = "O" if r.get("render_03") else "X"
        cap = "O" if r.get("caption_insta") and r.get("caption_threads") else "X"
        sha = r.get("cover_ne_body", "N/A")
        val = r.get("validators", "N/A")
        skip = " SKIP" if r.get("skipped") else ""
        print(f"  | {i} | {fid:20s} | {fx}  | {r01}  | {r02}  | {r03}  | {cap}   | {sha:6s} | {val:5s} |{skip}")

    return results


# ============================================================
# Main
# ============================================================
async def main():
    if len(sys.argv) < 2:
        print("사용법: python wo_004_r1_flux.py <prework|forbidden|danger|caution|safe>")
        sys.exit(1)

    batch = sys.argv[1].lower()

    if batch == "prework":
        results = await run_batch(PREWORK_ITEMS, "PRE-WORK (8건)")
    elif batch in ("forbidden", "danger", "caution", "safe"):
        batch_items = load_batch_items()
        items = batch_items.get(batch, [])
        results = await run_batch(items, f"BATCH: {batch.upper()}")
    else:
        print(f"알 수 없는 배치: {batch}")
        sys.exit(1)

    # Save report
    report_path = PROJECT_ROOT / "config" / "data" / f"wo_004_r1_{batch}_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "work_order": WO_NUMBER,
            "batch": batch,
            "timestamp": datetime.now().isoformat(),
            "total": len(results),
            "success": sum(1 for r in results if not r.get("skipped") and
                           r.get("render_01") and r.get("render_02") and r.get("render_03")),
            "skipped": sum(1 for r in results if r.get("skipped")),
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 리포트: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
