#!/usr/bin/env python3
"""
WO-040: 백업 시스템 전면 구축
1. 폴더 구조 정리
2. 노션 System Backup 페이지 생성
3. 노션 DB 컬럼 추가
4. 콘텐츠 노션 백업
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 폴더 구조 정리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup_folder_structure():
    """각 콘텐츠 폴더에 01_Insta&Thread/, 02_Blog/ 구조 생성"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📁 1단계: 폴더 구조 정리")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    created_insta = 0
    created_blog = 0
    total_folders = 0

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    import re
    for folder in CONTENTS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        # 콘텐츠 폴더 패턴 확인 (001_xxx)
        if not re.match(r'^\d{3}_', folder.name):
            continue

        total_folders += 1

        # 01_Insta&Thread/ 폴더 생성
        insta_dir = folder / "01_Insta&Thread"
        if not insta_dir.exists():
            insta_dir.mkdir(exist_ok=True)
            created_insta += 1

        # 02_Blog/ 폴더 생성
        blog_dir = folder / "02_Blog"
        if not blog_dir.exists():
            blog_dir.mkdir(exist_ok=True)
            created_blog += 1

    print(f"   전체 폴더: {total_folders}개")
    print(f"   ✅ 01_Insta&Thread/ 생성: {created_insta}개")
    print(f"   ✅ 02_Blog/ 생성: {created_blog}개")
    return total_folders


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 노션 System Backup 페이지 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_database_parent():
    """DB의 부모 페이지/워크스페이스 정보 가져오기"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        data = response.json()
        return data.get("parent", {})
    return None


def create_system_backup_page():
    """System Backup 페이지 생성"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📄 2단계: 노션 System Backup 페이지 생성")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 파일 목록 수집
    files_to_backup = []

    # scripts/
    scripts_dir = PROJECT_ROOT / "scripts"
    if scripts_dir.exists():
        for f in scripts_dir.glob("*.py"):
            files_to_backup.append(("scripts", f.name, f.read_text()[:1800]))

    # RULES.md, CLAUDE.md
    for md_file in ["RULES.md", "CLAUDE.md"]:
        md_path = PROJECT_ROOT / md_file
        if md_path.exists():
            files_to_backup.append(("root", md_file, md_path.read_text()[:1800]))

    # .claude/hooks/
    hooks_dir = PROJECT_ROOT / ".claude" / "hooks"
    if hooks_dir.exists():
        for f in hooks_dir.glob("*"):
            if f.is_file():
                files_to_backup.append(("hooks", f.name, f.read_text()[:1000] if f.suffix in ['.py', '.sh', '.md'] else "(binary)"))

    # .claude/commands/
    commands_dir = PROJECT_ROOT / ".claude" / "commands"
    if commands_dir.exists():
        for f in commands_dir.glob("*"):
            if f.is_file():
                files_to_backup.append(("commands", f.name, f.read_text()[:1000] if f.suffix in ['.py', '.sh', '.md'] else "(binary)"))

    # 페이지 내용 구성
    children = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "🔐 System Backup"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
    ]

    # 각 카테고리별 섹션
    current_category = None
    for category, filename, content in files_to_backup:
        if category != current_category:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": f"📁 {category}/"}}]
                }
            })
            current_category = category

        # 파일명
        children.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": filename}}]
            }
        })

        # 코드 블록
        if content != "(binary)":
            children.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": content[:1800]}}],
                    "language": "python" if filename.endswith(".py") else "markdown" if filename.endswith(".md") else "plain text"
                }
            })

    # DB 부모 정보로 같은 위치에 페이지 생성
    parent = get_database_parent()
    if not parent:
        print("   ⚠️ DB 부모 정보 조회 실패")
        return None

    # 페이지 생성
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": parent,
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": "🔐 System Backup"}}]
            }
        },
        "children": children[:100]  # 노션 API 제한
    }

    response = requests.post(url, headers=get_headers(), json=payload)
    if response.status_code == 200:
        page_url = response.json().get("url", "")
        print(f"   ✅ System Backup 페이지 생성 완료")
        print(f"   📍 URL: {page_url}")
        print(f"   📋 백업 파일: {len(files_to_backup)}개")
        return response.json().get("id")
    else:
        print(f"   ⚠️ 페이지 생성 실패: {response.status_code}")
        print(f"   {response.text[:200]}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 노션 DB 컬럼 추가
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def add_db_columns():
    """노션 DB에 백업 관련 컬럼 추가"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 3단계: 노션 DB 컬럼 추가")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"

    payload = {
        "properties": {
            "insta_images": {"number": {}},
            "blog_images": {"number": {}},
            "insta_caption": {"checkbox": {}},
            "blog_caption": {"checkbox": {}},
        }
    }

    response = requests.patch(url, headers=get_headers(), json=payload)
    if response.status_code == 200:
        print("   ✅ 4개 컬럼 추가/확인 완료")
        print("      - insta_images (Number)")
        print("      - blog_images (Number)")
        print("      - insta_caption (Checkbox)")
        print("      - blog_caption (Checkbox)")
        return True
    else:
        print(f"   ⚠️ 컬럼 추가 실패: {response.status_code}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 콘텐츠 노션 백업 (DB 업데이트)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def scan_and_update_notion():
    """폴더 스캔 후 노션 DB 업데이트"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📋 4단계: 콘텐츠 노션 백업")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 노션 페이지 가져오기
    pages = []
    has_more = True
    start_cursor = None

    while has_more:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        body = {"sorts": [{"property": "번호", "direction": "ascending"}]}
        if start_cursor:
            body["start_cursor"] = start_cursor

        response = requests.post(url, headers=get_headers(), json=body)
        if response.status_code != 200:
            break

        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    print(f"   노션 페이지: {len(pages)}개")

    # 각 페이지 업데이트
    updated = 0
    stats = {"insta_images": 0, "blog_images": 0, "insta_caption": 0, "blog_caption": 0}

    import re
    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")
        if num is None:
            continue

        page_id = page["id"]
        num_str = f"{num:03d}"

        # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
        folder = None
        for item in CONTENTS_DIR.iterdir():
            if item.is_dir() and item.name.startswith(num_str):
                folder = item
                break

        # 데이터 수집
        data = {
            "insta_images": 0,
            "blog_images": 0,
            "insta_caption": False,
            "blog_caption": False,
        }

        if folder:
            # 01_Insta&Thread/
            insta_dir = folder / "01_Insta&Thread"
            if insta_dir.exists():
                images = [f for f in insta_dir.iterdir()
                          if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
                data["insta_images"] = len(images)
                data["insta_caption"] = (insta_dir / "caption.txt").exists()

            # 02_Blog/
            blog_dir = folder / "02_Blog"
            if blog_dir.exists():
                images = [f for f in blog_dir.iterdir()
                          if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
                data["blog_images"] = len(images)
                data["blog_caption"] = (blog_dir / "caption.txt").exists()

        # 통계
        stats["insta_images"] += data["insta_images"]
        stats["blog_images"] += data["blog_images"]
        if data["insta_caption"]:
            stats["insta_caption"] += 1
        if data["blog_caption"]:
            stats["blog_caption"] += 1

        # 업데이트
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {
            "properties": {
                "insta_images": {"number": data["insta_images"]},
                "blog_images": {"number": data["blog_images"]},
                "insta_caption": {"checkbox": data["insta_caption"]},
                "blog_caption": {"checkbox": data["blog_caption"]},
            }
        }

        resp = requests.patch(update_url, headers=get_headers(), json=payload)
        if resp.status_code == 200:
            updated += 1
            if updated % 20 == 0:
                print(f"   진행: {updated}/{len(pages)}")

    print(f"\n   ✅ 업데이트 완료: {updated}/{len(pages)}개")
    print(f"   📸 insta_images 총합: {stats['insta_images']}개")
    print(f"   📝 blog_images 총합: {stats['blog_images']}개")
    print(f"   ✅ insta_caption 있음: {stats['insta_caption']}개")
    print(f"   ✅ blog_caption 있음: {stats['blog_caption']}개")

    return updated


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("━" * 60)
    print("🔐 WO-040: 백업 시스템 전면 구축")
    print("━" * 60)

    # 1. 폴더 구조 정리
    total_folders = setup_folder_structure()

    # 2. System Backup 페이지 생성
    backup_page_id = create_system_backup_page()

    # 3. DB 컬럼 추가
    add_db_columns()

    # 4. 콘텐츠 노션 백업
    updated = scan_and_update_notion()

    # 최종 보고
    print("\n" + "━" * 60)
    print("📊 WO-040 완료 보고")
    print("━" * 60)
    print(f"✅ 1. 폴더 구조 정리: {total_folders}개 폴더")
    print(f"✅ 2. System Backup 페이지: {'생성 완료' if backup_page_id else '실패'}")
    print(f"✅ 3. DB 컬럼 추가: 4개")
    print(f"✅ 4. 노션 백업: {updated}개 콘텐츠")
    print("━" * 60)


if __name__ == "__main__":
    main()
