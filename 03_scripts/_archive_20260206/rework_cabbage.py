#!/usr/bin/env python3
"""
WO-2026-0205-002 PART 1: 양배추(cabbage) 재작업

문제: 커버소스(cover_159)가 바디 bg로만 사용됨, _00 커버 미생성
수정: 커버 렌더링 추가 + 바디/CTA 재렌더링 (4장 전부)

봉인 파이프라인 무수정 (pillow_overlay.py, validators_strict.py)
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow 필요: pip install Pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from pipeline.pillow_overlay import (
    render_cover,
    render_body,
    render_cta,
    build_validation_config,
    get_safety_color,
)
from pipeline.validators_strict import (
    validate_before_render,
    validate_v31_slide,
    strip_emoji,
)

# ============================================
# 경로
# ============================================
CABBAGE_DIR = PROJECT_ROOT / "contents" / "2_body_ready" / "151_cabbage_양배추"
ARCHIVE_DIR = CABBAGE_DIR / "archive"
COVER_SOURCE = (
    PROJECT_ROOT / "backup_2026-02-03" / "content" / "images"
    / "000_cover" / "02_ready" / "cover_159_양배추_cabbage.png"
)
BEST_CTA_DIR = PROJECT_ROOT / "contents" / "sunshine" / "cta_source" / "best_cta"
TARGET_SIZE = (1080, 1080)

# ============================================
# 텍스트 (A그룹 배치에서 사용한 것과 동일)
# ============================================
COVER_TITLE = "CABBAGE"
BODY1 = {"title": "먹어도 돼요!", "subtitle": "익혀서 소량 급여 OK"}
BODY2 = {"title": "주의사항", "subtitle": "과다 급여 시 가스, 익혀서만"}
CTA = {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"}
SAFETY = "safe"

# ============================================
# CTA 선택 (SHA256 해시, reoverlay.py 로직 동일)
# ============================================
def select_cta_image(food_id: str) -> Path:
    import hashlib
    cta_files = sorted([f for f in BEST_CTA_DIR.iterdir()
                        if f.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    if not cta_files:
        raise FileNotFoundError(f"CTA 이미지 없음: {BEST_CTA_DIR}")
    h = hashlib.sha256(food_id.encode()).hexdigest()
    idx = int(h, 16) % len(cta_files)
    return cta_files[idx]


def main():
    print("=" * 60)
    print("WO-2026-0205-002 PART 1: 양배추(cabbage) 재작업")
    print("=" * 60)

    # 사전 확인
    assert CABBAGE_DIR.exists(), f"폴더 없음: {CABBAGE_DIR}"
    assert COVER_SOURCE.exists(), f"커버소스 없음: {COVER_SOURCE}"
    ARCHIVE_DIR.mkdir(exist_ok=True)

    errors = []
    rendered = 0

    # ── Slide 0: 커버 ──
    print("\n[1/4] 커버 렌더링 (cabbage_00)")
    bg_00 = ARCHIVE_DIR / "cabbage_00_bg.png"
    shutil.copy2(COVER_SOURCE, bg_00)
    print(f"  소스 복사: {COVER_SOURCE.name} → {bg_00.name}")

    # 커버 검증 (상대경로)
    v_config = build_validation_config("cover", SAFETY)
    rel_path = str(bg_00.relative_to(PROJECT_ROOT))
    validate_before_render("cover", rel_path, v_config)

    img = Image.open(bg_00).resize(TARGET_SIZE, Image.LANCZOS)
    img = render_cover(img, COVER_TITLE)
    out_00 = CABBAGE_DIR / "cabbage_00.png"
    img.save(out_00, "PNG")
    validate_v31_slide("cover", v_config, str(out_00))
    print(f"  ✅ {out_00.name} ({os.path.getsize(out_00) // 1024}KB)")
    rendered += 1

    # ── Slide 1: 바디① ──
    print("\n[2/4] 바디① 렌더링 (cabbage_01)")
    bg_01 = ARCHIVE_DIR / "cabbage_01_bg.png"
    if not bg_01.exists():
        shutil.copy2(COVER_SOURCE, bg_01)

    v_config = build_validation_config("body", SAFETY)
    rel_path = str(bg_01.relative_to(PROJECT_ROOT))
    validate_before_render("body", rel_path, v_config)

    img = Image.open(bg_01).resize(TARGET_SIZE, Image.LANCZOS)
    title_clean = strip_emoji(BODY1["title"])
    sub_clean = strip_emoji(BODY1["subtitle"])
    img = render_body(img, title_clean, sub_clean, SAFETY)
    out_01 = CABBAGE_DIR / "cabbage_01.png"
    img.save(out_01, "PNG")
    validate_v31_slide("body", v_config, str(out_01))
    print(f"  ✅ {out_01.name} ({os.path.getsize(out_01) // 1024}KB)")
    rendered += 1

    # ── Slide 2: 바디② ──
    print("\n[3/4] 바디② 렌더링 (cabbage_02)")
    bg_02 = ARCHIVE_DIR / "cabbage_02_bg.png"
    if not bg_02.exists():
        shutil.copy2(COVER_SOURCE, bg_02)

    v_config = build_validation_config("body", SAFETY)
    rel_path = str(bg_02.relative_to(PROJECT_ROOT))
    validate_before_render("body", rel_path, v_config)

    img = Image.open(bg_02).resize(TARGET_SIZE, Image.LANCZOS)
    title_clean = strip_emoji(BODY2["title"])
    sub_clean = strip_emoji(BODY2["subtitle"])
    img = render_body(img, title_clean, sub_clean, SAFETY)
    out_02 = CABBAGE_DIR / "cabbage_02.png"
    img.save(out_02, "PNG")
    validate_v31_slide("body", v_config, str(out_02))
    print(f"  ✅ {out_02.name} ({os.path.getsize(out_02) // 1024}KB)")
    rendered += 1

    # ── Slide 3: CTA ──
    print("\n[4/4] CTA 재렌더링 (cabbage_03)")
    cta_src = select_cta_image("cabbage")
    bg_03 = ARCHIVE_DIR / "cabbage_03_bg.png"
    shutil.copy2(cta_src, bg_03)
    print(f"  CTA 소스: {cta_src.name}")

    v_config = build_validation_config("cta", SAFETY)
    rel_path = str(bg_03.relative_to(PROJECT_ROOT))
    validate_before_render("cta", rel_path, v_config)

    img = Image.open(bg_03).resize(TARGET_SIZE, Image.LANCZOS)
    title_clean = strip_emoji(CTA["title"])
    sub_clean = strip_emoji(CTA["subtitle"])
    img = render_cta(img, title_clean, sub_clean, bg_path=rel_path)
    out_03 = CABBAGE_DIR / "cabbage_03.png"
    img.save(out_03, "PNG")
    validate_v31_slide("cta", v_config, str(out_03.relative_to(PROJECT_ROOT)))
    print(f"  ✅ {out_03.name} ({os.path.getsize(out_03) // 1024}KB)")
    rendered += 1

    # ── 최종 검증 ──
    print(f"\n{'=' * 60}")
    print(f"재작업 완료: {rendered}/4장")
    for f in sorted(CABBAGE_DIR.glob("cabbage_0*.png")):
        img = Image.open(f)
        print(f"  {f.name}: {img.size[0]}x{img.size[1]} ({os.path.getsize(f) // 1024}KB)")

    # metadata 업데이트
    meta_path = CABBAGE_DIR / "metadata.json"
    meta = {}
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
    meta["reworked_at"] = datetime.now().isoformat()
    meta["rework_wo"] = "WO-2026-0205-002"
    meta["slides_rendered"] = 4
    meta["cover_source"] = COVER_SOURCE.name
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ PART 1 완료: 양배추 4장 재작업 ({rendered}/4)")


if __name__ == "__main__":
    main()
