# Project Sunshine ID 규격

> **SSOT (Single Source of Truth):** Instagram > Local Folder > Google Sheet

---

## 1. food_id

| 항목 | 설명 |
|------|------|
| **형식** | 영문 소문자 + 언더스코어 |
| **예시** | `salmon`, `sweet_potato`, `coca_cola` |
| **용도** | 음식 종류 식별 |
| **유일성** | 음식 종류당 1개 (중복 불가) |

### 명명 규칙
```
✅ 올바른 예시
- salmon
- sweet_potato
- coca_cola
- boiled_egg

❌ 잘못된 예시
- Salmon (대문자)
- sweet-potato (하이픈)
- sweetpotato (언더스코어 누락)
```

---

## 2. posted_id

| 항목 | 설명 |
|------|------|
| **형식** | `{food_id}__{instagram_shortcode}` |
| **예시** | `salmon__DUPHwxiUT7` |
| **용도** | 개별 게시물 식별 |
| **구분자** | 더블 언더스코어 (`__`) |
| **유일성** | 게시물당 1개 (중복 게시물도 개별 관리) |

### 중복 게시물 처리
```
salmon 두 번 게시 시:
- salmon__DUPHwxiUT7  (첫 번째)
- salmon__DURnSyRiZ8k (두 번째)

→ 동일 food_id도 별도 엔티티로 관리
```

### shortcode 추출
```
Instagram URL: https://www.instagram.com/p/DUPHwxiUT7/
                                          ^^^^^^^^^^^
                                          shortcode
```

---

## 3. 폴더 구조

### posted 폴더 (게시 완료)
```
contents/4_posted/YYYY-MM/{posted_id}/
예: contents/4_posted/2026-02/salmon__DUPHwxiUT7/
```

### 기타 폴더 (게시 전)
```
contents/{status}/{번호}_{food_id}_{한글명}/
예: contents/1_cover_only/032_salmon_연어/
    contents/2_body_ready/044_burdock_우엉/
```

---

## 4. 상태 구분

| status | 폴더 | 설명 |
|--------|------|------|
| `cover_only` | `1_cover_only/` | 표지만 있음 |
| `body_ready` | `2_body_ready/` | 본문 준비 완료 |
| `approved` | `3_approved/` | PD 승인 완료 |
| `posted` | `4_posted/YYYY-MM/` | Instagram 게시 완료 |

---

## 5. Google Sheet 컬럼

| 컬럼 | 필드명 | 예시 |
|------|--------|------|
| A | 번호 | 1 |
| B | food_id | salmon |
| C | 한글명 | 연어 |
| D | posted_id | salmon__DUPHwxiUT7 |
| E | status | posted |
| F | posted_at | 2026-02-01 |
| G | instagram_url | https://instagram.com/p/... |

---

## 6. SSOT 동기화 규칙

```
Instagram (진실)
    ↓
Local Folder (반영)
    ↓
Google Sheet (표시)
```

### 동기화 방향
- **Instagram → Local**: Instagram에 있으면 Local posted에 있어야 함
- **Local → Sheet**: Local 상태가 Sheet에 반영됨
- **역방향 금지**: Sheet → Local → Instagram 방향으로 수정 불가

### 충돌 시 우선순위
1. Instagram 데이터 우선
2. Local 폴더 상태 다음
3. Sheet는 항상 위 둘을 따름

---

## 7. 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|----------|--------|
| 2026-02-04 | 최초 작성 | 최부장 |

---

**작성:** 최부장
**승인:** 김부장, 박세준 PD
