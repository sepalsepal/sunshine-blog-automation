# 📁 Project Sunshine - 폴더 구조 마스터 문서

> **운영 헌법** - 이 문서는 Project Sunshine의 뼈대입니다.
> 모든 동기화, 상태 판단, 자동화의 기준이 됩니다.

**확정일:** 2026-02-03
**확정자:** 박세준 PD + 레드2 + 김부장

---

## 🎯 핵심 원칙 (암기 필수)

### 제1원칙: 로컬 폴더 = 진실의 원천 (SSOT)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Instagram은 '사실'                                │
│   Google Sheets는 '리포트'                          │
│   로컬 폴더는 '결정'이다                             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 제2원칙: 폴더 위치가 상태다

| 위치 | 의미 | 상태 |
|------|------|------|
| `contents/` | 작업 중 | 미게시 |
| `posted/` | 게시 완료 | 게시됨 |
| `archive/` | 장기 보관 | 보관 |

**→ metadata.json, Sheets, Instagram은 전부 보조 정보**
**→ 충돌 시 로컬 폴더 위치가 정답**

### 제3원칙: 동기화 방향

```
          ┌──────────────┐
          │  로컬 폴더    │ ← 결정 (SSOT)
          │   (뼈대)     │
          └──────┬───────┘
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Sheets  │ │ metadata │ │Instagram │
│ (리포트) │ │  (로컬)  │ │  (사실)  │
└──────────┘ └──────────┘ └──────────┘
```

---

## 📁 폴더 구조

### 전체 구조

```
project_sunshine/
│
├── contents/                    # 🔥 작업 중 (큐)
│   ├── 001_beef_소고기/
│   ├── 002_kale_케일/
│   ├── 003_salmon_연어/
│   └── ...
│
├── posted/                      # ✅ 게시 완료 (아카이브)
│   ├── 2026-01/
│   │   ├── beef_소고기/
│   │   └── salmon_연어/
│   └── 2026-02/
│       ├── kale_케일/
│       └── shrimp_새우/
│
└── archive/                     # 📦 장기 보관 (6개월+)
    └── 2025-08/
        └── ...
```

---

## 📝 네이밍 규칙

### contents/ (작업 중)

```
{번호}_{food_id}_{한글명}/

예시:
001_beef_소고기/
002_kale_케일/
027_celery_셀러리/
```

| 요소 | 규칙 | 예시 |
|------|------|------|
| 번호 | 3자리 (001~999) | `001`, `027`, `100` |
| food_id | 영문 소문자 | `beef`, `kale` |
| 한글명 | 한글 표기 | `소고기`, `케일` |
| 구분자 | 언더스코어 `_` | `001_beef_소고기` |

**번호의 의미:**
- 작업 순서 / 우선순위
- `ls` 한 번에 "다음 할 일" 파악
- 큐(queue)로 작동

---

### posted/ (게시 완료)

```
{YYYY-MM}/{food_id}_{한글명}/

예시:
2026-01/beef_소고기/
2026-02/kale_케일/
```

| 요소 | 규칙 | 예시 |
|------|------|------|
| 월 폴더 | YYYY-MM 형식 | `2026-01`, `2026-02` |
| food_id | 영문 소문자 | `beef`, `kale` |
| 한글명 | 한글 표기 | `소고기`, `케일` |
| **번호** | **제거** | ~~001~~ |

**번호 제거 이유:**
- 게시 완료 후 순서 의미 없음
- 검색 기준 = food_id, 월(YYYY-MM)
- 번호는 노이즈

---

## 📄 폴더 내부 구조

### 필수 파일 (4+1)

```
{food_id}_{한글명}/
│
├── {food_id}_00.png           # 표지 (필수)
├── {food_id}_01.png           # 본문1 (필수)
├── {food_id}_02.png           # 본문2 (필수)
├── {food_id}_03.png           # CTA (필수)
│
├── metadata.json              # 상태 정보 (필수) ⭐
│
└── archive/                   # 작업 산출물 (선택)
    ├── {food_id}_00_bg.png
    ├── {food_id}_01_bg.png
    └── ...
```

### 파일 네이밍

| 파일 | 네이밍 | 용도 |
|------|--------|------|
| 표지 | `{food_id}_00.png` | 캐러셀 첫 장 |
| 본문1 | `{food_id}_01.png` | 정보 슬라이드 1 |
| 본문2 | `{food_id}_02.png` | 정보 슬라이드 2 |
| CTA | `{food_id}_03.png` | 저장/공유 유도 |
| 메타 | `metadata.json` | 상태/이력 정보 |

### 금지 사항

```
❌ 메인 폴더에 _bg.png, _draft, _temp 파일
❌ 파이널 4장 외 다른 이미지
❌ metadata.json 없는 폴더
```

---

## 📊 metadata.json 스키마

### 필수 필드

```json
{
  "food_id": "beef",
  "food_name_ko": "소고기",
  "safety_level": "SAFE",
  "color_code": "#4CAF50",

  "status": "verified",
  "pd_approved": false,
  "approved_at": null,
  "approved_by": null,

  "rule_name": "cover_v1",
  "rule_version": "1.0.0",
  "rule_hash": "1b1c6f1a23f68664",

  "created_at": "2026-02-01T10:00:00",
  "verified_at": "2026-02-01T12:00:00",
  "posted_at": null,

  "instagram_media_id": null,
  "instagram_url": null,

  "sheets_synced_at": "2026-02-01T12:00:00"
}
```

### 상태값 정의

| status | 의미 | 폴더 위치 |
|--------|------|----------|
| `cover_only` | 표지만 완료 | contents/ |
| `verified` | 본문 완료, 검증 통과 | contents/ |
| `approved` | PD 승인 완료 | contents/ |
| `posted` | 게시 완료 | posted/ |
| `rejected` | PD 반려 | contents/ |

---

## 🔄 상태 전이

### 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                      contents/                              │
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐        │
│  │ cover_only │ ─→ │  verified  │ ─→ │  approved  │        │
│  └────────────┘    └─────┬──────┘    └──────┬─────┘        │
│                          │                  │               │
│                     [PD 반려]          [게시 실행]          │
│                          │                  │               │
│                          ▼                  │               │
│                    ┌──────────┐             │               │
│                    │ rejected │             │               │
│                    └──────────┘             │               │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                                              ▼ 폴더 이동
┌─────────────────────────────────────────────────────────────┐
│                      posted/YYYY-MM/                        │
│                                                             │
│                       ┌────────────┐                        │
│                       │   posted   │                        │
│                       └────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 전이 규칙

| 현재 | 다음 | 트리거 | 폴더 변화 |
|------|------|--------|----------|
| cover_only | verified | 본문 생성 완료 | 없음 |
| verified | approved | PD 승인 | 없음 |
| verified | rejected | PD 반려 | 없음 |
| approved | posted | Instagram 게시 | contents/ → posted/ |
| rejected | cover_only | 재생성 | 없음 |

### 금지된 전이

```
❌ posted → approved (되돌림 금지)
❌ posted → contents/ (폴더 역이동 금지)
❌ 자동 승인 (approved는 반드시 PD만)
```

---

## 🔐 동기화 규칙

### 우선순위 (충돌 시)

```
1순위: 로컬 폴더 위치 (결정)
2순위: metadata.json (로컬 상태)
3순위: Google Sheets (리포트)
4순위: Instagram API (사실 확인)
```

### 동기화 방향

```
[로컬 폴더]
    │
    ├──→ [metadata.json] 업데이트
    │
    ├──→ [Google Sheets] 동기화
    │
    └──→ [Instagram] 확인 (읽기만)
```

### 불일치 처리

| 상황 | 처리 |
|------|------|
| 폴더는 contents/, Sheets는 posted | → Sheets를 contents로 수정 |
| 폴더는 posted/, Sheets는 verified | → Sheets를 posted로 수정 |
| Instagram 게시됨, 폴더는 contents/ | → 폴더를 posted/로 이동 |

**예외: Instagram에 실제 게시된 경우만 폴더 이동**

---

## 🔧 운영 명령어

### 텔레그램

| 명령어 | 동작 |
|--------|------|
| `/생성` | 작업 메뉴 표시 |
| `/상태` | 전체 현황 |
| `/전체동기화` | Instagram 기준 일괄 정리 |
| `{food_id} 동기화` | 단일 콘텐츠 동기화 |
| `{food_id} 승인` | PD 승인 |
| `{food_id} 반려` | PD 반려 |

### 터미널

```bash
# 전체 동기화
python scripts/full_sync.py

# 단일 콘텐츠 동기화
python scripts/sync_single.py beef

# 폴더 정리 (posted 이동)
python scripts/cleanup_posted.py
```

---

## ✅ 체크리스트

### 폴더 생성 시

- [ ] 번호_영문_한글 네이밍 준수
- [ ] metadata.json 생성
- [ ] 파이널 이미지 4장 확인
- [ ] archive/ 폴더에 작업물 정리

### 게시 완료 시

- [ ] posted/YYYY-MM/ 폴더로 이동
- [ ] 번호 제거 (001_beef → beef)
- [ ] metadata.json status="posted" 업데이트
- [ ] Google Sheets 동기화
- [ ] archive/ 폴더 삭제 (선택)

---

## 📌 자주 하는 실수

| 실수 | 올바른 방법 |
|------|------------|
| Sheets 보고 상태 판단 | 폴더 위치로 판단 |
| posted 폴더에 번호 남김 | 번호 제거 |
| metadata.json 없이 폴더 생성 | 반드시 함께 생성 |
| 작업 파일을 메인에 남김 | archive/로 이동 |
| posted → contents 되돌림 | 새 food_id로 재생성 |

---

## 📜 변경 이력

| 버전 | 날짜 | 변경 내용 | 승인자 |
|------|------|----------|--------|
| 1.0 | 2026-02-03 | 최초 작성 | PD + 레드2 + 김부장 |

---

**이 문서는 Project Sunshine의 운영 헌법입니다.**
**수정 시 반드시 PD 승인이 필요합니다.**

---

작성: 김부장 (Claude Opus 4.5)
검토: 레드2
확정: 박세준 PD
