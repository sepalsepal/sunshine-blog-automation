#!/usr/bin/env python3
"""
텍스트 오버레이 재작업 스크립트 v3.1

v3.0 -> v3.1 변경:
- pillow_overlay v3.1 렌더링 함수 사용 (inline 코드 제거)
- validate_before_render 통합 (v3.0 + v3.1 이중 검증)
- 본문: 88px Black + 44px Medium, 그라데이션, 레터 스페이싱
- 커버: 114px y=100, 2단 그림자
- CTA: 48px #FFD93D

작성: 김부장 + 레드2
승인: 박세준 PD
일시: 2026-02-05
버전: v3.1 (DESIGN_PARAMS_V31 적용)
"""

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

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# pillow_overlay v3.1 렌더링 함수
try:
    from pipeline.pillow_overlay import (
        render_cover,
        render_body,
        render_cta,
        build_validation_config,
    )
    OVERLAY_V31 = True
    print("[v3.1] pillow_overlay v3.1 로드됨")
except ImportError as e:
    OVERLAY_V31 = False
    print(f"[ERROR] pillow_overlay v3.1 로드 실패: {e}")
    sys.exit(1)

# 강제 검증 모듈 임포트
try:
    from pipeline.validators_strict import (
        validate_before_render,
        strip_emoji,
        assert_cta_real_photo,
        LOCKED_CONFIG,
    )
    STRICT_MODE = True
    print("[STRICT] 강제 검증 모드 활성화")
except ImportError:
    STRICT_MODE = False
    print("[WARN] 강제 검증 모듈 없음 - 검증 스킵")


def load_text_config(folder_path: Path, food_id: str) -> dict:
    """
    텍스트 설정 로드

    우선순위:
    1. config/settings/{food_id}_text.json
    2. metadata.json의 text_config
    3. 기본 설정

    Returns:
        dict with "slides" key containing list of slide configs
    """
    result = {
        "font_size": 80,
        "color": "#FFFFFF",
        "position": "bottom_center",
        "shadow": True,
        "slides": []
    }

    # 1. 전용 텍스트 설정 파일 확인
    text_config_path = PROJECT_ROOT / "config" / "settings" / f"{food_id}_text.json"
    if text_config_path.exists():
        try:
            with open(text_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[CONFIG] 텍스트 설정 로드: {text_config_path.name}")

                # 설정이 리스트인 경우 (슬라이드 배열)
                if isinstance(config, list):
                    result["slides"] = config
                    return result
                # 설정이 딕셔너리인 경우
                elif isinstance(config, dict):
                    if "slides" in config:
                        result["slides"] = config["slides"]
                    result.update(config)
                    return result
        except Exception as e:
            print(f"[WARN] 텍스트 설정 로드 실패: {e}")

    # 2. metadata.json에서 텍스트 정보 로드
    metadata_path = folder_path / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            if "text_config" in metadata:
                print(f"[CONFIG] metadata.json에서 텍스트 설정 로드")
                config = metadata["text_config"]
                if isinstance(config, list):
                    result["slides"] = config
                elif isinstance(config, dict):
                    result.update(config)
                return result
        except Exception as e:
            print(f"[WARN] metadata.json 로드 실패: {e}")

    # 3. 기본 텍스트 설정
    print(f"[CONFIG] 기본 텍스트 설정 사용")
    result["slides"] = [
        {"slide": 0, "title": food_id.upper(), "subtitle": ""},
        {"slide": 1, "title": "", "subtitle": ""},
        {"slide": 2, "title": "", "subtitle": ""},
        {"slide": 3, "title": "", "subtitle": ""}
    ]
    return result


def find_bg_images(folder: Path, food_id: str) -> dict:
    """
    클린 베이스 이미지(_bg.png) 찾기

    Args:
        folder: 콘텐츠 폴더
        food_id: 음식 ID

    Returns:
        dict: {slide_index: bg_path} 매핑
    """
    bg_files = {}

    # 1. archive 폴더에서 찾기
    archive_folder = folder / "archive"
    if archive_folder.exists():
        for bg_file in archive_folder.glob(f"{food_id}_*_bg.png"):
            # 파일명에서 슬라이드 번호 추출: food_01_bg.png -> 1
            name = bg_file.stem  # food_01_bg
            parts = name.replace("_bg", "").split("_")
            if len(parts) >= 2:
                try:
                    slide_num = int(parts[-1])
                    bg_files[slide_num] = bg_file
                except ValueError:
                    continue

    # 2. 메인 폴더에서도 찾기
    for bg_file in folder.glob(f"{food_id}_*_bg.png"):
        name = bg_file.stem
        parts = name.replace("_bg", "").split("_")
        if len(parts) >= 2:
            try:
                slide_num = int(parts[-1])
                if slide_num not in bg_files:  # archive 우선
                    bg_files[slide_num] = bg_file
            except ValueError:
                continue

    return bg_files


def select_cta_image(food_id: str) -> Path | None:
    """
    best_cta 폴더에서 food_id 기반 해시로 CTA 이미지 선택.

    - food_id 해시 → 인덱스 결정 (같은 food_id = 같은 이미지, 재현성 보장)
    - 파일 목록 정렬 후 순환 배정

    Returns:
        Path to selected CTA image, or None if folder empty
    """
    best_cta_dir = PROJECT_ROOT / "contents" / "sunshine" / "cta_source" / "best_cta"

    if not best_cta_dir.exists():
        print(f"  [WARN] best_cta 폴더 없음: {best_cta_dir}")
        return None

    # 이미지 파일만 수집 (README 등 제외)
    img_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    cta_files = sorted([
        f for f in best_cta_dir.iterdir()
        if f.is_file() and f.suffix.lower() in img_extensions
    ])

    if not cta_files:
        print(f"  [WARN] best_cta 이미지 없음")
        return None

    # food_id 해시 → 인덱스 (sha256: 충돌 최소화)
    h = int(hashlib.sha256(food_id.encode()).hexdigest(), 16)
    idx = h % len(cta_files)
    selected = cta_files[idx]

    print(f"  [CTA-SELECT] {food_id} → [{idx}/{len(cta_files)}] {selected.name}")
    return selected


def reoverlay(folder_path: str, food_id: str) -> dict:
    """
    메인 함수 - 텍스트 오버레이 재작업 v3.1

    pillow_overlay v3.1 렌더링 + validate_before_render 이중 검증

    Args:
        folder_path: 콘텐츠 폴더 경로
        food_id: 음식 ID

    Returns:
        dict: 결과 {"success": bool, "modified": int, "total": int, ...}
    """
    folder = Path(folder_path)

    if not folder.exists():
        return {"success": False, "error": f"폴더 없음: {folder}"}

    print(f"\n[START] reoverlay v3.1 (DESIGN_PARAMS_V31): {food_id}")
    print(f"[PATH] {folder}")

    # 클린 베이스 이미지(_bg.png) 찾기
    bg_files = find_bg_images(folder, food_id)

    if not bg_files:
        return {
            "success": False,
            "error": (
                f"클린 이미지(_bg.png) 없음!\n"
                f"   위치: {folder}/archive/ 또는 {folder}/\n"
                f"   필요: {food_id}_00_bg.png ~ {food_id}_03_bg.png\n"
                f"   -> 클린 이미지 먼저 준비 필요"
            )
        }

    print(f"[FOUND] 클린 이미지 {len(bg_files)}장: {sorted(bg_files.keys())}")

    # 텍스트 설정 로드
    text_config = load_text_config(folder, food_id)
    safety = text_config.get("safety", "safe").lower()
    print(f"[SAFETY] {safety}")

    # 각 클린 이미지에 텍스트 오버레이 적용
    modified_count = 0
    errors = []
    total_slides = len(bg_files)

    for slide_idx, bg_path in sorted(bg_files.items()):
        # 출력 파일명: food_01_bg.png -> food_01.png
        output_name = f"{food_id}_{slide_idx:02d}.png"
        output_path = folder / output_name

        print(f"\n  [{slide_idx}] {bg_path.name} -> {output_name}")

        # 슬라이드별 텍스트 결정
        slides = text_config.get("slides", [])
        if slide_idx < len(slides):
            slide_text = slides[slide_idx]
            title = slide_text.get("title", "")
            subtitle = slide_text.get("subtitle", "")
        else:
            title = ""
            subtitle = ""

        # 이모지 제거 (Pillow 렌더링 오류 방지)
        if STRICT_MODE and subtitle:
            subtitle = strip_emoji(subtitle)

        # 슬라이드 타입 결정
        if slide_idx == 0:
            slide_type = "cover"
        elif slide_idx == 3:
            slide_type = "cta"
        else:
            slide_type = "body"

        # ========================================
        # CTA: best_cta 폴더에서 다양한 이미지 선택
        # ========================================
        actual_bg_path = bg_path
        if slide_type == "cta":
            cta_img_path = select_cta_image(food_id)
            if cta_img_path:
                archive_dir = folder / "archive"
                if archive_dir.exists():
                    new_bg_name = f"{food_id}_03_bg.png"
                    new_bg_path = archive_dir / new_bg_name
                    # 기존 bg를 _bg_old로 백업 (최초 1회)
                    old_backup = archive_dir / f"{food_id}_03_bg_old.png"
                    if not old_backup.exists() and new_bg_path.exists():
                        shutil.copy2(new_bg_path, old_backup)
                        print(f"  [BACKUP] 기존 CTA bg → {old_backup.name}")
                    # best_cta 이미지를 _03_bg.png로 변환 저장
                    cta_src = Image.open(cta_img_path)
                    if cta_src.mode != 'RGBA':
                        cta_src = cta_src.convert('RGBA')
                    cta_src.save(new_bg_path, 'PNG')
                    actual_bg_path = new_bg_path
                    # bg_files도 업데이트 (metadata용)
                    bg_files[slide_idx] = new_bg_path
                    print(f"  [CTA-PREP] {cta_img_path.name} → {new_bg_name}")

        # ========================================
        # v3.0 + v3.1 강제 검증
        # ========================================
        if STRICT_MODE:
            try:
                v_config = build_validation_config(slide_type, safety)
                validate_before_render(slide_type, str(actual_bg_path), v_config)
            except Exception as e:
                print(f"  [FAIL] 검증 실패: {e}")
                errors.append(bg_path.name)
                continue

        # 이미지 로드
        try:
            img = Image.open(actual_bg_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        except Exception as e:
            print(f"  [ERROR] 이미지 로드 실패: {actual_bg_path.name} - {e}")
            errors.append(bg_path.name)
            continue

        # 1080x1080 리사이즈 (PD 규칙: 전 슬라이드 1080 통일)
        TARGET_SIZE = (1080, 1080)
        if img.size != TARGET_SIZE:
            original_size = img.size
            img = img.resize(TARGET_SIZE, Image.LANCZOS)
            print(f"  [RESIZE] {original_size[0]}x{original_size[1]} → 1080x1080")

        # 텍스트 없으면 클린 이미지 그대로 복사
        if not title:
            print(f"  [SKIP] 텍스트 없음: slide {slide_idx}")
            img.save(output_path, 'PNG')
            modified_count += 1
            continue

        # ========================================
        # v3.1 렌더링 (pillow_overlay 호출)
        # ========================================
        if slide_type == "cover":
            result = render_cover(img, title)
        elif slide_type == "cta":
            result = render_cta(img, title, subtitle, str(actual_bg_path))
        else:
            result = render_body(img, title, subtitle, safety)

        # 저장 (새 파일로)
        result.save(output_path, 'PNG')
        modified_count += 1
        print(f"  [OK] 생성됨: {output_name}")

    # 결과 판정
    if modified_count == 0 and len(errors) > 0:
        return {
            "success": False,
            "error": f"생성된 이미지 없음, 에러: {errors}"
        }

    # 메타데이터 업데이트
    metadata_path = folder / "metadata.json"
    try:
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {"food_id": food_id}

        metadata["last_reoverlay_at"] = datetime.now().isoformat()
        metadata["last_reoverlay_modified"] = modified_count
        metadata["reoverlay_version"] = "v3.1_clean_image"
        metadata["bg_images_used"] = [str(p.name) for p in bg_files.values()]

        # CTA 이미지 출처 기록
        cta_selected = select_cta_image(food_id)
        if cta_selected:
            metadata["cta_source_image"] = cta_selected.name

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"\n[META] metadata.json 업데이트됨 (v3.1)")
    except Exception as e:
        print(f"[WARN] metadata.json 업데이트 실패: {e}")

    return {
        "success": True,
        "modified": modified_count,
        "total": total_slides,
        "errors": errors if errors else None,
        "note": "v3.1 - DESIGN_PARAMS_V31 적용"
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reoverlay.py <folder_path> <food_id>")
        print("")
        print("Example:")
        print("  python reoverlay.py contents/2_body_ready/036_potato_감자 potato")
        sys.exit(1)

    folder_path = sys.argv[1]
    food_id = sys.argv[2]

    result = reoverlay(folder_path, food_id)

    print("")
    if result["success"]:
        print(f"[SUCCESS] 수정됨: {result['modified']}/{result['total']}장 ({result['note']})")
        if result.get("errors"):
            print(f"[WARN] 에러: {result['errors']}")
        sys.exit(0)
    else:
        print(f"[FAILED] {result.get('error', result.get('errors'))}")
        sys.exit(1)
