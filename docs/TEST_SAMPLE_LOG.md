# 테스트 샘플 생성 로그 (Draft)

> **상태:** DRAFT - 확정 아님
> **작성일:** 2026-01-31 (Day 11 야간)
> **목적:** Phase 2.5 병렬 3 Task 테스트 준비
> **경로:** content/TEST_SAMPLE/

---

## 생성 개요

| 항목 | 내용 |
|------|------|
| 생성 일시 | 2026-01-31 야간 |
| 생성자 | 김부장 (Claude Opus 4.5) |
| 콘텐츠 수 | 2건 |
| 목적 | Phase 2.5 병렬 Task 테스트용 |
| 상태 | 텍스트/캡션만 (이미지 미생성) |

---

## 생성 파일 목록

### 폴더 구조

```
content/TEST_SAMPLE/
├── NOT_FOR_PUBLISH.txt           ← 게시 금지 경고
├── turkey_칠면조/
│   ├── turkey_text.json          ← 텍스트 설정
│   └── caption_instagram.txt     ← Instagram 캡션
├── orange_오렌지/
│   ├── orange_text.json          ← 텍스트 설정
│   └── caption_instagram.txt     ← Instagram 캡션
└── shrimp_새우/                  ← Day 12 추가
    ├── shrimp_text.json          ← 텍스트 설정 (CAUTION 톤)
    └── caption_instagram.txt     ← Instagram 캡션 (⚠️ 포함)
```

### 파일별 상세

| 파일 | 크기 | 용도 |
|------|------|------|
| NOT_FOR_PUBLISH.txt | 0.8KB | 게시 금지 경고 |
| turkey_text.json | 1.2KB | 칠면조 슬라이드 텍스트 |
| turkey/caption_instagram.txt | 0.9KB | 칠면조 캡션 |
| orange_text.json | 1.1KB | 오렌지 슬라이드 텍스트 |
| orange/caption_instagram.txt | 0.9KB | 오렌지 캡션 |

---

## 콘텐츠 1: turkey (칠면조)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 영문명 | turkey |
| 한글명 | 칠면조 |
| 안전 분류 | SAFE |
| 예상 레벨 | L1 (AUTO_PUBLISH) |
| topics 등록 | ✅ turkey: safe |

### 슬라이드 구성

| 번호 | 역할 | 제목 | 부제목 |
|:----:|------|------|--------|
| 00 | 표지 | TURKEY | - |
| 01 | 결론+효능 | 먹어도 돼요! | 저지방 고단백 최고의 선택 ✅ |
| 02 | 주의+급여량 | 급여 시 주의사항 | 뼈 없이 익혀서 급여 |
| 03 | CTA | 저장하고 공유하세요! | 우리 댕댕이 건강 간식 정보 |

### 급여량 가이드

| 견종 | 급여량 |
|------|--------|
| 소형견 | 30~50g |
| 중형견 | 80~100g |
| 대형견 | 150~200g |

### 캡션 검수

| 항목 | 상태 | 비고 |
|------|:----:|------|
| 결론 명시 | ✅ | "급여 가능합니다!" |
| 급여량 포함 | ✅ | 소/중/대형 구분 |
| 주의사항 | ✅ | 4개 |
| AI 표기 | ✅ | 포함 |
| 해시태그 | ✅ | 16개 |

### 예상 Agent 평가

```
Agent A (팩트체크): 예상 PASS
- turkey는 topics_expanded.json에 safe로 등록됨
- 저지방 고단백 정보 정확

Agent B (의미 정합성): 예상 PASS
- SAFE 분류 + 긍정 캡션 일치
- 급여량/주의사항 포함

Agent C (브랜드 일관성): 미확인 (이미지 미생성)

Agent D (Red Flag): 예상 0개
- 금지 포즈 없음 (이미지 미생성)

Agent E (기술 품질): 미확인 (이미지 미생성)
```

---

## 콘텐츠 2: orange (오렌지)

### 기본 정보

| 항목 | 값 |
|------|-----|
| 영문명 | orange |
| 한글명 | 오렌지 |
| 안전 분류 | SAFE |
| 예상 레벨 | L1 (AUTO_PUBLISH) |
| topics 등록 | ✅ orange: safe |

### 슬라이드 구성

| 번호 | 역할 | 제목 | 부제목 |
|:----:|------|------|--------|
| 00 | 표지 | ORANGE | - |
| 01 | 결론+효능 | 먹어도 돼요! | 비타민C 풍부한 과일 간식 ✅ |
| 02 | 주의+급여량 | 급여 시 주의사항 | 껍질 제거 후 소량만 |
| 03 | CTA | 저장하고 공유하세요! | 우리 댕댕이 건강 간식 정보 |

### 급여량 가이드

| 견종 | 급여량 |
|------|--------|
| 소형견 | 1~2조각 |
| 중형견 | 2~3조각 |
| 대형견 | 3~4조각 |

### 캡션 검수

| 항목 | 상태 | 비고 |
|------|:----:|------|
| 결론 명시 | ✅ | "급여 가능합니다!" |
| 급여량 포함 | ✅ | 소/중/대형 구분 |
| 주의사항 | ✅ | 4개 |
| AI 표기 | ✅ | 포함 |
| 해시태그 | ✅ | 16개 |

### 예상 Agent 평가

```
Agent A (팩트체크): 예상 PASS
- orange는 topics_expanded.json에 safe로 등록됨
- 비타민C, 껍질 제거 정보 정확

Agent B (의미 정합성): 예상 PASS
- SAFE 분류 + 긍정 캡션 일치
- 급여량/주의사항 포함

Agent C (브랜드 일관성): 미확인 (이미지 미생성)

Agent D (Red Flag): 예상 0개
- 금지 포즈 없음 (이미지 미생성)

Agent E (기술 품질): 미확인 (이미지 미생성)
```

---

## Phase 2.5 테스트 계획

### 병렬 3 Task 배치

```
Phase 2.5 병렬 테스트 시나리오:

Task A: turkey (칠면조) - L1 SAFE
- 목적: 신규 L1 콘텐츠 정상 처리 검증
- 예상: AUTO_PUBLISH

Task B: orange (오렌지) - L1 SAFE
- 목적: 과일 카테고리 L1 처리 검증
- 예상: AUTO_PUBLISH

Task C: (의도적 FAIL 삽입 예정)
- incomplete_food 또는 paradox_food
- 목적: FAIL 발생 시 다른 Task 영향 없음 검증
```

### 테스트 검증 항목

```
□ 3개 Task 동시 실행 시 충돌 0건
□ 각 Task 독립적 판정 유지
□ FAIL 발생 Task가 다른 Task에 영향 없음
□ 질문 발생 0회
□ 자동 중단 정확도 100%
```

---

## 미완료 항목 (Phase 2.5에서 수행)

| 항목 | 상태 | Phase 2.5 작업 |
|------|:----:|----------------|
| 표지 이미지 (00) | ⏳ | PD님 제작 또는 커버 선택 |
| 본문 이미지 (01~03) | ⏳ | AI 이미지 생성 (fal-ai/flux-2-pro) |
| 텍스트 합성 | ⏳ | apply_content_overlay.js 적용 |
| Agent 5종 평가 | ⏳ | 이미지 생성 후 실행 |
| 실제 게시 | ⏳ | Phase 2.5 진입 후 결정 |

---

## 주의사항

```
⚠️ 이 폴더의 콘텐츠는 테스트 목적입니다!

1. 실제 게시하지 마세요
2. API 호출 없이 텍스트만 생성됨
3. Phase 2.5 진입 후 이미지 생성 예정
4. NOT_FOR_PUBLISH.txt 확인 필수
```

---

## 생성 완료 체크리스트

```
[turkey (칠면조)]
✅ 폴더 생성: content/TEST_SAMPLE/turkey_칠면조/
✅ 텍스트 설정: turkey_text.json
✅ 캡션: caption_instagram.txt
✅ 캡션 검수: 5/5 항목 통과
⏳ 이미지: Phase 2.5에서 생성

[orange (오렌지)]
✅ 폴더 생성: content/TEST_SAMPLE/orange_오렌지/
✅ 텍스트 설정: orange_text.json
✅ 캡션: caption_instagram.txt
✅ 캡션 검수: 5/5 항목 통과
⏳ 이미지: Phase 2.5에서 생성

[공통]
✅ NOT_FOR_PUBLISH.txt 생성
✅ TEST_SAMPLE_LOG.md 작성
```

---

⚠️ DRAFT - 확정 아님
**작성자:** 김부장 (Claude Opus 4.5)
**검토 대기:** PD님
