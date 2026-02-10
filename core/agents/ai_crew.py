# 🤖 Project Sunshine AI Crew
# Gemini API 기반 에이전트 시스템
#
# 사용법:
#   python ai_crew.py peach        # 특정 주제로 콘텐츠 생성
#   python ai_crew.py --auto       # 자동 주제 선정 + 콘텐츠 생성
#
# 파이프라인:
#   정분석(히스토리) → 이리서치(트렌드) → 김차장(선정+기획)
#   → 최검증(팩트체크) → 김작가(텍스트) → 박과장(검수) → 이카피(캡션)

import google.generativeai as genai
import json
import sys
import os
from datetime import datetime

# ============================================================
# 🔑 API 설정 (환경변수에서 로드)
# ============================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
genai.configure(api_key=GEMINI_API_KEY)

# 모델 설정 (2.0 Flash = 최신, 무료)
model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config={
        'temperature': 0.7,  # 창의성 조절 (0=보수적, 1=창의적)
        'max_output_tokens': 1024,
    }
)

# ============================================================
# 👥 에이전트 페르소나 정의
# ============================================================

AGENTS = {
    "정분석": {
        "role": "히스토리 체크",
        "prompt": """당신은 '정분석'입니다. Project Sunshine의 데이터 분석 담당자입니다.

역할:
- 기존 게시된 콘텐츠 히스토리 분석
- 중복 주제 필터링
- 게시 간격 확인 (같은 주제 최소 30일 간격)

분석 항목:
1. 이미 게시된 주제인가?
2. 마지막 게시일로부터 며칠 경과했는가?
3. 블랙리스트(독성 음식)에 포함되어 있는가?

출력 형식 (JSON):
{
    "already_published": ["주제1", "주제2"],
    "blacklist": ["포도", "초콜릿", "양파"],
    "available_gap_days": 30,
    "recommendation": "새 주제 선정 가능"
}
"""
    },

    "이리서치": {
        "role": "트렌드 조사",
        "prompt": """당신은 '이리서치'입니다. Project Sunshine의 트렌드 리서처입니다.

역할:
- 최신 반려견 식품 트렌드 조사
- 계절별 추천 음식 제안
- SNS 인기 키워드 분석

조사 기준:
1. 계절 적합성 (현재 계절에 맞는 음식)
2. SNS 화제성 (인스타그램, 유튜브 트렌드)
3. 영양학적 가치
4. 사진 촬영 용이성 (비주얼)

출력 형식 (JSON):
{
    "season": "겨울",
    "trending_foods": [
        {"food": "음식명", "food_en": "english", "reason": "추천 이유", "score": 85},
        ...
    ],
    "top_3_recommendation": ["1순위", "2순위", "3순위"]
}
"""
    },

    "김차장": {
        "role": "음식 선정 + 콘텐츠 기획",
        "prompt": """당신은 '김차장'입니다. Project Sunshine의 콘텐츠 기획 담당자입니다.

역할:
- 후보 음식 중 최종 주제 선정
- 강아지 음식 정보 콘텐츠 기획
- 4장 캐러셀 구성 설계
- 핵심 메시지 도출

선정 기준:
1. 기존에 다루지 않은 주제
2. 트렌드 점수 높은 음식
3. 햇살이(골든리트리버)와 어울리는 비주얼
4. 계절 적합성

성격:
- 체계적이고 논리적
- 반려견 영양학에 대한 전문 지식
- 간결하고 명확한 커뮤니케이션

★ 표지 타이틀 규칙 (필수):
- 반드시 영문 대문자 1단어만 (예: PEACH, APPLE, BANANA)
- 긴 문장이나 설명 절대 금지
- 음식명을 영어로 대문자 변환하여 사용

출력 형식 (JSON):
{
    "selected_topic": "선택한 음식",
    "selected_topic_en": "FOOD",
    "selection_reason": "선정 이유",
    "topic": "주제명",
    "slides": [
        {"slide": 1, "type": "cover", "title": "FOOD"},
        {"slide": 2, "type": "main", "main_text": "메인 텍스트", "sub_text": "서브 텍스트"},
        {"slide": 3, "type": "benefit", "main_text": "효능", "sub_text": "설명"},
        {"slide": 4, "type": "caution", "main_text": "주의사항", "sub_text": "설명"}
    ]
}
"""
    },
    
    "김작가": {
        "role": "텍스트 생성",
        "prompt": """당신은 '김작가'입니다. Project Sunshine의 텍스트 작성 담당자입니다.

역할:
- 강아지 음식 정보를 친근하고 이해하기 쉽게 작성
- 인스타그램에 적합한 짧고 임팩트 있는 문구
- 이모지 적절히 활용

스타일:
- 친근하고 따뜻한 톤
- 반말체 ("~해요!", "~이에요!")
- 핵심 정보만 간결하게

★ 글자수 규칙 (필수):
- 메인 텍스트: 반드시 10자 이내 (이모지 포함)
- 서브 텍스트: 반드시 15자 이내 (이모지 포함)
- 초과시 잘라서 맞추기

금지:
- 의학적 단정 표현 (무조건, 반드시, 절대)
- 부정확한 정보
"""
    },
    
    "최검증": {
        "role": "팩트체크",
        "prompt": """당신은 '최검증'입니다. Project Sunshine의 팩트체크 담당자입니다.

역할:
- 강아지 음식 정보의 정확성 검증
- 위험한 정보 필터링
- 수의학적 근거 확인

검증 항목:
1. 해당 음식이 강아지에게 안전한가?
2. 효능 설명이 과장되지 않았는가?
3. 주의사항이 충분히 안내되었는가?
4. 급여량/빈도 정보가 적절한가?

출력 형식 (JSON):
{
    "verified": true/false,
    "issues": ["이슈1", "이슈2"],
    "suggestions": ["수정제안1", "수정제안2"]
}
"""
    },
    
    "박과장": {
        "role": "품질 검수",
        "prompt": """당신은 '박과장'입니다. Project Sunshine의 품질 검수 담당자입니다.

역할:
- 콘텐츠 품질 최종 검수
- 브랜드 톤앤매너 일관성 확인
- 오탈자 및 문법 검사

검수 기준:
1. 텍스트 길이 적절한가? (메인 10자, 서브 15자 이내)
2. 이모지 사용이 적절한가?
3. 톤앤매너가 친근한가?
4. 기존 게시물과 일관성 있는가?

출력 형식 (JSON):
{
    "score": 0-100,
    "passed": true/false,
    "feedback": ["피드백1", "피드백2"]
}
"""
    },
    
    "이카피": {
        "role": "캡션 작성",
        "prompt": """당신은 '이카피'입니다. Project Sunshine의 인스타그램 캡션 작성 담당자입니다.

역할:
- 인스타그램 게시물 캡션 작성
- 해시태그 5개 선정 (2026년 인스타그램 정책)
- CTA(Call To Action) 포함

스타일:
- 친근하고 정보성 있는 톤
- 이모지로 시선 끌기
- 저장/공유 유도 문구

출력 형식:
{
    "caption": "캡션 본문",
    "hashtags": ["해시태그1", "해시태그2", "해시태그3", "해시태그4", "해시태그5"]
}
"""
    }
}

# ============================================================
# 🔧 에이전트 호출 함수
# ============================================================

def call_agent(agent_name: str, task: str) -> str:
    """에이전트 호출"""
    agent = AGENTS[agent_name]
    
    full_prompt = f"""{agent['prompt']}

---
작업 요청:
{task}
"""
    
    print(f"\n🤖 [{agent_name}] 작업 중... ({agent['role']})")
    
    response = model.generate_content(full_prompt)
    result = response.text
    
    print(f"✅ [{agent_name}] 완료")
    
    return result


def parse_json(text: str) -> dict:
    """JSON 파싱 (마크다운 코드블록 제거)"""
    # ```json ... ``` 제거
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    return json.loads(text.strip())


def load_history() -> dict:
    """게시 히스토리 로드"""
    history_path = os.path.join(
        os.path.dirname(__file__),
        "../../config/data/published_topics.json"
    )

    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"published": [], "blacklist": []}


def get_published_topics() -> list:
    """게시된 주제 목록 반환"""
    history = load_history()
    return [item["topic"] for item in history.get("published", [])]


def get_blacklist() -> list:
    """블랙리스트(독성 음식) 반환"""
    history = load_history()
    return [item["topic"] for item in history.get("blacklist", [])]


def add_to_history(topic: str, topic_kr: str):
    """새 주제를 히스토리에 추가"""
    history_path = os.path.join(
        os.path.dirname(__file__),
        "../../config/data/published_topics.json"
    )

    history = load_history()
    history["published"].append({
        "topic": topic,
        "topic_kr": topic_kr,
        "published_date": datetime.now().strftime("%Y-%m-%d"),
        "instagram_url": None,
        "performance": None
    })
    history["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ============================================================
# 🚀 메인 파이프라인
# ============================================================

def run_auto_pipeline():
    """자동 주제 선정 + 콘텐츠 생성 파이프라인"""

    print("=" * 60)
    print(f"🌟 Project Sunshine AI Crew - AUTO MODE")
    print(f"⏰ 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    # ----------------------------------------
    # Step 0: 정분석 - 히스토리 체크
    # ----------------------------------------
    published = get_published_topics()
    blacklist = get_blacklist()

    history_info = f"""
기존 게시된 주제 ({len(published)}개):
{', '.join(published)}

블랙리스트 (독성 음식):
{', '.join(blacklist)}
"""

    history_result = call_agent("정분석", f"""
아래 히스토리를 분석해주세요.

{history_info}

분석 후 JSON 형식으로 출력해주세요.
""")

    try:
        results["history"] = parse_json(history_result)
    except:
        results["history_raw"] = history_result

    # ----------------------------------------
    # Step 1: 이리서치 - 트렌드 조사
    # ----------------------------------------
    current_month = datetime.now().month
    season = "겨울" if current_month in [12, 1, 2] else \
             "봄" if current_month in [3, 4, 5] else \
             "여름" if current_month in [6, 7, 8] else "가을"

    trend_result = call_agent("이리서치", f"""
현재 계절: {season} ({current_month}월)

이미 다룬 주제 (제외):
{', '.join(published)}

금지 음식 (제외):
{', '.join(blacklist)}

위 조건을 고려하여, 강아지에게 좋은 트렌디한 음식 5개를 조사해주세요.
각 음식별 추천 이유와 점수(100점 만점)를 포함해주세요.

JSON 형식으로 출력해주세요.
""")

    try:
        results["trend"] = parse_json(trend_result)
    except:
        results["trend_raw"] = trend_result

    # ----------------------------------------
    # Step 2: 김차장 - 음식 선정 + 콘텐츠 기획
    # ----------------------------------------
    plan_result = call_agent("김차장", f"""
아래 트렌드 조사 결과를 바탕으로:
1. 최종 음식 1개를 선정하고
2. 4장 캐러셀 콘텐츠를 기획해주세요.

트렌드 조사 결과:
{trend_result}

이미 다룬 주제 (제외):
{', '.join(published)}

구성:
- 1장: 표지 (영문 대문자 1단어)
- 2장: 먹어도 되는지 여부 + 급여 방법
- 3장: 주요 효능 (2-3개 통합)
- 4장: 주의사항 (2-3개 통합)

JSON 형식으로 출력해주세요.
""")

    try:
        results["plan"] = parse_json(plan_result)
        selected_topic = results["plan"].get("selected_topic", "unknown")
        print(f"\n🎯 선정된 주제: {selected_topic}")
    except:
        results["plan_raw"] = plan_result
        selected_topic = "unknown"

    # 이후 기존 파이프라인 계속...
    return _continue_pipeline(results, plan_result, selected_topic)


def run_pipeline(topic: str):
    """특정 주제로 AI Crew 파이프라인 실행"""

    print("=" * 60)
    print(f"🌟 Project Sunshine AI Crew")
    print(f"📝 주제: {topic}")
    print(f"⏰ 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 중복/블랙리스트 체크
    published = get_published_topics()
    blacklist = get_blacklist()

    if topic.lower() in [p.lower() for p in published]:
        print(f"⚠️ '{topic}'은(는) 이미 게시된 주제입니다.")
        confirm = input("계속 진행하시겠습니까? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ 취소되었습니다.")
            return None

    if topic.lower() in [b.lower() for b in blacklist]:
        print(f"❌ '{topic}'은(는) 블랙리스트(독성 음식)입니다. 진행 불가.")
        return None

    results = {}

    # ----------------------------------------
    # Step 1: 김차장 - 콘텐츠 기획
    # ----------------------------------------
    plan_result = call_agent("김차장", f"""
'{topic}'에 대한 강아지 음식 정보 4장 캐러셀을 기획해주세요.

구성:
- 1장: 표지 (영문 타이틀)
- 2장: 먹어도 되는지 여부 + 급여 방법
- 3장: 주요 효능 (2-3개 통합)
- 4장: 주의사항 (2-3개 통합)

JSON 형식으로 출력해주세요.
""")
    
    try:
        results["plan"] = parse_json(plan_result)
    except:
        results["plan_raw"] = plan_result

    return _continue_pipeline(results, plan_result, topic)


def _continue_pipeline(results: dict, plan_result: str, topic: str):
    """기획 이후 파이프라인 계속 실행"""

    # ----------------------------------------
    # Step 3: 김작가 - 텍스트 다듬기
    # ----------------------------------------
    write_result = call_agent("김작가", f"""
아래 콘텐츠 기획을 바탕으로 인스타그램용 텍스트를 작성해주세요.

기획안:
{plan_result}

요구사항:
- 메인 텍스트: 10자 이내, 임팩트 있게
- 서브 텍스트: 15자 이내, 핵심 정보
- 이모지 1-2개 포함
- 반말체 사용 ("~해요!")

JSON 형식으로 출력해주세요.
""")
    
    try:
        results["text"] = parse_json(write_result)
    except:
        results["text_raw"] = write_result
    
    # ----------------------------------------
    # Step 4: 최검증 - 팩트체크
    # ----------------------------------------
    verify_result = call_agent("최검증", f"""
아래 강아지 음식 정보의 정확성을 검증해주세요.

주제: {topic}
콘텐츠:
{write_result}

검증 후 JSON 형식으로 출력해주세요.
""")
    
    try:
        results["verify"] = parse_json(verify_result)
    except:
        results["verify_raw"] = verify_result
    
    # ----------------------------------------
    # Step 5: 박과장 - 품질 검수
    # ----------------------------------------
    review_result = call_agent("박과장", f"""
아래 콘텐츠의 품질을 검수해주세요.

콘텐츠:
{write_result}

팩트체크 결과:
{verify_result}

검수 후 JSON 형식으로 출력해주세요.
""")
    
    try:
        results["review"] = parse_json(review_result)
    except:
        results["review_raw"] = review_result
    
    # ----------------------------------------
    # Step 6: 이카피 - 캡션 작성
    # ----------------------------------------
    caption_result = call_agent("이카피", f"""
아래 콘텐츠의 인스타그램 캡션과 해시태그를 작성해주세요.

주제: {topic}
콘텐츠:
{write_result}

요구사항:
- 캡션: 3-5문장, 정보성 + 친근함
- 해시태그: 정확히 5개 (2026년 인스타그램 정책)
- 저장/공유 유도 문구 포함

JSON 형식으로 출력해주세요.
""")
    
    try:
        results["caption"] = parse_json(caption_result)
    except:
        results["caption_raw"] = caption_result
    
    # ----------------------------------------
    # 결과 저장
    # ----------------------------------------
    output_file = f"{topic}_content.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ 파이프라인 완료!")
    print(f"📁 결과 파일: {output_file}")
    print("=" * 60)
    
    # 최종 텍스트 출력
    print("\n📋 최종 콘텐츠:")
    if "text" in results:
        for slide in results["text"].get("slides", []):
            print(f"  [{slide.get('slide')}] {slide.get('main_text', slide.get('title', ''))} / {slide.get('sub_text', '')}")
    
    return results


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python ai_crew.py <주제>     # 특정 주제로 콘텐츠 생성")
        print("  python ai_crew.py --auto     # 자동 주제 선정 + 콘텐츠 생성")
        print("")
        print("예시:")
        print("  python ai_crew.py peach")
        print("  python ai_crew.py --auto")
        sys.exit(1)

    if sys.argv[1] == "--auto":
        run_auto_pipeline()
    else:
        topic = sys.argv[1]
        run_pipeline(topic)
