# v3.1-stable 봉인선언문

**봉인일:** 2026-02-05
**봉인자:** 김부장 + 레드2
**승인자:** 박세준 PD

---

## 핵심 원칙

> "v3.1-stable은 운영 전용. 실험은 분기. 규칙 어기면 죽는다."

---

## 봉인 대상

| 컴포넌트 | 버전 | 상태 |
|----------|------|------|
| pillow_overlay.py | v3.1 | 🔒 봉인 |
| validators_strict.py | v3.1 | 🔒 봉인 |
| reoverlay.py | v3.1 | 🔒 봉인 |
| DESIGN_PARAMS_V31 | v3.1 | 🔒 봉인 |
| select_cta_image() | v1.0 | 🔒 봉인 |
| Puppeteer | - | 🔴 비활성 |
| Telegram | - | 🔴 비활성 |

---

## DESIGN_PARAMS_V31 (수정 금지)

### 폰트
| 항목 | 값 |
|------|-----|
| 제목 폰트 | NotoSansCJK-Black.ttc (index=1) |
| 서브 폰트 | NotoSansCJK-Regular/Medium.ttc (index=1) |
| 레터 스페이싱 | -2% |

### Cover (표지)
| 항목 | 값 |
|------|-----|
| 제목 크기 | 114px |
| 제목 색상 | #FFFFFF |
| Y 위치 | **200px** (레퍼런스 기준, 2026-02-09 수정) |
| 그림자 | 2단 (L1: blur 10, alpha 160 / L2: blur 4, alpha 180) |
| 상단 그라데이션 | 35%, alpha 140 |

### Body (본문)
| 항목 | 값 |
|------|-----|
| 제목 크기 | 88px |
| 제목 색상 | 안전도 기반 |
| 서브 크기 | 44px |
| 서브 색상 | #FFFFFF |

### CTA
| 항목 | 값 |
|------|-----|
| 제목 크기 | 48px |
| 제목 색상 | #FFD93D |
| 서브 크기 | 44px |
| 서브 색상 | #FFFFFF |
| 이미지 | 햇살이 실사진 only (SHA256 해시 배정) |

### 공통
| 항목 | 값 |
|------|-----|
| 하단 그라데이션 | 38%, alpha 180 |
| 그림자 (표준) | blur 5, offset (4,4), alpha 120 |
| 제목-서브 간격 | 48px |
| 하단 여백 | 72px |
| 해상도 | 1080x1080 통일 (리사이즈 자동 적용) |

### 안전도 색상
| 등급 | HEX |
|------|-----|
| SAFE | #4CAF50 |
| CAUTION | #FFD93D |
| DANGER | #FF6B6B |
| FORBIDDEN | #FF5252 |

---

## CTA 다양화 규칙

| 항목 | 규칙 |
|------|------|
| 소스 | best_cta/ 폴더 (50장) |
| 배정 방식 | SHA256 해시 기반 결정적 매핑 |
| 중복 | 연속 콘텐츠 간 동일 이미지 금지 |
| 재현성 | 같은 food_id → 항상 같은 CTA |

---

## 검증 체계 (15개 자동)

### v3.0 검증 (6개)
| # | 검증 | 차단 대상 |
|---|------|----------|
| 1 | assert_clean_image() | _bg/_clean 아닌 이미지 |
| 2 | assert_cta_real_photo() | AI/음식 이미지 CTA |
| 3 | assert_body_layout() | 레이아웃 위반 |
| 4 | assert_cover_rules() | 커버 규칙 위반 |
| 5 | strip_emoji() | □ 이모지 자동 제거 |
| 6 | assert_resolution() | 1080x1080 아닌 출력 |

### v3.1 검증 (9개)
| # | 검증 | 차단 대상 |
|---|------|----------|
| 7 | assert_v31_cover() | 114px/#FFFFFF/y=200 위반 |
| 8 | assert_v31_body() | 88px Black/44px Regular 위반 |
| 9 | assert_v31_cta() | 48px/#FFD93D 위반 |
| 10 | assert_v31_spacing() | gap<48, margin<72 |
| 11 | assert_v31_gradient() | 38%/alpha 180 위반 |
| 12 | assert_v31_safety_color() | 등급-색상 불일치 |
| 13 | assert_v31_cover_shadow() | 2단 그림자 누락 |
| 14 | assert_v31_letter_spacing() | -2% 미적용 |
| 15 | assert_v31_font_weight() | Black/Regular 위반 |

**원칙: 하나라도 ❌ → Exception → 렌더링 불가**

---

## 수정 금지 파일

```
pipeline/pillow_overlay.py (DESIGN_PARAMS_V31 영역)
pipeline/validators_strict.py
services/scripts/reoverlay.py (select_cta_image 영역)
```

---

## 운영 원칙

### 허용
- 신규 콘텐츠 제작 (v3.1 규칙 준수)
- CTA 이미지 추가 (best_cta/ 폴더)
- 텍스트 콘텐츠 변경 (레이아웃 유지)
- Cloudinary 업로드

### 금지
- DESIGN_PARAMS_V31 수정
- validators_strict.py 수정
- 검증 우회 또는 비활성화
- Puppeteer 재활성화
- CTA AI 이미지 사용

---

## 수정 절차 (필요 시)

```
Step 1. 실험 분기 생성 (v3.2-experimental)
Step 2. 개발 및 테스트
Step 3. 15/15 검증 테스트 통과
Step 4. PD 승인
Step 5. 신규 버전 봉인 (v3.2-stable)
Step 6. 이전 버전 아카이브
```

---

## 완성 콘텐츠 (v3.1-stable)

| # | 콘텐츠 | 안전도 | 색상 | CTA 이미지 | 상태 |
|---|--------|--------|------|-----------|------|
| 1 | onion | FORBIDDEN | #FF5252 | happy_033 | 🟢 게시 가능 |
| 2 | garlic | FORBIDDEN | #FF5252 | curious_004 | 🟢 게시 가능 |
| 3 | potato | CAUTION | #FFD93D | sit_indoor_0001 | 🟢 게시 가능 |
| 4 | naengmyeon | CAUTION | #FFD93D | sit_indoor_0002 | 🟢 게시 가능 |
| 5 | sandwich | CAUTION | #FFD93D | sit_indoor_0060 | 🟢 게시 가능 |
| 6 | cheetos | DANGER | #FF6B6B | sit_indoor_0003 | 🟢 게시 가능 |

**총 6종 24장 완성**

---

## 운영 원칙 (레드2)

> ※ 규칙 위반은 의도적 이탈로 간주하며, 시스템 오류가 아닙니다.

> ※ 이 시스템은 특정 개인이 아닌, 운영 규칙에 의해 유지됩니다.

---

## 책임 구조

| 역할 | 담당 | 권한 |
|------|------|------|
| 최종 승인 | 박세준 PD | 봉인 해제, 버전 승인 |
| 기술 총괄 | 김부장 | 지시서 작성, 검토 |
| 실행 | 최부장 | 코드 실행, 보고 |
| 검증 | 레드2 | 리스크 분석, 재발 방지 |

---

## v3.0 → v3.1 변경 이력

| 항목 | v3.0 | v3.1 |
|------|------|------|
| 제목 폰트 | Bold | **Black** |
| 서브 폰트 | Bold | **Regular** |
| 본문 제목 | 100px | **88px** |
| 서브 텍스트 | 56px | **44px** |
| 커버 제목색 | 노란색 | **#FFFFFF** |
| 커버 Y 위치 | 150px | **200px** (레퍼런스 기준) |
| 커버 그림자 | 1단 | **2단** |
| 그라데이션 | 없음 | **하단 38%** |
| 간격 | 24px | **48px** |
| CTA 배정 | 단일 고정 | **SHA256 해시 다양화** |
| 해상도 | 혼합 | **1080x1080 통일** |
| 검증 항목 | 6개 | **15개** |

---

**버전:** v3.1-stable
**상태:** 🟢 운영 중
**봉인일:** 2026-02-05
