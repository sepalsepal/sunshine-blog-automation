#!/usr/bin/env python3
"""
notion_pipeline_setup.py - 파이프라인 v2.7 노션 DB 컬럼 추가 및 동기화
[WO-NOTION-001]

Phase 1: 기획 (P1_*)
Phase 2: 텍스트 (P2_*)
Phase 3: 이미지 (P3_*)
Phase 4: 최종/게시 (P4_*)
메타: 진행률, 마지막업데이트, 에러내용
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

# === 새로운 컬럼 정의 ===
PIPELINE_COLUMNS = {
    # Phase 1: 기획
    "P1_규칙로드": {"type": "select", "options": ["완료", "실패", "대기"]},
    "P1_노션검토": {"type": "select", "options": ["완료", "실패", "대기"]},
    "P1_음식선정": {"type": "rich_text"},
    "P1_컨펌": {"type": "select", "options": ["승인", "거부", "대기"]},
    "P1_데이터수집": {"type": "select", "options": ["완료", "실패", "대기"]},
    "P1_안전도": {"type": "select", "options": ["SAFE", "CAUTION", "DANGER", "FORBIDDEN"]},
    "P1_팩트체크": {"type": "select", "options": ["완료", "실패", "대기"]},
    "P1_규칙검수": {"type": "select", "options": ["PASS", "FAIL", "대기"]},
    "P1_크리에이티브검수": {"type": "select", "options": ["PASS", "FAIL", "대기"]},

    # Phase 2: 텍스트
    "P2_텍스트규칙로드": {"type": "select", "options": ["완료", "대기"]},
    "P2_인스타캡션": {"type": "select", "options": ["PASS", "FAIL", "대기"]},
    "P2_인스타캡션_R": {"type": "select", "options": ["PASS", "FAIL"]},
    "P2_인스타캡션_C": {"type": "select", "options": ["PASS", "FAIL"]},
    "P2_쓰레드캡션": {"type": "select", "options": ["PASS", "FAIL", "대기"]},
    "P2_쓰레드캡션_R": {"type": "select", "options": ["PASS", "FAIL"]},
    "P2_쓰레드캡션_C": {"type": "select", "options": ["PASS", "FAIL"]},
    "P2_블로그본문": {"type": "select", "options": ["PASS", "FAIL", "대기"]},
    "P2_블로그본문_R": {"type": "select", "options": ["PASS", "FAIL"]},
    "P2_블로그본문_C": {"type": "select", "options": ["PASS", "FAIL"]},

    # Phase 3: 이미지
    "P3_이미지규칙로드": {"type": "select", "options": ["완료", "대기"]},
    "P3_표지제작": {"type": "select", "options": ["완료", "실패", "PENDING"]},
    "P3_표지_R": {"type": "select", "options": ["PASS", "FAIL"]},
    "P3_표지_C": {"type": "select", "options": ["PASS", "FAIL"]},
    "P3_슬라이드제작": {"type": "select", "options": ["완료", "실패", "PENDING"]},
    "P3_슬라이드_R": {"type": "select", "options": ["PASS", "FAIL"]},
    "P3_슬라이드_C": {"type": "select", "options": ["PASS", "FAIL"]},
    "P3_블로그이미지": {"type": "rich_text"},  # "6/8" 형식
    "P3_블로그이미지_1": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_블로그이미지_2": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_블로그이미지_3": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_블로그이미지_4": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_블로그이미지_5": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_블로그이미지_6": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_블로그이미지_7": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_블로그이미지_8": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_CTA제작": {"type": "select", "options": ["완료", "PENDING"]},
    "P3_CTA_R": {"type": "select", "options": ["PASS", "FAIL"]},
    "P3_CTA_C": {"type": "select", "options": ["PASS", "FAIL"]},

    # Phase 4: 최종/게시
    "P4_최종규칙검수": {"type": "select", "options": ["PASS", "FAIL", "진행중"]},
    "P4_최종크리에이티브": {"type": "select", "options": ["PASS", "FAIL", "대기"]},
    "P4_Cloudinary": {"type": "select", "options": ["완료", "대기"]},
    "P4_인스타게시": {"type": "select", "options": ["완료", "대기"]},
    "P4_쓰레드게시": {"type": "select", "options": ["완료", "대기"]},
    "P4_블로그게시": {"type": "select", "options": ["완료", "대기"]},
    "P4_동기화": {"type": "select", "options": ["완료", "대기"]},
    "P4_알림": {"type": "select", "options": ["완료", "대기"]},

    # 메타 정보
    "진행률": {"type": "number", "format": "percent"},
    "마지막업데이트": {"type": "date"},
    "에러내용": {"type": "rich_text"},
}


def get_headers() -> dict:
    """Notion API 헤더"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def get_database_schema() -> dict:
    """현재 DB 스키마 조회"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json()
    print(f"DB 스키마 조회 실패: {response.status_code}")
    print(response.text)
    return None


def add_database_properties(properties: Dict[str, Any]) -> bool:
    """
    DB에 새 속성(컬럼) 추가

    Notion API: PATCH /v1/databases/{database_id}
    """
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"

    payload = {"properties": properties}

    response = requests.patch(url, headers=get_headers(), json=payload)

    if response.status_code == 200:
        return True
    else:
        print(f"속성 추가 실패: {response.status_code}")
        print(response.text)
        return False


def build_property_schema(col_name: str, col_def: dict) -> dict:
    """컬럼 정의를 Notion property 스키마로 변환"""
    prop_type = col_def["type"]

    if prop_type == "select":
        return {
            "select": {
                "options": [{"name": opt} for opt in col_def.get("options", [])]
            }
        }
    elif prop_type == "multi_select":
        return {
            "multi_select": {
                "options": [{"name": opt} for opt in col_def.get("options", [])]
            }
        }
    elif prop_type == "rich_text":
        return {"rich_text": {}}
    elif prop_type == "number":
        schema = {"number": {}}
        if "format" in col_def:
            schema["number"]["format"] = col_def["format"]
        return schema
    elif prop_type == "date":
        return {"date": {}}
    elif prop_type == "checkbox":
        return {"checkbox": {}}
    elif prop_type == "url":
        return {"url": {}}
    else:
        return {"rich_text": {}}


def setup_pipeline_columns() -> bool:
    """
    파이프라인 컬럼 일괄 추가
    """
    print("=" * 60)
    print("노션 DB 파이프라인 컬럼 추가")
    print("=" * 60)

    # 현재 스키마 확인
    schema = get_database_schema()
    if not schema:
        return False

    existing_props = set(schema.get("properties", {}).keys())
    print(f"기존 컬럼: {len(existing_props)}개")

    # 추가할 속성 구성
    new_properties = {}
    skipped = []

    for col_name, col_def in PIPELINE_COLUMNS.items():
        if col_name in existing_props:
            skipped.append(col_name)
            continue
        new_properties[col_name] = build_property_schema(col_name, col_def)

    if skipped:
        print(f"이미 존재 (스킵): {len(skipped)}개")

    if not new_properties:
        print("추가할 새 컬럼 없음")
        return True

    print(f"추가할 컬럼: {len(new_properties)}개")

    # 배치로 추가 (Notion API 제한: 한 번에 최대 100개)
    batch_size = 50
    props_list = list(new_properties.items())

    for i in range(0, len(props_list), batch_size):
        batch = dict(props_list[i:i+batch_size])
        print(f"  배치 {i//batch_size + 1}: {len(batch)}개 추가 중...")

        if not add_database_properties(batch):
            print(f"  배치 {i//batch_size + 1} 실패")
            return False

        print(f"  배치 {i//batch_size + 1} 완료")

    print(f"\n총 {len(new_properties)}개 컬럼 추가 완료")
    return True


def find_notion_page(content_num: int) -> Optional[dict]:
    """번호로 노션 페이지 찾기"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    body = {
        "filter": {
            "property": "번호",
            "number": {"equals": content_num}
        }
    }

    response = requests.post(url, headers=get_headers(), json=body)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return results[0]
    return None


def update_notion_page(page_id: str, properties: dict) -> bool:
    """노션 페이지 업데이트"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": properties}

    response = requests.patch(url, headers=get_headers(), json=payload)
    if response.status_code != 200:
        print(f"업데이트 실패: {response.status_code}")
        print(response.text)
        return False
    return True


def build_property_value(prop_type: str, value: Any) -> dict:
    """값을 Notion property 형식으로 변환"""
    if prop_type == "select":
        return {"select": {"name": str(value)} if value else None}
    elif prop_type == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}] if value else []}
    elif prop_type == "number":
        return {"number": float(value) if value is not None else None}
    elif prop_type == "date":
        if isinstance(value, datetime):
            return {"date": {"start": value.isoformat()}}
        elif value:
            return {"date": {"start": str(value)}}
        return {"date": None}
    elif prop_type == "checkbox":
        return {"checkbox": bool(value)}
    elif prop_type == "url":
        return {"url": str(value) if value else None}
    return {"rich_text": [{"text": {"content": str(value)}}] if value else []}


def sync_fried_egg_data() -> bool:
    """
    계란후라이 (#163) 파이프라인 테스트 결과 동기화
    """
    print("\n" + "=" * 60)
    print("계란후라이 (#163) 데이터 동기화")
    print("=" * 60)

    # 노션 페이지 찾기
    page = find_notion_page(163)
    if not page:
        print("계란후라이 (#163) 페이지를 찾을 수 없음")
        # 페이지가 없으면 생성
        return create_fried_egg_page()

    page_id = page["id"]
    print(f"페이지 ID: {page_id}")

    # 파이프라인 테스트 결과 데이터
    data = {
        # Phase 1: 기획
        "P1_규칙로드": "완료",
        "P1_노션검토": "완료",
        "P1_음식선정": "계란후라이",
        "P1_컨펌": "승인",
        "P1_데이터수집": "완료",
        "P1_안전도": "CAUTION",
        "P1_팩트체크": "완료",
        "P1_규칙검수": "PASS",
        "P1_크리에이티브검수": "PASS",

        # Phase 2: 텍스트
        "P2_텍스트규칙로드": "완료",
        "P2_인스타캡션": "PASS",
        "P2_인스타캡션_R": "PASS",
        "P2_인스타캡션_C": "PASS",
        "P2_쓰레드캡션": "PASS",
        "P2_쓰레드캡션_R": "PASS",
        "P2_쓰레드캡션_C": "PASS",
        "P2_블로그본문": "PASS",
        "P2_블로그본문_R": "PASS",
        "P2_블로그본문_C": "PASS",

        # Phase 3: 이미지
        "P3_이미지규칙로드": "완료",
        "P3_표지제작": "PENDING",  # 표지 미생성
        "P3_표지_R": None,
        "P3_표지_C": None,
        "P3_슬라이드제작": "PENDING",  # 슬라이드 미생성
        "P3_슬라이드_R": None,
        "P3_슬라이드_C": None,
        "P3_블로그이미지": "6/8",  # 8장 중 6장 완료
        "P3_블로그이미지_1": "PENDING",  # 표지 (1번)
        "P3_블로그이미지_2": "PENDING",  # 음식사진 (2번)
        "P3_블로그이미지_3": "완료",  # 영양정보
        "P3_블로그이미지_4": "완료",  # 급여가능불가
        "P3_블로그이미지_5": "완료",  # 급여량표
        "P3_블로그이미지_6": "완료",  # 주의사항
        "P3_블로그이미지_7": "완료",  # 조리방법
        "P3_블로그이미지_8": "완료",  # 햇살이
        "P3_CTA제작": "PENDING",
        "P3_CTA_R": None,
        "P3_CTA_C": None,

        # Phase 4: 최종/게시
        "P4_최종규칙검수": "진행중",
        "P4_최종크리에이티브": "대기",
        "P4_Cloudinary": "대기",
        "P4_인스타게시": "대기",
        "P4_쓰레드게시": "대기",
        "P4_블로그게시": "대기",
        "P4_동기화": "대기",
        "P4_알림": "대기",

        # 메타
        "진행률": 0.65,  # 65%
        "마지막업데이트": datetime.now(),
        "에러내용": "Phase 3 이미지 2개 미완료 (표지, 음식사진)",
    }

    # 속성 변환
    properties = {}
    for col_name, value in data.items():
        if col_name in PIPELINE_COLUMNS:
            col_def = PIPELINE_COLUMNS[col_name]
            prop_value = build_property_value(col_def["type"], value)
            if prop_value:
                properties[col_name] = prop_value

    # 업데이트
    if update_notion_page(page_id, properties):
        print(f"계란후라이 (#163) 동기화 완료")
        print(f"  Phase 1 (기획): 완료")
        print(f"  Phase 2 (텍스트): 완료")
        print(f"  Phase 3 (이미지): 6/8")
        print(f"  Phase 4 (게시): 대기")
        print(f"  진행률: 65%")
        return True
    else:
        print("동기화 실패")
        return False


def create_fried_egg_page() -> bool:
    """계란후라이 페이지 생성"""
    url = "https://api.notion.com/v1/pages"

    # 기본 속성 (기존 DB 스키마에 맞춤)
    properties = {
        "이름": {"title": [{"text": {"content": "계란후라이"}}]},
        "번호": {"number": 163},
        "한글명": {"rich_text": [{"text": {"content": "계란후라이"}}]},
        "폴더명": {"rich_text": [{"text": {"content": "163_fried_egg_계란후라이"}}]},
        "안전도": {"select": {"name": "CAUTION"}},
    }

    # 파이프라인 상태 추가
    pipeline_data = {
        "P1_규칙로드": "완료",
        "P1_음식선정": "계란후라이",
        "P1_안전도": "CAUTION",
        "진행률": 0.65,
    }

    for col_name, value in pipeline_data.items():
        if col_name in PIPELINE_COLUMNS:
            col_def = PIPELINE_COLUMNS[col_name]
            properties[col_name] = build_property_value(col_def["type"], value)

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }

    response = requests.post(url, headers=get_headers(), json=payload)
    if response.status_code == 200:
        print("계란후라이 페이지 생성 완료")
        # 생성 후 전체 데이터 동기화
        page_data = response.json()
        page_id = page_data.get("id")
        if page_id:
            return sync_fried_egg_to_page(page_id)
        return True
    else:
        print(f"페이지 생성 실패: {response.status_code}")
        print(response.text)
        return False


def sync_fried_egg_to_page(page_id: str) -> bool:
    """계란후라이 전체 데이터를 페이지에 동기화"""
    # 파이프라인 테스트 결과 데이터
    data = {
        # Phase 1: 기획
        "P1_규칙로드": "완료",
        "P1_노션검토": "완료",
        "P1_음식선정": "계란후라이",
        "P1_컨펌": "승인",
        "P1_데이터수집": "완료",
        "P1_안전도": "CAUTION",
        "P1_팩트체크": "완료",
        "P1_규칙검수": "PASS",
        "P1_크리에이티브검수": "PASS",

        # Phase 2: 텍스트
        "P2_텍스트규칙로드": "완료",
        "P2_인스타캡션": "PASS",
        "P2_인스타캡션_R": "PASS",
        "P2_인스타캡션_C": "PASS",
        "P2_쓰레드캡션": "PASS",
        "P2_쓰레드캡션_R": "PASS",
        "P2_쓰레드캡션_C": "PASS",
        "P2_블로그본문": "PASS",
        "P2_블로그본문_R": "PASS",
        "P2_블로그본문_C": "PASS",

        # Phase 3: 이미지
        "P3_이미지규칙로드": "완료",
        "P3_표지제작": "PENDING",
        "P3_슬라이드제작": "PENDING",
        "P3_블로그이미지": "6/8",
        "P3_블로그이미지_1": "PENDING",
        "P3_블로그이미지_2": "PENDING",
        "P3_블로그이미지_3": "완료",
        "P3_블로그이미지_4": "완료",
        "P3_블로그이미지_5": "완료",
        "P3_블로그이미지_6": "완료",
        "P3_블로그이미지_7": "완료",
        "P3_블로그이미지_8": "완료",
        "P3_CTA제작": "PENDING",

        # Phase 4: 최종/게시
        "P4_최종규칙검수": "진행중",
        "P4_최종크리에이티브": "대기",
        "P4_Cloudinary": "대기",
        "P4_인스타게시": "대기",
        "P4_쓰레드게시": "대기",
        "P4_블로그게시": "대기",
        "P4_동기화": "대기",
        "P4_알림": "대기",

        # 메타
        "진행률": 0.65,
        "마지막업데이트": datetime.now(),
        "에러내용": "Phase 3 이미지 2개 미완료 (표지, 음식사진)",
    }

    # 속성 변환
    properties = {}
    for col_name, value in data.items():
        if col_name in PIPELINE_COLUMNS:
            col_def = PIPELINE_COLUMNS[col_name]
            prop_value = build_property_value(col_def["type"], value)
            if prop_value:
                properties[col_name] = prop_value

    if update_notion_page(page_id, properties):
        print(f"계란후라이 전체 동기화 완료")
        return True
    return False


def list_all_columns():
    """현재 DB의 모든 컬럼 출력"""
    schema = get_database_schema()
    if not schema:
        return

    props = schema.get("properties", {})
    print(f"\n현재 DB 컬럼 ({len(props)}개):")
    print("-" * 40)

    for name, prop in sorted(props.items()):
        prop_type = prop.get("type", "unknown")
        print(f"  {name}: {prop_type}")


def main():
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("NOTION_API_KEY 또는 NOTION_DATABASE_ID 미설정")
        return

    print("=" * 60)
    print("[WO-NOTION-001] 노션 DB 파이프라인 설정")
    print("=" * 60)

    # 1. 컬럼 추가
    if not setup_pipeline_columns():
        print("컬럼 추가 실패")
        return

    # 2. 계란후라이 데이터 동기화
    sync_fried_egg_data()

    # 3. 전체 컬럼 확인
    list_all_columns()

    print("\n" + "=" * 60)
    print("완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
