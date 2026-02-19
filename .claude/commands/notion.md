# /notion - 노션 DB 연동

콘텐츠 상태를 Notion DB와 동기화합니다.

## 하위 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/notion sync` | 전체 동기화 | 폴더 → Notion |
| `/notion update` | 단일 업데이트 | 특정 콘텐츠 상태 변경 |
| `/notion status` | 현황 보고 | Notion 기반 리포트 |

## /notion sync

### 실행 내용
1. contents/ 폴더 전체 스캔
2. 각 콘텐츠의 현재 상태 파악
3. Notion DB와 비교
4. 신규 생성 / 기존 업데이트

### 실행 명령
```bash
python3 scripts/notion_sync.py
```

### 출력 예시
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Notion 동기화 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 신규 생성: 5개
🔄 업데이트: 150개
📊 전체: 155개
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## /notion update

### 사용법
```
/notion update <번호> <상태> [--validator PASS|FAIL]
```

### 예시
```bash
/notion update 060 게시완료 --validator PASS
/notion update 061 승인완료
/notion update 062 본문완료 --validator FAIL
```

### 유효한 상태
- `표지완료`: 1_cover_only 단계
- `본문완료`: 2_body_ready 단계
- `승인완료`: 3_approved 단계
- `게시완료`: 4_posted 단계
- `아카이브`: 5_archived 단계

### 실행 명령
```bash
python3 scripts/notion_update.py <번호> <상태> [--validator PASS|FAIL]
```

## /notion status

### 실행 내용
1. Notion DB에서 전체 콘텐츠 조회
2. 상태별 집계
3. Validator 현황
4. FAIL 목록
5. 최근 게시 목록

### 실행 명령
```bash
python3 scripts/notion_report.py
```

### 출력 예시
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Project Sunshine 콘텐츠 현황 (Notion 기준)
   조회 시각: 2026-02-10 14:30:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 상태별 현황
   🖼️ 표지완료: 150개
   📝 본문완료: 7개
   ✅ 승인완료: 2개
   🚀 게시완료: 42개
   📦 아카이브: 0개

   📊 전체: 201개

🔍 Validator 현황
   ✅ PASS: 42개
   ❌ FAIL: 159개

📋 FAIL 콘텐츠 목록
   - 001: 바나나 (표지완료)
   - 002: 사과 (표지완료)
   ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 자동 연동

### Hook 연동
Validator 실행 후 자동으로 Notion 업데이트:
- PASS → Validator: PASS 업데이트
- FAIL → Validator: FAIL 업데이트

### 게시 완료 시
게시 성공 후 자동 업데이트:
- 상태: 게시완료
- Validator: PASS
- 게시URL: permalink

## 설정

### .env 필수 항목
```
NOTION_API_KEY=ntn_xxxxx...
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Notion DB 속성
| 속성명 | 타입 | 설명 |
|--------|------|------|
| 번호 | Title | 콘텐츠 번호 (001-999) |
| 음식명(한글) | Text | 한글 음식명 |
| 음식명(영어) | Text | 영어 음식명 |
| 상태 | Select | 표지완료/본문완료/승인완료/게시완료/아카이브 |
| Validator | Select | PASS/FAIL |
| 게시URL | URL | 인스타그램 permalink |

## 주의사항

1. **NOTION_DATABASE_ID 필수**
   - Notion에서 DB 생성 후 ID 복사
   - .env에 NOTION_DATABASE_ID 추가

2. **Integration 연결 필요**
   - Notion에서 Integration 생성
   - DB에 Integration 연결 (Share → Invite)

3. **속성명 일치**
   - DB 속성명이 위 표와 정확히 일치해야 함
   - 한글/영어 구분 주의
