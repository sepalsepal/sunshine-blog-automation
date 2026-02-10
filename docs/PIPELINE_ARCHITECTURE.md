# Project Sunshine 파이프라인 아키텍처

> **버전:** 1.0
> **작성일:** 2026-02-02
> **목적:** 콘텐츠 제작~게시 전체 파이프라인 문서화

---

## 1. 콘텐츠 제작 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTENT PIPELINE v6                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [1] 주제 선정          content_map.json에서 ready 확인     │
│         ↓                                                    │
│  [2] 안전도 확인        SAFE / CAUTION / DANGER / FORBIDDEN  │
│         ↓                                                    │
│  [3] GOLDEN_SAMPLE 참조  해당 안전도의 기준 샘플 확인        │
│         ↓                                                    │
│  [4] 이미지 생성        fal-ai/flux-2-pro + Puppeteer        │
│         ↓                                                    │
│  [5] 텍스트 오버레이    apply_content_overlay.js             │
│         ↓                                                    │
│  [6] 세트 비교 검수     GOLDEN_SAMPLE과 비교                 │
│         ↓                                                    │
│  [7] 게시               publish_content.py                   │
│         ↓                                                    │
│  [8] 동기화             sync_views.sh + content_map 업데이트 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. GOLDEN_SAMPLE 참조 체계

| 안전도 | GOLDEN_SAMPLE | 색상 코드 | 본문 패턴 |
|--------|---------------|-----------|-----------|
| **SAFE** | potato | `#4CAF50` (녹색) | "먹어도 돼요!" |
| **CAUTION** | shrimp | `#FFD93D` (노란색) | "급여 주의!" |
| **DANGER** | chocolate | `#FF6B6B` (빨간색) | "급여 금지!" |
| **FORBIDDEN** | (미정) | `#1A1A2E` (검정) | Phase 2.6 정의 예정 |

### 참조 규칙
1. 신규 콘텐츠 제작 시 해당 안전도의 GOLDEN_SAMPLE 필수 참조
2. 색상, 폰트, 레이아웃, 메시지 패턴 일치 확인
3. 세트 비교 검수 시 GOLDEN_SAMPLE과 나란히 비교

---

## 3. 규칙 참조 맵

| 문서 | 경로 | 용도 |
|------|------|------|
| **검수 규칙** | `docs/PHASE25_CONDITIONS.md` | G1/G2/G3 검수 기준 |
| **폴더 규칙** | `docs/FOLDER_RULES.md` | 옵션 D' 폴더 사용법 |
| **제작 가이드** | `docs/CONTENT_PRODUCTION_GUIDE.md` | 콘텐츠 제작 필수 규칙 |
| **Phase 상태** | `docs/PHASE_STATUS.md` | 현재 Phase 및 조건 |

---

## 4. 폴더 구조 (옵션 D')

```
content/images/
├── {ID}_{topic}/              # 콘텐츠 폴더 (상태 접미사 없음)
│   ├── {topic}_00.png         # 표지
│   ├── {topic}_01.png         # 본문 1
│   ├── {topic}_02.png         # 본문 2
│   ├── {topic}_03.png         # CTA
│   ├── caption_instagram.txt  # 캡션
│   └── archive/               # 작업 파일
│
└── 🔒_views/                  # 상태별 바로가기 (심볼릭 링크)
    ├── published/             # 게시 완료
    ├── ready/                 # 게시 대기
    ├── in_progress/           # 제작 중
    └── blocked/               # 차단됨
```

### 핵심 원칙
- 폴더 이동 없음 (ID 기반 고정)
- 상태는 `content_map.json`에서 관리
- `🔒_views`는 열람 전용 (수정 금지)

---

## 5. 자동화 스크립트

| 스크립트 | 경로 | 기능 |
|----------|------|------|
| **게시** | `services/scripts/publishing/publish_content.py` | Instagram + Threads 게시 |
| **동기화** | `services/scripts/sync_views.sh` | 🔒_views 심볼릭 링크 갱신 |
| **오버레이** | `services/scripts/text_overlay/apply_content_overlay.js` | 텍스트 합성 |
| **이미지 생성** | `services/scripts/generate_images.py` | fal-ai FLUX.2 Pro |

### 게시 명령어

```bash
# 단일 게시
python3 services/scripts/publishing/publish_content.py {topic}

# 자동 재시도 비활성화
python3 services/scripts/publishing/publish_content.py {topic} --no-retry

# 지원 토픽 목록
python3 services/scripts/publishing/publish_content.py --list
```

---

## 6. 검수 게이트

| 게이트 | 단계 | 검수 항목 |
|--------|------|-----------|
| **G1** | 기획/글 | 캡션 품질, 해시태그, 메시지 정합성 |
| **G2** | 이미지 | 햇살이 특징, 금지 포즈, 레이아웃 |
| **G3** | 합성 | 텍스트 가독성, 색상 일치, 세트 비교 |

### 자동 실패 조건
- 금지 포즈 감지 (먹기/핥기/만지기)
- GOLDEN_SAMPLE 색상 불일치
- 필수 텍스트 누락

---

## 7. 데이터 파일

| 파일 | 경로 | 용도 |
|------|------|------|
| **콘텐츠 맵** | `config/data/content_map.json` | 전체 콘텐츠 상태 관리 |
| **게시 이력** | `config/settings/publishing_history.json` | 게시 완료 기록 |
| **게시 스케줄** | `config/settings/publish_schedule.json` | 자동 게시 일정 |

---

## 8. Phase 운영 체계

| Phase | 상태 | 특징 |
|-------|------|------|
| **2.5** | 조건부 | GOLDEN_SAMPLE 3종 확정, 규칙 동결 |
| **3.0** | 완전 자동화 | Exit 조건 5개 충족, 일일 게시 가능 |

### Phase 3 진입 조건
1. 연속 게시 무장애 ≥ 5건
2. 기술 실패율 ≤ 3%
3. 정책 개입률 ≤ 10%
4. GOLDEN_SAMPLE 3종 확정
5. 파이프라인 문서화 완료

---

## 9. 트러블슈팅

### 게시 실패 시
1. Instagram API 일시 오류 → 5초 후 재시도
2. 이미지 파일 없음 → 폴더 확인
3. 캡션 파일 없음 → caption_instagram.txt 생성

### 동기화 오류 시
```bash
# 수동 동기화
bash services/scripts/sync_views.sh
```

---

**작성자:** 김부장 (자동화)
**검토:** PD님
