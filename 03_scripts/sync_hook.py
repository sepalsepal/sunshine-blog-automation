#!/usr/bin/env python3
"""
sync_hook.py - 파이프라인 v2.7 노션 동기화 훅
[WO-NOTION-001] 업데이트

사용법:
    from scripts.sync_hook import on_phase_complete, update_pipeline_status

    # 페이즈 완료 시
    on_phase_complete(163, "P1", {"규칙로드": "완료", "안전도": "CAUTION"})

    # 개별 상태 업데이트
    update_pipeline_status(163, "P3_블로그이미지_3", "완료")
"""

import os
import sys
import re
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# === 설정 ===
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
LOG_DIR = PROJECT_ROOT / "logs" / "sync"

# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]

# 폴더 → 노션 상태 매핑
FOLDER_STATUS_MAP = {
    "1_cover_only": "표지완료",
    "2_body_ready": "본문완료",
    "3_approved": "승인완료",
    "4_posted": "게시완료",
}

# === 파이프라인 v2.7 컬럼 정의 ===
PIPELINE_PHASES = {
    "P1": {
        "name": "기획",
        "columns": [
            "P1_규칙로드", "P1_노션검토", "P1_음식선정", "P1_컨펌",
            "P1_데이터수집", "P1_안전도", "P1_팩트체크",
            "P1_규칙검수", "P1_크리에이티브검수"
        ]
    },
    "P2": {
        "name": "텍스트",
        "columns": [
            "P2_텍스트규칙로드",
            "P2_인스타캡션", "P2_인스타캡션_R", "P2_인스타캡션_C",
            "P2_쓰레드캡션", "P2_쓰레드캡션_R", "P2_쓰레드캡션_C",
            "P2_블로그본문", "P2_블로그본문_R", "P2_블로그본문_C"
        ]
    },
    "P3": {
        "name": "이미지",
        "columns": [
            "P3_이미지규칙로드",
            "P3_표지제작", "P3_표지_R", "P3_표지_C",
            "P3_슬라이드제작", "P3_슬라이드_R", "P3_슬라이드_C",
            "P3_블로그이미지",
            "P3_블로그이미지_1", "P3_블로그이미지_2", "P3_블로그이미지_3",
            "P3_블로그이미지_4", "P3_블로그이미지_5", "P3_블로그이미지_6",
            "P3_블로그이미지_7", "P3_블로그이미지_8",
            "P3_CTA제작", "P3_CTA_R", "P3_CTA_C"
        ]
    },
    "P4": {
        "name": "최종/게시",
        "columns": [
            "P4_최종규칙검수", "P4_최종크리에이티브",
            "P4_Cloudinary", "P4_인스타게시", "P4_쓰레드게시",
            "P4_블로그게시", "P4_동기화", "P4_알림"
        ]
    }
}

# 컬럼 타입 정의
COLUMN_TYPES = {
    # Phase 1
    "P1_규칙로드": "select", "P1_노션검토": "select", "P1_음식선정": "rich_text",
    "P1_컨펌": "select", "P1_데이터수집": "select", "P1_안전도": "select",
    "P1_팩트체크": "select", "P1_규칙검수": "select", "P1_크리에이티브검수": "select",
    # Phase 2
    "P2_텍스트규칙로드": "select",
    "P2_인스타캡션": "select", "P2_인스타캡션_R": "select", "P2_인스타캡션_C": "select",
    "P2_쓰레드캡션": "select", "P2_쓰레드캡션_R": "select", "P2_쓰레드캡션_C": "select",
    "P2_블로그본문": "select", "P2_블로그본문_R": "select", "P2_블로그본문_C": "select",
    # Phase 3
    "P3_이미지규칙로드": "select",
    "P3_표지제작": "select", "P3_표지_R": "select", "P3_표지_C": "select",
    "P3_슬라이드제작": "select", "P3_슬라이드_R": "select", "P3_슬라이드_C": "select",
    "P3_블로그이미지": "rich_text",
    "P3_블로그이미지_1": "select", "P3_블로그이미지_2": "select",
    "P3_블로그이미지_3": "select", "P3_블로그이미지_4": "select",
    "P3_블로그이미지_5": "select", "P3_블로그이미지_6": "select",
    "P3_블로그이미지_7": "select", "P3_블로그이미지_8": "select",
    "P3_CTA제작": "select", "P3_CTA_R": "select", "P3_CTA_C": "select",
    # Phase 4
    "P4_최종규칙검수": "select", "P4_최종크리에이티브": "select",
    "P4_Cloudinary": "select", "P4_인스타게시": "select",
    "P4_쓰레드게시": "select", "P4_블로그게시": "select",
    "P4_동기화": "select", "P4_알림": "select",
    # Meta
    "진행률": "number", "마지막업데이트": "date", "에러내용": "rich_text",
}


def get_headers() -> dict:
    """Notion API 헤더"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def log_sync(message: str, level: str = "INFO"):
    """동기화 로그 기록"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{today}_sync.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {level} | {message}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)

    # 콘솔 출력
    if level == "ERROR":
        print(f"  {message}")
    elif level == "SUCCESS":
        print(f"  {message}")
    else:
        print(f"  {message}")


def find_content_by_name(content_name: str) -> Optional[tuple]:
    """콘텐츠 이름으로 폴더 및 번호 찾기"""
    # food_data.json에서 매핑 확인
    food_data_path = PROJECT_ROOT / "config" / "food_data.json"
    if food_data_path.exists():
        with open(food_data_path, "r", encoding="utf-8") as f:
            food_data = json.load(f)

        for food_id, data in food_data.items():
            if data.get("name_ko") == content_name or data.get("name_en") == content_name:
                content_num = int(food_id)
                folder = find_content_folder(content_num)
                if folder:
                    return content_num, folder

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue

        if content_name in item.name or content_name.lower() in item.name.lower():
            match = re.match(r'^(\d{3})_', item.name)
            if match:
                return int(match.group(1)), item

    return None


def find_content_folder(content_num: int) -> Optional[Path]:
    """번호로 콘텐츠 폴더 찾기 - contents/ 직접 스캔"""
    num_str = f"{content_num:03d}"

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item

    return None


def find_notion_page(content_num: int) -> Optional[dict]:
    """노션에서 해당 번호의 페이지 찾기"""
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        log_sync("NOTION_API_KEY 또는 NOTION_DATABASE_ID 미설정", "ERROR")
        return None

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    body = {
        "filter": {
            "property": "번호",
            "number": {"equals": content_num}
        }
    }

    try:
        response = requests.post(url, headers=get_headers(), json=body, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0]
    except requests.exceptions.RequestException as e:
        log_sync(f"노션 API 오류: {e}", "ERROR")

    return None


def build_property_value(col_name: str, value: Any) -> dict:
    """값을 Notion property 형식으로 변환"""
    col_type = COLUMN_TYPES.get(col_name, "rich_text")

    if col_type == "select":
        if value is None:
            return {"select": None}
        return {"select": {"name": str(value)}}
    elif col_type == "rich_text":
        if value is None:
            return {"rich_text": []}
        return {"rich_text": [{"text": {"content": str(value)}}]}
    elif col_type == "number":
        return {"number": float(value) if value is not None else None}
    elif col_type == "date":
        if isinstance(value, datetime):
            return {"date": {"start": value.isoformat()}}
        elif value:
            return {"date": {"start": str(value)}}
        return {"date": None}
    elif col_type == "checkbox":
        return {"checkbox": bool(value)}
    elif col_type == "url":
        return {"url": str(value) if value else None}

    return {"rich_text": [{"text": {"content": str(value)}}] if value else []}


def update_notion_page(page_id: str, properties: dict) -> bool:
    """노션 페이지 업데이트"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": properties}

    try:
        response = requests.patch(url, headers=get_headers(), json=payload, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        log_sync(f"노션 업데이트 오류: {e}", "ERROR")
        return False


def update_pipeline_status(content_num: int, column: str, value: Any) -> bool:
    """
    단일 파이프라인 컬럼 업데이트

    Args:
        content_num: 콘텐츠 번호 (예: 163)
        column: 컬럼명 (예: "P3_블로그이미지_3")
        value: 값 (예: "완료")

    Returns:
        성공 여부
    """
    log_sync(f"UPDATE | #{content_num} | {column} = {value}")

    page = find_notion_page(content_num)
    if not page:
        log_sync(f"#{content_num} 페이지를 찾을 수 없음", "ERROR")
        return False

    properties = {
        column: build_property_value(column, value),
        "마지막업데이트": {"date": {"start": datetime.now().isoformat()}}
    }

    if update_notion_page(page["id"], properties):
        log_sync(f"#{content_num} | {column} 업데이트 완료", "SUCCESS")
        return True
    else:
        log_sync(f"#{content_num} | {column} 업데이트 실패", "ERROR")
        return False


def on_phase_complete(content_num: int, phase: str, results: Dict[str, Any]) -> bool:
    """
    페이즈 완료 시 호출되는 훅

    Args:
        content_num: 콘텐츠 번호 (예: 163)
        phase: 페이즈 (P1, P2, P3, P4)
        results: 결과 딕셔너리 (컬럼 접미사 → 값)
            예: {"규칙로드": "완료", "안전도": "CAUTION"}

    Returns:
        성공 여부
    """
    log_sync(f"PHASE 완료 | #{content_num} | {phase}")

    page = find_notion_page(content_num)
    if not page:
        log_sync(f"#{content_num} 페이지를 찾을 수 없음", "ERROR")
        return False

    # 속성 구성
    properties = {}

    for key, value in results.items():
        # P1_규칙로드 형식이면 그대로, 아니면 접두사 추가
        if key.startswith(phase + "_"):
            col_name = key
        else:
            col_name = f"{phase}_{key}"

        if col_name in COLUMN_TYPES:
            properties[col_name] = build_property_value(col_name, value)

    # 마지막 업데이트
    properties["마지막업데이트"] = {"date": {"start": datetime.now().isoformat()}}

    if update_notion_page(page["id"], properties):
        log_sync(f"#{content_num} | {phase} 동기화 완료 ({len(results)}개 컬럼)", "SUCCESS")
        return True
    else:
        log_sync(f"#{content_num} | {phase} 동기화 실패", "ERROR")
        return False


def calculate_progress(content_num: int) -> float:
    """
    콘텐츠 진행률 계산

    Returns:
        진행률 (0.0 ~ 1.0)
    """
    folder = find_content_folder(content_num)
    if not folder:
        return 0.0

    progress = 0.0
    total_weight = 100

    # Phase 1: 기획 (20%)
    # food_data.json에 데이터 있으면 완료
    food_data_path = PROJECT_ROOT / "config" / "food_data.json"
    if food_data_path.exists():
        with open(food_data_path, "r", encoding="utf-8") as f:
            food_data = json.load(f)
        if str(content_num) in food_data:
            progress += 20

    # Phase 2: 텍스트 (20%)
    # 2026-02-13: 플랫 구조 - captions/ 제거, 각 플랫폼 폴더 내에서 확인
    insta_thread_dir = folder / "01_Insta&Thread"
    blog_text_dir = folder / "02_Blog"
    caption_files_found = 0
    if insta_thread_dir.exists():
        if (insta_thread_dir / "instagram_caption.txt").exists():
            caption_files_found += 1
        if (insta_thread_dir / "threads_caption.txt").exists():
            caption_files_found += 1
    if blog_text_dir.exists():
        if (blog_text_dir / "blog_caption.txt").exists():
            caption_files_found += 1
    progress += (caption_files_found / 3) * 20

    # Legacy captions_dir check (deprecated)
    captions_dir = folder / "captions"  # 2026-02-13: deprecated
    if captions_dir.exists():
        caption_files = ["instagram_caption.txt", "threads_caption.txt", "blog_caption.txt"]
        existing = sum(1 for f in caption_files if (captions_dir / f).exists())
        progress += (existing / len(caption_files)) * 20

    # Phase 3: 이미지 (40%)
    blog_dir = folder / "02_Blog"
    if blog_dir.exists():
        images = [f for f in blog_dir.iterdir() if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]]
        progress += (len(images) / 8) * 30  # 8장 기준

    insta_dir = folder / "01_Insta&Thread"
    if insta_dir.exists():
        slides = [f for f in insta_dir.iterdir() if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]]
        progress += min(len(slides) / 10, 1.0) * 10  # 10장 기준

    # Phase 4: 게시 (20%)
    folder_status = str(folder.parent.name)
    if "4_posted" in folder_status:
        progress += 20
    elif "3_approved" in folder_status:
        progress += 10

    return min(progress / total_weight, 1.0)


def sync_progress(content_num: int) -> bool:
    """진행률 동기화"""
    progress = calculate_progress(content_num)

    page = find_notion_page(content_num)
    if not page:
        return False

    properties = {
        "진행률": {"number": progress},
        "마지막업데이트": {"date": {"start": datetime.now().isoformat()}}
    }

    return update_notion_page(page["id"], properties)


def scan_content_folder(folder_path: Path) -> dict:
    """콘텐츠 폴더 스캔하여 이미지/캡션 정보 추출"""
    result = {
        "insta_images": 0,
        "blog_images": 0,
        "insta_caption": False,
        "blog_caption": False,
        "thread_caption": False,
    }

    if not folder_path or not folder_path.exists():
        return result

    # insta/
    insta_dir = folder_path / "01_Insta&Thread"
    if insta_dir.exists():
        images = [f for f in insta_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["insta_images"] = len(images)
        result["insta_caption"] = (insta_dir / "caption.txt").exists()

    # blog/
    blog_dir = folder_path / "02_Blog"
    if blog_dir.exists():
        images = [f for f in blog_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["blog_images"] = len(images)
        result["blog_caption"] = (blog_dir / "caption.txt").exists()

    # 2026-02-13: 플랫 구조 - captions는 각 플랫폼 폴더 내에서 확인
    # captions/ 폴더 제거 - 각 플랫폼 폴더에서 캡션 확인
    if insta_dir.exists():
        result["insta_caption"] = (insta_dir / "instagram_caption.txt").exists()
        result["thread_caption"] = (insta_dir / "threads_caption.txt").exists()
    if blog_dir.exists():
        result["blog_caption"] = (blog_dir / "blog_caption.txt").exists()

    # thread/
    thread_dir = folder_path / "thread"
    if thread_dir.exists():
        result["thread_caption"] = result["thread_caption"] or (thread_dir / "caption.txt").exists()

    return result


def sync_folder_to_notion(content_num: int) -> bool:
    """
    폴더 상태 기반 전체 동기화

    Args:
        content_num: 콘텐츠 번호

    Returns:
        성공 여부
    """
    log_sync(f"FOLDER SYNC | #{content_num}")

    folder = find_content_folder(content_num)
    if not folder:
        log_sync(f"#{content_num} 폴더를 찾을 수 없음", "ERROR")
        return False

    page = find_notion_page(content_num)
    if not page:
        log_sync(f"#{content_num} 노션 페이지를 찾을 수 없음", "ERROR")
        return False

    # 폴더 스캔
    scan = scan_content_folder(folder)

    # 블로그 이미지 개별 확인
    blog_dir = folder / "02_Blog"
    blog_images = {}
    if blog_dir.exists():
        for i in range(1, 9):
            # 파일명 패턴: 1_표지.png, 2_음식사진.png, 3_영양정보.png 등
            found = False
            for f in blog_dir.iterdir():
                if f.name.startswith(f"{i}_") or f.name.startswith(f"{i}번") or f"_{i}." in f.name:
                    found = True
                    break
            blog_images[f"P3_블로그이미지_{i}"] = "완료" if found else "PENDING"

    # 진행률 계산
    progress = calculate_progress(content_num)

    # 속성 구성
    properties = {
        # 기존 호환
        "insta_images": {"number": scan["insta_images"]},
        "blog_images": {"number": scan["blog_images"]},
        "insta_caption": {"checkbox": scan["insta_caption"]},
        "blog_caption": {"checkbox": scan["blog_caption"]},
        "Thread_caption": {"checkbox": scan["thread_caption"]},

        # Phase 2 캡션
        "P2_인스타캡션": {"select": {"name": "PASS" if scan["insta_caption"] else "대기"}},
        "P2_쓰레드캡션": {"select": {"name": "PASS" if scan["thread_caption"] else "대기"}},
        "P2_블로그본문": {"select": {"name": "PASS" if scan["blog_caption"] else "대기"}},

        # Phase 3 이미지
        "P3_블로그이미지": {"rich_text": [{"text": {"content": f"{scan['blog_images']}/8"}}]},

        # 메타
        "진행률": {"number": progress},
        "마지막업데이트": {"date": {"start": datetime.now().isoformat()}},
    }

    # 블로그 이미지 개별 상태
    for col, val in blog_images.items():
        properties[col] = {"select": {"name": val}}

    if update_notion_page(page["id"], properties):
        log_sync(f"#{content_num} 폴더 동기화 완료 (진행률: {progress*100:.0f}%)", "SUCCESS")
        return True
    else:
        log_sync(f"#{content_num} 폴더 동기화 실패", "ERROR")
        return False


# === 기존 호환 함수 (deprecated) ===

def on_node_complete(node_name: str, content_name: str, result: Dict[str, Any]) -> bool:
    """
    노드 완료 시 자동 호출되는 훅 (기존 호환)

    Args:
        node_name: 노드명
        content_name: 음식명
        result: 노드 결과

    Returns:
        동기화 성공 여부
    """
    log_sync(f"NODE 완료 | {node_name} | {content_name}")

    # 콘텐츠 번호 찾기
    content_result = find_content_by_name(content_name)
    if not content_result:
        log_sync(f"{content_name}: 콘텐츠를 찾을 수 없음", "ERROR")
        return False

    content_num, folder_path = content_result

    # 노드 → 페이즈 매핑
    node_phase_map = {
        "입력/기획": "P1",
        "팩트체크": "P1",
        "텍스트작성": "P2",
        "이미지제작": "P3",
        "검수": "P4",
        "게시": "P4",
    }

    phase = node_phase_map.get(node_name, "P1")

    # 폴더 기반 동기화
    return sync_folder_to_notion(content_num)


def sync_to_notion(content_name: str, updates: Dict[str, Any]) -> bool:
    """기존 호환 함수"""
    content_result = find_content_by_name(content_name)
    if not content_result:
        return False

    content_num, _ = content_result
    return sync_folder_to_notion(content_num)


# === 전체 동기화 ===

def get_all_content_folders() -> list:
    """모든 콘텐츠 폴더 스캔 - contents/ 직접 스캔"""
    import re
    folders = []

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_', item.name)
        if match:
            folders.append({
                "num": int(match.group(1)),
                "name": item.name,
                "path": item,
                "status_dir": "contents"  # flat structure
            })

    return sorted(folders, key=lambda x: x["num"])


def create_notion_page(folder: dict) -> Optional[str]:
    """
    신규 노션 페이지 생성

    Args:
        folder: {"num": int, "name": str, "path": Path, "status_dir": str}

    Returns:
        생성된 페이지 ID 또는 None
    """
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        log_sync("NOTION_API_KEY 또는 NOTION_DATABASE_ID 미설정", "ERROR")
        return None

    # 폴더명 파싱
    parts = folder["name"].split("_")
    food_en = "_".join(parts[1:]) if len(parts) > 1 else folder["name"]

    # food_data.json에서 한글명 찾기
    food_ko = food_en  # 기본값
    safety_level = "CAUTION"  # 기본값

    food_data_path = PROJECT_ROOT / "config" / "food_data.json"
    if food_data_path.exists():
        with open(food_data_path, "r", encoding="utf-8") as f:
            food_data = json.load(f)

        # 영문명으로 매핑 시도
        for food_id, data in food_data.items():
            if data.get("english_name") == food_en:
                food_ko = data.get("name", food_en)
                safety_level = data.get("safety", "CAUTION")
                break

    # 상태 매핑
    status = FOLDER_STATUS_MAP.get(folder["status_dir"], "대기")

    # 페이지 생성
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "이름": {"title": [{"text": {"content": food_ko}}]},
            "한글명": {"rich_text": [{"text": {"content": food_ko}}]},
            "번호": {"number": folder["num"]},
            "폴더명": {"rich_text": [{"text": {"content": folder["name"]}}]},
            "안전도": {"select": {"name": safety_level}},
            "P1_안전도": {"select": {"name": safety_level}},
            "진행률": {"number": 0.0},
            "마지막업데이트": {"date": {"start": datetime.now().isoformat()}}
        }
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            page_id = response.json().get("id")
            log_sync(f"#{folder['num']} {food_ko} 페이지 생성 완료", "SUCCESS")
            return page_id
        else:
            error_msg = response.json().get("message", "Unknown error")
            log_sync(f"#{folder['num']} 페이지 생성 실패: {error_msg}", "ERROR")
            return None
    except requests.exceptions.RequestException as e:
        log_sync(f"#{folder['num']} API 오류: {e}", "ERROR")
        return None


def sync_all_to_notion() -> dict:
    """전체 폴더 → 노션 동기화"""
    print("=" * 50)
    print("노션 전체 동기화")
    print("=" * 50)

    folders = get_all_content_folders()
    print(f"로컬 폴더: {len(folders)}개")

    # 노션 페이지 수 확인
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(url, headers=get_headers(), json={}, timeout=30)
    notion_count = 0
    if response.status_code == 200:
        data = response.json()
        notion_count = len(data.get("results", []))
        # 페이지네이션 처리
        while data.get("has_more"):
            response = requests.post(url, headers=get_headers(),
                                    json={"start_cursor": data["next_cursor"]}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                notion_count += len(data.get("results", []))
            else:
                break

    print(f"노션 등록: {notion_count}개")
    print(f"미등록: {len(folders) - notion_count}개")
    print()

    # 동기화 실행
    synced = 0
    updated = 0
    errors = []

    for folder in folders:
        try:
            page = find_notion_page(folder["num"])
            if page:
                # 기존 페이지 업데이트
                if sync_folder_to_notion(folder["num"]):
                    updated += 1
            else:
                # 신규 페이지 생성
                page_id = create_notion_page(folder)
                if page_id:
                    synced += 1
                    print(f"  ✅ 신규: #{folder['num']} {folder['name']}")
                else:
                    errors.append({"num": folder["num"], "error": "생성 실패"})
                    print(f"  ❌ 실패: #{folder['num']} {folder['name']}")
        except Exception as e:
            errors.append({"num": folder["num"], "error": str(e)})
            print(f"  ❌ 에러: #{folder['num']} - {e}")

    result = {
        "local_folders": len(folders),
        "notion_count": notion_count,
        "synced": synced,
        "updated": updated,
        "errors": len(errors)
    }

    print()
    print("=" * 50)
    print(f"✅ 신규 등록: {synced}개")
    print(f"🔄 업데이트: {updated}개")
    print(f"❌ 에러: {len(errors)}개")
    print(f"📊 노션 총: {notion_count} → {notion_count + synced}개")
    print("=" * 50)

    return result


def show_status():
    """동기화 상태 조회"""
    print("=" * 50)
    print("동기화 상태")
    print("=" * 50)

    folders = get_all_content_folders()

    # 상태별 집계
    status_count = {}
    for folder in folders:
        status = folder["status_dir"]
        status_count[status] = status_count.get(status, 0) + 1

    print(f"\n로컬 폴더 총: {len(folders)}개")
    print("-" * 30)
    for status, count in sorted(status_count.items()):
        print(f"  {status}: {count}개")

    # 노션 상태
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(url, headers=get_headers(), json={}, timeout=30)
    if response.status_code == 200:
        data = response.json()
        notion_count = len(data.get("results", []))
        while data.get("has_more"):
            response = requests.post(url, headers=get_headers(),
                                    json={"start_cursor": data["next_cursor"]}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                notion_count += len(data.get("results", []))
            else:
                break
        print(f"\n노션 등록: {notion_count}개")


# === CLI ===
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("sync_hook.py - 파이프라인 v2.8 노션 동기화")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\n사용법:")
        print("  python sync_hook.py --sync-all              전체 동기화")
        print("  python sync_hook.py --sync <번호>           단일 동기화")
        print("  python sync_hook.py --status                상태 확인")
        print("  python sync_hook.py --update-progress <번호> 진행률 업데이트")
        print("  python sync_hook.py <번호> <컬럼> <값>       컬럼 업데이트")
        print("\n예시:")
        print("  python sync_hook.py --sync-all")
        print("  python sync_hook.py --sync 163")
        print("  python sync_hook.py --status")
        print("  python sync_hook.py 163 P3_블로그이미지_3 완료")
        sys.exit(0)

    arg = sys.argv[1]

    if arg == "--sync-all":
        sync_all_to_notion()
    elif arg == "--status":
        show_status()
    elif arg == "--sync" and len(sys.argv) >= 3:
        content_num = int(sys.argv[2])
        sync_folder_to_notion(content_num)
    elif arg == "--update-progress" and len(sys.argv) >= 3:
        content_num = int(sys.argv[2])
        sync_progress(content_num)
    elif arg.isdigit():
        content_num = int(arg)
        if len(sys.argv) == 2:
            sync_folder_to_notion(content_num)
        elif len(sys.argv) >= 4:
            column = sys.argv[2]
            value = sys.argv[3]
            update_pipeline_status(content_num, column, value)
    else:
        print(f"알 수 없는 명령: {arg}")
