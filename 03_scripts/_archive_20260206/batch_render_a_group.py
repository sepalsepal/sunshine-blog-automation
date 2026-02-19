#!/usr/bin/env python3
"""
WO-2026-0205-001: A그룹 7건 바디+CTA 렌더링 배치 스크립트

작업지시서 기반 자동화:
- 7건 cover_only → body_ready 전환
- 본문 2장 + CTA 1장 = 21장 렌더링
- v3.1 봉인 파이프라인 사용 (수정 없이 import만)
- 15항 validator strict 검증

실행순서: chocolate(FORBIDDEN) → cheese(CAUTION) → SAFE 5건
"""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

# PIL 임포트
try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow 라이브러리 필요: pip install Pillow")
    sys.exit(1)

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# CWD를 프로젝트 루트로 설정 (CTA 검증 시 상대경로 사용 위해)
os.chdir(PROJECT_ROOT)

# v3.1 봉인 모듈 임포트 (수정 금지)
from pipeline.pillow_overlay import (
    render_body,
    render_cta,
    build_validation_config,
    get_safety_color,
)
from pipeline.validators_strict import (
    validate_before_render,
    validate_v31_slide,
    strip_emoji,
    DESIGN_PARAMS_V31,
)

# ============================================
# 경로 설정
# ============================================

CONTENTS_DIR = PROJECT_ROOT / "contents" / "1_cover_only"
BODY_READY_DIR = PROJECT_ROOT / "contents" / "2_body_ready"
COVER_SOURCE_DIR = (
    PROJECT_ROOT / "backup_2026-02-03" / "content" / "images" / "000_cover" / "02_ready"
)
BEST_CTA_DIR = PROJECT_ROOT / "contents" / "sunshine" / "cta_source" / "best_cta"
TARGET_SIZE = (1080, 1080)

# ============================================
# A그룹 7건 정의
# ============================================

ITEMS = [
    # 1. chocolate (FORBIDDEN) - 최고 위험등급 우선
    {
        "food_id": "chocolate",
        "food_ko": "초콜릿",
        "number": "064",
        "safety": "forbidden",
        "folder": "064_chocolate_초콜릿",
        "clean_source": "cover_63_초콜릿_chocolate_DANGER.png",
        "body1": {"title": "절대 금지!", "subtitle": "테오브로민 성분 매우 위험"},
        "body2": {"title": "증상 & 대처", "subtitle": "구토, 경련 시 즉시 병원!"},
        "cta":   {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    # 2. cheese (CAUTION)
    {
        "food_id": "cheese",
        "food_ko": "치즈",
        "number": "131",
        "safety": "caution",
        "folder": "131_cheese_치즈",
        "clean_source": "cover_131_치즈_cheese.png",
        "body1": {"title": "조건부 OK!", "subtitle": "저염/저지방 치즈만 소량 급여"},
        "body2": {"title": "주의사항", "subtitle": "유당불내증 & 고지방 주의"},
        "cta":   {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    # 3. blackberry (SAFE)
    {
        "food_id": "blackberry",
        "food_ko": "블랙베리",
        "number": "028",
        "safety": "safe",
        "folder": "028_blackberry_블랙베리",
        "clean_source": "cover_27_블랙베리_blackberry.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "항산화 성분이 풍부해요"},
        "body2": {"title": "주의사항", "subtitle": "소량만, 씻어서 급여"},
        "cta":   {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    # 4. mackerel (SAFE)
    {
        "food_id": "mackerel",
        "food_ko": "고등어",
        "number": "034",
        "safety": "safe",
        "folder": "034_mackerel_고등어",
        "clean_source": "cover_33_고등어_mackerel.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "오메가3와 DHA 풍부"},
        "body2": {"title": "주의사항", "subtitle": "뼈 완전 제거, 익혀서"},
        "cta":   {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    # 5. tofu (SAFE)
    {
        "food_id": "tofu",
        "food_ko": "두부",
        "number": "052",
        "safety": "safe",
        "folder": "052_tofu_두부",
        "clean_source": "cover_51_두부_tofu.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "식물성 단백질 풍부"},
        "body2": {"title": "주의사항", "subtitle": "소량만, 간이 안된 것으로"},
        "cta":   {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    # 6. cabbage (SAFE)
    {
        "food_id": "cabbage",
        "food_ko": "양배추",
        "number": "151",
        "safety": "safe",
        "folder": "151_cabbage_양배추",
        "clean_source": "cover_159_양배추_cabbage.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "익혀서 소량 급여 OK"},
        "body2": {"title": "주의사항", "subtitle": "과다 급여 시 가스, 익혀서만"},
        "cta":   {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    # 7. yogurt (SAFE)
    {
        "food_id": "yogurt",
        "food_ko": "요거트",
        "number": "041",
        "safety": "safe",
        "folder": "041_yogurt_요거트",
        "clean_source": "cover_30_요거트_yogurt.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "프로바이오틱스 장 건강에 좋아요"},
        "body2": {"title": "주의사항", "subtitle": "무가당 플레인만, 소량만"},
        "cta":   {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
]


# ============================================
# CTA 이미지 선택 (reoverlay.py 동일 로직)
# ============================================

def select_cta_image(food_id: str) -> Path | None:
    """SHA256 해시 기반 CTA 이미지 선택 (봉인 로직 동일)"""
    if not BEST_CTA_DIR.exists():
        print(f"  [WARN] best_cta 폴더 없음: {BEST_CTA_DIR}")
        return None

    img_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    cta_files = sorted([
        f for f in BEST_CTA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in img_extensions
    ])

    if not cta_files:
        return None

    h = int(hashlib.sha256(food_id.encode()).hexdigest(), 16)
    idx = h % len(cta_files)
    selected = cta_files[idx]
    print(f"  [CTA-SELECT] {food_id} -> [{idx}/{len(cta_files)}] {selected.name}")
    return selected


# ============================================
# 단일 아이템 렌더링
# ============================================

def render_item(item: dict) -> dict:
    """
    단일 아이템 body+CTA 렌더링

    Returns:
        {"success": bool, "food_id": str, "rendered": int, "errors": list}
    """
    food_id = item["food_id"]
    safety = item["safety"]
    folder_name = item["folder"]
    result = {"success": False, "food_id": food_id, "rendered": 0, "errors": []}

    print(f"\n{'='*70}")
    print(f"  [{food_id.upper()}] {item['food_ko']} | safety={safety}")
    print(f"{'='*70}")

    # 1. 콘텐츠 폴더 확인/생성
    content_dir = CONTENTS_DIR / folder_name
    if not content_dir.exists():
        content_dir.mkdir(parents=True)
        print(f"  [MKDIR] {content_dir}")

    archive_dir = content_dir / "archive"
    if not archive_dir.exists():
        archive_dir.mkdir()
        print(f"  [MKDIR] archive/")

    # 2. 클린 커버 소스 → _bg 복사
    clean_src = COVER_SOURCE_DIR / item["clean_source"]
    if not clean_src.exists():
        msg = f"클린 커버 소스 없음: {clean_src}"
        print(f"  [ERROR] {msg}")
        result["errors"].append(msg)
        return result

    for slide_num in [1, 2]:
        bg_name = f"{food_id}_{slide_num:02d}_bg.png"
        bg_path = archive_dir / bg_name
        shutil.copy2(clean_src, bg_path)
        print(f"  [COPY] {item['clean_source']} -> archive/{bg_name}")

    # 3. CTA 이미지 선택 → _03_bg.png
    cta_src = select_cta_image(food_id)
    if not cta_src:
        msg = "CTA 이미지 선택 실패"
        print(f"  [ERROR] {msg}")
        result["errors"].append(msg)
        return result

    cta_bg_path = archive_dir / f"{food_id}_03_bg.png"
    # CTA는 원본 형식 유지하되 PNG로 저장
    cta_img = Image.open(cta_src)
    if cta_img.mode != 'RGBA':
        cta_img = cta_img.convert('RGBA')
    cta_img.save(cta_bg_path, 'PNG')
    print(f"  [CTA-PREP] {cta_src.name} -> archive/{food_id}_03_bg.png")

    # 4. 슬라이드별 렌더링
    slides_to_render = [
        (1, "body",  item["body1"]),
        (2, "body",  item["body2"]),
        (3, "cta",   item["cta"]),
    ]

    for slide_num, slide_type, text_data in slides_to_render:
        bg_path = archive_dir / f"{food_id}_{slide_num:02d}_bg.png"
        output_path = content_dir / f"{food_id}_{slide_num:02d}.png"

        title = text_data["title"]
        subtitle = strip_emoji(text_data.get("subtitle", ""))

        print(f"\n  --- Slide {slide_num:02d} ({slide_type}) ---")
        print(f"      title: {title}")
        print(f"      subtitle: {subtitle}")

        # 4a. v3.0 + v3.1 강제 검증
        # CTA: 상대경로 사용 (프로젝트 경로 Jun_AI의 "ai" 오탐 방지)
        try:
            v_config = build_validation_config(slide_type, safety)
            validation_path = str(bg_path.relative_to(PROJECT_ROOT)) if slide_type == "cta" else str(bg_path)
            validate_before_render(slide_type, validation_path, v_config)
        except Exception as e:
            msg = f"slide {slide_num:02d} 검증 실패: {e}"
            print(f"  [FAIL] {msg}")
            result["errors"].append(msg)
            continue

        # 4b. 이미지 로드 + 리사이즈
        try:
            img = Image.open(bg_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            if img.size != TARGET_SIZE:
                original_size = img.size
                img = img.resize(TARGET_SIZE, Image.LANCZOS)
                print(f"      [RESIZE] {original_size[0]}x{original_size[1]} -> 1080x1080")
        except Exception as e:
            msg = f"slide {slide_num:02d} 이미지 로드 실패: {e}"
            print(f"  [ERROR] {msg}")
            result["errors"].append(msg)
            continue

        # 4c. 렌더링 (v3.1 pillow_overlay)
        try:
            if slide_type == "body":
                rendered = render_body(img, title, subtitle, safety)
            elif slide_type == "cta":
                rendered = render_cta(img, title, subtitle, str(bg_path))
            else:
                msg = f"알 수 없는 slide_type: {slide_type}"
                result["errors"].append(msg)
                continue

            # 4d. 저장
            rendered.save(output_path, 'PNG')
            result["rendered"] += 1
            print(f"      [OK] -> {output_path.name} ({rendered.size[0]}x{rendered.size[1]})")

        except Exception as e:
            msg = f"slide {slide_num:02d} 렌더링 실패: {e}"
            print(f"  [ERROR] {msg}")
            result["errors"].append(msg)
            continue

    # 5. 메타데이터 업데이트
    metadata_path = content_dir / "metadata.json"
    try:
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {"food_id": food_id, "food_name_ko": item["food_ko"]}

        metadata.update({
            "status": "body_ready" if result["rendered"] == 3 else "cover_only",
            "body_rendered_at": datetime.now().isoformat(),
            "body_version": "v3.1_WO-2026-0205-001",
            "safety": safety,
            "slides_rendered": result["rendered"],
            "cta_source_image": cta_src.name if cta_src else None,
            "clean_cover_source": item["clean_source"],
        })

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"\n  [META] metadata.json 업데이트됨")
    except Exception as e:
        print(f"  [WARN] metadata.json 업데이트 실패: {e}")

    # 6. 결과 판정
    result["success"] = result["rendered"] == 3
    status = "SUCCESS" if result["success"] else "PARTIAL"
    print(f"\n  [{status}] {food_id}: {result['rendered']}/3장 렌더링")

    return result


# ============================================
# 폴더 이동 (cover_only → body_ready)
# ============================================

def move_to_body_ready(item: dict) -> bool:
    """렌더링 성공 시 폴더를 2_body_ready/로 이동"""
    src = CONTENTS_DIR / item["folder"]
    dst = BODY_READY_DIR / item["folder"]

    if not src.exists():
        print(f"  [WARN] 소스 폴더 없음: {src}")
        return False

    if not BODY_READY_DIR.exists():
        BODY_READY_DIR.mkdir(parents=True)

    if dst.exists():
        print(f"  [WARN] 대상 폴더 이미 존재: {dst}")
        return False

    shutil.move(str(src), str(dst))
    print(f"  [MOVE] {src.name} -> 2_body_ready/")
    return True


# ============================================
# 메인 실행
# ============================================

def main():
    print("=" * 70)
    print("  WO-2026-0205-001: A그룹 바디+CTA 렌더링")
    print(f"  실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  대상: {len(ITEMS)}건")
    print(f"  파이프라인: v3.1 (DESIGN_PARAMS_V31)")
    print("=" * 70)

    # 사전 확인
    if not COVER_SOURCE_DIR.exists():
        print(f"[FATAL] 클린 커버 소스 폴더 없음: {COVER_SOURCE_DIR}")
        sys.exit(1)

    if not BEST_CTA_DIR.exists():
        print(f"[FATAL] best_cta 폴더 없음: {BEST_CTA_DIR}")
        sys.exit(1)

    results = []
    for idx, item in enumerate(ITEMS, 1):
        print(f"\n\n{'#'*70}")
        print(f"  [{idx}/{len(ITEMS)}] {item['food_id'].upper()} ({item['safety'].upper()})")
        print(f"{'#'*70}")

        res = render_item(item)
        results.append(res)

        # 성공 시 폴더 이동
        if res["success"]:
            move_to_body_ready(item)

    # ============================================
    # 최종 보고
    # ============================================
    print("\n\n" + "=" * 70)
    print("  최종 보고: WO-2026-0205-001")
    print("=" * 70)

    success_count = sum(1 for r in results if r["success"])
    total_rendered = sum(r["rendered"] for r in results)

    print(f"\n  성공: {success_count}/{len(ITEMS)}건")
    print(f"  렌더링: {total_rendered}/21장")

    print(f"\n  {'아이템':<15} {'안전도':<12} {'렌더링':>5} {'상태':>8}")
    print(f"  {'-'*42}")
    for item, res in zip(ITEMS, results):
        status = "PASS" if res["success"] else "FAIL"
        print(f"  {item['food_id']:<15} {item['safety']:<12} {res['rendered']:>2}/3  {status:>8}")
        if res["errors"]:
            for err in res["errors"]:
                print(f"    -> {err[:60]}")

    # 보고서 저장
    report = {
        "work_order": "WO-2026-0205-001",
        "executed_at": datetime.now().isoformat(),
        "pipeline_version": "v3.1",
        "total_items": len(ITEMS),
        "success_count": success_count,
        "total_rendered": total_rendered,
        "results": results,
    }

    report_path = PROJECT_ROOT / "config" / "data" / "wo_2026_0205_001_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  보고서: {report_path}")

    return success_count == len(ITEMS)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
