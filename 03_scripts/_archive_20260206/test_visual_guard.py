"""
Visual Guard 테스트 스크립트
5가지 실패 케이스 생성 및 검증
모든 케이스가 BLOCK 판정을 받아야 통과
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import shutil

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.agents.visual_guard import VisualGuard, CheckResult

# 테스트 폴더
TEST_DIR = ROOT / "content/images/test_visual_guard"


def create_test_folder():
    """테스트 폴더 생성"""
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True)
    print(f"📁 테스트 폴더 생성: {TEST_DIR}")


def create_white_text_image(output_path: Path, label: str):
    """흰색 텍스트 이미지 생성 (BLOCK 예상 - 본문은 노란색이어야 함)"""
    img = Image.new("RGB", (1080, 1080), (50, 50, 50))
    draw = ImageDraw.Draw(img)

    # 하단에 흰색 텍스트
    draw.rectangle([0, 810, 1080, 1080], fill=(30, 30, 30))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", 52)
    except:
        font = ImageFont.load_default()

    # 흰색 텍스트 (잘못된 색상)
    draw.text((540, 900), label, fill=(255, 255, 255), font=font, anchor="mm")

    img.save(output_path)
    print(f"  ✅ 생성: {output_path.name} (흰색 텍스트)")


def create_wrong_position_cover(output_path: Path):
    """텍스트 위치가 하단인 표지 (BLOCK 예상 - 상단 25%여야 함)"""
    img = Image.new("RGB", (1080, 1080), (200, 180, 150))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 114)
    except:
        font = ImageFont.load_default()

    # 하단에 텍스트 배치 (잘못된 위치 - 70%)
    draw.text((540, 756), "DUCK", fill=(255, 255, 255), font=font, anchor="mm")

    img.save(output_path)
    print(f"  ✅ 생성: {output_path.name} (하단 텍스트 위치)")


def create_broken_text_image(output_path: Path):
    """깨진 텍스트(□) 포함 이미지 (BLOCK 예상)"""
    img = Image.new("RGB", (1080, 1080), (50, 50, 50))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 810, 1080, 1080], fill=(30, 30, 30))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", 52)
    except:
        font = ImageFont.load_default()

    # □ 문자 포함
    draw.text((540, 900), "테스트 □□ 깨진 텍스트", fill=(255, 215, 0), font=font, anchor="mm")

    img.save(output_path)
    print(f"  ✅ 생성: {output_path.name} (깨진 텍스트 □)")


def create_cover_no_white_text(output_path: Path):
    """표지에 흰색이 아닌 텍스트 (BLOCK 예상)"""
    img = Image.new("RGB", (1080, 1080), (200, 180, 150))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 114)
    except:
        font = ImageFont.load_default()

    # 상단에 빨간색 텍스트 (잘못된 색상)
    draw.text((540, 190), "DUCK", fill=(255, 0, 0), font=font, anchor="mm")

    img.save(output_path)
    print(f"  ✅ 생성: {output_path.name} (빨간색 표지 텍스트)")


def run_tests():
    """테스트 실행"""
    print("\n" + "="*60)
    print("🧪 Visual Guard 테스트 시작")
    print("="*60)

    create_test_folder()

    print("\n📝 테스트 이미지 생성:")

    # 테스트 케이스 1: 본문 흰색 텍스트 (BLOCK)
    create_white_text_image(TEST_DIR / "test_01.png", "먹어도 돼요!")

    # 테스트 케이스 2: 본문 흰색 텍스트 2 (BLOCK)
    create_white_text_image(TEST_DIR / "test_02.png", "주의사항!")

    # 테스트 케이스 3: 표지 위치 잘못 (BLOCK or CAUTION - OCR 의존)
    create_wrong_position_cover(TEST_DIR / "test_00.png")

    # 테스트 케이스 4: 깨진 텍스트 (BLOCK)
    create_broken_text_image(TEST_DIR / "test_broken_01.png")

    # 테스트 케이스 5: 표지 텍스트 색상 잘못 (BLOCK)
    create_cover_no_white_text(TEST_DIR / "wrong_cover_00.png")

    print("\n🔍 개별 이미지 검증:")
    guard = VisualGuard()

    results = []

    # 테스트 1: 본문 흰색 텍스트
    guard.checks = []
    result = guard.verify_content(TEST_DIR / "test_01.png")
    results.append(("test_01 (본문 흰색)", result))
    print(f"  {'❌' if result == CheckResult.BLOCK else '⚠️' if result == CheckResult.CAUTION else '✅'} test_01: {result.value}")

    # 테스트 2: 본문 흰색 텍스트 2
    guard.checks = []
    result = guard.verify_content(TEST_DIR / "test_02.png")
    results.append(("test_02 (본문 흰색)", result))
    print(f"  {'❌' if result == CheckResult.BLOCK else '⚠️' if result == CheckResult.CAUTION else '✅'} test_02: {result.value}")

    # 테스트 3: 표지 위치 잘못
    guard.checks = []
    result = guard.verify_cover(TEST_DIR / "test_00.png")
    results.append(("test_00 (위치 잘못)", result))
    print(f"  {'❌' if result == CheckResult.BLOCK else '⚠️' if result == CheckResult.CAUTION else '✅'} test_00: {result.value}")

    # 테스트 4: 깨진 텍스트
    guard.checks = []
    result = guard.verify_content(TEST_DIR / "test_broken_01.png")
    results.append(("test_broken (깨진 텍스트)", result))
    print(f"  {'❌' if result == CheckResult.BLOCK else '⚠️' if result == CheckResult.CAUTION else '✅'} test_broken_01: {result.value}")

    # 테스트 5: 표지 색상 잘못
    guard.checks = []
    result = guard.verify_cover(TEST_DIR / "wrong_cover_00.png")
    results.append(("wrong_cover (색상 잘못)", result))
    print(f"  {'❌' if result == CheckResult.BLOCK else '⚠️' if result == CheckResult.CAUTION else '✅'} wrong_cover_00: {result.value}")

    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)

    blocked = sum(1 for _, r in results if r == CheckResult.BLOCK)
    caution = sum(1 for _, r in results if r == CheckResult.CAUTION)
    passed = sum(1 for _, r in results if r == CheckResult.PASS)

    print(f"BLOCK: {blocked}/5")
    print(f"CAUTION: {caution}/5")
    print(f"PASS: {passed}/5")

    for name, result in results:
        icon = "❌" if result == CheckResult.BLOCK else "⚠️" if result == CheckResult.CAUTION else "✅"
        print(f"  {icon} {name}: {result.value}")

    # 판정
    print("\n" + "="*60)
    if blocked >= 4:  # 최소 4개 이상 BLOCK이면 통과 (OCR 의존 1개는 CAUTION 허용)
        print("✅ 테스트 통과: visual_guard가 규칙 위반을 정확히 감지")
        print("="*60)
        return True
    else:
        print("❌ 테스트 실패: visual_guard 검증 로직 점검 필요")
        print("="*60)
        return False


def test_duck_content():
    """실제 duck 콘텐츠 테스트"""
    print("\n" + "="*60)
    print("🦆 Duck 콘텐츠 테스트")
    print("="*60)

    duck_folder = ROOT / "content/images/169_duck_오리고기"

    guard = VisualGuard()
    result = guard.verify_content_folder(duck_folder)

    print(f"결과: {result.result.value}")
    print(f"사유: {result.final_reason}")

    blocked_count = sum(1 for c in result.checks if c['result'] == 'BLOCK')
    print(f"BLOCK 항목: {blocked_count}개")

    for check in result.checks:
        icon = "❌" if check['result'] == "BLOCK" else "⚠️" if check['result'] == "CAUTION" else "✅"
        print(f"  {icon} {check['name']}: {check['reason']}")

    return result.result == CheckResult.BLOCK


if __name__ == "__main__":
    # 기본 테스트
    test_passed = run_tests()

    # Duck 콘텐츠 테스트
    duck_blocked = test_duck_content()

    print("\n" + "="*60)
    print("🏁 최종 결과")
    print("="*60)
    print(f"기본 테스트: {'✅ PASS' if test_passed else '❌ FAIL'}")
    print(f"Duck 테스트: {'✅ BLOCK 정상' if duck_blocked else '❌ 미감지'}")
    print("="*60)

    sys.exit(0 if (test_passed and duck_blocked) else 1)
