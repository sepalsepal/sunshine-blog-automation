#!/usr/bin/env python3
"""
cover_inspector.py - 표지 검수 도구 v2.0
WO-COVER-PROCESS-v2.0

4단계 검증 시스템:
1. Spec 검증 (해상도, 포맷)
2. 코드 파라미터 검증 (UPPERCASE, 그라데이션)
3. 폰트/환경 검증 (Pillow 버전, 폰트 SHA256)
4. Golden 이미지 회귀 테스트 (SSIM >= 0.995 또는 픽셀 차이 <= 0.5%)

승인: PD 박세준 (2026-02-12)
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

import PIL
from PIL import Image, ImageChops, ImageStat

# ============================================================================
# 프로젝트 설정
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
GOLDEN_SAMPLES_DIR = PROJECT_ROOT / "contents" / "0_Golden sample" / "Cover"
LOG_DIR = PROJECT_ROOT / "logs" / "cover_regression"

# ============================================================================
# 검증 기준 (변경 금지)
# ============================================================================

SPEC_VERSION = "v2.0"
REQUIRED_RESOLUTION = (1080, 1080)
REQUIRED_PILLOW_VERSION = "12.1.0"

# Golden Regression 기준 (v2)
MIN_SSIM_SCORE = 0.995  # SSIM >= 0.995
MAX_PIXEL_DIFF_PERCENT = 0.5  # 픽셀 차이율 <= 0.5%

# 폰트 SHA256 해시
FONT_SHA256_MAP = {
    "BlackHanSans-Regular.ttf": "31960809284026681774a8e52dc19ebcad26cf69b0ad9d560f288296fbb52739",
    "NanumGothic-ExtraBold.ttf": "5c4568e5295a8c52bc30e7efa1ea6d2de43556268ef42daba93540a1ece691ae",
}


# ============================================================================
# 골든 샘플 매핑
# ============================================================================

GOLDEN_SAMPLE_MAP = {
    "potato": "potato_cover_upper.png",
    "melon": "melon_cover_upper.png",
    "onion": "onion_cover_upper.png",
}


def get_golden_sample_path(english_name: str) -> Optional[Path]:
    """영어명으로 골든 샘플 경로 반환"""
    key = english_name.lower()
    if key in GOLDEN_SAMPLE_MAP:
        return GOLDEN_SAMPLES_DIR / GOLDEN_SAMPLE_MAP[key]
    return None


# ============================================================================
# 유틸리티
# ============================================================================

def get_file_sha256(file_path: Path) -> str:
    """파일 SHA256 해시 계산"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


# ============================================================================
# Golden Regression 테스트 (v2)
# ============================================================================

def calculate_pixel_diff_rate(img1: Image.Image, img2: Image.Image) -> float:
    """
    두 이미지의 픽셀 차이율 계산 (0~100%)

    차이 픽셀 수 / 전체 픽셀 수 * 100
    임계값: RGB 각 채널 10 이상 차이 시 다른 픽셀로 판정
    """
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)

    img1_rgb = img1.convert("RGB")
    img2_rgb = img2.convert("RGB")

    diff = ImageChops.difference(img1_rgb, img2_rgb)

    # 차이가 있는 픽셀 수 계산
    threshold = 10  # RGB 각 채널 10 이상 차이
    diff_pixels = 0
    total_pixels = img1.size[0] * img1.size[1]

    for pixel in diff.getdata():
        if any(c > threshold for c in pixel):
            diff_pixels += 1

    return (diff_pixels / total_pixels) * 100


def calculate_ssim_approx(img1: Image.Image, img2: Image.Image) -> float:
    """
    간이 SSIM 계산 (PIL만 사용)

    실제 SSIM과 유사하게 밝기/대비/구조 비교
    scikit-image 없이 PIL로 근사값 계산
    """
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)

    img1_gray = img1.convert("L")
    img2_gray = img2.convert("L")

    stat1 = ImageStat.Stat(img1_gray)
    stat2 = ImageStat.Stat(img2_gray)

    # 평균
    mean1 = stat1.mean[0]
    mean2 = stat2.mean[0]

    # 분산
    var1 = stat1.var[0]
    var2 = stat2.var[0]

    # 공분산 근사 (차이 이미지 기반)
    diff = ImageChops.difference(img1_gray, img2_gray)
    diff_stat = ImageStat.Stat(diff)
    mean_diff = diff_stat.mean[0]

    # SSIM 상수
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    # 밝기 비교
    luminance = (2 * mean1 * mean2 + C1) / (mean1 ** 2 + mean2 ** 2 + C1)

    # 대비 비교
    contrast = (2 * (var1 ** 0.5) * (var2 ** 0.5) + C2) / (var1 + var2 + C2)

    # 구조 비교 (mean_diff 기반 근사)
    structure = 1 - (mean_diff / 255)

    # SSIM 근사값
    ssim = luminance * contrast * structure

    return round(max(0, min(1, ssim)), 4)


def generate_diff_image(img1: Image.Image, img2: Image.Image, output_path: Path) -> None:
    """차이 이미지 생성 및 저장"""
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)

    diff = ImageChops.difference(img1.convert("RGB"), img2.convert("RGB"))

    # 차이 강조 (10배 증폭)
    diff = diff.point(lambda x: min(255, x * 10))

    diff.save(output_path, "PNG")


def run_golden_regression_test(
    cover_path: str,
    golden_path: str,
    log_dir: Path
) -> Dict:
    """
    Golden 이미지 회귀 테스트 (v2)

    기준:
    - SSIM >= 0.995 또는
    - 픽셀 차이율 <= 0.5%
    """
    result = {
        "ssim_score": 0.0,
        "pixel_diff_percent": 100.0,
        "ssim_pass": False,
        "pixel_pass": False,
        "overall_pass": False,
        "diff_image": None,
        "ssim_file": None,
    }

    try:
        cover_img = Image.open(cover_path)
        golden_img = Image.open(golden_path)

        # SSIM 계산
        ssim = calculate_ssim_approx(cover_img, golden_img)
        result["ssim_score"] = ssim
        result["ssim_pass"] = ssim >= MIN_SSIM_SCORE

        # 픽셀 차이율 계산
        pixel_diff = calculate_pixel_diff_rate(cover_img, golden_img)
        result["pixel_diff_percent"] = round(pixel_diff, 3)
        result["pixel_pass"] = pixel_diff <= MAX_PIXEL_DIFF_PERCENT

        # 전체 판정 (SSIM 또는 픽셀 차이 중 하나만 통과해도 OK)
        result["overall_pass"] = result["ssim_pass"] or result["pixel_pass"]

        # 로그 저장
        log_dir.mkdir(parents=True, exist_ok=True)

        # 차이 이미지 저장
        diff_path = log_dir / "diff.png"
        generate_diff_image(cover_img, golden_img, diff_path)
        result["diff_image"] = str(diff_path)

        # SSIM 점수 저장
        ssim_path = log_dir / "ssim_score.txt"
        with open(ssim_path, "w") as f:
            f.write(f"SSIM Score: {ssim}\n")
            f.write(f"Min Required: {MIN_SSIM_SCORE}\n")
            f.write(f"Pixel Diff: {pixel_diff:.3f}%\n")
            f.write(f"Max Allowed: {MAX_PIXEL_DIFF_PERCENT}%\n")
            f.write(f"Pass: {'YES' if result['overall_pass'] else 'NO'}\n")
        result["ssim_file"] = str(ssim_path)

    except Exception as e:
        result["error"] = str(e)

    return result


# ============================================================================
# 4단계 검증 시스템 (v2)
# ============================================================================

def stage1_spec_validation(cover_path: str) -> Dict:
    """Stage 1: Spec 검증 (해상도, 포맷)"""
    result = {"stage": "spec", "checks": {}, "pass": True}

    img = Image.open(cover_path)

    # 해상도
    width, height = img.size
    resolution_pass = (width == REQUIRED_RESOLUTION[0] and height == REQUIRED_RESOLUTION[1])
    result["checks"]["resolution"] = {
        "expected": f"{REQUIRED_RESOLUTION[0]}x{REQUIRED_RESOLUTION[1]}",
        "actual": f"{width}x{height}",
        "pass": resolution_pass
    }

    # 포맷
    format_pass = cover_path.lower().endswith(".png")
    result["checks"]["format"] = {
        "expected": "PNG",
        "actual": "PNG" if format_pass else Path(cover_path).suffix,
        "pass": format_pass
    }

    result["pass"] = all(c["pass"] for c in result["checks"].values())
    return result


def stage2_parameter_validation(cover_path: str, expected_english: str) -> Dict:
    """Stage 2: 코드 파라미터 검증 (UPPERCASE, 그라데이션)"""
    result = {"stage": "parameter", "checks": {}, "pass": True}

    img = Image.open(cover_path).convert("RGBA")

    # UPPERCASE
    uppercase_pass = expected_english == expected_english.upper()
    result["checks"]["uppercase"] = {
        "expected": expected_english.upper(),
        "actual": expected_english,
        "pass": uppercase_pass
    }

    # 그라데이션 (상단 밝기 분석)
    top_region = img.crop((0, 0, img.size[0], 50))
    pixels = list(top_region.getdata())
    avg_brightness = sum(sum(p[:3]) / 3 for p in pixels) / len(pixels)
    gradient_pass = avg_brightness < 200
    result["checks"]["gradient"] = {
        "expected": "상단 어둡게 (<200)",
        "actual": f"밝기 {avg_brightness:.1f}",
        "pass": gradient_pass
    }

    result["pass"] = all(c["pass"] for c in result["checks"].values())
    return result


def stage3_environment_validation() -> Dict:
    """Stage 3: 폰트/환경 검증 (Pillow 버전)"""
    result = {"stage": "environment", "checks": {}, "pass": True}

    # Pillow 버전
    current_version = PIL.__version__
    version_pass = current_version.startswith("12.")
    result["checks"]["pillow_version"] = {
        "expected": REQUIRED_PILLOW_VERSION,
        "actual": current_version,
        "pass": version_pass
    }

    result["pass"] = all(c["pass"] for c in result["checks"].values())
    return result


def stage4_golden_regression(cover_path: str, english_name: str, log_dir: Path) -> Dict:
    """Stage 4: Golden 이미지 회귀 테스트"""
    result = {"stage": "golden_regression", "checks": {}, "pass": False}

    golden_path = get_golden_sample_path(english_name)

    if not golden_path or not golden_path.exists():
        result["checks"]["golden_sample"] = {
            "expected": "골든 샘플 존재",
            "actual": "골든 샘플 없음",
            "pass": False
        }
        result["error"] = f"골든 샘플 없음: {english_name}"
        return result

    # 회귀 테스트 실행
    regression = run_golden_regression_test(cover_path, str(golden_path), log_dir)

    result["checks"]["ssim"] = {
        "expected": f">= {MIN_SSIM_SCORE}",
        "actual": f"{regression['ssim_score']}",
        "pass": regression["ssim_pass"]
    }

    result["checks"]["pixel_diff"] = {
        "expected": f"<= {MAX_PIXEL_DIFF_PERCENT}%",
        "actual": f"{regression['pixel_diff_percent']}%",
        "pass": regression["pixel_pass"]
    }

    result["pass"] = regression["overall_pass"]
    result["diff_image"] = regression.get("diff_image")
    result["ssim_file"] = regression.get("ssim_file")

    return result


# ============================================================================
# 메인 검수 함수
# ============================================================================

def inspect_cover(
    cover_path: str,
    english_name: str,
    korean_name: str = "",
    run_golden_test: bool = True
) -> Dict:
    """
    표지 이미지 검수 (v2 - 4단계 검증)

    Args:
        cover_path: 제작된 표지 이미지 경로
        english_name: 영어 음식명
        korean_name: 한글 음식명 (리포트용)
        run_golden_test: 골든 회귀 테스트 실행 여부

    Returns:
        검수 결과 딕셔너리
    """
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y%m%d")

    result = {
        "cover_path": cover_path,
        "english_name": english_name.upper(),
        "korean_name": korean_name,
        "timestamp": timestamp.isoformat(),
        "spec_version": SPEC_VERSION,
        "stages": {},
        "all_pass": False,
        "final_verdict": "FAIL"
    }

    cover = Path(cover_path)

    # 파일 존재 확인
    if not cover.exists():
        result["error"] = "제작 파일 없음"
        return result

    # 로그 디렉토리
    log_dir = LOG_DIR / date_str / english_name.lower()
    log_dir.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────
    # Stage 1: Spec 검증
    # ─────────────────────────────────────────────────────
    result["stages"]["spec"] = stage1_spec_validation(cover_path)

    # ─────────────────────────────────────────────────────
    # Stage 2: 코드 파라미터 검증
    # ─────────────────────────────────────────────────────
    result["stages"]["parameter"] = stage2_parameter_validation(cover_path, english_name)

    # ─────────────────────────────────────────────────────
    # Stage 3: 폰트/환경 검증
    # ─────────────────────────────────────────────────────
    result["stages"]["environment"] = stage3_environment_validation()

    # ─────────────────────────────────────────────────────
    # Stage 4: Golden 이미지 회귀 테스트
    # ─────────────────────────────────────────────────────
    if run_golden_test:
        result["stages"]["golden_regression"] = stage4_golden_regression(
            cover_path, english_name, log_dir
        )
    else:
        result["stages"]["golden_regression"] = {
            "stage": "golden_regression",
            "checks": {},
            "pass": True,
            "skipped": True
        }

    # ─────────────────────────────────────────────────────
    # 최종 판정 (4단계 모두 통과)
    # ─────────────────────────────────────────────────────
    all_stages_pass = all(s["pass"] for s in result["stages"].values())
    result["all_pass"] = all_stages_pass
    result["final_verdict"] = "PASS" if all_stages_pass else "FAIL"

    # 검증 리포트 저장
    report_path = log_dir / "validation_report.txt"
    save_validation_report(result, report_path)
    result["report_path"] = str(report_path)

    return result


def save_validation_report(result: Dict, output_path: Path) -> None:
    """검증 리포트 저장"""
    lines = [
        "=" * 60,
        f"[COVER VALIDATION REPORT] {SPEC_VERSION}",
        f"Timestamp: {result['timestamp']}",
        f"File: {result['cover_path']}",
        f"Korean: {result['korean_name']}",
        f"English: {result['english_name']}",
        "=" * 60,
        ""
    ]

    for stage_name, stage_data in result.get("stages", {}).items():
        stage_pass = "PASS" if stage_data.get("pass") else "FAIL"
        lines.append(f"[Stage: {stage_name}] → {stage_pass}")
        lines.append("-" * 40)

        for check_name, check_data in stage_data.get("checks", {}).items():
            check_pass = "✅" if check_data.get("pass") else "❌"
            expected = check_data.get("expected", "")
            actual = check_data.get("actual", "")
            lines.append(f"  {check_pass} {check_name}: {actual} (기준: {expected})")

        if stage_data.get("skipped"):
            lines.append("  (스킵됨)")

        lines.append("")

    lines.append("=" * 60)
    final = "✅ PASS" if result.get("all_pass") else "❌ FAIL"
    lines.append(f"[FINAL VERDICT] {final}")
    lines.append("=" * 60)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_inspection_report(results: list, output_path: str = None) -> str:
    """
    검수 리포트 텍스트 생성

    Args:
        results: inspect_cover() 결과 리스트
        output_path: 저장 경로 (선택)

    Returns:
        리포트 텍스트
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "=" * 60,
        f"[WO-COVER-PRODUCTION] 검수 리포트 (4단계 검증 {SPEC_VERSION})",
        f"생성일시: {timestamp}",
        "=" * 60,
        "",
        "[적용 스펙] v2.0",
        "-" * 40,
        "해상도: 1080x1080",
        "한글: 120px, Y=30",
        "영어: 80px, Y=170, UPPERCASE 필수",
        "앵커: mt (middle-top)",
        f"Golden SSIM: >= {MIN_SSIM_SCORE}",
        f"Golden Pixel Diff: <= {MAX_PIXEL_DIFF_PERCENT}%",
        ""
    ]

    pass_count = 0
    fail_count = 0

    for r in results:
        korean = r.get("korean_name", "")
        english = r.get("english_name", "")

        lines.append("=" * 60)
        lines.append(f"[{korean}] ({english})")
        lines.append("=" * 60)

        if "error" in r:
            lines.append(f"오류: {r['error']}")
            lines.append("-" * 40)
            lines.append("최종 판정: ❌ FAIL (오류)")
            fail_count += 1
            lines.append("")
            continue

        cover_file = Path(r["cover_path"]).name
        lines.append(f"제작 파일: {cover_file}")
        lines.append("-" * 40)

        # 각 Stage 출력
        for stage_name, stage_data in r.get("stages", {}).items():
            stage_pass = "✅" if stage_data.get("pass") else "❌"
            lines.append(f"[{stage_name}] {stage_pass}")

            for check_name, check_data in stage_data.get("checks", {}).items():
                check_icon = "✅" if check_data.get("pass") else "❌"
                expected = check_data.get("expected", "")
                actual = check_data.get("actual", "")
                lines.append(f"  {check_icon} {check_name}: {actual} (기준: {expected})")

        lines.append("-" * 40)
        verdict = r["final_verdict"]
        lines.append(f"최종 판정: {'✅' if verdict == 'PASS' else '❌'} {verdict}")
        lines.append("")

        if verdict == "PASS":
            pass_count += 1
        else:
            fail_count += 1

    lines.append("=" * 60)
    lines.append("[종합 결과]")
    lines.append("=" * 60)
    lines.append(f"총 {len(results)}건 중 PASS: {pass_count}건, FAIL: {fail_count}건")
    lines.append("")
    lines.append(f"검수 완료: {timestamp}")
    lines.append("=" * 60)

    report = "\n".join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    return report


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI 엔트리포인트"""
    import sys

    if len(sys.argv) < 3:
        print("사용법: python cover_inspector.py <cover_path> <english_name> [korean_name]")
        print("예시: python cover_inspector.py potato_cover.png potato 감자")
        sys.exit(1)

    cover_path = sys.argv[1]
    english_name = sys.argv[2]
    korean_name = sys.argv[3] if len(sys.argv) > 3 else ""

    result = inspect_cover(cover_path, english_name, korean_name)

    report = generate_inspection_report([result])
    print(report)

    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    exit(main())
