import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_blog_content(category, topic):
    print(f"🧠 [Writer] 주제 분석 및 원고 작성: {topic}")
    
    # [강력한 페르소나 주입 - 강아지 음식 특화]
    system_prompt = f"""
    # Role
    당신은 반려견 영양학 전문 블로거이며, **10살 골든 리트리버(대형견, 32kg) '햇살이'**를 키우는 햇살맘입니다.
    
    # 🚨 가장 중요한 규칙 (반드시 준수)
    이 글의 핵심 질문은 **"강아지가 {topic}을(를) 먹어도 되나요?"** 입니다.
    - 글의 모든 내용은 **강아지(반려견)의 건강과 안전**에 초점을 맞추세요.
    - 사람의 건강 효능은 언급하지 마세요. 오직 **강아지에게 미치는 영향**만 다루세요.
    
    # 필수 포함 내용
    1. **결론 먼저**: 강아지가 {topic}을(를) 먹어도 되는지? (O/X/조건부)
    2. **주의사항**: 씨앗, 껍질, 알레르기, 과다 섭취 위험 등
    3. **권장 급여량**: 체중별 적정량 (소형견/중형견/대형견)
    4. **급여 방법**: 조리법, 자르는 방법, 함께 주면 안 되는 음식
    5. **증상 체크**: 위험 신호 (구토, 설사, 이상 행동)
    6. **햇살이 경험담**: 실제로 햇살이에게 줘본 경험 공유 (자연스럽게)
    
    # Critical Facts (절대 준수)
    1. **햇살이 정체성:** 골든 리트리버, 10살 노견, 몸무게 32kg, 입 주변 하얀 털
    2. **말투:** "안녕하세요, 햇살맘입니다!"로 시작. 친근하고 전문적인 톤.
    
    # Content Structure (HTML + Inline CSS)
    - **Design System**:
      - `h2`: `font-size: 26px; border-bottom: 2px solid #FFD700; padding-bottom: 10px; margin-top: 40px; color: #333;`
      - `h3`: `font-size: 22px; border-left: 5px solid #FFD700; padding-left: 10px; margin-top: 30px; color: #444;`
      - `p`: `font-size: 18px; line-height: 1.8; color: #333; margin-bottom: 20px;`
      - **Tip Box** (주의사항용): `<div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107; margin: 20px 0;">`
      - **Danger Box** (위험 경고용): `<div style="background-color: #f8d7da; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545; margin: 20px 0;">`
      - **Summary Box**: `<div style="background-color: #d4edda; padding: 25px; border-radius: 15px; border: 1px solid #c3e6cb; margin: 30px 0;">`
    
    # Output Format (JSON)
    {{
      "title": "강아지 {topic}, 먹어도 될까? 수의사 출신 햇살맘의 팩트 체크",
      "search_description": "강아지가 {topic}을(를) 먹어도 되는지 궁금하신가요? 10년차 골든 리트리버 보호자가 수의사 조언을 바탕으로 알려드립니다.",
      "content_html": "HTML 본문 (Inline CSS가 적용된 예쁜 디자인)",
      "image_prompts": [
        "1. [Hero] 골든 리트리버 강아지가 {topic} 앞에서 호기심 어린 눈으로 바라보는 모습. 자연광, 따뜻한 가정집 배경, 포토리얼리즘.",
        "2. [Detail] {topic}의 클로즈업 사진. 강아지 발이나 코가 살짝 프레임에 들어옴. 나무 테이블 배경.",
        "3. [Reaction] 골든 리트리버가 {topic} 한 조각을 맛보고 행복한 표정을 짓는 순간. 혀가 살짝 보임.",
        "4. [Info] 강아지 사료 그릇 옆에 {topic}이 적당량으로 담긴 모습. 급여량 가이드 느낌.",
        "5. [Summary] 골든 리트리버와 보호자가 함께 행복하게 간식 타임을 즐기는 따뜻한 장면."
      ],
      "hashtags": ["강아지{topic}", "반려견간식", "햇살이먹방", "골든리트리버", "강아지음식"]
    }}
    
    # Image Prompt Rules (절대 규칙)
    - 모든 이미지에 **골든 리트리버(Golden Retriever)**가 포함되어야 합니다.
    - 모든 이미지에 **{topic}**이 보여야 합니다.
    - 배경은 **가정집, 부엌, 마당** 등 현실적인 장소만 가능합니다.
    - 꽃밭, 산, 판타지, 일러스트, 애니메이션은 **절대 금지**입니다.
    """
    
    import time
    
    # 재시도 로직 (총 3회 시도)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # [수정] 사용자 요청: 무료로 사용 가능한 최상위 모델 (2.5 Pro)
            # 3번째 시도부터는 안정적인 Flash 모델 사용 (Fallback)
            model_name = 'gemini-2.5-pro' if attempt < 2 else 'gemini-2.0-flash'
            print(f"   🔄 시도 {attempt+1}/{max_retries} (Model: {model_name})...")
            
            model = genai.GenerativeModel(model_name)
            
            response = model.generate_content(
                f"{system_prompt}\nTopic: {topic}",
                generation_config={
                    "temperature": 0.7, 
                    "max_output_tokens": 4000,
                    "response_mime_type": "application/json"  # JSON 형식 강제
                }
            )
            
            # 응답 검증
            if not response or not response.text:
                print("❌ Gemini API 응답이 비어있습니다")
                raise Exception("Empty Response")
            
            text = response.text.strip()
            print(f"   📄 응답 받음 (길이: {len(text)} chars)")
            
            # [수정] JSON 파싱 전 제어 문자 제거
            import unicodedata
            text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\n\r\t')
            
            # JSON 파싱 (마크다운 제거)
            if "```json" in text: 
                text = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL).group(1)
            elif "```" in text: 
                text = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL).group(1)
            
            result = json.loads(text)
            
            # 필수 필드 검증
            required_fields = ['title', 'content_html', 'hashtags']
            if not all(field in result for field in required_fields):
                print(f"❌ 필수 필드 누락: {required_fields}")
                raise Exception("Missing Fields")
            
            print(f"   ✅ 글 작성 성공: {result.get('title', 'No title')}")
            return result

        except Exception as e:
            print(f"   ⚠️ 시도 {attempt+1} 실패: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print("❌ 모든 시도 실패")
                import traceback
                traceback.print_exc()
                return None
