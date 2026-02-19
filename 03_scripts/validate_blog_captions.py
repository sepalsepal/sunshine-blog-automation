#!/usr/bin/env python3
"""
validate_blog_captions.py - 블로그 캡션 검수
BLOG_RULE.md 기준 검증 (v2.0)

Validator 체크리스트:
□ 글자수 1,620~1,980자
□ H2 4개 이상
□ 키워드 5회 이상
□ [이미지 N번: 설명] 8개
□ 4단계 급여량 포함
□ 직관적 단위 포함
□ 햇살이 엄마 톤
□ 보호자 동질감 3요소 포함
□ 팩트체크 항목 누락 없음
□ 해시태그 12~16개
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"


def validate_blog_caption(content: str, safety: str, name: str) -> dict:
    """블로그 캡션 검증 (BLOG_RULE.md 기준)"""
    result = {
        "passes": [],
        "fails": [],
        "warnings": [],
        "stats": {}
    }

    # 1. 글자수 1,620~1,980자
    char_count = len(content.replace(" ", "").replace("\n", ""))
    result["stats"]["글자수"] = char_count
    if 1620 <= char_count <= 1980:
        result["passes"].append(f"글자수 {char_count}자 PASS")
    elif 1500 <= char_count < 1620:
        result["warnings"].append(f"글자수 {char_count}자 (1,620자 미만)")
    elif 1980 < char_count <= 2100:
        result["warnings"].append(f"글자수 {char_count}자 (1,980자 초과)")
    else:
        result["fails"].append(f"글자수 {char_count}자 FAIL (1,620~1,980 필요)")

    # 2. H2 4개 이상
    h2_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
    result["stats"]["H2"] = h2_count
    if h2_count >= 4:
        result["passes"].append(f"H2 {h2_count}개 PASS")
    else:
        result["fails"].append(f"H2 {h2_count}개 FAIL (4개 이상 필요)")

    # 3. 키워드(음식명) 5회 이상
    keyword_count = content.count(name)
    result["stats"]["키워드"] = keyword_count
    if keyword_count >= 5:
        result["passes"].append(f"키워드 {keyword_count}회 PASS")
    else:
        result["fails"].append(f"키워드 {keyword_count}회 FAIL (5회 이상 필요)")

    # 4. [이미지 N번: 설명] 8개
    image_tags = re.findall(r'\[이미지\s*\d+번[:\s]', content)
    result["stats"]["이미지태그"] = len(image_tags)
    if len(image_tags) >= 8:
        result["passes"].append(f"이미지 태그 {len(image_tags)}개 PASS")
    else:
        result["fails"].append(f"이미지 태그 {len(image_tags)}개 FAIL (8개 필요)")

    # 5. 4단계 급여량 + 직관적 단위 (FORBIDDEN 제외)
    if safety != "FORBIDDEN":
        sizes = ["소형견", "중형견", "대형견", "초대형견"]
        found_sizes = [s for s in sizes if s in content]
        result["stats"]["급여량단계"] = len(found_sizes)
        if len(found_sizes) >= 4:
            result["passes"].append("급여량 4단계 PASS")
        else:
            result["fails"].append(f"급여량 {len(found_sizes)}단계 FAIL (4단계 필요)")

        # 직관적 단위 (괄호 안) - FAIL로 승격
        if re.search(r'\d+[~\-]\d+g.*\(.*\)', content):
            result["passes"].append("직관적 단위 PASS")
        else:
            result["fails"].append("직관적 단위 없음 FAIL")

    # 6. 햇살이 엄마 톤
    if "햇살이" in content:
        result["passes"].append("햇살이 언급 PASS")
    else:
        result["fails"].append("햇살이 언급 없음 FAIL")

    if "엄마" in content or "11살" in content:
        result["passes"].append("햇살이 엄마 톤 PASS")
    else:
        result["warnings"].append("햇살이 엄마 톤 확인 필요")

    # 7. 보호자 동질감 3요소
    empathy_elements = 0
    empathy_checks = []

    # 요소 1: 경험 공유 ("저도", "저희", "우리")
    if re.search(r'(저도|저희|우리\s*(아이|강아지|햇살이))', content):
        empathy_elements += 1
        empathy_checks.append("경험공유")

    # 요소 2: 감정 표현 ("좋아해요", "걱정", "사랑")
    if re.search(r'(좋아해요|걱정|사랑|행복|기뻐|마음이)', content):
        empathy_elements += 1
        empathy_checks.append("감정표현")

    # 요소 3: 조언/권유 ("추천해요", "해보세요", "드려요")
    if re.search(r'(추천|해보세요|드려요|해주세요|좋아요)', content):
        empathy_elements += 1
        empathy_checks.append("조언권유")

    result["stats"]["동질감요소"] = empathy_elements
    if empathy_elements >= 3:
        result["passes"].append(f"동질감 3요소 PASS ({'/'.join(empathy_checks)})")
    elif empathy_elements >= 2:
        result["warnings"].append(f"동질감 {empathy_elements}요소 ({'/'.join(empathy_checks)})")
    else:
        result["fails"].append(f"동질감 {empathy_elements}요소 FAIL (3요소 필요)")

    # 8. 팩트체크 5항목 (SAFE/CAUTION만 전체 체크, DANGER/FORBIDDEN은 완화)
    factcheck_items = 0
    factcheck_list = []

    # 8-1. 왜 익혀야 하는지/조리 이유
    if re.search(r'(익혀|삶|찌|굽|조리|가열|열을|생으로)', content):
        factcheck_items += 1
        factcheck_list.append("조리법")

    # 8-2. 독성/위험 부위 경고
    if re.search(r'(씨앗|씨|껍질|줄기|뿌리|독성|위험|제거)', content):
        factcheck_items += 1
        factcheck_list.append("위험부위")

    # 8-3. 기저 질환 견 주의
    if re.search(r'(당뇨|신장|알레르기|질환|수의사|병원|상담)', content):
        factcheck_items += 1
        factcheck_list.append("기저질환")

    # 8-4. 조리법 차이 설명
    if re.search(r'(vs|보다|차이|방법|최적|추천)', content):
        factcheck_items += 1
        factcheck_list.append("조리차이")

    # 8-5. 가공식품 경고
    if re.search(r'(가공|양념|시판|첨가물|조미료|금지|피하)', content):
        factcheck_items += 1
        factcheck_list.append("가공식품")

    result["stats"]["팩트체크"] = factcheck_items

    if safety in ["SAFE", "CAUTION"]:
        if factcheck_items >= 4:
            result["passes"].append(f"팩트체크 {factcheck_items}/5 PASS")
        elif factcheck_items >= 3:
            result["warnings"].append(f"팩트체크 {factcheck_items}/5 ({'/'.join(factcheck_list)})")
        else:
            result["fails"].append(f"팩트체크 {factcheck_items}/5 FAIL (4개 이상 필요)")
    else:  # DANGER, FORBIDDEN
        if factcheck_items >= 2:
            result["passes"].append(f"팩트체크 {factcheck_items}/5 PASS")
        else:
            result["warnings"].append(f"팩트체크 {factcheck_items}/5 ({'/'.join(factcheck_list)})")

    # 9. 해시태그 12~16개
    hashtags = re.findall(r'#[가-힣a-zA-Z0-9_]+', content)
    result["stats"]["해시태그"] = len(hashtags)
    if 12 <= len(hashtags) <= 16:
        result["passes"].append(f"해시태그 {len(hashtags)}개 PASS")
    elif len(hashtags) < 12:
        result["fails"].append(f"해시태그 {len(hashtags)}개 FAIL (12개 이상 필요)")
    else:
        result["warnings"].append(f"해시태그 {len(hashtags)}개 (16개 초과)")

    # 10. AI 고지 없어야 함
    if "AI로 생성" in content or "AI 고지" in content or "AI의 도움" in content:
        result["fails"].append("AI 고지 포함됨 FAIL")
    else:
        result["passes"].append("AI 고지 없음 PASS")

    # 11. 제목 질문형 (권장)
    if re.search(r'먹어도.*(되나요|될까요)\?', content):
        result["passes"].append("질문형 제목 PASS")
    else:
        result["warnings"].append("질문형 제목 확인 필요")

    return result


def main():
    # 범위 파싱
    start_id = 6
    end_id = 20

    if len(sys.argv) >= 3:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[2])
    elif len(sys.argv) == 2:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[1])

    # food_data.json 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    print("=" * 70)
    print(f"블로그 캡션 검수 v2.0 ({start_id:03d}~{end_id:03d})")
    print("BLOG_RULE.md Validator 체크리스트 기준")
    print("=" * 70)

    total = 0
    pass_count = 0
    fail_count = 0

    for food_id in range(start_id, end_id + 1):
        food_id_str = str(food_id)

        if food_id_str not in food_data:
            continue

        data = food_data[food_id_str]
        name = data.get("name", "")
        safety = data.get("safety", "SAFE")

        # 폴더 찾기
        folder_pattern = f"{food_id:03d}_*"
        matches = list(CONTENTS_DIR.glob(folder_pattern))

        if not matches:
            print(f"\n[{food_id:03d}] {name} - 폴더 없음")
            continue

        content_folder = matches[0]
        blog_folder = content_folder / "02_Blog"

        if not blog_folder.exists():
            print(f"\n[{food_id:03d}] {name} - 02_Blog 폴더 없음")
            continue

        # 블로그 캡션 찾기
        caption_files = list(blog_folder.glob("*_Blog_Caption.txt"))

        if not caption_files:
            print(f"\n[{food_id:03d}] {name} - 캡션 파일 없음")
            continue

        total += 1
        caption_file = caption_files[0]

        try:
            content = caption_file.read_text(encoding='utf-8')
            result = validate_blog_caption(content, safety, name)

            has_fail = len(result["fails"]) > 0

            if has_fail:
                fail_count += 1
                status = "❌ FAIL"
            else:
                pass_count += 1
                status = "✅ PASS"

            stats = result["stats"]
            print(f"\n[{food_id:03d}] {name} ({safety}) - {status}")
            print(f"    글자수: {stats.get('글자수', 0)}자 | H2: {stats.get('H2', 0)}개 | 키워드: {stats.get('키워드', 0)}회 | 이미지: {stats.get('이미지태그', 0)}개")
            print(f"    해시태그: {stats.get('해시태그', 0)}개 | 동질감: {stats.get('동질감요소', 0)}요소 | 팩트체크: {stats.get('팩트체크', 0)}/5")

            if result["fails"]:
                for f in result["fails"]:
                    print(f"    ❌ {f}")

            if result["warnings"]:
                for w in result["warnings"]:
                    print(f"    ⚠️ {w}")

        except Exception as e:
            fail_count += 1
            print(f"\n[{food_id:03d}] {name} - 오류: {e}")

    print("\n" + "=" * 70)
    print(f"검수 완료: {total}개")
    print(f"  PASS: {pass_count}개")
    print(f"  FAIL: {fail_count}개")
    print("=" * 70)


if __name__ == "__main__":
    main()
