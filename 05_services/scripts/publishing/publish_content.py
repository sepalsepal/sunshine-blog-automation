#!/usr/bin/env python3
"""
범용 Instagram + Threads 게시 스크립트
- 계정: @sunshinedogfood
- 형식: 캐러셀 4장 (v6)
- 자동 재시도: 최대 3회 (5분, 15분, 30분 간격)
- Threads 자동 연동: 캡션 변환 후 동시 게시
"""

import asyncio
import os
import sys
import time
import random
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent  # services/scripts/publishing → services/scripts → services → project_sunshine
sys.path.insert(0, str(ROOT))

# v3 폴더 구조: contents/1_cover_only, 2_body_ready, 3_approved, 4_posted
CONTENTS_DIR = ROOT / "contents"
STATUS_FOLDERS = ["3_approved", "2_body_ready", "1_cover_only"]  # 게시용은 3_approved 우선
POSTED_DIR = CONTENTS_DIR / "4_posted"  # v3: posted → contents/4_posted


def move_to_posted(folder_name: str, source_dir: Path = None) -> bool:
    """게시 완료 후 폴더를 4_posted로 이동 + metadata 업데이트

    Args:
        folder_name: 폴더명 (예: "030_nuts_견과류")
        source_dir: 원본 폴더 경로 (없으면 자동 탐색)

    Returns:
        성공 여부
    """
    import shutil
    import json
    from datetime import datetime

    # 원본 폴더 찾기
    if source_dir is None:
        source_dir = find_content_folder(folder_name, status_filter="3_approved")

    if not source_dir or not source_dir.exists():
        print(f"   ⚠️ 원본 폴더 없음: {folder_name}")
        return False

    # 이미 4_posted에 있으면 스킵
    if "4_posted" in str(source_dir):
        print(f"   ℹ️ 이미 4_posted에 있음: {folder_name}")
        return True

    # metadata.json 업데이트 (이동 전)
    metadata_path = source_dir / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata["status"] = "posted"
            metadata["posted_at"] = datetime.now().isoformat()
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"   ⚠️ metadata 업데이트 실패: {e}")

    # 대상 폴더 확인
    POSTED_DIR.mkdir(parents=True, exist_ok=True)
    dest_dir = POSTED_DIR / folder_name

    # 이미 존재하면 백업
    if dest_dir.exists():
        backup_dir = POSTED_DIR / f"{folder_name}_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        dest_dir.rename(backup_dir)
        print(f"   📦 기존 폴더 백업: {backup_dir.name}")

    # 이동
    try:
        shutil.move(str(source_dir), str(dest_dir))
        print(f"   📁 폴더 이동 완료: 3_approved → 4_posted")
        return True
    except Exception as e:
        print(f"   ❌ 폴더 이동 실패: {e}")
        return False


def find_content_folder(folder_name: str, status_filter: str = None) -> Path:
    """콘텐츠 폴더 찾기 (v3 구조 지원)

    Args:
        folder_name: 폴더명 (예: "028_pasta_파스타")
        status_filter: 특정 상태만 검색 ("3_approved" 등)

    Returns:
        폴더 경로 또는 None
    """
    # 1. 특정 상태 필터가 있으면 해당 폴더만 검색
    if status_filter:
        target = CONTENTS_DIR / status_filter / folder_name
        if target.exists():
            return target
        return None

    # 2. 상태 폴더 순서대로 검색
    for status_folder in STATUS_FOLDERS:
        target = CONTENTS_DIR / status_folder / folder_name
        if target.exists():
            return target

    # 3. 구버전 호환: contents/ 루트에 있는 경우
    target = CONTENTS_DIR / folder_name
    if target.exists():
        return target

    return None

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Threads API 설정
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_API_URL = "https://graph.threads.net/v1.0"

from core.agents.publisher import PublisherAgent
from core.utils.sync_manager import on_publish_complete
from core.utils.retry_manager import RetryManager, publish_with_retry
from core.utils.google_sheets_manager import ContentSheetManager


class PublishError(Exception):
    """게시 관련 오류"""
    pass


def sync_to_google_sheets(topic: str, topic_kr: str, folder: str, date: str, instagram_url: str) -> bool:
    """Google Sheets 동기화 - HARD FAIL 조건

    Args:
        topic: 영문명
        topic_kr: 한글명
        folder: 폴더명
        date: 게시일
        instagram_url: Instagram URL

    Returns:
        성공 여부

    Raises:
        PublishError: 동기화 실패 시 (HARD FAIL)
    """
    try:
        # content_map.json에서 안전도 정보 가져오기
        content_map_path = ROOT / "config" / "data" / "content_map.json"
        safety = "safe"  # 기본값

        if content_map_path.exists():
            import json
            with open(content_map_path, 'r', encoding='utf-8') as f:
                content_map = json.load(f)
                if topic in content_map.get("contents", {}):
                    safety = content_map["contents"][topic].get("safety", "safe").upper()

        # 폴더 번호 추출
        folder_parts = folder.split("_")
        number = folder_parts[0] if folder_parts[0].isdigit() else "000"

        # Google Sheets 업데이트
        sheet_manager = ContentSheetManager()

        if sheet_manager.is_configured:
            if sheet_manager.connect():
                # 기존 항목 확인
                existing = sheet_manager.get_content(topic)

                if existing:
                    # 업데이트
                    result = sheet_manager.update_content(topic, {
                        '게시상태': '게시완료',
                        '게시일': date,
                        '인스타URL': instagram_url
                    })
                else:
                    # 새로 추가
                    result = sheet_manager.add_content(
                        number=number,
                        topic_en=topic,
                        topic_kr=topic_kr,
                        safety=safety,
                        status='게시완료',
                        publish_date=date,
                        instagram_url=instagram_url
                    )

                if result:
                    print(f"📊 Google Sheets 동기화 완료: {topic_kr}")
                    return True
                else:
                    raise PublishError(f"Google Sheets 반영 실패: {topic}")
            else:
                raise PublishError("Google Sheets 연결 실패")
        else:
            print(f"⚠️ Google Sheets 미설정 - 로컬 캐시만 사용")
            return True  # 설정 안 된 경우는 통과

    except PublishError:
        raise
    except Exception as e:
        raise PublishError(f"Google Sheets 동기화 오류: {e}")

# 콘텐츠 폴더 매핑 (옵션 D' 적용 - 상태 접미사 제거)
CONTENT_MAP = {
    # 기본 콘텐츠
    "pumpkin": "001_pumpkin",
    "blueberries": "002_blueberries",
    "carrot": "003_carrot",
    "cherry": "004_cherry",
    "sweet_potato": "005_sweet_potato",
    "cherries": "004_cherry",  # 별칭
    "apple": "006_apple",
    "pineapple": "007_pineapple",
    "banana": "008_banana",
    "broccoli": "009_broccoli",
    "watermelon": "010_watermelon",
    "strawberry": "011_strawberry",
    "mango": "012_mango",
    "orange": "013_orange",
    "pear": "014_pear",
    "kiwi": "015_kiwi",
    "papaya": "016_papaya",
    "peach": "017_peach",
    "rice": "018_rice",
    "cucumber": "019_cucumber",
    "pringles": "020_pringles_프링글스",
    "sausage": "021_sausage_소시지",
    "avocado": "022_avocado_아보카도",
    "coca_cola": "023_coca_cola_코카콜라",
    "beef": "024_beef_소고기",
    "olive": "024_olive_올리브",
    "blackberry": "025_blackberry_블랙베리",
    "kale": "026_kale_케일",
    "spinach": "026_spinach_시금치",
    "celery": "027_celery_셀러리",
    "zucchini": "027_zucchini_애호박",
    "pasta": "028_pasta_파스타",
    "chicken": "029_chicken_닭고기",
    "poached_egg": "029_poached_egg_수란",
    "nuts": "030_nuts_견과류",
    "boiled_egg": "032_boiled_egg_삶은달걀",
    "tuna": "036_tuna_참치",
    "potato": "036_potato_감자",
    "burdock": "044_burdock_우엉",
    "salmon": "054_salmon_연어",
    "grape": "060_grape_포도",
    "yangnyeom_chicken": "074_yangnyeom_chicken_양념치킨",
    "samgyeopsal": "089_samgyeopsal_삼겹살",
    "icecream": "094_icecream_아이스크림",
    "budweiser": "107_budweiser_버드와이저",
    "kitkat": "117_kitkat_킷캣",
    "shrimp": "140_shrimp_새우",
    "duck": "169_duck_오리고기",
}


# 토픽 한글명 매핑
TOPIC_KR_MAP = {
    # 구버전
    "pumpkin": "호박", "blueberries": "블루베리", "carrot": "당근",
    "apple": "사과", "sweet_potato": "고구마", "cherries": "체리",
    "pineapple": "파인애플", "watermelon": "수박", "banana": "바나나",
    "broccoli": "브로콜리",
    # 신버전
    "strawberry": "딸기", "mango": "망고", "orange": "오렌지",
    "pear": "배", "kiwi": "키위", "papaya": "파파야", "peach": "복숭아",
    "rice": "흰쌀밥", "cucumber": "오이", "pringles": "프링글스",
    "sausage": "소시지", "avocado": "아보카도", "coca_cola": "코카콜라",
    "olive": "올리브", "blackberry": "블랙베리", "grape": "포도",
    "spinach": "시금치", "zucchini": "애호박", "pasta": "파스타", "chicken": "닭고기",
    "beef": "소고기", "salmon": "연어", "tuna": "참치",
    "yogurt": "요거트", "tofu": "두부", "boiled_egg": "삶은달걀",
    "mackerel": "고등어", "potato": "감자", "chocolate": "초콜릿",
    "cake": "케이크",
    # Day 11 추가
    "celery": "셀러리", "burdock": "우엉", "kale": "케일",
    # Day 12 추가
    "shrimp": "새우",
    "duck": "오리고기",
    "nuts": "견과류",
}


def convert_caption_for_threads(caption: str, topic_kr: str) -> str:
    """Instagram 캡션을 Threads용 대화체로 변환"""
    hooks = [
        f"우리 집 강아지만 {topic_kr} 좋아하나? 🐕",
        f"나만 몰랐나... {topic_kr} 줘도 되는 거였어?",
        f"{topic_kr} 주기 전에 이것만 알아두자!",
        f"다들 {topic_kr} 어떻게 주고 있어?",
    ]
    ctas = [
        "너네 강아지는 이거 좋아해? 댓글 ㄱㄱ 🐕",
        "다들 어떻게 주고 있어? 궁금해!",
        "댓글로 알려줘~ 참고할게 ㅎㅎ",
    ]

    lines = [l.strip() for l in caption.split('\n') if l.strip()]
    core_info = ""
    for line in lines:
        if any(m in line for m in ['→', '좋', '주의', '적정', '비타민', '수분', '칼로리']):
            clean = line.replace('•', '').replace('✅', '').replace('⚠️', '').strip()
            if 10 < len(clean) < 60:
                core_info = clean
                break
    if not core_info:
        for line in lines[1:5]:
            if 15 < len(line) < 60 and '정답' not in line and '#' not in line:
                core_info = line.replace('•', '').strip()
                break

    for f, c in [("입니다", "야"), ("합니다", "해"), ("됩니다", "돼"), ("좋아요", "좋아")]:
        core_info = core_info.replace(f, c)

    hook = random.choice(hooks)
    cta = random.choice(ctas)
    return f"{hook}\n\n{core_info}\n\n{cta}" if core_info else f"{hook}\n\n{cta}"


def post_to_threads(topic_kr: str, caption: str, image_urls: list) -> dict:
    """Threads에 캐러셀 게시 (4장 이미지)

    Args:
        topic_kr: 한글 토픽명
        caption: Threads용 캡션
        image_urls: Cloudinary 이미지 URL 목록 (4장)

    Returns:
        {"success": bool, "post_id": str, "url": str, "error": str}
    """
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        return {"success": False, "error": "Threads API 미설정"}

    if not image_urls or len(image_urls) < 1:
        return {"success": False, "error": "이미지 URL 없음"}

    print(f"\n📤 Threads 캐러셀 게시 중... ({len(image_urls)}장)")

    try:
        # 1. 각 이미지별 미디어 컨테이너 생성
        media_container_ids = []
        for i, img_url in enumerate(image_urls):
            url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads"
            params = {
                "access_token": THREADS_ACCESS_TOKEN,
                "media_type": "IMAGE",
                "image_url": img_url,
                "is_carousel_item": "true"
            }

            resp = requests.post(url, params=params, timeout=30)
            data = resp.json()

            if "id" not in data:
                error_msg = data.get("error", {}).get("message", str(data))
                return {"success": False, "error": f"이미지 {i+1} 컨테이너 생성 실패: {error_msg}"}

            media_container_ids.append(data["id"])
            print(f"   ✅ 이미지 {i+1}/4 컨테이너 생성")
            time.sleep(1)  # API 레이트 리밋 방지

        # 2. 캐러셀 컨테이너 생성
        carousel_url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads"
        carousel_params = {
            "access_token": THREADS_ACCESS_TOKEN,
            "media_type": "CAROUSEL",
            "children": ",".join(media_container_ids),
            "text": caption
        }

        resp = requests.post(carousel_url, params=carousel_params, timeout=30)
        data = resp.json()

        if "id" not in data:
            error_msg = data.get("error", {}).get("message", str(data))
            return {"success": False, "error": f"캐러셀 컨테이너 생성 실패: {error_msg}"}

        carousel_container_id = data["id"]
        print(f"   ✅ 캐러셀 컨테이너 생성")
        time.sleep(3)  # 미디어 처리 대기

        # 3. 캐러셀 게시
        pub_url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads_publish"
        pub_params = {
            "access_token": THREADS_ACCESS_TOKEN,
            "creation_id": carousel_container_id
        }

        resp = requests.post(pub_url, params=pub_params, timeout=30)
        data = resp.json()

        if "id" in data:
            post_id = data["id"]
            threads_url = f"https://www.threads.net/post/{post_id}"
            return {"success": True, "post_id": post_id, "url": threads_url}
        else:
            error_msg = data.get("error", {}).get("message", str(data))
            return {"success": False, "error": f"캐러셀 게시 실패: {error_msg}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def _do_publish(topic: str, image_paths: list, caption: str) -> dict:
    """실제 게시 수행 (내부 함수)

    Args:
        topic: 토픽명
        image_paths: 이미지 경로 목록
        caption: 캡션 텍스트

    Returns:
        {"success": bool, "data": {...}, "error": str}

    🔐 게시 성공 판정 규칙 (2026-02-04 확정):
    1. API 호출 성공 ≠ 게시 성공
    2. 성공 조건 = media_id 존재 + 시뮬레이션 아님
    3. media_id 없거나 시뮬레이션이면 무조건 실패 처리
    """
    publisher = PublisherAgent()
    publisher.config["instagram"] = {"caption_template": caption}
    publisher.config["platforms"] = ["cloudinary", "instagram"]

    images_with_paths = [{"path": p, "type": "content"} for p in image_paths]

    result = await publisher.run({
        "images": images_with_paths,
        "topic": topic,
        "passed": True,
    })

    if result.success:
        data = result.data
        publish_results = data.get("publish_results", {})
        instagram_result = publish_results.get("instagram", {})

        # 🔐 [FIX] 시뮬레이션 모드 체크 - False Positive 방지 (2026-02-04)
        if instagram_result.get("simulated", False):
            print("   ⚠️ [FIX] 시뮬레이션 모드 감지 - 실패로 처리")
            return {
                "success": False,
                "error": "시뮬레이션 모드 - 실제 게시 안 됨 (Instagram 토큰/계정ID 미설정)",
                "simulated": True
            }

        # 🔐 [FIX] media_id 검증 - 실제 게시 확인 (2026-02-04)
        post_id = instagram_result.get("post_id", "")
        if instagram_result.get("success") and post_id:
            # media_id 유효성 검사 (Instagram media_id는 숫자만으로 구성)
            if not post_id.isdigit() and not post_id.startswith("17"):
                print(f"   ⚠️ [FIX] 유효하지 않은 post_id 형식: {post_id}")
                return {
                    "success": False,
                    "error": f"유효하지 않은 post_id 형식: {post_id}",
                    "invalid_post_id": True
                }

            return {
                "success": True,
                "data": data,
                "post_id": post_id,
                "permalink": instagram_result.get("permalink", ""),
                "simulated": False
            }
        else:
            # media_id 없음 = 게시 실패
            return {
                "success": False,
                "error": instagram_result.get("error", "Instagram 게시 실패 - media_id 없음")
            }
    else:
        return {
            "success": False,
            "error": result.error or "게시 실패"
        }


async def publish_content(topic: str, auto_retry: bool = True):
    """콘텐츠 게시

    Args:
        topic: 토픽명
        auto_retry: 실패 시 자동 재시도 여부 (기본: True)

    Returns:
        게시 결과
    """
    folder = CONTENT_MAP.get(topic)
    if not folder:
        print(f"❌ 지원하지 않는 토픽: {topic}")
        return {"success": False, "error": f"지원하지 않는 토픽: {topic}"}

    # v3 폴더 구조: contents/3_approved/ (PD 승인된 콘텐츠만 게시)
    image_dir = find_content_folder(folder, status_filter="3_approved")
    if not image_dir:
        # 승인 대기 콘텐츠 확인
        pending_dir = find_content_folder(folder)
        if pending_dir:
            status_name = pending_dir.parent.name
            print(f"❌ 미승인 콘텐츠: {folder}")
            print(f"   현재 위치: contents/{status_name}/")
            print(f"   → PD 승인 후 3_approved/로 이동 필요")
            return {"success": False, "error": f"미승인 콘텐츠 - 현재 {status_name}"}
        else:
            print(f"❌ 콘텐츠 폴더 없음: {folder}")
            return {"success": False, "error": f"콘텐츠 폴더 없음: {folder}"}
    # 캡션 파일명: caption_instagram.txt 또는 caption.txt
    caption_path = image_dir / "caption_instagram.txt"
    if not caption_path.exists():
        caption_path = image_dir / "caption.txt"

    print("=" * 60)
    print(f"📤 {topic.upper()} Instagram 게시")
    if auto_retry:
        print(f"   (자동 재시도 활성화: 최대 3회)")
    print("=" * 60)
    print(f"\n계정: @sunshinedogfood")

    # 이미지 수집 - 신버전(00-03) 또는 구버전(01-04) 자동 감지
    image_paths = []

    # 신버전 형식 시도 (00-03)
    new_format = image_dir / f"{topic}_00.png"
    if new_format.exists():
        print("  📁 신버전 형식 (00-03)")
        for i in range(4):
            img_path = image_dir / f"{topic}_{i:02d}.png"
            if img_path.exists():
                image_paths.append(str(img_path))
                print(f"  ✅ {topic}_{i:02d}.png")
            else:
                print(f"  ❌ {topic}_{i:02d}.png - 파일 없음!")
                return {"success": False, "error": f"이미지 파일 없음: {topic}_{i:02d}.png"}
    else:
        # 구버전 형식 시도 (01-04 또는 첫 4장)
        old_format = image_dir / f"{topic}_01.png"
        if old_format.exists():
            print("  📁 구버전 형식 (01-04)")
            for i in range(1, 5):
                img_path = image_dir / f"{topic}_{i:02d}.png"
                if img_path.exists():
                    image_paths.append(str(img_path))
                    print(f"  ✅ {topic}_{i:02d}.png")
                else:
                    print(f"  ❌ {topic}_{i:02d}.png - 파일 없음!")
                    return {"success": False, "error": f"이미지 파일 없음: {topic}_{i:02d}.png"}
        else:
            print(f"  ❌ 이미지 파일을 찾을 수 없습니다")
            return {"success": False, "error": "이미지 파일 없음"}

    print(f"\n이미지: {len(image_paths)}장 캐러셀")

    # 캡션 로드
    if not caption_path.exists():
        print(f"❌ 캡션 파일 없음: {caption_path}")
        return {"success": False, "error": f"캡션 파일 없음: {caption_path}"}

    with open(caption_path, 'r', encoding='utf-8') as f:
        caption = f.read().strip()

    print(f"\n캡션 미리보기:")
    print("-" * 40)
    print(caption[:200] + "..." if len(caption) > 200 else caption)
    print("-" * 40)

    # 토픽 한글명
    topic_kr = TOPIC_KR_MAP.get(topic, topic)

    # 게시 함수 정의
    async def do_publish():
        return await _do_publish(topic, image_paths, caption)

    # 자동 재시도 여부에 따라 분기
    if auto_retry:
        # RetryManager를 통한 자동 재시도
        result = await publish_with_retry(topic, topic_kr, do_publish)
    else:
        # 단일 시도
        result = await do_publish()
        if result.get("success"):
            result = {"success": True, "data": result, "attempts": 1, "status": "success"}
        else:
            result = {"success": False, "error": result.get("error"), "attempts": 1, "status": "failed"}

    print("\n" + "=" * 60)

    if result.get("success"):
        data = result.get("data", {})
        publish_results = data.get("data", {}).get("publish_results", {}) if isinstance(data.get("data"), dict) else {}

        # Cloudinary 결과
        cloudinary_result = publish_results.get("cloudinary", {})
        if cloudinary_result.get("success"):
            print(f"☁️  Cloudinary: {cloudinary_result.get('count', 0)}장 업로드 완료")

        # Instagram 결과
        post_id = data.get("post_id", "")
        permalink = data.get("permalink", "")

        print(f"\n🎉 Instagram 게시 완료!")
        print(f"   Post ID: {post_id}")
        print(f"   URL: {permalink}")
        print(f"   시도 횟수: {result.get('attempts', 1)}회")

        if data.get("simulated"):
            print("\n   ⚠️  시뮬레이션 모드 (실제 게시 안 됨)")
        else:
            # 🔄 자동 동기화: 게시 완료 후 모든 데이터 파일 업데이트
            from datetime import datetime
            publish_date = datetime.now().strftime("%Y-%m-%d")

            sync_result = on_publish_complete(
                topic=topic,
                topic_kr=topic_kr,
                date=publish_date,
                instagram_url=permalink,
                post_id=post_id,
                score=95
            )
            print(f"\n🔄 로컬 동기화 완료: +{sync_result.get('added', 0)}건")

            # 📊 Google Sheets 동기화 (HARD FAIL 조건 - Phase 3 필수)
            try:
                sync_to_google_sheets(
                    topic=topic,
                    topic_kr=topic_kr,
                    folder=folder,
                    date=publish_date,
                    instagram_url=permalink
                )
            except PublishError as e:
                print(f"\n❌ HARD FAIL: {e}")
                print("   → 게시는 완료되었으나 시트 동기화 실패")
                print("   → 수동 동기화 필요: python -c \"from core.utils.google_sheets_manager import ContentSheetManager; ...\"")
                # HARD FAIL - 게시 실패로 간주
                return {"success": False, "error": str(e), "partial_success": True, "instagram_url": permalink}

            # 📁 폴더 자동 이동: 3_approved → 4_posted
            print(f"\n📁 폴더 이동 중...")
            move_to_posted(folder, image_dir)

            # 🧵 Threads 자동 게시 (캐러셀 4장)
            cloudinary_urls = cloudinary_result.get("urls", [])
            if cloudinary_urls and len(cloudinary_urls) >= 4:
                threads_caption = convert_caption_for_threads(caption, topic_kr)

                print(f"\n🧵 Threads 캐러셀 게시 ({len(cloudinary_urls)}장)...")
                print(f"   캡션: {threads_caption[:50]}...")

                # 4장 모두 전달
                threads_result = post_to_threads(topic_kr, threads_caption, cloudinary_urls[:4])

                if threads_result.get("success"):
                    print(f"   ✅ Threads 캐러셀 게시 완료!")
                    print(f"   URL: {threads_result.get('url')}")
                else:
                    print(f"   ⚠️ Threads 게시 실패: {threads_result.get('error')}")
            else:
                print(f"\n   ⚠️ Threads 스킵: 이미지 부족 ({len(cloudinary_urls) if cloudinary_urls else 0}장)")
    else:
        error = result.get("error", "알 수 없는 오류")
        attempts = result.get("attempts", 1)
        status = result.get("status", "failed")

        if status == "exhausted":
            print(f"\n❌ 게시 최종 실패 (재시도 {attempts}회 소진)")
            print(f"   오류: {error}")
            print(f"\n   ⚠️  텔레그램으로 알림이 전송되었습니다.")
        else:
            print(f"\n❌ 게시 실패: {error}")

    print("\n" + "=" * 60)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Instagram 콘텐츠 게시 (자동 재시도 지원)")
    parser.add_argument("topic", help="게시할 토픽명")
    parser.add_argument("--no-retry", action="store_true", help="자동 재시도 비활성화")
    parser.add_argument("--list", action="store_true", help="지원 토픽 목록 출력")

    args = parser.parse_args()

    if args.list:
        print("지원 토픽 목록:")
        for topic in CONTENT_MAP.keys():
            kr = TOPIC_KR_MAP.get(topic, "")
            print(f"  - {topic} ({kr})")
        sys.exit(0)

    topic = args.topic.lower()
    auto_retry = not args.no_retry

    asyncio.run(publish_content(topic, auto_retry=auto_retry))
