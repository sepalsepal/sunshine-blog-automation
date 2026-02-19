#!/usr/bin/env python3
"""
batch_produce_v2.py - WO-BATCH-003-B AI팀 담당 어셋 일괄 제작 (보완)
지시자: 김부장 / 승인: PD 박세준

보완 사항:
- 블로그 슬라이드 5장 신규 생성 (infographic_generator.py)
- 캡션 3종 신규 생성

RULE-REPORT-001 적용
"""

# ═══════════════════════════════════════════════════════════════
# 🔴 WO-FREEZE-001 동결 — 파이프라인 외부 단독 실행 차단
# ═══════════════════════════════════════════════════════════════
import sys
import os

# 파이프라인 CLI 통해 실행 시 환경변수 설정됨
if os.environ.get("PIPELINE_AUTHORIZED") != "true":
    print("🔴 FROZEN: WO-FREEZE-001 동결 중. 직접 실행 차단됨.")
    print("   사유: 파이프라인 외부 단독 실행 금지")
    print("   해제: cli.py 통해 실행하거나 --force-pd-approved 플래그 사용")
    print("   또는: PIPELINE_AUTHORIZED=true python3 batch_produce_v2.py")
    sys.exit(1)
# ═══════════════════════════════════════════════════════════════

import os
import json
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# infographic_generator 임포트
from scripts.infographic_generator import (
    generate_nutrition_info,
    generate_do_dont,
    generate_dosage_table,
    generate_precautions,
    generate_cooking_method
)

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CTA_SOURCE_DIR = PROJECT_ROOT / "01_contents" / "sunshine photos" / "00_Best" / "crop"
COVER_SCRIPT = PROJECT_ROOT / "services" / "scripts" / "blog_cover_v2.py"

# 2026-02-13: 플랫 구조로 변경 - STATUS_DIRS 제거
# 이제 contents/ 직접 스캔

# 결과 저장
results = {
    "processed": [],
    "skipped": [],
    "errors": [],
    "stats": {
        "cover": 0,
        "cta": 0,
        "slide_03": 0,
        "slide_04": 0,
        "slide_05": 0,
        "slide_06": 0,
        "slide_07": 0,
        "caption_insta": 0,
        "caption_thread": 0,
        "caption_blog": 0,
    },
    "pd_todo": {
        "clean_source": [],
        "food_image": [],
        "dog_image": [],
        "food_data": []
    }
}


def load_food_data():
    """food_data.json 로드"""
    if FOOD_DATA_PATH.exists():
        with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_cta_images():
    """CTA 이미지 목록"""
    if CTA_SOURCE_DIR.exists():
        return list(CTA_SOURCE_DIR.glob("*.png"))
    return []


def get_all_folders():
    """모든 콘텐츠 폴더 스캔 (플랫 구조)"""
    folders = []
    # 2026-02-13: contents/ 직접 스캔 (플랫 구조)
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        # PascalCase 폴더명: 001_Pumpkin, 002_Carrot
        match = re.match(r'^(\d{3})_([A-Za-z]+)', item.name)
        if match:
            folders.append({
                "num": int(match.group(1)),
                "food_en": match.group(2),
                "name": item.name,
                "path": item
            })
    return sorted(folders, key=lambda x: x["num"])


def generate_instagram_caption(food_info: dict) -> str:
    """인스타 캡션 생성"""
    name_ko = food_info.get("name", "음식")
    safety = food_info.get("safety", "SAFE")
    dosages = food_info.get("dosages", {})
    do_items = food_info.get("do_items", [])

    safety_emoji = "🟢" if safety == "SAFE" else "🟡" if safety == "CAUTION" else "🔴"
    answer = f"네, {name_ko}은(는) 강아지에게 급여 가능해요! 🎉" if safety in ["SAFE", "CAUTION"] else f"❌ {name_ko}은(는) 강아지에게 급여 금지예요!"

    dosage_text = ""
    if dosages:
        for size, info in dosages.items():
            if isinstance(info, dict):
                dosage_text += f"{size} ({info.get('weight', '')}) — {info.get('amount', '')} ({info.get('desc', '')})\n"

    tips_text = "\n".join([f"• {tip}" for tip in do_items[:3]])

    caption = f"""🐕 강아지 {name_ko}, 줘도 되나요?

{answer}

📏 체중별 급여량

{dosage_text}
✅ 급여 팁
{tips_text}

우리 햇살이도 {name_ko} 좋아하는데, 처음 줄 땐 아주 조금만 줬어요.

처음 주실 땐 조금만! 반응 보고 늘려주세요.

#강아지{name_ko.replace(' ', '')} #강아지간식 #반려견음식 #강아지먹어도되나요 #펫푸드 #반려견간식 #햇살이네음식연구소

⚠️ 이 콘텐츠는 AI의 도움을 받아 작성되었습니다."""
    return caption


def generate_threads_caption(food_info: dict) -> str:
    """쓰레드 캡션 생성"""
    name_ko = food_info.get("name", "음식")
    safety = food_info.get("safety", "SAFE")
    dosages = food_info.get("dosages", {})

    answer = "네! 급여 가능해요 ✅" if safety in ["SAFE", "CAUTION"] else "❌ 급여 금지예요"

    small_dose = ""
    large_dose = ""
    if dosages:
        if "소형견" in dosages:
            small_dose = dosages["소형견"].get("amount", "소량")
        if "대형견" in dosages:
            large_dose = dosages["대형견"].get("amount", "적당량")

    caption = f"""🐕 강아지 {name_ko} 줘도 되나요?

{answer}

📏 급여량
소형견: {small_dose}
대형견: {large_dose}

처음엔 아주 조금만!
반응 보고 늘려주세요

⚠️ AI 도움 작성"""
    return caption


def generate_blog_caption(food_info: dict) -> str:
    """블로그 캡션 생성"""
    name_ko = food_info.get("name", "음식")
    safety = food_info.get("safety", "SAFE")
    nutrients = food_info.get("nutrients", [])
    dosages = food_info.get("dosages", {})
    do_items = food_info.get("do_items", [])
    dont_items = food_info.get("dont_items", [])
    precautions = food_info.get("precautions", [])

    safety_text = "SAFE" if safety == "SAFE" else "CAUTION" if safety == "CAUTION" else "FORBIDDEN"
    safety_emoji = "🟢" if safety == "SAFE" else "🟡" if safety == "CAUTION" else "🔴"

    nutrient_text = ""
    for n in nutrients[:5]:
        if isinstance(n, dict):
            nutrient_text += f"- {n.get('name', '')}: {n.get('value', '')}{n.get('unit', '')} ({n.get('benefit', '')})\n"

    dosage_text = ""
    for size, info in dosages.items():
        if isinstance(info, dict):
            dosage_text += f"- {size} ({info.get('weight', '')}): {info.get('amount', '')} - {info.get('desc', '')}\n"

    do_text = "\n".join([f"✅ {item}" for item in do_items[:5]])
    dont_text = "\n".join([f"❌ {item}" for item in dont_items[:5]])

    precaution_text = ""
    for p in precautions[:5]:
        if isinstance(p, dict):
            precaution_text += f"⚠️ {p.get('title', '')}: {p.get('desc', '')}\n"

    caption = f"""[이미지 1번: 표지]

안녕하세요, 11살 골든리트리버 햇살이 엄마예요.

오늘은 많은 분들이 궁금해하시는 '{name_ko}' 급여에 대해 이야기해볼게요.
우리 햇살이도 {name_ko}을(를) 정말 좋아하는데요, 처음 줬을 때 반응이 아직도 기억나요!

[이미지 2번: 음식 사진]


## 강아지 {name_ko}, 먹어도 되나요?

{safety_emoji} 결론부터 말씀드리면, {safety_text} 등급이에요.

{name_ko}에는 다양한 영양소가 들어있어요:
{nutrient_text}

[이미지 3번: 영양 정보]


## 체중별 급여량

{dosage_text}

[이미지 4번: 급여 가능/불가]


## 급여 시 이렇게 하세요

{do_text}

## 이건 피해주세요

{dont_text}

[이미지 5번: 급여량 표]


## 주의사항

{precaution_text}

[이미지 6번: 주의사항]


## 간단 레시피

1. {name_ko}을(를) 깨끗이 씻어주세요
2. 적당한 크기로 잘라주세요
3. 필요 시 익혀서 급여하세요
4. 처음엔 소량만 급여하세요
5. 반응을 관찰하세요

[이미지 7번: 조리 방법]


## 마무리

{name_ko}은(는) 올바르게 급여하면 우리 강아지에게 좋은 간식이 될 수 있어요.
처음 급여할 때는 소량으로 시작하고, 반응을 잘 살펴봐 주세요!

궁금한 점이 있으시면 댓글로 남겨주세요 💛

[이미지 8번: CTA]

---

⚠️ 이 콘텐츠는 AI의 도움을 받아 작성되었습니다.
전문적인 수의학적 조언이 필요하시면 수의사와 상담해 주세요."""
    return caption


def process_folder(folder, food_data, cta_images):
    """단일 폴더 처리"""
    num = folder["num"]
    food_en = folder["food_en"]
    path = folder["path"]

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"[{num:03d}/165] #{num:03d}_{food_en}")

    # food_data 확인
    food_info = food_data.get(str(num))
    if not food_info:
        print(f"  ⚠️ food_data.json에 없음 - SKIP")
        results["skipped"].append(f"#{num} - food_data 없음")
        results["pd_todo"]["food_data"].append(f"#{num}_{food_en}")
        return

    food_ko = food_info.get("name", "")
    safety = food_info.get("safety", "SAFE")

    # 2026-02-13: 새 폴더 구조
    blog_dir = path / "02_Blog"
    insta_dir = path / "01_Insta&Thread"
    clean_dir = path / "00_Clean"

    # 폴더 생성
    blog_dir.mkdir(exist_ok=True)
    insta_dir.mkdir(exist_ok=True)

    produced = []

    # === 노드 11: 인스타 캡션 (PascalCase) ===
    insta_caption_file = insta_dir / f"{food_en}_{safety}_Insta_Caption.txt"
    if insta_caption_file.exists():
        print(f"  ├─ 인스타캡션 ✅ (기존재 SKIP)")
    else:
        try:
            caption = generate_instagram_caption(food_info)
            with open(insta_caption_file, "w", encoding="utf-8") as f:
                f.write(caption)
            print(f"  ├─ 인스타캡션 ✅ (신규 생성)")
            results["stats"]["caption_insta"] += 1
            produced.append("insta_caption")
        except Exception as e:
            print(f"  ├─ 인스타캡션 ❌ ({e})")
            results["errors"].append(f"#{num} 인스타캡션: {str(e)[:30]}")

    # === 노드 12: 쓰레드 캡션 (PascalCase) ===
    threads_caption_file = insta_dir / f"{food_en}_{safety}_Threads_Caption.txt"
    if threads_caption_file.exists():
        print(f"  ├─ 쓰레드캡션 ✅ (기존재 SKIP)")
    else:
        try:
            caption = generate_threads_caption(food_info)
            with open(threads_caption_file, "w", encoding="utf-8") as f:
                f.write(caption)
            print(f"  ├─ 쓰레드캡션 ✅ (신규 생성)")
            results["stats"]["caption_thread"] += 1
            produced.append("threads_caption")
        except Exception as e:
            print(f"  ├─ 쓰레드캡션 ❌ ({e})")
            results["errors"].append(f"#{num} 쓰레드캡션: {str(e)[:30]}")

    # === 노드 13: 블로그 캡션 (PascalCase) ===
    blog_caption_file = blog_dir / f"{food_en}_{safety}_Blog_Caption.txt"
    if blog_caption_file.exists():
        print(f"  ├─ 블로그캡션 ✅ (기존재 SKIP)")
    else:
        try:
            caption = generate_blog_caption(food_info)
            with open(blog_caption_file, "w", encoding="utf-8") as f:
                f.write(caption)
            print(f"  ├─ 블로그캡션 ✅ (신규 생성)")
            results["stats"]["caption_blog"] += 1
            produced.append("blog_caption")
        except Exception as e:
            print(f"  ├─ 블로그캡션 ❌ ({e})")
            results["errors"].append(f"#{num} 블로그캡션: {str(e)[:30]}")

    # === 노드 21: 표지 제작 (PascalCase) ===
    cover_file = blog_dir / f"{food_en}_Common_01_Cover.png"
    if cover_file.exists():
        print(f"  ├─ 표지 ✅ (기존재 SKIP)")
    else:
        clean_images = list(clean_dir.glob("hf_*.png")) if clean_dir.exists() else []
        if clean_images:
            clean_src = clean_images[0]
            try:
                result = subprocess.run(
                    ["python3", str(COVER_SCRIPT), str(clean_src), food_ko, str(cover_file)],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    print(f"  ├─ 표지 ✅ (blog_cover_v2.py)")
                    results["stats"]["cover"] += 1
                    produced.append("cover")
                else:
                    print(f"  ├─ 표지 ❌ (생성 실패)")
                    results["errors"].append(f"#{num} 표지: 생성 실패")
            except Exception as e:
                print(f"  ├─ 표지 ❌ ({e})")
                results["errors"].append(f"#{num} 표지: {str(e)[:30]}")
        else:
            print(f"  ├─ 표지 ⚠️ (클린소스 없음 → PD투두)")
            results["pd_todo"]["clean_source"].append(f"#{num}_{food_en}")

    # === 노드 23: CTA 선정 (PascalCase) ===
    cta_file = blog_dir / f"{food_en}_Common_08_Cta.png"
    if cta_file.exists():
        print(f"  ├─ CTA ✅ (기존재 SKIP)")
    else:
        if cta_images:
            cta_idx = num % len(cta_images)
            cta_src = cta_images[cta_idx]
            shutil.copy(cta_src, cta_file)
            print(f"  ├─ CTA ✅ (크롭폴더 선정)")
            results["stats"]["cta"] += 1
            produced.append("cta")
        else:
            print(f"  ├─ CTA ❌ (소스 없음)")

    # === 노드 24: 블로그 슬라이드 5장 ===
    nutrients = food_info.get("nutrients", [])
    do_items = food_info.get("do_items", [])
    dont_items = food_info.get("dont_items", [])
    dosages = food_info.get("dosages", {})
    precautions = food_info.get("precautions", [])

    # 슬라이드 03: 영양정보 (PascalCase)
    slide_03 = blog_dir / f"{food_en}_Blog_03_Nutrition.png"
    if slide_03.exists():
        print(f"  ├─ 슬라이드03 ✅ (기존재 SKIP)")
    else:
        try:
            generate_nutrition_info(food_ko, nutrients, safety, "", slide_03)
            print(f"  ├─ 슬라이드03 ✅ (infographic_generator)")
            results["stats"]["slide_03"] += 1
            produced.append("slide_03")
        except Exception as e:
            print(f"  ├─ 슬라이드03 ❌ ({e})")
            results["errors"].append(f"#{num} 슬라이드03: {str(e)[:30]}")

    # 슬라이드 04: 급여가능/불가 (PascalCase)
    slide_04 = blog_dir / f"{food_en}_Blog_04_Feeding.png"
    if slide_04.exists():
        print(f"  ├─ 슬라이드04 ✅ (기존재 SKIP)")
    else:
        try:
            generate_do_dont(food_ko, do_items, dont_items, safety, slide_04)
            print(f"  ├─ 슬라이드04 ✅ (infographic_generator)")
            results["stats"]["slide_04"] += 1
            produced.append("slide_04")
        except Exception as e:
            print(f"  ├─ 슬라이드04 ❌ ({e})")
            results["errors"].append(f"#{num} 슬라이드04: {str(e)[:30]}")

    # 슬라이드 05: 급여량표 (PascalCase)
    slide_05 = blog_dir / f"{food_en}_Blog_05_Amount.png"
    if slide_05.exists():
        print(f"  ├─ 슬라이드05 ✅ (기존재 SKIP)")
    else:
        try:
            generate_dosage_table(dosages, None, "", safety, slide_05)
            print(f"  ├─ 슬라이드05 ✅ (infographic_generator)")
            results["stats"]["slide_05"] += 1
            produced.append("slide_05")
        except Exception as e:
            print(f"  ├─ 슬라이드05 ❌ ({e})")
            results["errors"].append(f"#{num} 슬라이드05: {str(e)[:30]}")

    # 슬라이드 06: 주의사항 (PascalCase)
    slide_06 = blog_dir / f"{food_en}_Blog_06_Caution.png"
    if slide_06.exists():
        print(f"  ├─ 슬라이드06 ✅ (기존재 SKIP)")
    else:
        try:
            # precautions는 List[Dict] 형태로 직접 전달 (WO-SCHEMA-001 버그 수정)
            generate_precautions(food_ko, precautions, "", safety, slide_06)
            print(f"  ├─ 슬라이드06 ✅ (infographic_generator)")
            results["stats"]["slide_06"] += 1
            produced.append("slide_06")
        except Exception as e:
            print(f"  ├─ 슬라이드06 ❌ ({e})")
            results["errors"].append(f"#{num} 슬라이드06: {str(e)[:30]}")

    # 슬라이드 07: 조리방법 (PascalCase)
    slide_07 = blog_dir / f"{food_en}_Blog_07_Cooking.png"
    if slide_07.exists():
        print(f"  └─ 슬라이드07 ✅ (기존재 SKIP)")
    else:
        try:
            steps = [
                {"title": "깨끗이 씻기", "desc": "흐르는 물에 깨끗이 세척하세요"},
                {"title": "적당히 자르기", "desc": "강아지가 먹기 좋은 크기로 자르세요"},
                {"title": "익히기(선택)", "desc": "필요시 삶거나 쪄서 급여하세요"},
                {"title": "식히기", "desc": "적당한 온도로 식혀주세요"},
                {"title": "소량 급여", "desc": "처음엔 소량만 급여하세요"},
            ]
            generate_cooking_method(food_ko, steps, "처음 급여 시 소량으로 시작하세요", safety, slide_07)
            print(f"  └─ 슬라이드07 ✅ (infographic_generator)")
            results["stats"]["slide_07"] += 1
            produced.append("slide_07")
        except Exception as e:
            print(f"  └─ 슬라이드07 ❌ ({e})")
            results["errors"].append(f"#{num} 슬라이드07: {str(e)[:30]}")

    # === insta 폴더에 공통 이미지 복사 (PascalCase) ===
    for common_file in ["Common_01_Cover", "Common_08_Cta"]:
        src = blog_dir / f"{food_en}_{common_file}.png"
        dst = insta_dir / f"{food_en}_{common_file}.png"
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)

    # === PD님 투두 추가 (PascalCase) ===
    food_img = blog_dir / f"{food_en}_Common_02_Food.png"
    if not food_img.exists():
        results["pd_todo"]["food_image"].append(f"#{num}_{food_en}")

    dog_img = insta_dir / f"{food_en}_Insta_03_Dog.png"
    if not dog_img.exists():
        results["pd_todo"]["dog_image"].append(f"#{num}_{food_en}")

    if produced:
        results["processed"].append(f"#{num}_{food_en}: {', '.join(produced)}")

    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def run_notion_sync():
    """노션 동기화 실행"""
    print("\n" + "="*60)
    print("노션 동기화 실행")
    print("="*60)

    sync_script = PROJECT_ROOT / "scripts" / "notion_sync.py"
    if sync_script.exists():
        try:
            result = subprocess.run(
                ["python3", str(sync_script)],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print("✅ 노션 동기화 완료")
                print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
            else:
                print(f"❌ 노션 동기화 실패: {result.stderr[:200]}")
        except Exception as e:
            print(f"❌ 노션 동기화 에러: {e}")
    else:
        print("⚠️ notion_sync.py 없음")


def print_report():
    """결과 보고서 출력"""
    print("\n")
    print("━"*60)
    print("📋 WO-BATCH-003-B 제작 완료 보고서")
    print("━"*60)
    print(f"\n실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n[1. 제작 현황]")
    print(f"  완료: {len(results['processed'])}건")
    print(f"  스킵: {len(results['skipped'])}건")
    print(f"  에러: {len(results['errors'])}건")

    print(f"\n[2. 노드별 제작 건수]")
    print(f"  캡션 3종:")
    print(f"    - 인스타캡션 (노드11): {results['stats']['caption_insta']}건")
    print(f"    - 쓰레드캡션 (노드12): {results['stats']['caption_thread']}건")
    print(f"    - 블로그캡션 (노드13): {results['stats']['caption_blog']}건")
    print(f"  이미지:")
    print(f"    - 표지 (노드21): {results['stats']['cover']}건")
    print(f"    - CTA (노드23): {results['stats']['cta']}건")
    print(f"    - 슬라이드03: {results['stats']['slide_03']}건")
    print(f"    - 슬라이드04: {results['stats']['slide_04']}건")
    print(f"    - 슬라이드05: {results['stats']['slide_05']}건")
    print(f"    - 슬라이드06: {results['stats']['slide_06']}건")
    print(f"    - 슬라이드07: {results['stats']['slide_07']}건")

    print(f"\n[3. 스킵 사유별 분류]")
    print(f"  - food_data 없음: {len(results['pd_todo']['food_data'])}건")
    print(f"  - 기존재 SKIP: (다수)")

    if results['errors']:
        print(f"\n[에러 목록]")
        for err in results['errors'][:10]:
            print(f"  ❌ {err}")
        if len(results['errors']) > 10:
            print(f"  ... 외 {len(results['errors'])-10}건")

    print("\n" + "━"*60)
    print("📋 PD님 투두리스트")
    print("━"*60)

    print(f"\n[표지 클린 소스 필요] {len(results['pd_todo']['clean_source'])}건")
    for item in results['pd_todo']['clean_source'][:10]:
        print(f"  □ {item}")
    if len(results['pd_todo']['clean_source']) > 10:
        print(f"  ... 외 {len(results['pd_todo']['clean_source'])-10}건")

    print(f"\n[음식 이미지 필요] {len(results['pd_todo']['food_image'])}건")
    print(f"  (전체 목록 생략 - 대부분 미제작)")

    print(f"\n[강아지 이미지 필요] {len(results['pd_todo']['dog_image'])}건")
    print(f"  (전체 목록 생략 - 대부분 미제작)")

    print(f"\n[food_data 추가 필요] {len(results['pd_todo']['food_data'])}건")
    for item in results['pd_todo']['food_data']:
        print(f"  □ {item}")

    print("\n" + "━"*60)


def main():
    print("="*60)
    print("WO-BATCH-003-B: AI팀 담당 어셋 일괄 제작 (보완)")
    print("="*60)

    food_data = load_food_data()
    print(f"food_data.json: {len(food_data)}개 음식")

    cta_images = get_cta_images()
    print(f"CTA 소스: {len(cta_images)}개 이미지")

    folders = get_all_folders()
    print(f"콘텐츠 폴더: {len(folders)}개")

    # 전체 처리
    for i, folder in enumerate(folders):
        process_folder(folder, food_data, cta_images)

        # 10개마다 진행률 표시
        if (i + 1) % 10 == 0:
            print(f"\n>>> 진행률: {i+1}/{len(folders)} ({(i+1)*100//len(folders)}%)")

    # 노션 동기화
    run_notion_sync()

    # 결과 보고
    print_report()


if __name__ == "__main__":
    main()
