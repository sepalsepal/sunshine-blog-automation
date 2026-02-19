import random

def get_todays_food_topic():
    """
    오늘의 음식 주제와 AI 이미지 생성용 상세 프롬프트를 반환합니다.
    """
    print("🍽️ [Food Manager] 오늘의 먹거리 주제 선정 중...")
    
    # [푸드 데이터베이스]
    # 형식: "음식명": {"상태": "안전/주의/위험", "프롬프트": "구체적 묘사"}
    food_db = {
        "고구마": {
            "status": "safe",
            "prompt": "steamed sweet potato with golden yellow flesh, slightly cracked open, steam rising, rustic style"
        },
        "당근": {
            "status": "safe",
            "prompt": "fresh raw carrot with green leaves attached, washed, vibrant orange color, water droplets, farm-to-table style"
        },
        "사과": {
            "status": "safe",
            "prompt": "crisp red apple sliced into wedges, with skin, on a wooden cutting board, fresh and juicy"
        },
        "계란 노른자": {
            "status": "safe",
            "prompt": "boiled egg yolk, crumbled, bright yellow, soft texture, in a small ceramic bowl"
        },
        "황태": {
            "status": "safe",
            "prompt": "dried pollack strips (hwangtae), fluffy texture, light beige color, piled naturally, traditional Korean ingredient"
        },
        "포도": {
            "status": "danger",
            "prompt": "bunch of fresh purple grapes with natural bloom, on a vine, glistening with water"
        },
        "초콜릿": {
            "status": "danger",
            "prompt": "dark chocolate bar broken into pieces, rich cocoa texture, next to cocoa beans"
        }
    }
    
    # 랜덤 선택
    food_key = random.choice(list(food_db.keys()))
    food_info = food_db[food_key]
    
    # 주제 및 프롬프트 생성
    topic = f"강아지, {food_key} 먹어도 되나요?"
    prompt = food_info["prompt"]
    
    print(f"   ✅ 선정된 주제: {topic} (프롬프트: {prompt})")
    
    # 주제 문자열과 상세 프롬프트를 튜플로 반환
    return topic, prompt
