import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
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
    """구글 검색 결과 크롤링 (개선 버전 - 타임아웃 및 에러 처리 강화)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    driver = None
    try:
        # [수정] 자동 드라이버 설치
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(15)
        
        search_url = f"https://www.google.com/search?q={keyword}"
        print(f"   🔍 크롤링: {search_url}")
        driver.get(search_url)
        
        # [수정] 명시적 대기 추가
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"   ✅ 크롤링 완료 ({len(body_text)} chars)")
        return body_text[:2000]

    except Exception as e:
        print(f"   ⚠️ 크롤링 에러: {e}")
        
        # [NEW] 에러 스크린샷 저장
        if driver:
            try:
                os.makedirs("debug", exist_ok=True)
                screenshot_path = f"debug/audit_error_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                print(f"   📸 에러 스크린샷 저장: {screenshot_path}")
            except:
                pass
        
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


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

