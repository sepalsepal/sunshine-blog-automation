# SYNC.md - 현재 작업 상태

**최종 업데이트:** 2026-02-06 19:01

---

## 현재 상태: 안정화 국면

---

## 금일 완료 작업

| WO번호 | 내용 | 상태 |
|--------|------|------|
| WO-2026-0206-001 | CTA 규칙 강제 패치 검토 | ✅ 완료 |
| WO-2026-0206-003 | CTA 9건 재렌더링 (v3.1) | ✅ 완료 |
| WO-2026-0206-004 | RULES.md + 레퍼런스 고정 | ✅ 완료 |
| - | BOOTSTRAP v3.1 배포 (행동 규약 추가) | ✅ 완료 |
| WO-2026-0206-006 | 커버 텍스트 수정 (5/6건) | ⚠️ 1건 대기 |
| WO-2026-0206-007 | 구글시트 P~S열 업데이트 (136건) | ✅ 완료 |
| - | Cloudinary 업로드 (body_ready 11건) + S열 전수조사 | ✅ 완료 |
| WO-2026-0206-008 | 커버 텍스트 v3.1 렌더러 적용 (5건 재렌더링) | ✅ 완료 |
| WO-2026-0206-009 | 좀비 규칙 제거 + 폴더 정리 (41개 삭제, 29개 아카이브) | ✅ 완료 |
| - | archive → clean 폴더 이름 변경 (11개 폴더) | ✅ 완료 |
| - | Git pre-commit hook 설정 (로컬→시트 자동 동기화) | ✅ 완료 |
| WO-2026-0206-010 | GOLDEN SNAPSHOT 생성 + MELTDOWN 프로토콜 | ✅ 완료 |
| - | BOOTSTRAP v3.2 배포 | ✅ 완료 |
| WO-2026-0206-012 | 구글시트 자동화 시스템 (P~R열, 승인→Cloudinary) | ✅ 완료 |
| WO-2026-0206-013 | approved 정의 확정 + 11건 정합성 복구 | ✅ 완료 |
| WO-2026-0206-014 | approved 전체 정합성 복구 (61건) + 안전도 검증 | ✅ 완료 |
| WO-2026-0206-015 | 긴급 수정 + blackberry 게시 | ✅ 완료 |
| WO-2026-0206-016 | 캡션 규칙 확정 + U열 정리 + 에러 체크 | ✅ 완료 |
| WO-2026-0206-017 | approved 불완전 26건 상태 변경 | ✅ 완료 |

---

## WO-2026-0206-017 실행 결과

### 상태 변경: 26건
- F열: approved → body_ready

### 폴더 이동: 26건
- 3_approved → 2_body_ready

### 변경된 항목 목록

| 번호 | 콘텐츠 | 미완료 항목 |
|------|--------|-------------|
| 029 | poached_egg | P, Q, R, S |
| 032 | milk | P, Q, R, S |
| 035 | potato | P, Q, R, S |
| 038 | bean_sprouts | P, Q, R, S |
| 039 | yogurt | P, Q, R, S |
| 043 | melon | P, Q, R, S |
| 047 | mackerel | P, Q, R, S |
| 052 | banana_milk | P, Q, R, S |
| 053 | garlic | P, Q, R, S |
| 058 | kimchi | P, Q, R, S |
| 059 | quail_egg | P, Q, R, S |
| 064 | kimbap | P, Q, R, S |
| 069 | naengmyeon | P, Q, R, S |
| 074 | bulgogi | P, Q, R, S |
| 075 | cake | P, Q, R, S |
| 086 | meatball | P, Q, R, S |
| 087 | bacon | P, Q, R, S |
| 091 | croissant | P, Q, R, S |
| 092 | doritos | P, Q, R, S |
| 100 | ritz | P, Q, R, S |
| 101 | skittles | P, Q, R, S |
| 107 | sprite | P, Q, R, S |
| 110 | raspberry | P, Q, R, S |
| 115 | asparagus | P, Q, R, S |
| 116 | beet | P, Q, R, S |
| 122 | duck | P, Q, R, S |

### sheet_validator 재실행 결과
- approved 불완전: **0건** ✅

---

## WO-2026-0206-016 실행 결과

### 작업 1: 캡션 규칙 RULES.md 추가
- RULES.md에 `[캡션 규칙]` 섹션 추가
- 8단계 필수 구조 정의
- 해시태그 기본 세트 정의

### 작업 2: blackberry 캡션 수정
- 캡션 파일 업데이트: `caption_instagram.txt`
- 파스타 스타일 규칙 적용

### 작업 3: U열 정리
- 헤더 변경: (비어있음) → "폴더유무"
- 이상값 수정: 12건 (approved → O)

### 작업 4: 에러 체크 스크립트
- 파일: `services/scripts/sheet_validator.py`
- 테스트 결과:
  - U열 이상값: 0건
  - approved 불완전: 26건 (정상 - 미처리 항목)
  - posted 불완전: 0건
  - 안전도 이상값: 0건
  - 폴더 불일치: 0건

---

## WO-2026-0206-015 실행 결과

### 작업 1: 029 poached_egg 폴더 이동
- **이동 경로:** `1_cover_only/` → `3_approved/`
- **U열 업데이트:** O → approved

### 작업 2: posted 항목 폴더 문제 해결
- **원인:** sync 스크립트가 `3_approved/`만 검색하고 `4_posted/`는 누락
- **수정:** 19건 U열 X → O 업데이트 (001~019 모두 `4_posted/`에 존재)

### 작업 3: blackberry 게시
- **Instagram URL:** https://www.instagram.com/p/DUaSQ7YiSE4/
- **Post ID:** 18057151556380848
- **게시 시각:** 2026-02-06 18:02:55
- **F열 업데이트:** approved → posted
- **T열 업데이트:** → 완료

---

## WO-2026-0206-014 실행 결과

### 정합성 복구

| 항목 | 수량 |
|------|------|
| 처리 대상 | 62건 |
| 성공 | 61건 |
| 에러 | 1건 (029 poached_egg - 폴더 없음) |
| 시트 업데이트 | 244셀 |

### 안전도 검증

| 분류 | 수량 |
|------|------|
| SAFE | 53건 |
| CAUTION | 36건 |
| DANGER | 21건 |
| FORBIDDEN | 16건 |

**FORBIDDEN 항목 확인 완료:**
- 022 avocado ✅ (CAUTION → FORBIDDEN 수정)
- 051 onion ✅
- 053 garlic ✅
- 055 grape ✅
- 057 chocolate ✅

> **정합성 복구 태그:** `reconciled_wo014_full_approved_fix`

---

## 폴더 상태 (WO-2026-0206-013 정합성 복구 완료)

### 2_body_ready: 비어있음

### 3_approved: 11건 이동 완료

| 번호 | 콘텐츠 | F(상태) | P | Q | R | S | U |
|------|--------|:-------:|:-:|:-:|:-:|:-:|:-:|
| 060 | fried_chicken | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 066 | jjajangmyeon | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 071 | toast | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 076 | donut | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 093 | fanta | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 096 | milkis | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 102 | soju | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 118 | lettuce | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 121 | green_beans | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 124 | peas | approved | ✅ | ✅ | ✅ | ✅ | approved |
| 126 | mushroom | approved | ✅ | ✅ | ✅ | ✅ | approved |

> **정합성 복구 태그:** `reconciled_after_definition_fix`

---

## 레퍼런스 파일

```
reference/
├── cover_reference_pasta.png    ← 커버 기준
├── cover_reference_burdock.png  ← 커버 기준
└── cta_reference.png            ← CTA 기준
```

---

## 다음 작업 (대기)

- **커버 클린소스 필요** (5건): jjajangmyeon, donut, fanta, milkis, soju
- 미완성 커버 생성 (076, 093, 096, 102, 118) - 클린소스 대기
- 미완성 CTA 생성 (121, 124)
- 신규 콘텐츠 제작 시 2_body_ready에서 시작 → approved 조건 충족 시 3_approved로 자동 이동

---

## 폴더 구조 변경

- `archive/` → `clean/` 이름 변경 완료 (11개 폴더)
- 클린소스 파일명: `{음식명}_00_source.png`
- 현행 렌더러: `cover_text_overlay_v31.py`

---

## 자동화 스크립트 (WO-2026-0206-012)

```
services/scripts/
├── sync_local_to_sheet.py     ← 기본 상태 동기화
├── check_folder_contents.py   ← P~R열 자동 체크 (캡션/메타데이터)
├── auto_cloudinary_upload.py  ← 승인→approved→Cloudinary 자동 업로드
└── full_sync_pipeline.py      ← 전체 파이프라인 통합 실행
```

**사용법:**
```bash
# 전체 파이프라인 한번 실행
python services/scripts/full_sync_pipeline.py

# 감시 모드 (30초 간격 자동 실행)
python services/scripts/full_sync_pipeline.py --watch

# git commit 시 자동 실행 (pre-commit hook 설정됨)
git commit -m "..."
```

---

## 주의사항

- 모든 규칙은 `RULES.md` 참조
- 신규 코드 작성 금지
- 레퍼런스 이미지 수정 금지
- 구버전 텍스트 스크립트 삭제됨 (v31만 유지)
- **MELTDOWN 발생 시:** `SNAPSHOT/SNAPSHOT_v3.1_GOLDEN/` 에서 복구
