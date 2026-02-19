#!/usr/bin/env python3
"""
caption_fix.py - 캡션 FAIL 수정 (WO-2026-0216-CAPTION-FIX)

우선순위:
1. FORBIDDEN 급여량 제거 (블로그 B7, 인스타 A6)
2. 수의사 상담 문구 추가 (인스타 A9)
3. 쓰레드 해시태그 추가 (C6) - 001~020 제외
4. 블로그 소량 수정 (B3/B4 이미지 마커) - 001~020 제외
"""

import os
import sys
import re
import json
from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"

# 수정 통계
stats = {
    "p1_forbidden": {"total": 0, "success": 0, "fail": 0},
    "p2_vet": {"total": 0, "success": 0, "fail": 0},
    "p3_hashtag": {"total": 0, "success": 0, "fail": 0},
    "p4_blog": {"total": 0, "success": 0, "fail": 0},
}

# ============================================================
# 유틸리티 함수
# ============================================================

def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기"""
    pattern = f"{num:03d}_*"
    matches = list(CONTENTS_DIR.glob(pattern))
    if matches:
        return matches[0]
    return None


def find_caption_file(folder: Path, platform: str) -> Path:
    """캡션 파일 찾기"""
    if platform == "insta":
        dir_path = folder / "01_Insta&Thread"
        pattern = "*_Insta_Caption.txt"
    elif platform == "blog":
        dir_path = folder / "02_Blog"
        pattern = "*_Blog_Caption.txt"
    elif platform == "thread":
        dir_path = folder / "01_Insta&Thread"
        pattern = "*_Threads_Caption.txt"
    else:
        return None

    if dir_path.exists():
        files = list(dir_path.glob(pattern))
        if files:
            return files[0]
    return None


def read_file(path: Path) -> str:
    """파일 읽기"""
    if path and path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def write_file(path: Path, content: str):
    """파일 쓰기"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


# ============================================================
# 우선순위 1: FORBIDDEN 급여량 제거
# ============================================================

FORBIDDEN_WARNING = """## ⛔ 이 음식은 급여량·조리법이 없습니다

이 음식은 어떤 형태로든, 어떤 양이든 강아지에게 줄 수 없습니다.
"조금만", "한 번만"이라는 생각이 가장 위험합니다."""


def fix_forbidden_dosage_blog(folder: Path) -> bool:
    """블로그 캡션에서 FORBIDDEN 급여량 제거"""
    caption_path = find_caption_file(folder, "blog")
    if not caption_path:
        return False

    content = read_file(caption_path)
    original = content

    # 급여량 관련 패턴 제거
    # 패턴 1: ## 급여량 or ## 체중별 급여량 섹션 전체
    content = re.sub(
        r'##\s*(급여량|체중별 급여량|권장 급여량).*?(?=##|\Z)',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 패턴 2: 소형견/중형견/대형견 라인 제거
    content = re.sub(
        r'[-•]\s*(소형견|중형견|대형견|초소형견|초대형견)[^\n]*\n?',
        '',
        content,
        flags=re.IGNORECASE
    )

    # 패턴 3: Xg 형태의 급여량 (15~20g 등)
    content = re.sub(
        r'(:\s*)?\d+~?\d*g[^\n]*\n?',
        '',
        content
    )

    # 패턴 4: 조리법/레시피 섹션 제거 (FORBIDDEN에서)
    content = re.sub(
        r'##\s*(조리법|레시피|조리방법|만들기).*?(?=##|\Z)',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 경고문이 없으면 추가
    if "급여량·조리법이 없습니다" not in content:
        # 적절한 위치에 삽입 (이미지 8번 또는 이미지 7번 후)
        if "[이미지 8번" in content:
            content = re.sub(
                r'(\[이미지 8번[^\]]*\])',
                f'\\1\n\n{FORBIDDEN_WARNING}\n',
                content
            )
        elif "[이미지 7번" in content:
            content = re.sub(
                r'(\[이미지 7번[^\]]*\])',
                f'\\1\n\n{FORBIDDEN_WARNING}\n',
                content
            )
        else:
            # 해시태그 앞에 삽입
            if "#" in content:
                hashtag_pos = content.rfind("\n#")
                if hashtag_pos > 0:
                    content = content[:hashtag_pos] + f"\n\n{FORBIDDEN_WARNING}\n" + content[hashtag_pos:]

    # 중복 빈 줄 정리
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        write_file(caption_path, content)
        return True
    return False


def fix_forbidden_dosage_insta(folder: Path) -> bool:
    """인스타 캡션에서 FORBIDDEN 급여량 제거"""
    caption_path = find_caption_file(folder, "insta")
    if not caption_path:
        return False

    content = read_file(caption_path)
    original = content

    # 급여량 섹션 제거
    content = re.sub(
        r'📏\s*급여량.*?(?=\n\n|\n[^\s]|$)',
        '',
        content,
        flags=re.DOTALL
    )

    # 소형견/중형견/대형견 라인 제거
    content = re.sub(
        r'[-•]\s*(소형견|Small|중형견|Medium|대형견|Large)[^\n]*\n?',
        '',
        content,
        flags=re.IGNORECASE
    )

    # Xg 형태 제거
    content = re.sub(
        r'\d+~?\d*g[^\n]*\n?',
        '',
        content
    )

    # 중복 빈 줄 정리
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        write_file(caption_path, content)
        return True
    return False


# ============================================================
# 우선순위 2: 수의사 상담 문구 추가
# ============================================================

VET_TEXT = """
🏥 이상 증상이 보이면 수의사와 상담하세요.
If you notice any symptoms, consult your vet.
"""


def add_vet_consultation(folder: Path) -> bool:
    """인스타 캡션에 수의사 상담 문구 추가"""
    caption_path = find_caption_file(folder, "insta")
    if not caption_path:
        return False

    content = read_file(caption_path)

    # 이미 수의사 문구 있으면 스킵
    if "수의사" in content or "veterinarian" in content.lower() or "vet" in content.lower():
        # "vet" 단독으로 있는지 확인 (다른 단어 일부가 아닌)
        if re.search(r'\bvet\b', content, re.IGNORECASE):
            return False

    # 해시태그 위치 찾기
    lines = content.split('\n')
    hashtag_line_idx = -1

    for i, line in enumerate(lines):
        if line.strip().startswith('#') and len(re.findall(r'#\w+', line)) >= 3:
            hashtag_line_idx = i
            break

    if hashtag_line_idx == -1:
        # 해시태그 못 찾으면 끝에 추가
        content = content.rstrip() + VET_TEXT
    else:
        # 해시태그 바로 위에 삽입
        lines.insert(hashtag_line_idx, VET_TEXT.strip())
        content = '\n'.join(lines)

    write_file(caption_path, content)
    return True


# ============================================================
# 우선순위 3: 쓰레드 해시태그 추가
# ============================================================

def add_thread_hashtag(folder: Path) -> bool:
    """쓰레드 캡션에 #CanMyDogEatThis 추가"""
    caption_path = find_caption_file(folder, "thread")
    if not caption_path:
        return False

    content = read_file(caption_path)

    # 이미 있으면 스킵
    if "#CanMyDogEatThis" in content or "#canmydogeatthis" in content.lower():
        return False

    # 해시태그 찾기
    hashtag_match = re.search(r'(#\w+)', content)
    if hashtag_match:
        # 기존 해시태그 앞에 추가
        first_hashtag = hashtag_match.group(1)
        content = content.replace(first_hashtag, f"#CanMyDogEatThis {first_hashtag}")
    else:
        # 없으면 끝에 추가
        content = content.rstrip() + "\n\n#CanMyDogEatThis"

    write_file(caption_path, content)
    return True


# ============================================================
# 우선순위 4: 블로그 이미지 마커 수정
# ============================================================

def fix_blog_image_markers(folder: Path) -> bool:
    """블로그 캡션 이미지 마커 9개로 수정"""
    caption_path = find_caption_file(folder, "blog")
    if not caption_path:
        return False

    content = read_file(caption_path)

    # 현재 이미지 마커 확인
    markers = re.findall(r'\[이미지\s*(\d+)번', content)
    marker_nums = set(int(m) for m in markers)

    # 이미 9개 있으면 스킵
    if len(marker_nums) >= 9 and all(i in marker_nums for i in range(1, 10)):
        return False

    # 누락된 마커 찾기
    missing = [i for i in range(1, 10) if i not in marker_nums]

    if not missing:
        return False

    # 누락된 마커 추가 (간단한 설명과 함께)
    additions = []
    for num in missing:
        if num == 9:
            marker = f"\n[이미지 9번: CTA - 더 많은 정보는 프로필 링크에서]\n"
        else:
            marker = f"\n[이미지 {num}번: 추가 정보]\n"
        additions.append(marker)

    # 해시태그 앞에 추가
    if "#" in content:
        hashtag_pos = content.rfind("\n#")
        if hashtag_pos > 0:
            insert_text = '\n'.join(additions)
            content = content[:hashtag_pos] + insert_text + content[hashtag_pos:]
    else:
        content += '\n'.join(additions)

    write_file(caption_path, content)
    return True


# ============================================================
# 메인 실행
# ============================================================

def main():
    print("=" * 60)
    print("WO-2026-0216-CAPTION-FIX 실행")
    print("=" * 60)

    # 검증 결과 로드
    result_path = PROJECT_ROOT / "caption_verify_result.json"
    with open(result_path, 'r', encoding='utf-8') as f:
        verify_result = json.load(f)

    # ============================================================
    # [우선순위 1] FORBIDDEN 급여량 제거
    # ============================================================
    print("\n[우선순위 1] FORBIDDEN 급여량 제거...")

    # B7 FAIL (블로그)
    forbidden_blog = [
        f for f in verify_result["blog"]["fails"]
        if "B7" in f["failed"] and f["safety"] == "FORBIDDEN"
    ]

    # A6 FAIL (인스타)
    forbidden_insta = [
        f for f in verify_result["insta"]["fails"]
        if "A6" in f["failed"]
    ]

    print(f"  대상: 블로그 {len(forbidden_blog)}건, 인스타 {len(forbidden_insta)}건")

    for item in forbidden_blog:
        folder = find_content_folder(item["num"])
        if folder:
            stats["p1_forbidden"]["total"] += 1
            if fix_forbidden_dosage_blog(folder):
                stats["p1_forbidden"]["success"] += 1
                print(f"    ✅ {item['num']:03d}_{item['name']} (블로그)")
            else:
                stats["p1_forbidden"]["fail"] += 1
                print(f"    ⚠️ {item['num']:03d}_{item['name']} (블로그) - 변경 없음")

    for item in forbidden_insta:
        folder = find_content_folder(item["num"])
        if folder:
            stats["p1_forbidden"]["total"] += 1
            if fix_forbidden_dosage_insta(folder):
                stats["p1_forbidden"]["success"] += 1
                print(f"    ✅ {item['num']:03d}_{item['name']} (인스타)")
            else:
                stats["p1_forbidden"]["fail"] += 1
                print(f"    ⚠️ {item['num']:03d}_{item['name']} (인스타) - 변경 없음")

    # ============================================================
    # [우선순위 2] 수의사 상담 문구 추가
    # ============================================================
    print("\n[우선순위 2] 수의사 상담 문구 추가...")

    # A9 FAIL 중 001~020 제외
    vet_targets = [
        f for f in verify_result["insta"]["fails"]
        if "A9" in f["failed"] and f["num"] > 20
    ]

    print(f"  대상: {len(vet_targets)}건 (001~020 제외)")

    fixed_count = 0
    for item in vet_targets:
        folder = find_content_folder(item["num"])
        if folder:
            stats["p2_vet"]["total"] += 1
            if add_vet_consultation(folder):
                stats["p2_vet"]["success"] += 1
                fixed_count += 1
            else:
                stats["p2_vet"]["fail"] += 1

    print(f"    완료: {fixed_count}건 수정")

    # ============================================================
    # [우선순위 3] 쓰레드 해시태그 추가
    # ============================================================
    print("\n[우선순위 3] 쓰레드 해시태그 추가...")

    # C6 FAIL 중 001~020 제외
    hashtag_targets = [
        f for f in verify_result["thread"]["fails"]
        if "C6" in f["failed"] and f["num"] > 20
    ]

    print(f"  대상: {len(hashtag_targets)}건 (001~020 제외)")

    for item in hashtag_targets:
        folder = find_content_folder(item["num"])
        if folder:
            stats["p3_hashtag"]["total"] += 1
            if add_thread_hashtag(folder):
                stats["p3_hashtag"]["success"] += 1
                print(f"    ✅ {item['num']:03d}_{item['name']}")
            else:
                stats["p3_hashtag"]["fail"] += 1
                print(f"    ⚠️ {item['num']:03d}_{item['name']} - 변경 없음")

    # ============================================================
    # [우선순위 4] 블로그 이미지 마커 수정
    # ============================================================
    print("\n[우선순위 4] 블로그 이미지 마커 수정...")

    # B3/B4 FAIL 중 001~020 제외
    marker_targets = [
        f for f in verify_result["blog"]["fails"]
        if ("B3" in f["failed"] or "B4" in f["failed"]) and f["num"] > 20
    ]

    print(f"  대상: {len(marker_targets)}건 (001~020 제외)")

    for item in marker_targets:
        folder = find_content_folder(item["num"])
        if folder:
            stats["p4_blog"]["total"] += 1
            if fix_blog_image_markers(folder):
                stats["p4_blog"]["success"] += 1
                print(f"    ✅ {item['num']:03d}_{item['name']}")
            else:
                stats["p4_blog"]["fail"] += 1
                print(f"    ⚠️ {item['num']:03d}_{item['name']} - 변경 없음")

    # ============================================================
    # 결과 출력
    # ============================================================
    print("\n" + "=" * 60)
    print("===== WO-2026-0216-CAPTION-FIX 완료 보고 =====")
    print("=" * 60)

    print(f"\n[우선순위 1] FORBIDDEN 급여량 제거: {stats['p1_forbidden']['success']}/{stats['p1_forbidden']['total']}건 완료")
    print(f"[우선순위 2] 수의사 문구 추가: {stats['p2_vet']['success']}/{stats['p2_vet']['total']}건 완료")
    print(f"[우선순위 3] 쓰레드 해시태그: {stats['p3_hashtag']['success']}/{stats['p3_hashtag']['total']}건 완료")
    print(f"[우선순위 4] 블로그 이미지 마커: {stats['p4_blog']['success']}/{stats['p4_blog']['total']}건 완료")

    total_success = sum(s["success"] for s in stats.values())
    total_target = sum(s["total"] for s in stats.values())

    print(f"\n총 수정: {total_success}/{total_target}건")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
