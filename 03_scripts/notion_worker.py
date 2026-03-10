"""
notion_worker.py — 노션 컨트롤타워 워커 (백그라운드 프로세스)
Project Sunshine v1.0

[동작]
무한 루프로 60초마다 노션 DB를 확인하여:
1. '생성요청' → 파이프라인 실행 → '승인대기'
2. '승인' → 인스타 게시 → '게시완료'

[실행]
  python notion_worker.py              # 포그라운드
  nohup python notion_worker.py &      # 백그라운드
  python notion_worker.py --once       # 1회만 실행 (테스트)

[텔레그램 알림]
  제작 시작/완료/오류/게시 완료 시 자동 알림
"""

import os
import sys
import time
import json
import subprocess
import traceback
from datetime import datetime

# 같은 폴더의 notion_sync 임포트
sys.path.insert(0, os.path.dirname(__file__))
from notion_sync import NotionSync, load_env

# ============================================================
# 설정
# ============================================================

POLL_INTERVAL = 60  # 초 (상태 확인 주기)
TELEGRAM_BOT_TOKEN = None  # .env에서 로드
TELEGRAM_CHAT_ID = "5360443525"

# 파이프라인 경로 (최부장이 실제 경로로 수정)
PROJECT_ROOT = os.path.expanduser(
    "~/Desktop/Jun_AI/Dog_Contents/project_sunshine"
)


# ============================================================
# 텔레그램 알림
# ============================================================

def send_telegram(message: str):
    """텔레그램 봇으로 알림 전송"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    if not token:
        print(f"  📱 (텔레그램 미설정) {message}")
        return
    
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  ⚠️ 텔레그램 전송 실패: {e}")


# ============================================================
# 캡션 필터링 (영어 제거) — v11 규칙
# ============================================================

import re

def filter_korean_only(caption: str) -> str:
    """
    캡션에서 영어 번역 부분 제거.

    규칙 (v11):
    - 본문 = 한국어만
    - 해시태그만 한/영 병행 허용

    처리:
    1. 해시태그 섹션 분리
    2. 본문에서 영어 라인/부분 제거
    3. 해시태그는 그대로 유지 (한/영 모두)
    """
    if not caption:
        return caption

    # 해시태그 섹션 분리 (첫 번째 # 등장 위치)
    lines = caption.split('\n')
    body_lines = []
    hashtag_lines = []
    in_hashtag = False

    for line in lines:
        stripped = line.strip()
        # 해시태그 라인 시작 감지 (# 으로 시작하는 라인이 여러 해시태그 포함)
        if stripped.startswith('#') and stripped.count('#') >= 3:
            in_hashtag = True

        if in_hashtag:
            hashtag_lines.append(line)
        else:
            body_lines.append(line)

    # 본문에서 영어 제거
    filtered_body = []

    # 영어만 있는 라인 패턴 (한글 없이 영문자+숫자+공백+기호만)
    # 이모지와 특수문자도 포함
    english_only_pattern = re.compile(
        r'^[A-Za-z0-9\s\.\,\!\?\-\—\:\;\'\"\(\)\[\]\/\+\*\&\%\$\@\~\`\'\'\u2018\u2019]+$'
    )

    for line in body_lines:
        stripped = line.strip()

        # 빈 줄은 유지
        if not stripped:
            filtered_body.append(line)
            continue

        # "Save & Share!" 제거
        if 'Save & Share' in stripped:
            continue

        # 한글이 전혀 없는 라인 제거 (영어만 또는 영어+이모지)
        if not re.search(r'[가-힣]', stripped):
            continue

        # 한글이 있는 라인에서 영어 부분 제거
        processed = stripped

        # 패턴 1: "한글텍스트 English text" → "한글텍스트"
        # 한글 뒤 공백 + 대문자 시작 영어 문장 → 제거
        # 단, 수량 뒤의 한글 괄호 설명은 유지: "1~2조각 (물에 헹궈서)"
        processed = re.sub(r'([가-힣\!\?\.\,\~🐾])\s+[A-Z][A-Za-z][A-Za-z\s\'\'\'\-]+$', r'\1', processed)

        # 패턴 1b: "수량 영어설명" → "수량"
        # "1~2조각 rinse first" → "1~2조각"
        processed = re.sub(r'(\d+[~\-]\d+\S*)\s+[A-Za-z][A-Za-z\s]+$', r'\1', processed)

        # 패턴 2: "Benefits", "Caution", "Tips", "Serving Size" 등 영어 키워드 제거
        processed = re.sub(r'\s*Benefits\s*$', '', processed)
        processed = re.sub(r'\s*Caution\s*$', '', processed)
        processed = re.sub(r'\s*Tips\s*$', '', processed)
        processed = re.sub(r'\s*Serving Size\s*$', '', processed)

        # 패턴 3: "Small:", "Medium:", "Large:" 라벨만 제거 (뒤의 수량은 유지)
        # "소형견 Small: 1~2조각" → "소형견 1~2조각"
        processed = re.sub(r'\s+Small:\s*', ' ', processed)
        processed = re.sub(r'\s+Medium:\s*', ' ', processed)
        processed = re.sub(r'\s+Large:\s*', ' ', processed)

        # 패턴 4: "— English text" 제거
        processed = re.sub(r'\s*—\s*[A-Za-z][A-Za-z\s\,\.\!\-\'\'\u2018\u2019]+$', '', processed)

        # 패턴 5: 소괄호 안 영어 제거: (물에 헹궈서) 는 유지, (rinse first) 는 제거
        processed = re.sub(r'\s*\([A-Za-z][A-Za-z\s]+\)\s*', ' ', processed)

        # 이중 공백 정리
        processed = re.sub(r'\s{2,}', ' ', processed).strip()

        # 처리 후 내용이 의미있는 경우만 추가 (이모지만 남은 경우 제외)
        if processed and re.search(r'[가-힣]', processed):
            filtered_body.append(processed)

    # 본문 + 해시태그 결합
    result = '\n'.join(filtered_body)
    if hashtag_lines:
        result += '\n' + '\n'.join(hashtag_lines)

    return result.strip()


def convert_to_thread_caption(insta_caption: str) -> str:
    """
    인스타 캡션을 쓰레드용으로 변환.

    변환:
    1. 영어 제거 (filter_korean_only)
    2. 해시태그 3~5개로 축소 (한국어 우선)
    3. "Save & Share!" 제거
    """
    # 1. 영어 제거
    filtered = filter_korean_only(insta_caption)

    # 2. 해시태그 축소
    lines = filtered.split('\n')
    body_lines = []
    hashtags = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            # 해시태그 추출
            tags = re.findall(r'#\S+', stripped)
            hashtags.extend(tags)
        else:
            body_lines.append(line)

    # 한국어 해시태그 우선 (3~5개)
    korean_tags = [t for t in hashtags if re.search(r'[가-힣]', t)]
    english_tags = [t for t in hashtags if not re.search(r'[가-힣]', t)]

    # 한국어 3개 + 영어 2개 = 5개
    selected = korean_tags[:3] + english_tags[:2]

    result = '\n'.join(body_lines).strip()
    if selected:
        result += '\n\n' + ' '.join(selected)

    return result


# ============================================================
# 파이프라인 실행
# ============================================================

def run_pipeline(food_name_en: str, food_name_kr: str, safety: str, number: int):
    """
    콘텐츠 제작 파이프라인

    1. 이미 콘텐츠가 준비되어 있으면 → 바로 성공
    2. 없으면 → 오류 (수동 제작 필요)

    반환: {
        "success": True/False,
        "cover_url": "...",
        "body_urls": [...],
        "cta_url": "...",
        "caption": "...",
        "hashtags": "...",
        "error": "에러 메시지" (실패 시)
    }
    """
    from pathlib import Path

    result = {
        "success": False,
        "cover_url": None,
        "body_urls": [],
        "cta_url": None,
        "caption": None,
        "hashtags": None,
        "error": None,
    }

    try:
        print(f"  🔧 콘텐츠 확인: {food_name_kr} ({food_name_en})")
        print(f"     안전도: {safety} / 번호: {number:03d}")

        # ================================================
        # 콘텐츠 폴더 확인
        # ================================================
        content_folder = find_content_folder(number, food_name_en)

        if not content_folder:
            result["error"] = f"콘텐츠 폴더 없음: {number:03d}_{food_name_en}"
            return result

        print(f"  📁 폴더 확인: {content_folder.name}")

        insta_folder = content_folder / "01_Insta&Thread"
        if not insta_folder.exists():
            result["error"] = f"01_Insta&Thread 폴더 없음"
            return result

        # ================================================
        # 이미지 4장 확인
        # ================================================
        image_patterns = ["*Cover*", "*Food*", "*DogWithFood*", "*Cta*"]
        image_files = []

        for pattern in image_patterns:
            found = list(insta_folder.glob(pattern))
            png_files = [f for f in found if f.suffix.lower() in ['.png', '.jpg', '.jpeg']]
            if png_files:
                image_files.append(png_files[0])

        if len(image_files) < 4:
            result["error"] = f"이미지 부족: {len(image_files)}/4장"
            print(f"  ❌ 이미지 부족")
            for pattern in image_patterns:
                found = list(insta_folder.glob(pattern))
                status = "✅" if any(f.suffix.lower() in ['.png', '.jpg'] for f in found) else "❌"
                print(f"     {status} {pattern}")
            return result

        print(f"  ✅ 이미지 4장 확인")

        # ================================================
        # 캡션 파일 확인
        # ================================================
        caption_file = None
        for f in insta_folder.glob("*_Insta_Caption.txt"):
            caption_file = f
            break

        if not caption_file:
            result["error"] = "인스타 캡션 파일 없음"
            return result

        with open(caption_file, 'r', encoding='utf-8') as f:
            caption_text = f.read().strip()

        if not caption_text:
            result["error"] = "캡션 파일이 비어있음"
            return result

        print(f"  ✅ 캡션 확인: {caption_file.name}")

        # 캡션에서 해시태그 분리
        if '#' in caption_text:
            parts = caption_text.split('#', 1)
            result["caption"] = parts[0].strip()
            result["hashtags"] = '#' + parts[1] if len(parts) > 1 else ""
        else:
            result["caption"] = caption_text

        # ================================================
        # 성공
        # ================================================
        result["success"] = True
        print(f"  ✅ 콘텐츠 준비 완료 → 승인대기로 전환")

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        traceback.print_exc()

    return result


def find_content_folder(number: int, food_name_en: str):
    """콘텐츠 폴더 찾기 (신규 안전도별 폴더 구조 지원)

    구조:
      01_contents/🟢_safe/S{num}_{FoodName}/
      01_contents/🟡_caution/C{num}_{FoodName}/
      01_contents/🔴_forbidden/F{num}_{FoodName}/
    """
    from pathlib import Path
    contents_root = Path(PROJECT_ROOT) / "01_contents"

    # 안전도별 서브폴더
    safety_folders = ["🟢_safe", "🟡_caution", "🔴_forbidden"]
    prefixes = ["S", "C", "F"]

    # 1. 번호로 폴더 찾기 (새 구조: S052_*, C052_*, F052_*)
    for safety_folder, prefix in zip(safety_folders, prefixes):
        safety_path = contents_root / safety_folder
        if safety_path.exists():
            pattern = f"{prefix}{number:03d}_*"
            for folder in safety_path.glob(pattern):
                if folder.is_dir():
                    return folder

    # 2. 영문명으로 폴더 찾기
    for safety_folder in safety_folders:
        safety_path = contents_root / safety_folder
        if safety_path.exists():
            for folder in safety_path.glob(f"*{food_name_en}*"):
                if folder.is_dir():
                    return folder

    # 3. 레거시: 01_contents 직접 하위 (이전 구조)
    pattern = f"{number:03d}_*"
    for folder in contents_root.glob(pattern):
        if folder.is_dir():
            return folder

    for folder in contents_root.glob(f"*{food_name_en}*"):
        if folder.is_dir():
            return folder

    return None


# ============================================================
# 인스타 게시
# ============================================================

def publish_to_instagram(page_id: str, food_name_kr: str, food_name_en: str = None, number: int = None):
    """
    인스타그램 + 쓰레드 캐러셀 게시

    반환: {"success": True, "post_url": "...", "threads_url": "..."} 또는 에러
    """
    import requests
    from pathlib import Path

    print(f"  📤 게시 시작: {food_name_kr}")

    result = {
        "success": False,
        "post_url": None,
        "threads_url": None,
        "error": None,
    }

    # 콘텐츠 폴더 찾기
    content_folder = find_content_folder(number, food_name_en) if number else None

    if not content_folder:
        # 3_approved 폴더에서 찾기
        approved_dir = Path(PROJECT_ROOT) / "01_contents"
        for folder in approved_dir.rglob(f"*{food_name_en}*"):
            if folder.is_dir() and "01_Insta&Thread" in str(folder) or (folder / "01_Insta&Thread").exists():
                content_folder = folder
                break

    if not content_folder:
        result["error"] = f"콘텐츠 폴더 없음: {food_name_en}"
        return result

    insta_folder = content_folder / "01_Insta&Thread"
    if not insta_folder.exists():
        insta_folder = content_folder

    # 이미지 파일 찾기 (다양한 네이밍 패턴 지원)
    image_files = []
    image_patterns = [
        # 패턴 1: Common_01_Cover, Common_02_Food 등
        ["*Common*01*Cover*", "*Common*02*Food*", "*Common*03*DogWithFood*", "*Common*09*Cta*"],
        # 패턴 2: 045_EggYolk_insta_01_Cover 등
        ["*01*Cover*", "*02*Food*", "*03*DogWithFood*", "*04*Cta*"],
        # 패턴 3: Cover, Food, DogWithFood, Cta (단순)
        ["*Cover*", "*Food*", "*DogWithFood*", "*Cta*"],
    ]

    for patterns in image_patterns:
        image_files = []
        for pattern in patterns:
            for img in insta_folder.glob(pattern):
                if img.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    image_files.append(img)
                    break
        if len(image_files) >= 4:
            break

    if len(image_files) < 4:
        result["error"] = f"이미지 부족: {len(image_files)}/4"
        return result

    # 캡션 파일 읽기 + 영어 제거 (v11 규칙)
    caption = ""
    for caption_file in insta_folder.glob("*_Insta_Caption.txt"):
        with open(caption_file, 'r', encoding='utf-8') as f:
            raw_caption = f.read().strip()
        # 영어 제거 (본문만, 해시태그는 한/영 유지)
        caption = filter_korean_only(raw_caption)
        print(f"    ✅ 캡션 필터링 완료 (영어 제거)")
        break

    if not caption:
        result["error"] = "캡션 파일 없음"
        return result

    # Cloudinary 업로드
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )

    image_urls = []
    for i, img in enumerate(image_files):
        print(f"    Cloudinary 업로드: {img.name}")
        upload_result = cloudinary.uploader.upload(
            str(img),
            folder=f'sunshine/{food_name_en}',
            public_id=f'{food_name_en}_{i:02d}',
            overwrite=True,
            resource_type='image'
        )
        image_urls.append(upload_result['secure_url'])

    # Instagram 게시
    ig_user_id = os.environ.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    ig_token = os.environ.get('INSTAGRAM_ACCESS_TOKEN')

    if not ig_user_id or not ig_token:
        result["error"] = "Instagram 토큰 미설정"
        return result

    base_url = 'https://graph.facebook.com/v18.0'

    try:
        # 1. 각 이미지 컨테이너 생성
        container_ids = []
        for i, url in enumerate(image_urls):
            resp = requests.post(
                f'{base_url}/{ig_user_id}/media',
                data={
                    'image_url': url,
                    'is_carousel_item': 'true',
                    'access_token': ig_token
                },
                timeout=30
            )
            data = resp.json()
            if 'id' not in data:
                result["error"] = f"IG 컨테이너 {i} 실패: {data}"
                return result
            container_ids.append(data['id'])
            print(f"    IG 컨테이너 {i+1}/4 생성")
            time.sleep(1)

        # 2. 캐러셀 컨테이너 생성
        resp = requests.post(
            f'{base_url}/{ig_user_id}/media',
            data={
                'media_type': 'CAROUSEL',
                'children': ','.join(container_ids),
                'caption': caption,
                'access_token': ig_token
            },
            timeout=30
        )
        data = resp.json()
        if 'id' not in data:
            result["error"] = f"IG 캐러셀 생성 실패: {data}"
            return result
        carousel_id = data['id']

        time.sleep(3)

        # 3. 게시
        resp = requests.post(
            f'{base_url}/{ig_user_id}/media_publish',
            data={
                'creation_id': carousel_id,
                'access_token': ig_token
            },
            timeout=30
        )
        data = resp.json()
        if 'id' in data:
            post_id = data['id']
            result["post_url"] = f"https://instagram.com/p/{post_id}"
            print(f"  ✅ Instagram 게시 완료: {post_id}")
        else:
            result["error"] = f"IG 게시 실패: {data}"
            return result

    except Exception as e:
        result["error"] = f"Instagram 오류: {str(e)}"
        return result

    # Threads 게시 (인스타 캡션 기반 한국어 변환 — v11 규칙)
    # Thread_Caption.txt (영어) 사용 금지 → 인스타 캡션에서 해시태그만 축소
    threads_caption = convert_to_thread_caption(caption)
    print(f"    ✅ 쓰레드 캡션 변환 완료 (해시태그 축소)")

    threads_user_id = os.environ.get('THREADS_USER_ID')
    threads_token = os.environ.get('THREADS_ACCESS_TOKEN')

    if threads_user_id and threads_token:
        threads_base = 'https://graph.threads.net/v1.0'
        try:
            # Threads 컨테이너 생성
            media_ids = []
            for i, url in enumerate(image_urls):
                resp = requests.post(
                    f'{threads_base}/{threads_user_id}/threads',
                    data={
                        'media_type': 'IMAGE',
                        'image_url': url,
                        'access_token': threads_token
                    },
                    timeout=30
                )
                data = resp.json()
                if 'id' in data:
                    media_ids.append(data['id'])
                time.sleep(1)

            if len(media_ids) == 4:
                # 캐러셀 생성
                resp = requests.post(
                    f'{threads_base}/{threads_user_id}/threads',
                    data={
                        'media_type': 'CAROUSEL',
                        'children': ','.join(media_ids),
                        'text': threads_caption,
                        'access_token': threads_token
                    },
                    timeout=30
                )
                data = resp.json()
                if 'id' in data:
                    carousel_id = data['id']
                    time.sleep(3)

                    # 게시
                    resp = requests.post(
                        f'{threads_base}/{threads_user_id}/threads_publish',
                        data={
                            'creation_id': carousel_id,
                            'access_token': threads_token
                        },
                        timeout=30
                    )
                    pub_data = resp.json()
                    if 'id' in pub_data:
                        result["threads_url"] = f"https://threads.net/t/{pub_data['id']}"
                        print(f"  ✅ Threads 게시 완료: {pub_data['id']}")
        except Exception as e:
            print(f"  ⚠️ Threads 게시 실패: {e}")

    result["success"] = True
    return result


# ============================================================
# 메인 워커 루프
# ============================================================

def worker_loop(sync: NotionSync, run_once=False):
    """
    메인 루프 (플랫폼별 3분할 폴링):
    1. 인스타_상태 '생성요청' 감지 → 제작 → '승인' 감지 → 게시
    2. 블로그_상태 '생성요청' 감지 → 제작 → '승인' 감지 → 게시
    3. 쓰레드_상태 '생성요청' 감지 → 제작 → '승인' 감지 → 게시
    """
    cycle = 0
    PLATFORMS = [
        {"field": "인스타_상태", "name": "인스타", "emoji": "📸"},
        {"field": "블로그_상태", "name": "블로그", "emoji": "📝"},
        {"field": "쓰레드_상태", "name": "쓰레드", "emoji": "🧵"},
    ]

    while True:
        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")

        if cycle % 10 == 1:  # 10분마다 헬스체크 출력
            print(f"\n🔄 [{now}] 워커 동작 중 (cycle #{cycle})")

        # ==================================================
        # 플랫폼별 폴링
        # ==================================================
        for platform in PLATFORMS:
            field = platform["field"]
            pname = platform["name"]
            emoji = platform["emoji"]

            # --------------------------------------------------
            # 1단계: '생성요청' 감지 → 제작
            # --------------------------------------------------
            requests = sync.poll_status_changes("생성요청", field=field)

            for item in requests:
                page_id = item["page_id"]
                name_kr = item["음식명"]
                name_en = item["음식명_EN"]
                safety = item["안전도"]
                number = item["번호"]

                print(f"\n{'='*50}")
                print(f"{emoji} [{pname}] 제작 요청 감지: {name_kr} ({name_en})")
                print(f"{'='*50}")

                # 상태 → 제작중
                sync.update_status(page_id, "제작중", field=field)
                send_telegram(f"{emoji} <b>[{pname}]</b> {name_kr} 제작 시작")

                # 파이프라인 실행
                result = run_pipeline(name_en, name_kr, safety, number)

                if result["success"]:
                    # 결과 업로드 → 승인대기
                    sync.upload_results(page_id, result)
                    sync.update_status(page_id, "승인대기", field=field)
                    send_telegram(
                        f"✅ <b>[{pname}]</b> {name_kr} 제작 완료\n"
                        f"노션에서 확인 후 '승인'으로 변경하세요"
                    )
                else:
                    # 오류 기록
                    sync.update_status(page_id, "오류", result.get("error", "알 수 없는 오류"), field=field)
                    send_telegram(
                        f"❌ <b>[{pname}]</b> {name_kr} 제작 오류\n"
                        f"오류: {result.get('error', '알 수 없음')[:200]}"
                    )

            # --------------------------------------------------
            # 2단계: '승인' 감지 → 게시
            # --------------------------------------------------
            approved = sync.poll_status_changes("승인", field=field)

            for item in approved:
                page_id = item["page_id"]
                name_kr = item["음식명"]
                name_en = item["음식명_EN"]
                number = item["번호"]

                print(f"\n{emoji} [{pname}] 게시 실행: {name_kr}")

                # 플랫폼별 게시 분기
                if pname == "인스타":
                    pub = publish_to_instagram(
                        page_id=page_id,
                        food_name_kr=name_kr,
                        food_name_en=name_en,
                        number=number
                    )
                    post_url = pub.get("post_url", "")
                elif pname == "쓰레드":
                    pub = publish_to_threads_only(
                        page_id=page_id,
                        food_name_kr=name_kr,
                        food_name_en=name_en,
                        number=number
                    )
                    post_url = pub.get("threads_url", "")
                elif pname == "블로그":
                    # 블로그는 수동 게시 (HTML 생성만)
                    pub = {"success": True, "message": "블로그 HTML 준비 완료 - 수동 게시 필요"}
                    post_url = ""
                else:
                    pub = {"success": False, "error": f"알 수 없는 플랫폼: {pname}"}

                if pub.get("success"):
                    sync.record_publish(page_id, post_url, field=field)
                    msg = f"{emoji} <b>[{pname}]</b> {name_kr} 게시 완료"
                    if post_url:
                        msg += f"\n🔗 {post_url}"
                    send_telegram(msg)
                else:
                    error_msg = pub.get("error", "알 수 없는 오류")
                    sync.update_status(page_id, "오류", error_msg, field=field)
                    send_telegram(f"❌ <b>[{pname}]</b> {name_kr} 게시 실패\n오류: {error_msg[:100]}")

        # --------------------------------------------------
        # 루프 제어
        # --------------------------------------------------
        if run_once:
            print("\n✅ 1회 실행 완료")
            break

        time.sleep(POLL_INTERVAL)


def publish_to_threads_only(page_id: str, food_name_kr: str, food_name_en: str = None, number: int = None):
    """쓰레드 전용 게시 (인스타 없이 쓰레드만)"""
    import requests
    from pathlib import Path

    print(f"  🧵 Threads 게시: {food_name_kr}")

    result = {"success": False, "threads_url": None, "error": None}

    # 콘텐츠 폴더 찾기
    content_folder = find_content_folder(number, food_name_en) if number else None
    if not content_folder:
        result["error"] = f"콘텐츠 폴더 없음: {food_name_en}"
        return result

    insta_folder = content_folder / "01_Insta&Thread"
    if not insta_folder.exists():
        insta_folder = content_folder

    # 이미지 파일 찾기
    image_files = []
    image_patterns = ["Common_01_Cover*", "Common_02_Food*", "Common_03_DogWithFood*", "Common_09_Cta*"]
    for pattern in image_patterns:
        for img in insta_folder.glob(pattern):
            if img.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                image_files.append(img)
                break

    if len(image_files) < 4:
        result["error"] = f"이미지 부족: {len(image_files)}/4"
        return result

    # 쓰레드 캡션: 인스타 캡션(한국어) 기반 변환 — v11 규칙
    # Thread_Caption.txt (영어) 사용 금지
    raw_caption = ""
    for caption_file in insta_folder.glob("*_Insta_Caption.txt"):
        with open(caption_file, 'r', encoding='utf-8') as f:
            raw_caption = f.read().strip()
        break

    if not raw_caption:
        result["error"] = "캡션 파일 없음"
        return result

    # 영어 제거 + 해시태그 축소
    caption = convert_to_thread_caption(raw_caption)
    print(f"    ✅ 쓰레드 캡션 변환 완료 (영어 제거 + 해시태그 축소)")

    # Cloudinary 업로드
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )

    image_urls = []
    for i, img in enumerate(image_files):
        upload_result = cloudinary.uploader.upload(
            str(img),
            folder=f'sunshine/{food_name_en}',
            public_id=f'{food_name_en}_threads_{i:02d}',
            overwrite=True,
            resource_type='image'
        )
        image_urls.append(upload_result['secure_url'])

    # Threads 게시
    threads_user_id = os.environ.get('THREADS_USER_ID')
    threads_token = os.environ.get('THREADS_ACCESS_TOKEN')

    if not threads_user_id or not threads_token:
        result["error"] = "Threads 토큰 미설정"
        return result

    threads_base = 'https://graph.threads.net/v1.0'
    try:
        media_ids = []
        for i, url in enumerate(image_urls):
            resp = requests.post(
                f'{threads_base}/{threads_user_id}/threads',
                data={'media_type': 'IMAGE', 'image_url': url, 'access_token': threads_token},
                timeout=30
            )
            data = resp.json()
            if 'id' in data:
                media_ids.append(data['id'])
            time.sleep(1)

        if len(media_ids) == 4:
            resp = requests.post(
                f'{threads_base}/{threads_user_id}/threads',
                data={
                    'media_type': 'CAROUSEL',
                    'children': ','.join(media_ids),
                    'text': caption,
                    'access_token': threads_token
                },
                timeout=30
            )
            data = resp.json()
            if 'id' in data:
                carousel_id = data['id']
                time.sleep(3)
                resp = requests.post(
                    f'{threads_base}/{threads_user_id}/threads_publish',
                    data={'creation_id': carousel_id, 'access_token': threads_token},
                    timeout=30
                )
                pub_data = resp.json()
                if 'id' in pub_data:
                    result["success"] = True
                    result["threads_url"] = f"https://threads.net/t/{pub_data['id']}"
                    print(f"  ✅ Threads 게시 완료: {pub_data['id']}")
                    return result

        result["error"] = "Threads 캐러셀 생성 실패"
    except Exception as e:
        result["error"] = f"Threads 오류: {str(e)}"

    return result


# ============================================================
# 엔트리포인트
# ============================================================

if __name__ == "__main__":
    load_env()
    
    print("=" * 60)
    print("🌞 Project Sunshine — 노션 컨트롤타워 워커")
    print(f"   폴링 간격: {POLL_INTERVAL}초")
    print(f"   시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    sync = NotionSync()
    
    if not sync.client:
        print("\n⚠️ Notion API 미설정 — 설정 후 다시 실행하세요")
        sys.exit(1)
    
    run_once = "--once" in sys.argv
    
    try:
        worker_loop(sync, run_once=run_once)
    except KeyboardInterrupt:
        print("\n\n🛑 워커 중지 (Ctrl+C)")
    except Exception as e:
        send_telegram(f"🚨 워커 비정상 종료: {e}")
        raise
