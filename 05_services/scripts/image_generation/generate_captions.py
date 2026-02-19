#!/usr/bin/env python3
"""
캡션 분리 스크립트
- 기존 caption.txt → caption_instagram.txt + caption_threads.txt 생성
"""

import random
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
IMAGES_DIR = ROOT / "content" / "images"

# 토픽별 한글명
TOPIC_KR = {
    "pumpkin": "호박", "blueberries": "블루베리", "carrot": "당근",
    "apple": "사과", "sweet_potato": "고구마", "cherries": "체리",
    "pineapple": "파인애플", "watermelon": "수박", "banana": "바나나",
    "broccoli": "브로콜리", "strawberry": "딸기", "mango": "망고",
    "orange": "오렌지", "pear": "배", "kiwi": "키위", "papaya": "파파야",
    "peach": "복숭아", "rice": "흰쌀밥", "cucumber": "오이",
    "pringles": "프링글스", "sausage": "소시지", "avocado": "아보카도",
    "coca_cola": "코카콜라", "olive": "올리브", "grape": "포도",
    "spinach": "시금치", "zucchini": "애호박", "pasta": "파스타",
    "chicken": "닭고기", "salmon": "연어", "tofu": "두부",
    "boiled_egg": "삶은달걀", "mackerel": "고등어", "yogurt": "요거트",
    "tuna": "참치", "potato": "감자", "chocolate": "초콜릿", "cake": "케이크",
}


def convert_to_threads(caption: str, topic_kr: str) -> str:
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

    # 핵심 정보 추출
    for line in lines:
        if any(m in line for m in ['풍부', '좋', '주의', '적정', '비타민', '수분', '칼로리', '단백질']):
            clean = line.replace('•', '').replace('✅', '').replace('⚠️', '').replace('💚', '').strip()
            if 10 < len(clean) < 60:
                core_info = clean
                break

    if not core_info:
        for line in lines[1:5]:
            if 15 < len(line) < 60 and '정답' not in line and '#' not in line:
                core_info = line.replace('•', '').strip()
                break

    # 반말로 변환
    for f, c in [("입니다", "야"), ("합니다", "해"), ("됩니다", "돼"), ("좋아요", "좋아"), ("에요", "야"), ("해요", "해")]:
        core_info = core_info.replace(f, c)

    hook = random.choice(hooks)
    cta = random.choice(ctas)

    return f"{hook}\n\n{core_info}\n\n{cta}" if core_info else f"{hook}\n\n{cta}"


def process_folder(folder_path: Path):
    """폴더 내 캡션 처리"""
    caption_file = folder_path / "caption.txt"

    if not caption_file.exists():
        return None

    # 토픽 추출
    folder_name = folder_path.name
    topic = None
    for t in TOPIC_KR.keys():
        if t in folder_name.lower():
            topic = t
            break

    if not topic:
        # 폴더명에서 영문명 추출 시도
        parts = folder_name.split('_')
        for part in parts:
            if part.lower() in TOPIC_KR:
                topic = part.lower()
                break

    if not topic:
        print(f"  ⚠️ 토픽 추출 실패: {folder_name}")
        return None

    topic_kr = TOPIC_KR.get(topic, topic)

    # 캡션 읽기
    caption = caption_file.read_text(encoding='utf-8')

    # Instagram 캡션 저장 (기존 caption.txt 복사)
    instagram_file = folder_path / "caption_instagram.txt"
    instagram_file.write_text(caption, encoding='utf-8')

    # Threads 캡션 생성 및 저장
    threads_caption = convert_to_threads(caption, topic_kr)
    threads_file = folder_path / "caption_threads.txt"
    threads_file.write_text(threads_caption, encoding='utf-8')

    return {
        "topic": topic,
        "topic_kr": topic_kr,
        "instagram": len(caption),
        "threads": len(threads_caption)
    }


def main():
    print("=" * 60)
    print("📝 캡션 분리 생성 (Instagram + Threads)")
    print("=" * 60)

    # 콘텐츠 폴더 찾기
    folders = sorted(IMAGES_DIR.glob("0[0-9][0-9]_*"))

    results = []
    for folder in folders:
        if not folder.is_dir():
            continue
        if "000_cover" in folder.name:
            continue

        print(f"\n📁 {folder.name}")
        result = process_folder(folder)

        if result:
            print(f"  ✅ {result['topic_kr']} ({result['topic']})")
            print(f"     Instagram: {result['instagram']}자")
            print(f"     Threads: {result['threads']}자")
            results.append(result)
        else:
            print(f"  ⏭️ 스킵 (캡션 없음)")

    print("\n" + "=" * 60)
    print(f"✨ 완료! {len(results)}개 폴더 처리")
    print("=" * 60)


if __name__ == "__main__":
    main()
