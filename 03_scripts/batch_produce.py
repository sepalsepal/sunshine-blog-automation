#!/usr/bin/env python3
"""
batch_produce.py - WO-BATCH-003 AI팀 담당 어셋 일괄 제작
지시자: 김부장 / 승인: PD 박세준

제작 대상:
- 노드 21: 표지 (0_clean 있는 경우만)
- 노드 23: CTA 선정
- 노드 24: 블로그 슬라이드 리네이밍
- 노드 11,12,13: 캡션 (기존 있으면 SKIP)

PD님 담당 (SKIP):
- 노드 22: 음식 이미지 (AI 생성)
- 노드 25: 강아지 이미지 (AI 생성)
"""

import os
import sys
import json
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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
    "pd_todo": {
        "clean_source": [],
        "food_image": [],
        "dog_image": []
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


def process_folder(folder, food_data, cta_images):
    """단일 폴더 처리"""
    num = folder["num"]
    food_en = folder["food_en"]
    path = folder["path"]

    print(f"\n{'='*50}")
    print(f"[{num:03d}] {folder['name']}")
    print(f"{'='*50}")

    # food_data 확인
    food_info = food_data.get(str(num))
    if not food_info:
        print(f"  ⚠️ food_data.json에 없음 - SKIP")
        results["skipped"].append(f"#{num} - food_data 없음")
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

    # === 노드 21: 표지 제작 (PascalCase) ===
    cover_file = blog_dir / f"{food_en}_Common_01_Cover.png"
    if cover_file.exists():
        print(f"  ✓ 표지 이미 존재")
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
                    print(f"  ✅ 표지 생성 완료")
                    produced.append("cover")
                else:
                    print(f"  ❌ 표지 생성 실패: {result.stderr[:100]}")
                    results["errors"].append(f"#{num} 표지: {result.stderr[:50]}")
            except Exception as e:
                print(f"  ❌ 표지 생성 에러: {e}")
                results["errors"].append(f"#{num} 표지: {str(e)[:50]}")
        else:
            print(f"  ⚠️ 클린 소스 없음 → PD님 투두")
            results["pd_todo"]["clean_source"].append(f"#{num}_{food_en}")

    # === 노드 23: CTA 선정 (PascalCase) ===
    cta_file = blog_dir / f"{food_en}_Common_08_Cta.png"
    if cta_file.exists():
        print(f"  ✓ CTA 이미 존재")
    else:
        if cta_images:
            # 번호를 기반으로 CTA 선택 (순환)
            cta_idx = num % len(cta_images)
            cta_src = cta_images[cta_idx]
            shutil.copy(cta_src, cta_file)
            print(f"  ✅ CTA 선정 완료: {cta_src.name}")
            produced.append("cta")
        else:
            print(f"  ⚠️ CTA 소스 없음")

    # === 노드 24: 블로그 슬라이드 리네이밍 (PascalCase) ===
    slide_mapping = {
        "03": ["Nutrition", "영양정보", "Blog_03"],
        "04": ["Feeding", "급여가능불가", "Blog_04", "dodont"],
        "05": ["Amount", "급여량표", "Blog_05", "dosage"],
        "06": ["Caution", "주의사항", "Blog_06", "precautions"],
        "07": ["Cooking", "조리방법", "Blog_07"]
    }

    for num_str, patterns in slide_mapping.items():
        target_name = f"{food_en}_Blog_{num_str}_{patterns[0]}.png"
        target_file = blog_dir / target_name

        if target_file.exists():
            continue

        # 기존 파일 찾기
        found = False
        for pattern in patterns:
            for existing in blog_dir.glob(f"*{pattern}*.png"):
                if existing.name != target_name:
                    shutil.copy(existing, target_file)
                    print(f"  ✅ 슬라이드 {num_str}: {existing.name} → {target_name}")
                    produced.append(f"slide_{num_str}")
                    found = True
                    break
            if found:
                break

    # === insta 폴더에 공통 이미지 복사 (PascalCase) ===
    for common_file in ["Common_01_Cover", "Common_08_Cta"]:
        src = blog_dir / f"{food_en}_{common_file}.png"
        dst = insta_dir / f"{food_en}_{common_file}.png"
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
            print(f"  ✅ insta 복사: {common_file}")

    # === PD님 투두 추가 (PascalCase) ===
    food_img = blog_dir / f"{food_en}_Common_02_Food.png"
    if not food_img.exists():
        results["pd_todo"]["food_image"].append(f"#{num}_{food_en}")

    dog_img = insta_dir / f"{food_en}_Insta_03_Dog.png"
    if not dog_img.exists():
        results["pd_todo"]["dog_image"].append(f"#{num}_{food_en}")

    if produced:
        results["processed"].append(f"#{num}_{food_en}: {', '.join(produced)}")

    return produced


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
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
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
    print("📋 WO-BATCH-003 제작 완료 보고서")
    print("━"*60)
    print(f"\n실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n[제작 완료] {len(results['processed'])}건")
    for item in results['processed'][:20]:
        print(f"  ✅ {item}")
    if len(results['processed']) > 20:
        print(f"  ... 외 {len(results['processed'])-20}건")

    print(f"\n[스킵] {len(results['skipped'])}건")
    for item in results['skipped'][:10]:
        print(f"  ⏭️ {item}")

    print(f"\n[에러] {len(results['errors'])}건")
    for item in results['errors'][:10]:
        print(f"  ❌ {item}")

    print("\n" + "━"*60)
    print("📋 PD님 투두리스트")
    print("━"*60)

    print(f"\n[표지 클린 소스 필요] {len(results['pd_todo']['clean_source'])}건")
    for item in results['pd_todo']['clean_source'][:10]:
        print(f"  □ {item}")
    if len(results['pd_todo']['clean_source']) > 10:
        print(f"  ... 외 {len(results['pd_todo']['clean_source'])-10}건")

    print(f"\n[음식 이미지 필요] {len(results['pd_todo']['food_image'])}건")
    for item in results['pd_todo']['food_image'][:10]:
        print(f"  □ {item}")
    if len(results['pd_todo']['food_image']) > 10:
        print(f"  ... 외 {len(results['pd_todo']['food_image'])-10}건")

    print(f"\n[강아지 이미지 필요] {len(results['pd_todo']['dog_image'])}건")
    for item in results['pd_todo']['dog_image'][:10]:
        print(f"  □ {item}")
    if len(results['pd_todo']['dog_image']) > 10:
        print(f"  ... 외 {len(results['pd_todo']['dog_image'])-10}건")

    print("\n" + "━"*60)


def main():
    print("="*60)
    print("WO-BATCH-003: AI팀 담당 어셋 일괄 제작")
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
