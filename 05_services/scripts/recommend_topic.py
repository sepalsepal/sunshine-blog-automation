#!/usr/bin/env python3
"""
Project Sunshine - 주제 추천 자동화
Cloudinary에서 기존 폴더 검색 → Gemini로 새 주제 추천

사용법: python recommend_topic.py
"""

import google.generativeai as genai
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import os

# ========== API 설정 (환경변수에서 로드) ==========
# Cloudinary
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

# Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 환경변수 검증
if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, GEMINI_API_KEY]):
    raise ValueError("필수 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

genai.configure(api_key=GEMINI_API_KEY)


def get_existing_topics():
    """
    Cloudinary에서 기존 폴더(=완료된 주제) 목록 가져오기
    """
    print("\n🔍 Cloudinary에서 기존 주제 검색 중...")
    
    url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/folders"
    
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)
        )
        
        if response.status_code == 200:
            data = response.json()
            folders = [folder['name'] for folder in data.get('folders', [])]
            print(f"✅ 기존 주제 {len(folders)}개 발견: {folders}")
            return folders
        else:
            print(f"⚠️ Cloudinary API 응답: {response.status_code}")
            # 폴더 API 실패 시 리소스에서 asset_folder 추출
            return get_existing_topics_from_resources()
            
    except Exception as e:
        print(f"❌ Cloudinary 연결 실패: {str(e)}")
        return get_existing_topics_from_resources()


def get_existing_topics_from_resources():
    """
    폴더 API 실패 시 리소스에서 asset_folder 추출
    """
    print("🔄 리소스에서 폴더 정보 추출 중...")
    
    url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/resources/image"
    
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET),
            params={"max_results": 500}
        )
        
        if response.status_code == 200:
            data = response.json()
            resources = data.get('resources', [])
            
            # asset_folder 추출 (중복 제거)
            folders = set()
            for resource in resources:
                folder = resource.get('asset_folder', '')
                if folder:
                    folders.add(folder)
            
            folders = list(folders)
            print(f"✅ 기존 주제 {len(folders)}개 발견: {folders}")
            return folders
        else:
            print(f"❌ API 실패: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ 에러: {str(e)}")
        return []


def translate_folder_to_korean(folder_name):
    """
    폴더명(영어)을 한글로 변환
    """
    translations = {
        'carrot': '당근',
        'sweet_potato': '고구마',
        'watermelon': '수박',
        'cherry': '체리',
        'broccoli': '브로콜리',
        'banana': '바나나',
        'apple': '사과',
        'grape': '포도',
        'pumpkin': '단호박',
        'chicken': '닭가슴살',
        'blueberry': '블루베리',
        'strawberry': '딸기',
        'cucumber': '오이',
        'spinach': '시금치',
        'egg': '계란',
        'salmon': '연어',
        'potato': '감자',
        'tomato': '토마토',
        'pear': '배',
        'orange': '귤',
        'mandarin': '귤',
        'persimmon': '감',
        'cabbage': '양배추',
        'lettuce': '상추',
        'zucchini': '애호박',
        'peanut': '땅콩',
        'cheese': '치즈',
        'yogurt': '요거트',
    }
    return translations.get(folder_name.lower(), folder_name)


def recommend_topics(existing_folders):
    """
    Gemini API로 새 주제 추천
    """
    print("\n🤖 Gemini에게 새 주제 추천 요청 중...")
    
    # 기존 폴더명을 한글로 변환
    existing_korean = [translate_folder_to_korean(f) for f in existing_folders]
    
    # 현재 날짜/계절 정보
    now = datetime.now()
    month = now.month
    
    if month in [12, 1, 2]:
        season = "겨울"
        season_foods = "귤, 고구마, 배, 사과, 땅콩, 치즈"
    elif month in [3, 4, 5]:
        season = "봄"
        season_foods = "딸기, 상추, 시금치, 양배추, 브로콜리"
    elif month in [6, 7, 8]:
        season = "여름"
        season_foods = "수박, 참외, 오이, 블루베리, 토마토"
    else:
        season = "가을"
        season_foods = "사과, 배, 감, 단호박, 고구마"
    
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
    
    prompt = f"""
당신은 강아지 음식 콘텐츠 기획자입니다.

## 현재 상황
- 날짜: {now.strftime('%Y년 %m월 %d일')}
- 계절: {season}
- 제철 음식: {season_foods}

## 이미 제작 완료된 주제 (제외해야 함)
{existing_korean}

## 요청
강아지에게 먹여도 되는/안 되는 음식 중에서 새로운 콘텐츠 주제 3개를 추천해주세요.

## 추천 기준
1. 계절/제철에 맞는 음식 우선
2. 반려인들이 궁금해할 만한 음식
3. 위험한 음식(포도, 양파 등)도 포함 가능 (경고 콘텐츠)
4. 이미 제작된 주제는 절대 추천하지 마세요

## 출력 형식 (JSON)
```json
{{
  "recommendations": [
    {{
      "korean": "음식명(한글)",
      "english": "음식명(영어, 폴더명용, 소문자, 언더스코어)",
      "can_eat": true/false,
      "reason": "추천 이유 (1줄)",
      "season_match": "제철/비제철/무관"
    }},
    ...
  ]
}}
```

JSON만 출력하세요. 다른 설명 없이.
"""
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # JSON 파싱
        # ```json 제거
        content = content.replace('```json', '').replace('```', '').strip()
        data = json.loads(content)
        
        return data.get('recommendations', [])
        
    except Exception as e:
        print(f"❌ Gemini API 에러: {str(e)}")
        return []


def display_recommendations(recommendations, existing_folders):
    """
    추천 결과 출력
    """
    existing_korean = [translate_folder_to_korean(f) for f in existing_folders]
    
    print("\n" + "=" * 60)
    print("🎯 이번 주 추천 주제")
    print("=" * 60)
    
    now = datetime.now()
    print(f"📅 {now.strftime('%Y년 %m월 %d일')}")
    print(f"❄️ 계절: 겨울\n")
    
    for idx, rec in enumerate(recommendations, 1):
        can_eat = "⭕ 먹어도 됨" if rec.get('can_eat', True) else "❌ 위험"
        season = rec.get('season_match', '무관')
        
        print(f"{idx}. {rec['korean']} ({rec['english']})")
        print(f"   {can_eat} | {season}")
        print(f"   💡 {rec['reason']}")
        print()
    
    print("-" * 60)
    print(f"🚫 제외된 주제 ({len(existing_korean)}개):")
    print(f"   {', '.join(existing_korean)}")
    print("-" * 60)
    
    print("\n📋 사용법:")
    if recommendations:
        first = recommendations[0]
        print(f"   python kim_chajang_gemini.py --food {first['korean']} --number XX")
        print(f"   python upload_to_cloudinary.py --folder {first['english']} --path ./images/{first['english']}/")
    
    print()


def main():
    print("=" * 60)
    print("🌟 Project Sunshine - 주제 추천 시스템")
    print("=" * 60)
    
    # 1. 기존 주제 검색
    existing_folders = get_existing_topics()
    
    # 2. 새 주제 추천
    recommendations = recommend_topics(existing_folders)
    
    # 3. 결과 출력
    if recommendations:
        display_recommendations(recommendations, existing_folders)
    else:
        print("❌ 추천 생성 실패. 다시 시도해주세요.")


if __name__ == "__main__":
    main()
