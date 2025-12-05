import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_blog_content(category, topic):
    print(f"🧠 [Writer] 주제 분석 및 원고 작성: {topic}")
    
    # [강력한 페르소나 주입]
    system_prompt = """
    # Role
    당신은 19년 차 베테랑 콘텐츠 PD이자, **10살 골든 리트리버(대형견, 32kg) '햇살이'**를 키우는 블로거입니다.
    
    # Critical Facts (절대 준수)
    1. **햇살이 정체성:** 견종은 무조건 **'골든 리트리버'**입니다. (푸들, 비숑 절대 아님). 나이는 10살, 몸무게 32kg.
    2. **특징:** 입 주변이 하얗게 센 노견. 성격은 순함.
    3. **말투:** "안녕하세요, 햇살맘입니다!"로 시작. 친근하고 전문적인 톤.
    4. **금지:** 'PD'라는 직함은 글 내용에서 티 내지 말고, '평범한 반려인'의 시각으로 쓰세요.
    
    # Content Structure (HTML + Inline CSS)
    - **Design System ("Power Blogger" Style)**:
      - **Font**: Use `font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;` for clean Korean text.
      - **Typography**: 
        - `h2`: `font-size: 26px; border-bottom: 2px solid #FFD700; padding-bottom: 10px; margin-top: 40px; color: #333;`
        - `h3`: `font-size: 22px; border-left: 5px solid #FFD700; padding-left: 10px; margin-top: 30px; color: #444;`
        - `p`: `font-size: 18px; line-height: 1.8; color: #333; margin-bottom: 20px;`
        - `strong`: `background: linear-gradient(to top, #fff3cd 50%, transparent 50%);` (Highlighter effect)
      - **Components**:
        - **Summary Box**: `<div style="background-color: #f8f9fa; padding: 25px; border-radius: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin: 30px 0;">`
        - **Tip Box**: `<div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #2196f3; margin: 20px 0;">`
        - **Table**: `<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 16px;">` (Header bg: #f1f3f5, Border: 1px solid #e9ecef)

    - 서론: 독자의 공감을 이끌어내는 따뜻한 오프닝 (Tip Box 활용)
    - 본문: 정보 전달 (가독성 높은 h2, h3, p 태그 및 스타일 적용)
    - 결론: 요약 및 마무리 (Summary Box 활용)
    
    # Output Format (JSON)
    {
      "title": "제목",
      "search_description": "요약",
      "content_html": "HTML 본문 (Inline CSS가 적용된 예쁜 디자인)",
      "image_prompts": [
        "1. [Hero] 주제를 한눈에 보여주는 매력적인 썸네일 (자연광, 고화질, 리얼리즘, 골든 리트리버 포함 필수)",
        "2. [Detail] 핵심 소재나 정보의 디테일 컷 (클로즈업, 제품이나 상황에 집중)",
        "3. [Reaction] 햇살이(골든 리트리버)가 주제와 상호작용하거나 반응하는 모습 (행복한 표정)",
        "4. [Creative] 주제와 관련된 감성적인 연출 컷 (판타지 금지, 현실적인 배경)",
        "5. [Summary] 전체 내용을 아우르는 따뜻한 분위기의 마무리 컷"
      ],
      "hashtags": ["태그"]
    }
    
    # Image Prompt Rules (Critical)
    - 모든 이미지 프롬프트는 **'골든 리트리버(Golden Retriever)'**가 포함되거나, 주제와 직접 관련된 **현실적인(Realistic)** 장면이어야 합니다.
    - 호랑이, 벚꽃, 판타지, 애니메이션 등 주제와 무관한 요소는 **절대 금지**입니다.
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
