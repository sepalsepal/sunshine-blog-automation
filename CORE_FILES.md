# 🔒 Core Files (보호 파일 목록)

이 파일들은 시스템의 핵심 안정성에 영향을 미칩니다.
**수정 전 반드시 승인이 필요합니다.**

---

## 🔴 Critical Core (절대 보호)

| 파일 | 역할 | 수정 시 영향 |
|---|---|---|
| `config/image_templates.json` | 이미지 프롬프트 템플릿 | 이미지 품질/일관성 변경 |
| `wordpress.py` | 블로그 포스팅 | 업로드 실패 위험 |
| `.env` | API 키, 인증 정보 | 전체 서비스 중단 위험 |

---

## 🟡 Important Core (주의 필요)

| 파일 | 역할 | 수정 시 영향 |
|---|---|---|
| `image_utils.py` | 이미지 생성 엔진 | 이미지 생성 로직 변경 |
| `content.py` | 글 생성 엔진 | 글 품질/스타일 변경 |
| `firebase_uploader.py` | 이미지 저장소 | 이미지 URL 변경 |

---

## 🟢 Flexible (자유 수정 가능)

| 파일 | 역할 |
|---|---|
| `app.py` | UI/UX |
| `auditor.py` | 글 검수 |
| `research.py` | 트렌드 조사 |
| `telegram_notifier.py` | 알림 |
| `bot_runner.py`, `bot_listener.py` | 텔레그램 봇 |
| `state_manager.py` | 상태 관리 |
| `food_manager.py` | 음식 주제 관리 |
| `weather_utils.py` | 날씨 |
| `g_sheet_archiver.py` | 기록 |

---

## 📋 수정 요청 시 프로세스

1. **Core 파일 수정 감지** → AI가 자동 알림
2. **변경 이유 설명** → 왜 이 파일을 건드려야 하는지
3. **영향 범위 분석** → 어떤 기능에 영향이 가는지
4. **사용자 승인** → 승인 후에만 수정 진행

---

*마지막 업데이트: 2024-12-08*
