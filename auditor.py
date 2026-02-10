import os
import json
import urllib.request
import urllib.parse
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def audit_and_improve(topic, current_draft_html):
    print(f"⚖️ [Auditor] 경쟁사 분석 및 원고 감수 시작... (주제: {topic})")

    competitor_text = _scrape_top_competitor(topic)

    if not competitor_text:
        competitor_text = "비교할 대상 없음. 자체 완성도에 집중할 것."

    print("   🥊 [Comparison] 내 글 vs 경쟁사 글 비교 분석 중...")

    audit_prompt = f"""
    당신은 악독한 블로그 편집장입니다.
    아래 두 개의 글을 비교하고, [내 글]을 보강하여 다시 작성해 주세요.

    [목표 주제] {topic}
    [경쟁사 글] {competitor_text[:1000]}...
    [내 글] {current_draft_html}

    [지시사항]
    1. 경쟁사보다 더 친근한 말투('햇살이 엄마')를 유지하세요.
    2. HTML 태그 구조를 유지하며 전체 본문을 재작성하세요.
    3. 결과는 오직 수정된 HTML 코드만 출력하세요.
    """

    try:
        # [수정] 사용자 요청: 최고 품질 감수를 위해 2.5 Pro 사용
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(audit_prompt)
        improved_html = response.text.strip()

        if "```html" in improved_html:
            improved_html = improved_html.replace("```html", "").replace("```", "")

        print("   ✅ [Upgrade] 원고 업그레이드 완료!")
        return improved_html

    except Exception as e:
        print(f"   ❌ 감수 실패: {e}")
        return current_draft_html

def _scrape_top_competitor(keyword):
    """
    네이버 블로그 API로 경쟁사 글 수집 (Selenium 제거)
    
    장점:
    - 안정적 (API라서 차단 없음)
    - 빠름 (1초 이내)
    - 클라우드 호환 (Selenium 불필요)
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("   ⚠️ [Auditor] Naver API 키 없음 - 자체 완성도 집중")
        return None
    
    try:
        encText = urllib.parse.quote(keyword)
        url = f"https://openapi.naver.com/v1/search/blog?query={encText}&display=3&sort=sim"
        
        print(f"   🔍 [Auditor] 네이버 블로그 API 검색: {keyword}")
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        response = urllib.request.urlopen(request, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        
        # 상위 3개 블로그 글의 제목+설명 결합
        competitor_text = ""
        for item in data.get('items', [])[:3]:
            title = item['title'].replace('<b>', '').replace('</b>', '')
            desc = item['description'].replace('<b>', '').replace('</b>', '')
            blogger = item.get('bloggername', '')
            competitor_text += f"[{blogger}] {title}: {desc}\n\n"
        
        if competitor_text:
            print(f"   ✅ [Auditor] 경쟁사 {len(data.get('items', []))}개 블로그 분석 완료")
            return competitor_text
        else:
            print("   ⚠️ [Auditor] 검색 결과 없음")
            return None
            
    except Exception as e:
        print(f"   ❌ [Auditor] 경쟁사 분석 실패: {e}")
        return None


def audit_image_prompts(topic, content_html, image_prompts, max_retries=2):
    """
    이미지 프롬프트가 글 내용과 일치하는지 검수
    
    Returns:
        dict: {
            "approved": True/False,
            "reason": "검수 결과 설명",
            "improved_prompts": [...] (승인 안 될 경우 개선된 프롬프트)
        }
    """
    print(f"🔍 [Prompt Auditor] 이미지 프롬프트 검수 시작... (주제: {topic})")
    
    audit_prompt = f"""
    당신은 이미지 생성 프롬프트 검수자입니다.
    
    [글 주제] {topic}
    [글 요약] (HTML에서 첫 500자) {content_html[:500]}...
    
    [검수할 이미지 프롬프트들]
    {chr(10).join([f"{i+1}. {p}" for i, p in enumerate(image_prompts)])}
    
    [검수 기준]
    1. 모든 프롬프트에 "골든 리트리버(Golden Retriever)"가 포함되어야 함
    2. 모든 프롬프트에 "{topic}"이 포함되어야 함
    3. 배경은 가정집, 부엌, 마당 등 현실적인 장소여야 함
    4. 꽃밭, 산, 판타지, 일러스트, 애니메이션은 금지
    5. 글 내용과 관련 없는 요소(예: 호랑이, 벚꽃)는 금지
    
    [출력 형식 - JSON만 출력]
    {{
        "approved": true 또는 false,
        "reason": "검수 결과 설명 (한국어)",
        "issues": ["문제점1", "문제점2"],
        "improved_prompts": [
            "수정된 프롬프트 1",
            "수정된 프롬프트 2",
            "수정된 프롬프트 3",
            "수정된 프롬프트 4",
            "수정된 프롬프트 5"
        ]
    }}
    
    승인(approved=true)일 경우에도 improved_prompts에 원본을 그대로 넣어주세요.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(audit_prompt)
        result_text = response.text.strip()
        
        # JSON 추출
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        import json
        result = json.loads(result_text)
        
        if result.get("approved"):
            print(f"   ✅ [Approved] 프롬프트 검수 통과!")
        else:
            print(f"   ⚠️ [Rejected] 프롬프트 수정 필요: {result.get('reason')}")
            print(f"   📝 문제점: {result.get('issues')}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ 검수 실패: {e}")
        # 실패 시 원본 승인
        return {
            "approved": True,
            "reason": f"검수 에러로 원본 승인: {str(e)}",
            "improved_prompts": image_prompts
        }

