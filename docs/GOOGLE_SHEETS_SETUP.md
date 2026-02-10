# Google Sheets API 설정 가이드

> 콘텐츠 관리 시트를 Google Sheets로 연동하는 방법

---

## 📋 개요

| 항목 | 값 |
|------|-----|
| 초기 비용 | **무료** |
| 월간 비용 | **무료** (개인용) |
| API 한도 | 500 요청/100초/프로젝트 |
| 설정 시간 | 약 10분 |

---

## 🚀 빠른 설정 (5단계)

### 1단계: Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. "새 프로젝트" 클릭
3. 프로젝트 이름: `project-sunshine` (자유롭게)
4. "만들기" 클릭

### 2단계: Google Sheets API 활성화

1. 좌측 메뉴 → "API 및 서비스" → "라이브러리"
2. "Google Sheets API" 검색
3. "사용" 클릭
4. "Google Drive API"도 동일하게 활성화

### 3단계: 서비스 계정 생성

1. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
2. "사용자 인증 정보 만들기" → "서비스 계정"
3. 이름: `sunshine-sheets` (자유롭게)
4. "만들고 계속하기" 클릭
5. 역할 선택 스킵 → "완료"

### 4단계: JSON 키 다운로드

1. 생성된 서비스 계정 클릭
2. "키" 탭 → "키 추가" → "새 키 만들기"
3. JSON 선택 → "만들기"
4. 다운로드된 JSON 파일을 프로젝트 폴더에 저장
   ```
   /path/to/project_sunshine/config/google-credentials.json
   ```

### 5단계: Google Sheet 생성 및 공유

1. [Google Sheets](https://sheets.google.com) 접속
2. 새 스프레드시트 생성: "Project Sunshine 콘텐츠"
3. 첫 번째 시트 이름: `게시콘텐츠`
4. 헤더 행 추가:
   ```
   번호 | 영문명 | 한글명 | 폴더명 | 안전도 | 게시상태 | 게시일 | 인스타URL
   ```
5. **중요:** 서비스 계정과 공유
   - "공유" 클릭
   - JSON 파일의 `client_email` 값 입력
   - "편집자" 권한 부여
   - "공유" 클릭

---

## ⚙️ 환경변수 설정

`.env` 파일에 다음 추가:

```bash
# Google Sheets API
GOOGLE_SHEET_ID=1ABC...xyz        # 시트 URL에서 /d/ 뒤의 ID
GOOGLE_CREDENTIALS_PATH=/Users/.../config/google-credentials.json
GOOGLE_WORKSHEET_NAME=게시콘텐츠
```

### 시트 ID 찾기

URL 예시:
```
https://docs.google.com/spreadsheets/d/1ABC123xyz/edit#gid=0
                                        ^^^^^^^^^^^
                                        이 부분이 SHEET_ID
```

---

## 📦 패키지 설치

```bash
pip install gspread google-auth
```

---

## ✅ 연결 테스트

```bash
python -c "from core.utils.google_sheets_manager import ContentSheetManager; m = ContentSheetManager(); m.connect(); m.print_status()"
```

---

## 📝 사용법

### 콘텐츠 제작 전 체크

```python
from core.utils.google_sheets_manager import check_before_creation

result = check_before_creation('banana')
if result['can_create']:
    print("제작 가능!")
else:
    print(f"제작 불가: {result['reason']}")
```

### 게시 후 업데이트

```python
from core.utils.google_sheets_manager import update_after_publishing

update_after_publishing(
    topic_en='banana',
    topic_kr='바나나',
    safety='SAFE',
    instagram_url='https://instagram.com/p/...'
)
```

### 현황 확인

```python
from core.utils.google_sheets_manager import ContentSheetManager

manager = ContentSheetManager()
manager.print_status()
```

---

## 🔄 로컬 CSV와 동기화

Google Sheets 연결 실패 시 자동으로 로컬 CSV 사용:
- 위치: `config/data/published_contents.csv`
- 시트 복구 후 자동 동기화 가능

```python
manager = ContentSheetManager()
manager.sync_from_local()  # 로컬 → 시트 동기화
```

---

## ❓ 문제 해결

### "Request had insufficient authentication scopes"

→ Google Drive API 활성화 필요

### "Spreadsheet not found"

→ 서비스 계정에 시트 공유 확인

### "Permission denied"

→ 서비스 계정에 "편집자" 권한 부여

---

**작성일:** 2026-01-31
