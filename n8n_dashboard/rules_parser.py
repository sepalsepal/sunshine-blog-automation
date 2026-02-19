#!/usr/bin/env python3
"""
RULES.md 파서
입력 형식: "1, 00룰 - 입력 체크 : 체크완료"
출력: {"number": 1, "rule_id": "00룰", "description": "입력 체크", "result": "체크완료"}
"""
import re
from pathlib import Path

RULES_PATH = Path(__file__).parent.parent / "RULES.md"

def parse_rule_line(line: str) -> dict:
    """
    단일 룰 라인 파싱
    형식: "N, XX룰 - 설명 : 결과"
    """
    try:
        # 쉼표로 번호 분리
        parts = line.split(",", 1)
        if len(parts) < 2:
            return {"raw": line.strip(), "parsed": False}

        number = parts[0].strip()
        rest = parts[1].strip()

        # 대시로 룰ID와 나머지 분리
        if " - " in rest:
            rule_parts = rest.split(" - ", 1)
            rule_id = rule_parts[0].strip()
            desc_result = rule_parts[1].strip()
        else:
            return {"raw": line.strip(), "parsed": False}

        # 콜론으로 설명과 결과 분리
        if " : " in desc_result:
            desc_parts = desc_result.split(" : ", 1)
            description = desc_parts[0].strip()
            result = desc_parts[1].strip()
        else:
            description = desc_result
            result = None

        return {
            "number": int(number) if number.isdigit() else number,
            "rule_id": rule_id,
            "description": description,
            "result": result,
            "parsed": True
        }
    except Exception as e:
        return {"raw": line.strip(), "parsed": False, "error": str(e)}


def parse_rules_block(text: str) -> list:
    """여러 줄의 룰 텍스트 파싱"""
    lines = text.strip().split("\n")
    return [parse_rule_line(line) for line in lines if line.strip()]


def extract_rules_from_md(section_pattern: str = None) -> list:
    """RULES.md에서 룰 목록 추출"""
    if not RULES_PATH.exists():
        return []

    with open(RULES_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 섹션 헤더 추출 (## 또는 ### 로 시작)
    rules = []
    section_pattern = re.compile(r"^###?\s+(\d+\.?\d*)\s+(.+?)(?:\s+🔒)?$", re.MULTILINE)

    for match in section_pattern.finditer(content):
        section_num = match.group(1)
        section_title = match.group(2).strip()
        rules.append({
            "section": section_num,
            "title": section_title,
            "rule_id": f"{section_num}룰"
        })

    return rules


def get_node_rules(node_name: str) -> list:
    """노드명에 해당하는 룰 목록 반환"""
    # 노드-룰 매핑 (실제 n8n 노드 구성에 맞게 수정 필요)
    node_rule_map = {
        "입력": ["00룰"],
        "텍스트작성": ["01룰", "02룰"],
        "이미지생성": ["03룰"],
        "검증": ["04룰", "05룰"],
        "게시": ["06룰", "07룰"],
    }
    return node_rule_map.get(node_name, [])


if __name__ == "__main__":
    # 테스트
    print("=" * 50)
    print("RULES.md 파서 테스트")
    print("=" * 50)

    # 단일 라인 파싱 테스트
    test_lines = [
        "1, 00룰 - 입력 체크 : 체크완료",
        "2, 01룰 - 문장 끝 마침표 : 체크완료",
        "3, 02룰 - 이모지 사용 : 실패",
        "잘못된 형식",
    ]

    print("\n📋 단일 라인 파싱:")
    for line in test_lines:
        result = parse_rule_line(line)
        print(f"  입력: {line}")
        print(f"  출력: {result}")
        print()

    # RULES.md 섹션 추출
    print("📄 RULES.md 섹션 추출:")
    rules = extract_rules_from_md()
    for rule in rules[:10]:
        print(f"  {rule}")
