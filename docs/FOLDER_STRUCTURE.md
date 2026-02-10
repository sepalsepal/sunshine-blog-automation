# Folder Structure Policy

> 폴더 구조 정책 (2026-02-03 PD 확정)
> Option C 채택: 작업 중/게시 완료 분리

---

## 🔐 봉인 운영 원칙

```
1. 로컬 폴더 = 상태의 결과
   - 상태의 "원인"은 metadata / Sheets / API
   - 폴더는 결과물일 뿐 판단 근거 아님

2. posted 이동은 단방향
   - posted → contents 되돌림 ❌
   - 재작업 시 새 food_id 생성

3. 동기화 우선순위
   Instagram API > Sheets > Local metadata > Folder
```

---

## 📁 폴더 구조

```
project_sunshine/
├── content/images/     # 작업 중 (게시 전)
│   ├── 000_cover/      # 커버 이미지 전용
│   ├── 027_celery_셀러리/
│   └── ...
│
├── posted/             # 게시 완료 (월별)
│   ├── 2026-01/
│   │   ├── apple_사과/
│   │   └── banana_바나나/
│   └── 2026-02/
│       └── celery_셀러리/
│
└── archive/            # 장기 보관 (향후)
```

---

## 📛 네이밍 규칙

### content/images/ 내부
```
{번호:03d}_{food_id}_{한글명}/
예: 027_celery_셀러리/
```

### posted/ 내부
```
{YYYY-MM}/{food_id}_{한글명}/
예: 2026-02/celery_셀러리/
```

**이동 시 번호 제거:**
```
027_celery_셀러리 → celery_셀러리
```

---

## 🔄 상태 전이 및 폴더 이동

```
┌─────────────────────────────────────────────────────┐
│                   content/images/                    │
│                                                      │
│  cover_only → verified → approved → [게시]          │
│                                                      │
└─────────────────────────────────────────────────────┘
                          │
                          │ 게시 완료 시 자동 이동
                          ▼
┌─────────────────────────────────────────────────────┐
│                      posted/                         │
│                                                      │
│  2026-02/celery_셀러리/                              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📋 상태별 위치

| 상태 | 폴더 위치 | 설명 |
|------|----------|------|
| cover_only | content/images/ | 표지만 완료 |
| verified | content/images/ | 본문 완료, 승인 대기 |
| approved | content/images/ | PD 승인됨, 게시 대기 |
| rejected | content/images/ | PD 반려됨, 재생성 필요 |
| published | posted/YYYY-MM/ | 게시 완료 |

---

## 🛠️ 유틸리티 스크립트

### move_to_posted.py
```bash
# 특정 콘텐츠 이동
python utils/move_to_posted.py move celery

# 게시완료 콘텐츠 정리
python utils/move_to_posted.py cleanup

# 게시완료 목록
python utils/move_to_posted.py list
```

### sync_status.py
```bash
# 전체 동기화
python utils/sync_status.py sync

# 특정 콘텐츠 동기화
python utils/sync_status.py sync celery

# 상태별 분류
python utils/sync_status.py status

# 3중 상태 확인
python utils/sync_status.py check celery
```

---

## 🔄 자동 동기화 시점

| 시점 | 동작 | 구현 위치 |
|------|------|----------|
| /생성 명령 | 목록 표시 전 동기화 | simple_bot.py |
| 게시 완료 직후 | 즉시 posted/로 이동 | publish_gate.py |
| 매일 07:00 | 전체 동기화 | 크론잡 (TODO) |
| 매일 19:00 | 전체 동기화 | 크론잡 (TODO) |

---

## ⚠️ 금지 사항

1. **posted → contents 이동 금지**
   - 재작업 필요 시 새 food_id 생성

2. **폴더 위치로 상태 판단 금지**
   - 항상 metadata > Sheets > API 순으로 확인

3. **수동 폴더 이동 금지**
   - 반드시 스크립트 또는 봇 통해 이동

---

**작성:** 김부장
**확정:** 박세준 PD
**날짜:** 2026-02-03
