# 콘텐츠 텍스트 규칙 v1.0

> **작성일:** 2026-02-03
> **기준:** 기존 콘텐츠 분석 결과 (boiled_egg, spinach, shrimp, grape)
> **상태:** 검증 완료

---

## 1. 표지 텍스트 규칙 (v9 확정)

| 항목 | 값 | 비고 |
|------|-----|------|
| 폰트 | Arial Black | 필수 |
| 크기 | 114px | 고정 |
| 색상 | #FFFFFF | 흰색 |
| 위치 | top: 150px | 상단 약 14% |
| 그림자 | `0 4px 12px rgba(0,0,0,0.6)` | 필수 |
| 자간 | 0.02em | 선택 |

### 근거 파일
- `services/scripts/text_overlay.js:31-40`
- `services/scripts/cover_text_overlay.js:23-24`
- `CLAUDE.md:433`

---

## 2. 본문 텍스트 규칙 (안전도 기반)

### 2.1 색상 규칙

| 안전도 | 색상명 | HEX 코드 | RGB |
|--------|--------|----------|-----|
| **SAFE** | 초록 | `#4CAF50` | (76, 175, 80) |
| **CAUTION** | 노랑 | `#FFD93D` | (255, 217, 61) |
| **DANGER** | 빨강 | `#FF6B6B` | (255, 107, 107) |

### 2.2 기준 콘텐츠

| 안전도 | 기준 콘텐츠 | 확인된 색상 |
|--------|-------------|-------------|
| SAFE | boiled_egg, spinach | #4CAF50 ✅ |
| CAUTION | shrimp | #FFD93D ✅ |
| DANGER | grape | #FF6B6B ✅ |

### 2.3 폰트 규칙

| 항목 | 값 |
|------|-----|
| 폰트 | Noto Sans KR |
| 제목 크기 | 72px |
| 제목 굵기 | 900 (Black) |
| 부제목 크기 | 36px |
| 부제목 색상 | #FFFFFF |

### 근거 파일
- `services/scripts/text_overlay/render_boiled_egg.js:22-27`
- `services/scripts/text_overlay/render_spinach_clean.js:28-34`
- `services/scripts/text_overlay/render_shrimp_v2.js:41-49`
- `services/scripts/text_overlay/render_grape.js:66`

---

## 3. CTA 텍스트 규칙

| 항목 | 값 |
|------|-----|
| 제목 색상 | #FFD93D (노랑) |
| 제목 크기 | 64px |
| 부제목 색상 | #FFFFFF |
| 부제목 크기 | 40px |

> CTA는 모든 안전도에서 동일하게 노란색 사용

---

## 4. 검증 체크리스트

### 표지 (00)
- [ ] 폰트: Arial Black 114px
- [ ] 색상: #FFFFFF (흰색)
- [ ] 위치: 상단 150px
- [ ] 그림자 효과 적용

### 본문 (01, 02)
- [ ] 음식 안전도 확인 (config에서)
- [ ] 안전도에 맞는 색상 적용
  - SAFE → #4CAF50 (초록)
  - CAUTION → #FFD93D (노랑)
  - DANGER → #FF6B6B (빨강)
- [ ] 기준 콘텐츠와 색상 일치 확인

### CTA (03)
- [ ] 제목: #FFD93D (노랑)
- [ ] 부제목: #FFFFFF (흰색)

---

## 5. 버전 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-02-03 | 초기 버전 - 기존 콘텐츠 분석 기반 작성 |

---

## 6. 참고: 안전도 분류

| 안전도 | 설명 | 예시 |
|--------|------|------|
| SAFE | 안전하게 급여 가능 | 삶은달걀, 시금치, 오리고기 |
| CAUTION | 주의 필요, 조리/소량 | 새우, 삼겹살 |
| DANGER | 급여 금지 | 포도, 초콜릿, 양파 |
