# 자동화 반려견 블로그 설정 가이드

## 필수 조건

1.  **Python 3.8 이상** 설치.
2.  **Google 계정** (Blogger 블로그 생성 완료).
3.  **Telegram 계정** (봇 승인용).

## 상세 설정 가이드

### 1. 파이썬(Python) 설치 방법 (Mac 기준)
현재 Mac을 사용 중이시군요. 다음 방법 중 하나로 설치하세요.

**방법 A: 공식 홈페이지 설치 (가장 쉬움)**
1.  [Python.org 다운로드 페이지](https://www.python.org/downloads/macos/)로 이동합니다.
2.  **"Latest Python 3 Release"** 버튼을 클릭하여 설치 파일(`.pkg`)을 다운로드합니다.
3.  다운로드된 파일을 실행하고 계속 버튼을 눌러 설치를 완료합니다.
4.  설치가 끝나면 터미널을 열고 `python3 --version`을 입력해 버전이 나오는지 확인합니다.

**방법 B: Homebrew 사용 (개발자 추천)**
터미널에 다음 명령어를 입력하세요:
```bash
brew install python
```

### 2. 구글 블로그(Blogger) 만들기
1.  [Blogger.com](https://www.blogger.com/)에 접속합니다.
2.  **"블로그 만들기"** 버튼을 클릭하고 구글 계정으로 로그인합니다.
3.  **블로그 이름**을 입력합니다 (예: "댕댕이의 하루").
4.  **URL(주소)**을 입력합니다 (예: `my-dog-blog-2024`). *중복되지 않는 주소를 찾아야 합니다.*
5.  **"완료"**를 누르면 블로그가 생성됩니다.

### 3. 라이브러리 설치
터미널에서 이 프로젝트 폴더로 이동한 후 실행하세요:
```bash
cd /Users/al01742017/Desktop/Blog
pip install -r requirements.txt
```

### 4. Google Cloud 프로젝트 설정 (Blogger API용)
1.  [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
2.  새 프로젝트를 만듭니다 (예: "Dog Blog Automation").
3.  **API 및 서비스 > 라이브러리**로 이동합니다.
4.  **"Blogger API"**를 검색하고 (보통 "Blogger API v3"라고 되어있거나 그냥 "Blogger API"입니다) **사용**을 클릭합니다.
5.  **API 및 서비스 > OAuth 동의 화면**으로 이동합니다.
    - **외부(External)**를 선택합니다.
    - 필수 정보(앱 이름, 이메일)를 입력합니다.
    - **테스트 사용자**에 본인의 이메일을 추가합니다.
6.  **API 및 서비스 > 사용자 인증 정보**로 이동합니다.
    - **사용자 인증 정보 만들기 > OAuth 클라이언트 ID**를 클릭합니다.
    - 애플리케이션 유형: **데스크톱 앱**.
    - JSON 파일을 다운로드하고 이름을 `client_secret.json`으로 변경합니다.
    - 이 `client_secret.json` 파일을 프로젝트 폴더 (`/Users/al01742017/Desktop/Blog/`)에 넣습니다.

### 5. Gemini API 설정
1.  [Google AI Studio](https://aistudio.google.com/)에 접속합니다.
2.  API 키를 발급받습니다.
3.  **`/Users/al01742017/Desktop/Blog/`** 폴더에 `.env`라는 이름의 파일을 만듭니다.
4.  다음과 같이 키를 입력하고 저장합니다:
    ```
    GENAI_API_KEY=여기에_API_키를_붙여넣으세요
    TELEGRAM_BOT_TOKEN=여기에_텔레그램_봇_토큰을_붙여넣으세요
    ```

### 6. Telegram Bot 설정
1.  텔레그램에서 **@BotFather** 검색
2.  `/newbot` 명령어 입력
3.  봇 이름 및 사용자명 입력
4.  받은 토큰을 `.env` 파일에 추가

## 사용 방법

### 텔레그램 봇 실행
```bash
python3 bot.py
```

### 봇 사용법
1.  텔레그램에서 생성한 봇을 검색하여 시작
2.  `/start` 명령어로 봇 활성화
3.  `1` 입력 → 즉시 콘텐츠 생성 및 승인 요청
4.  승인/거부 버튼으로 발행 제어

### 자동 스케줄링
- 매일 오전 7시, 오후 7시에 자동으로 콘텐츠 생성
- 텔레그램으로 승인 요청 전송
- 승인 시 자동 발행

## 수동 실행 (텔레그램 없이)
```bash
python3 main.py
```
