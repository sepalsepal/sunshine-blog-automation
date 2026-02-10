import datetime
import random

def get_weather_vibe(location="Seoul, Yongsan-gu"):
    """
    [펫시터 모드] 
    실제 산책 시간인 '오전 7시'와 '오후 4시'의 조명과 분위기만 시뮬레이션합니다.
    """
    # 랜덤하게 아침(7시) 또는 오후(4시) 선택
    target_hour = random.choice([7, 16])
    
    # 1. 시간대별 조명 (Lighting)
    if target_hour == 7:
        time_prompt = "7:00 AM morning, soft sunrise, golden hour, morning mist, long shadows"
        time_desc = "오전 7시 (아침 산책)"
    else: # 16시
        time_prompt = "4:00 PM afternoon, warm daylight, sun starting to lower, cozy atmosphere"
        time_desc = "오후 4시 (오후 산책)"

    # 2. 계절/날씨 (겨울 고정)
    weather_conditions = [
        {"type": "Clear", "prompt": "clear blue sky, crisp winter air", "desc": "맑음"},
        {"type": "Cloudy", "prompt": "cloudy sky, soft diffused light", "desc": "흐림"},
        {"type": "Snow", "prompt": "light snow on ground, winter vibe", "desc": "눈 쌓임"}
    ]
    current_weather = random.choice(weather_conditions)
    
    return {
        "description": f"{time_desc}, {current_weather['desc']}",
        "prompt_suffix": f", {time_prompt}, {current_weather['prompt']}, winter season"
    }