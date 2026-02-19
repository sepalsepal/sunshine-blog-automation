#!/usr/bin/env python3
"""
☁️ Cloudinary 자동 업로드 파이프라인

기능:
- 2_body_ready/ 스캔
- 4장 이미지 완성된 폴더 감지
- Cloudinary 업로드
- metadata.json에 URL 저장
- 텔레그램 알림

사용법:
    python3 scripts/cloudinary_uploader.py           # 실행
    python3 scripts/cloudinary_uploader.py --dry-run # 테스트 (업로드 없음)

크론 등록 (하루 2번):
    0 12 * * * cd /path/to/project_sunshine && python3 scripts/cloudinary_uploader.py
    0 18 * * * cd /path/to/project_sunshine && python3 scripts/cloudinary_uploader.py
"""

# ═══════════════════════════════════════════════════════════════
# 🔴 WO-FREEZE-001 동결 — Cloudinary 업로드 차단
# ═══════════════════════════════════════════════════════════════
import os
import sys

CLOUDINARY_FROZEN = True

if CLOUDINARY_FROZEN and os.environ.get("CLOUDINARY_UNFROZEN") != "true":
    print("🔴 FROZEN: WO-FREEZE-001 동결 중. Cloudinary 업로드 차단됨.")
    print("   사유: 이력 오염 방지")
    print("   해제: CLOUDINARY_UNFROZEN=true 환경변수 설정")
    sys.exit(1)
# ═══════════════════════════════════════════════════════════════

import os
import json
from datetime import datetime
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Cloudinary 임포트
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    print("⚠️ cloudinary 미설치. pip install cloudinary 실행 필요")

# ==========================================
# 설정
# ==========================================

# 2026-02-13: 플랫 구조 - BODY_READY_DIR 제거
CONTENTS_DIR = ROOT / "01_contents"
# BODY_READY_DIR = CONTENTS_DIR / "2_body_ready"
CLOUDINARY_FOLDER = "sunshinedogfood"

# Cloudinary 설정
if CLOUDINARY_AVAILABLE:
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "ddzbnrfei"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )

# 텔레그램 설정
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5360443525")


# ==========================================
# 핵심 함수
# ==========================================

def get_ready_folders():
    """
    4장 이미지 완성된 폴더 찾기
    조건: {food_id}_00.png ~ {food_id}_03.png 존재
    """
    ready_folders = []

    if not BODY_READY_DIR.exists():
        print(f"⚠️ 폴더 없음: {BODY_READY_DIR}")
        return ready_folders

    for folder in BODY_READY_DIR.iterdir():
        if not folder.is_dir():
            continue

        # metadata.json 확인
        meta_path = folder / "metadata.json"
        if not meta_path.exists():
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ JSON 파싱 오류: {meta_path}")
            continue

        # 이미 업로드됨 → 스킵
        if meta.get("cloudinary_uploaded"):
            continue

        # food_id 추출
        food_id = meta.get("food_id", "unknown")

        if food_id == "unknown" or food_id == "미지정":
            # 폴더명에서 추출 시도
            folder_parts = folder.name.split("_")
            if len(folder_parts) >= 2:
                food_id = folder_parts[1]

        # 4장 이미지 체크
        required_images = [
            f"{food_id}_00.png",
            f"{food_id}_01.png",
            f"{food_id}_02.png",
            f"{food_id}_03.png"
        ]

        all_exist = all((folder / img).exists() for img in required_images)

        if all_exist:
            ready_folders.append({
                "path": folder,
                "food_id": food_id,
                "images": required_images,
                "metadata": meta
            })

    return ready_folders


def upload_to_cloudinary(folder_info):
    """
    단일 폴더 Cloudinary 업로드
    """
    if not CLOUDINARY_AVAILABLE:
        print("  ❌ cloudinary 라이브러리 미설치")
        return None

    folder_path = folder_info["path"]
    food_id = folder_info["food_id"]
    images = folder_info["images"]

    uploaded_urls = []

    for img_name in images:
        img_path = folder_path / img_name

        # public_id 설정 (폴더/파일명)
        public_id = f"{CLOUDINARY_FOLDER}/{food_id}/{img_name.replace('.png', '')}"

        try:
            result = cloudinary.uploader.upload(
                str(img_path),
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )

            uploaded_urls.append({
                "file": img_name,
                "url": result["secure_url"],
                "public_id": result["public_id"]
            })

            print(f"  ✅ {img_name} 업로드 완료")

        except Exception as e:
            print(f"  ❌ {img_name} 업로드 실패: {e}")
            return None

    return uploaded_urls


def update_metadata(folder_info, uploaded_urls):
    """
    metadata.json에 Cloudinary URL 저장
    """
    folder_path = folder_info["path"]
    meta_path = folder_path / "metadata.json"

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Cloudinary 정보 추가
    meta["cloudinary_uploaded"] = True
    meta["cloudinary_uploaded_at"] = datetime.now().isoformat()
    meta["cloudinary_urls"] = uploaded_urls

    # 게시용 URL 리스트 (순서대로)
    meta["image_urls"] = [u["url"] for u in uploaded_urls]

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"  ✅ metadata.json 업데이트 완료")


def send_telegram_report(results):
    """
    텔레그램 알림
    """
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN 미설정 - 알림 스킵")
        return

    if not results:
        return

    import requests

    message = f"""☁️ Cloudinary 업로드 완료

처리: {len(results)}개
시간: {datetime.now().strftime("%Y-%m-%d %H:%M")}

업로드된 콘텐츠:
"""

    for r in results:
        message += f"- {r['food_id']} (4장)\n"

    message += "\n👉 게시 가능 상태입니다"

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }, timeout=10)

        if response.status_code == 200:
            print("✅ 텔레그램 알림 전송 완료")
        else:
            print(f"⚠️ 텔레그램 응답 오류: {response.status_code}")
    except Exception as e:
        print(f"⚠️ 텔레그램 알림 실패: {e}")


def run_pipeline(dry_run=False):
    """
    메인 실행
    """
    print("=" * 50)
    print("☁️ Cloudinary 자동 업로드 파이프라인")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Cloudinary 설정 확인
    if not dry_run and CLOUDINARY_AVAILABLE:
        api_key = os.getenv("CLOUDINARY_API_KEY")
        if not api_key:
            print("\n❌ CLOUDINARY_API_KEY 미설정")
            print("   .env 파일에 Cloudinary 인증 정보를 추가하세요.")
            return

    # 1. 준비된 폴더 찾기
    ready_folders = get_ready_folders()

    if not ready_folders:
        print("\n📭 업로드할 콘텐츠가 없습니다.")
        return

    print(f"\n📦 발견된 콘텐츠: {len(ready_folders)}개")
    for folder_info in ready_folders:
        print(f"  - {folder_info['food_id']} ({folder_info['path'].name})")

    results = []

    for folder_info in ready_folders:
        food_id = folder_info["food_id"]
        print(f"\n🔄 처리 중: {food_id}")

        if dry_run:
            print("  [DRY RUN] 업로드 스킵")
            results.append({"food_id": food_id, "urls": []})
            continue

        # 2. Cloudinary 업로드
        uploaded_urls = upload_to_cloudinary(folder_info)

        if not uploaded_urls:
            print(f"  ❌ {food_id} 업로드 실패 - 스킵")
            continue

        # 3. metadata 업데이트
        update_metadata(folder_info, uploaded_urls)

        results.append({
            "food_id": food_id,
            "urls": uploaded_urls
        })

    # 4. 텔레그램 알림
    if results and not dry_run:
        send_telegram_report(results)

    print("\n" + "=" * 50)
    print(f"✅ 완료: {len(results)}개 {'확인' if dry_run else '업로드'}")
    print("=" * 50)

    if dry_run:
        print("\n⚠️ DRY-RUN 모드: 실제 업로드 없음")


# ==========================================
# 실행부
# ==========================================

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_pipeline(dry_run=dry_run)
