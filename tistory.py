import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()
TISTORY_ID = os.getenv("TISTORY_ID")
TISTORY_PW = os.getenv("TISTORY_PW")
BLOG_NAME = os.getenv("TISTORY_BLOG_NAME")

def upload_to_tistory(title, content_html, hashtags):
    """티스토리에 글 업로드 (undetected-chromedriver 사용)"""
    print("🚀 [Tistory] 업로드 시작 (Stealth Mode)...")
    
    if not TISTORY_ID or not TISTORY_PW or not BLOG_NAME:
        print("   ❌ 오류: .env 파일에 티스토리 정보가 없습니다.")
        return False

    # undetected-chromedriver 옵션
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")  # 디버깅을 위해 headless OFF
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        # undetected Chrome 드라이버 생성
        driver = uc.Chrome(options=options, version_main=None)
        wait = WebDriverWait(driver, 30)
        
        # 1. 카카오 로그인
        print("   🔐 로그인 중 (봇 탐지 우회)...")
        driver.get("https://accounts.kakao.com/login?continue=https://www.tistory.com/")
        time.sleep(5)  # 페이지 로딩 대기

        # 로그인 폼 찾기
        try:
            id_input = wait.until(EC.presence_of_element_located((By.NAME, "loginId")))
            id_input.clear()
            id_input.send_keys(TISTORY_ID)
            print(f"   📧 ID 입력: {TISTORY_ID}")
            
            pw_input = driver.find_element(By.NAME, "password")
            pw_input.clear()
            pw_input.send_keys(TISTORY_PW)
            print("   🔑 PW 입력 완료")
            
            # Submit
            pw_input.send_keys(Keys.ENTER)
            print("   ✅ 로그인 요청 전송")
            
        except Exception as e:
            print(f"   ❌ 로그인 폼 오류: {e}")
            raise Exception("로그인 폼을 찾을 수 없습니다")
        
        # 로그인 처리 대기 (reCAPTCHA 자동 해결 기대)
        time.sleep(15)  # 충분한 대기 시간
        
        # 로그인 성공 확인
        current_url = driver.current_url
        print(f"   🔍 로그인 후 URL: {current_url}")
        
        if "login" in current_url.lower():
            # 스크린샷 저장
            os.makedirs("debug", exist_ok=True)
            driver.save_screenshot(f"debug/uc_login_failed_{int(time.time())}.png")
            
            with open(f"debug/uc_page_source_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            raise Exception(f"로그인 실패! URL: {current_url}")
        
        print("   ✅ 로그인 성공!")
        
        # 2. 글쓰기 페이지 이동
        write_url = f"https://{BLOG_NAME}.tistory.com/manage/newpost"
        print(f"   📝 글쓰기 페이지 이동: {write_url}")
        driver.get(write_url)
        
        # 페이지 로딩 대기
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(5)
        
        print(f"   🔍 현재 URL: {driver.current_url}")

        # 3. 제목 입력 - 다중 셀렉터 시도
        print(f"   ✍️ 제목 입력: {title}")
        title_selectors = [
            (By.ID, "editorTitle"),
            (By.CSS_SELECTOR, "input[id*='title' i]"),
            (By.CSS_SELECTOR, "input[placeholder*='제목']"),
            (By.XPATH, "//input[@type='text' and contains(@class, 'title')]"),
            (By.CSS_SELECTOR, ".editor-title input"),
        ]
        
        title_input = None
        for by, selector in title_selectors:
            try:
                title_input = wait.until(EC.presence_of_element_located((by, selector)))
                print(f"      ✅ 제목 입력란 발견: {selector}")
                break
            except:
                continue
        
        if not title_input:
            raise Exception("제목 입력란을 찾을 수 없습니다")
        
        title_input.clear()
        title_input.send_keys(title)
        time.sleep(1)

        # 4. 내용 입력
        print("   📄 내용 입력...")
        try:
            # contenteditable 요소 찾기
            content_area = driver.find_element(By.CSS_SELECTOR, "[contenteditable='true']")
            driver.execute_script("arguments[0].innerHTML = arguments[1];", content_area, content_html)
            print("   ✅ 내용 입력 완료")
        except Exception as e:
            print(f"   ⚠️ 내용 입력 실패 (계속 진행): {e}")

        # 5. 태그 입력
        if hashtags:
            print(f"   🏷️ 태그: {hashtags}")
            try:
                tag_input = driver.find_element(By.ID, "tagText")
                for tag in hashtags:
                    tag_input.send_keys(tag)
                    tag_input.send_keys(Keys.ENTER)
                    time.sleep(0.3)
                print("   ✅ 태그 입력 완료")
            except Exception as e:
                print(f"   ⚠️ 태그 입력 실패: {e}")

        # 6. 발행 버튼 클릭
        print("   🚀 발행 시도...")
        try:
            publish_btn = wait.until(EC.element_to_be_clickable((By.ID, "publish-btn")))
            publish_btn.click()
            time.sleep(3)
            print("   ✅ 티스토리 업로드 성공!")
            return True
        except:
            print("   ⚠️ 발행 버튼 클릭 실패, 대체 방법 시도...")
            alt_selectors = [
                "button[id*='publish' i]",
                ".btn-publish"
            ]
            for selector in alt_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    btn.click()
                    time.sleep(3)
                    print("   ✅ 대체 방법으로 발행 성공!")
                    return True
                except:
                    continue
            
            raise Exception("발행 버튼을 찾을 수 없습니다")

    except Exception as e:
        print(f"   ❌ 업로드 실패: {e}")
        
        # 에러 스크린샷 저장
        if driver:
            try:
                os.makedirs("debug", exist_ok=True)
                screenshot_path = f"debug/uc_error_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                print(f"   📸 스크린샷 저장: {screenshot_path}")
                
                # 페이지 소스도 저장
                with open(f"debug/uc_page_source_{int(time.time())}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"   📄 페이지 소스 저장 완료")
            except:
                pass
        
        return False
        
    finally:
        if driver:
            driver.quit()

def upload_via_debug_port(title, content_html, hashtags):
    """
    [최후의 수단] 이미 실행된 크롬(디버깅 모드)에 접속하여 업로드
    실행 전 터미널 명령: 
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_debug_profile"
    """
    print("🚀 [Tistory] 브라우저 하이재킹 시도 (Port 9222)...")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 30)
        
        # 1. 로그인 여부 확인
        print("   🔍 현재 페이지 확인 중...")
        current_url = driver.current_url
        print(f"   📍 URL: {current_url}")
        
        # 로그인 페이지라면?
        if "login" in current_url.lower() or "kakao" in current_url.lower():
            print("   ⚠️ 로그인 페이지 감지! 30초 대기할테니 수동으로 로그인해주세요!")
            for i in range(30):
                print(f"   ⏳ {30-i}초 남음...", end='\r')
                time.sleep(1)
                if "tistory.com" in driver.current_url and "login" not in driver.current_url:
                    print("\n   ✅ 로그인 감지됨!")
                    break
            print()
            
        # 2. 글쓰기 페이지 이동
        write_url = f"https://{BLOG_NAME}.tistory.com/manage/newpost"
        print(f"   📝 글쓰기 페이지 이동: {write_url}")
        driver.get(write_url)
        
        # 페이지 로딩 대기
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(3)
        
        # 3. 제목 입력
        print(f"   ✍️ 제목 입력: {title}")
        title_input = wait.until(EC.presence_of_element_located((By.ID, "editorTitle")))
        title_input.clear()
        title_input.send_keys(title)
        
        # 4. 내용 입력
        print("   📄 내용 입력...")
        content_area = driver.find_element(By.CSS_SELECTOR, ".editor-content, [contenteditable='true']")
        driver.execute_script("arguments[0].innerHTML = arguments[1];", content_area, content_html)
        
        # 5. 태그 입력
        if hashtags:
            print(f"   🏷️ 태그: {hashtags}")
            tag_input = driver.find_element(By.ID, "tagText")
            for tag in hashtags:
                tag_input.send_keys(tag)
                tag_input.send_keys(Keys.ENTER)
                time.sleep(0.3)
                
        # 6. 발행
        print("   🚀 발행 버튼 클릭...")
        publish_btn = wait.until(EC.element_to_be_clickable((By.ID, "publish-btn")))
        publish_btn.click()
        time.sleep(3)
        
        # 최종 발행 확인
        try:
            final_publish_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_publish") # 팝업 내 발행 버튼
            final_publish_btn.click()
            print("   ✅ 최종 발행 클릭")
        except:
            print("   ℹ️ 팝업 발행 버튼 없음 (바로 발행됨)")
            
        time.sleep(5)
        print("   ✅ 티스토리 업로드 성공 (하이재킹)!")
        return True
        
    except Exception as e:
        print(f"   ❌ 하이재킹 실패: {e}")
        return False
    # driver.quit() 하지 않음 (브라우저 유지)
