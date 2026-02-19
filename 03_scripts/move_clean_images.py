#!/usr/bin/env python3
"""CleanReady 이미지를 각 음식폴더 blog/ 로 이동"""
import os
import shutil

BASE = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents"
CLEAN_READY = f"{BASE}/99_CleanReady"

# 이미지 타임스탬프 → (폴더상위, 폴더명) 매핑
MAPPING = {
    "120403": ("4_posted", "006_apple"),
    "122848": ("4_posted", "003_blueberry"),
    "125907": ("4_posted", "010_watermelon"),
    "130026": ("4_posted", "004_cherry"),
    "130103": ("4_posted", "007_pineapple"),
    "130106": ("4_posted", "008_banana"),
    "130113": ("4_posted", "009_broccoli"),
    "130428": ("4_posted", "011_strawberry"),
    "130432": ("4_posted", "012_mango"),
    "130437": ("4_posted", "013_orange_오렌지"),
    "130443": ("4_posted", "014_pear_배"),
    "130628": ("4_posted", "015_kiwi_키위"),
    "130632": ("4_posted", "016_papaya_파파야"),
    "130640": ("4_posted", "018_rice_흰쌀밥"),
    "130647": ("4_posted", "019_cucumber_오이"),
    "130834": ("4_posted", "020_pringles_프링글스"),
    "130839": ("4_posted", "022_avocado_아보카도"),
    "130848": ("4_posted", "021_sausage_소시지"),
    "130853": ("4_posted", "023_coca_cola_콜라"),
    "131120": ("4_posted", "024_olive_올리브"),
    "131125": ("4_posted", "025_blackberry_블랙베리"),
    "131130": ("4_posted", "026_spinach_시금치"),
    "131138": ("4_posted", "027_zucchini_애호박"),
    "131508": ("4_posted", "028_chicken_닭고기"),
    "131520": ("4_posted", "029_poached_egg_수란"),
    "131529": ("4_posted", "030_nuts_견과류"),
    "131536": ("4_posted", "031_boiled_egg_삶은달걀"),
    "131817": ("1_cover_only", "048_tofu"),
    "131822": ("4_posted", "036_beef_소고기"),
    "131829": ("4_posted", "041_burdock_우엉"),
    "131833": ("4_posted", "049_salmon_연어"),
    "131951": ("4_posted", "054_sweet_pumpkin"),
    "132017": ("4_posted", "055_grape_포도"),
    "132021": ("4_posted", "056_raisin"),
    "132250": ("4_posted", "061_yangnyeom_chicken_양념치킨"),
    "132255": ("4_posted", "073_samgyeopsal_삼겹살"),
    "132300": ("4_posted", "077_icecream_아이스크림"),
    "132434": ("4_posted", "032_milk_우유"),
    "132454": ("4_posted", "094_kitkat_킷캣"),
    "132500": ("4_posted", "102_soju_소주"),
    "132559": ("4_posted", "105_cheese"),
    "132608": ("4_posted", "109_shrimp_새우"),
    "132620": ("4_posted", "119_tuna_참치"),
    "132627": ("4_posted", "120_celery_셀러리"),
    "132902": ("4_posted", "132_kale_케일"),
    "132913": ("4_posted", "133_pasta_파스타(면)"),
    "132924": ("4_posted", "035_potato_감자"),
    "132927": ("1_cover_only", "136_korean_melon"),
    "133109": ("3_approved", "051_onion_양파"),
    "133114": ("3_approved", "052_banana_milk_바나나우유"),
    "133314": ("3_approved", "053_garlic_마늘"),
    "133321": ("3_approved", "060_fried_chicken_후라이드치킨"),
}

def main():
    moved = 0
    errors = []

    for fname in os.listdir(CLEAN_READY):
        if not fname.endswith(".png") or not fname.startswith("hf_"):
            continue

        # 타임스탬프 추출: hf_20260212_HHMMSS_uuid.png
        parts = fname.split("_")
        if len(parts) < 3:
            continue
        timestamp = parts[2]  # HHMMSS

        if timestamp not in MAPPING:
            print(f"⚠️ 매핑 없음: {fname} (timestamp: {timestamp})")
            errors.append(fname)
            continue

        parent, folder = MAPPING[timestamp]
        # 2026-02-13: 플랫 구조 - 직접 폴더 참조
        dest_dir = f"{BASE}/{folder}/02_Blog"

        # blog 폴더 생성
        os.makedirs(dest_dir, exist_ok=True)

        src = f"{CLEAN_READY}/{fname}"
        dst = f"{dest_dir}/2_음식사진.png"

        try:
            shutil.move(src, dst)
            print(f"✅ {folder} → blog/2_음식사진.png")
            moved += 1
        except Exception as e:
            print(f"❌ {fname}: {e}")
            errors.append(fname)

    print(f"\n{'='*50}")
    print(f"완료: {moved}개 이동")
    if errors:
        print(f"오류: {len(errors)}개")
        for e in errors:
            print(f"  - {e}")

if __name__ == "__main__":
    main()
