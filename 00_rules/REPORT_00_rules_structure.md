# 00_rules 폴더 구조 상세 보고서

**작성일:** 2026-02-15
**작성자:** 최부장 (Claude Code)
**수신:** 김부장 (Opus)
**버전:** 2.0 (상세 버전)

---

## 1. 개요

`00_rules/` 폴더는 Project Sunshine의 **모든 규칙을 통합 관리**하는 중앙 저장소입니다.
기존 `rules/` 폴더에서 `00_rules/`로 이름을 변경하여 폴더 정렬 시 최상단에 위치하도록 했습니다.

---

## 2. 최상위 파일 (Root)

```
00_rules/
├── 00_INDEX.md          ← 규칙 인덱스 (v2.5)
├── 00_INDEX.txt
├── RULES.md             ← 헌법/최상위 규칙 (v4.2)
└── REPORT_00_rules_structure.md  ← 이 보고서
```

| 파일 | 버전 | 역할 |
|------|------|------|
| **RULES.md** | v4.2 | 헌법. 최상위 규칙. 여기 없으면 없는 것 |
| **00_INDEX.md** | v2.5 | 규칙 맵/인덱스. 작업별 참조 가이드 |

---

## 3. 01_Caption_rules/ (캡션 규칙)

### 3.1 루트 파일

```
01_Caption_rules/
├── CAPTION_RULE.md      ← 3플랫폼 통합 캡션 규칙 (v1.0)
├── CAPTION_RULE.txt
├── SAFETY_MATRIX.md     ← 안전도 정의 SSOT (v1.0)
├── SAFETY_MATRIX.txt
├── Blog/
├── Insta/
└── Thread/
```

| 파일 | 버전 | 역할 |
|------|------|------|
| CAPTION_RULE.md | v1.0 | 인스타/쓰레드/블로그 공통 캡션 규칙 |
| SAFETY_MATRIX.md | v1.0 | **SSOT** - 안전도 4등급 정의 (SAFE/CAUTION/DANGER/FORBIDDEN) |

---

### 3.2 Blog/ (블로그 캡션)

```
01_Caption_rules/Blog/
├── BLOG_RULE.md         ← 블로그 캡션 상세 규칙
├── BLOG_RULE.txt
├── GOLDEN_Blog_Caption.txt  ← 블로그 캡션 골든 샘플
├── SAFE/
│   └── Golden_Blog_Safe_Template.txt
├── CAUTION/
│   └── Golden_Blog_Caution_Template.txt
├── DANGER/
│   └── Golden_Blog_Danger_Template.txt
└── FORBIDDEN/
    └── Golden_Blog_Forbidden_Template.txt
```

---

### 3.3 Insta/ (인스타그램 캡션)

```
01_Caption_rules/Insta/
├── INSTAGRAM_RULE.md    ← 인스타그램 캡션 상세 규칙
├── INSTAGRAM_RULE.txt
├── GOLDEN_Insta_Caption.txt  ← 인스타 캡션 골든 샘플
├── SAFE/
│   └── Golden_Insta_Safe_Template.txt
├── CAUTION/
│   └── Golden_Insta_Caution_Template.txt
├── DANGER/
│   └── Golden_Insta_Danger_Template.txt
└── FORBIDDEN/
    └── Golden_Insta_Forbidden_Template.txt
```

---

### 3.4 Thread/ (쓰레드 캡션)

```
01_Caption_rules/Thread/
├── THREADS_RULE.md      ← 쓰레드 캡션 상세 규칙
├── THREADS_RULE.txt
├── GOLDEN_Thread_Caption.txt  ← 쓰레드 캡션 골든 샘플
├── SAFE/
│   └── Golden_Thread_Safe_Template.txt
├── CAUTION/
│   └── Golden_Thread_Caution_Template.txt
├── DANGER/
│   └── Golden_Thread_Danger_Template.txt
└── FORBIDDEN/
    └── Golden_Thread_Forbidden_Template.txt
```

**01_Caption_rules 총계:** 규칙 6개 + 골든 템플릿 15개 = **21개 파일**

---

## 4. 02_Image_rules/ (이미지 규칙)

### 4.1 루트 파일

```
02_Image_rules/
├── TEXT_OVERLAY_RULE.md     ← 텍스트 합성 공통 규칙 (v1.1)
├── TEXT_OVERLAY_RULE.txt
├── 01_Cover/
├── 02_Food/
├── 03_DogWithFood/
├── 08_HaetsalReal/
└── Blog_04-07/
```

| 파일 | 버전 | 역할 |
|------|------|------|
| TEXT_OVERLAY_RULE.md | v1.1 | 드롭쉐도우, 폰트, 이모지 금지 등 텍스트 합성 공통 규칙 |

---

### 4.2 01_Cover/ (표지 이미지)

```
02_Image_rules/01_Cover/
├── COVER_RULE.md            ← 표지 디자인 규칙 (v2.0)
├── COVER_RULE.txt
├── COVER_PROMPT.md          ← 표지 AI 프롬프트 (v2.0)
├── COVER_PROMPT.txt
└── Golden_Cover_Sample.png  ← 골든 샘플 이미지
```

| 파일 | 버전 | 역할 |
|------|------|------|
| COVER_RULE.md | v2.0 | 해상도 1080x1080, 한글 Y=80px/120px, 영어 Y=210px/72px |
| COVER_PROMPT.md | v2.0 | 햇살이+음식 표지 프롬프트 |
| Golden_Cover_Sample.png | - | 표지 골든 샘플 (호박) |

---

### 4.3 02_Food/ (음식 이미지)

```
02_Image_rules/02_Food/
├── FOOD_RULE.md             ← 음식 이미지 규칙
├── FOOD_RULE.txt
├── FOOD_PROMPT.md           ← 음식 AI 프롬프트
├── FOOD_PROMPT.txt
└── Golden_Food_Sample.png   ← 골든 샘플 이미지
```

| 파일 | 역할 |
|------|------|
| FOOD_RULE.md | 블로그 2장용 음식 클로즈업 이미지 규칙 |
| FOOD_PROMPT.md | AI 생성 음식 이미지 프롬프트 |
| Golden_Food_Sample.png | 음식 골든 샘플 |

---

### 4.4 03_DogWithFood/ (햇살이+음식)

```
02_Image_rules/03_DogWithFood/
├── DOG_WITH_FOOD_RULE.md        ← 햇살이+음식 규칙
├── DOG_WITH_FOOD_RULE.txt
├── DOG_WITH_FOOD_PROMPT.md      ← AI 프롬프트
├── DOG_WITH_FOOD_PROMPT.txt
└── Golden_DogWithFood_Sample.png ← 골든 샘플 이미지
```

| 파일 | 역할 |
|------|------|
| DOG_WITH_FOOD_RULE.md | 햇살이가 음식과 함께 있는 이미지 규칙 |
| DOG_WITH_FOOD_PROMPT.md | AI 생성 프롬프트 |
| Golden_DogWithFood_Sample.png | 골든 샘플 |

---

### 4.5 08_HaetsalReal/ (햇살이 실사)

```
02_Image_rules/08_HaetsalReal/
├── HAETSAL_REAL_RULE.md         ← 햇살이 실사 규칙
├── HAETSAL_REAL_RULE.txt
└── Golden_HaetsalReal_Sample.png ← 골든 샘플 이미지
```

| 파일 | 역할 |
|------|------|
| HAETSAL_REAL_RULE.md | 블로그 8장용 햇살이 실사 사진 규칙 (AI 금지) |
| Golden_HaetsalReal_Sample.png | 햇살이 실사 골든 샘플 |

---

### 4.6 Blog_04-07/ (블로그 슬라이드)

```
02_Image_rules/Blog_04-07/
├── BLOG_SLIDE_DESIGN_RULE.md    ← 슬라이드 디자인 규칙 (v2.1)
├── BLOG_SLIDE_DESIGN_RULE.txt
├── SLIDE_NAMING_BY_SAFETY.md    ← 안전도별 네이밍 규칙
├── SLIDE_NAMING_BY_SAFETY.txt
├── SAFE/                        ← SAFE 골든 샘플 5장
├── CAUTION/                     ← CAUTION 골든 샘플 5장
├── DANGER/                      ← DANGER 골든 샘플 5장
└── FORBIDDEN/                   ← FORBIDDEN 골든 샘플 5장
```

| 파일 | 버전 | 역할 |
|------|------|------|
| BLOG_SLIDE_DESIGN_RULE.md | **v2.1** | 슬라이드 03~07 디자인 규격, 색상 체계, 이모지 처리 |
| SLIDE_NAMING_BY_SAFETY.md | - | 안전도별 슬라이드 네이밍 (레드2 대응) |

---

#### 4.6.1 SAFE/ 골든 샘플

```
Blog_04-07/SAFE/
├── Golden_Blog_Safe_03_Nutrition.png   ← 영양 정보
├── Golden_Blog_Safe_04_Feeding.png     ← 급여 방법
├── Golden_Blog_Safe_05_Amount.png      ← 급여량
├── Golden_Blog_Safe_06_Caution.png     ← 주의사항
└── Golden_Blog_Safe_07_Cooking.png     ← 조리법
```

**색상 체계:** 민트 (#7ECEC1 → #A8DED2), 카드 #E8F6F3

---

#### 4.6.2 CAUTION/ 골든 샘플 (v2.1 수정 완료)

```
Blog_04-07/CAUTION/
├── Golden_Blog_CAUTION_03_Nutrition.png ← 영양 정보
├── Golden_Blog_CAUTION_04_Feeding.png   ← 급여 조건
├── Golden_Blog_CAUTION_05_Amount.png    ← 급여량 (3컬럼 TABLE)
├── Golden_Blog_CAUTION_06_Caution.png   ← 주의사항
└── Golden_Blog_CAUTION_07_Cooking.png   ← 조리법
```

**색상 체계:** 노랑 (#FFD93D → #FFE680), 카드 #FFF8E1

---

#### 4.6.3 DANGER/ 골든 샘플

```
Blog_04-07/DANGER/
├── Golden_Blog_DANGER_03_Nutrition.png  ← 영양 정보
├── Golden_Blog_DANGER_04_Risk.png       ← 위험 요소
├── Golden_Blog_DANGER_05_Symptoms.png   ← 중독 증상
├── Golden_Blog_DANGER_06_Alternative.png ← 대체 식품
└── Golden_Blog_DANGER_07_Warning.png    ← 경고
```

**색상 체계:** 빨강 (#FF6B6B → #FF9B9B), 카드 #FDE8E8

---

#### 4.6.4 FORBIDDEN/ 골든 샘플

```
Blog_04-07/FORBIDDEN/
├── Golden_Blog_FORBIDDEN_03_Toxicity.png  ← 독성 정보
├── Golden_Blog_FORBIDDEN_04_Symptoms.png  ← 중독 증상
├── Golden_Blog_FORBIDDEN_05_Emergency.png ← 응급 처치
├── Golden_Blog_FORBIDDEN_06_Alternative.png ← 대체 식품
└── Golden_Blog_FORBIDDEN_07_Warning.png   ← 경고
```

**색상 체계:** 진빨강 (#FF5252 → #FF7B7B), 카드 #FFEBEE

---

**02_Image_rules 총계:** 규칙 12개 + 골든 샘플 24개 = **36개 파일**

---

## 5. 03_Folder_rules/ (폴더/파일 관리)

```
03_Folder_rules/
├── FOLDER_STRUCTURE.md          ← 폴더 구조 규칙
├── FOLDER_STRUCTURE.txt
├── NAMING_RULE.md               ← 파일 네이밍 규칙
├── NAMING_RULE.txt
├── FILE_MANAGEMENT_RULE.md      ← 생성/백업/덮어쓰기 정책
├── FILE_MANAGEMENT_RULE.txt
├── CLOUDINARY_RULE.md           ← Cloudinary 업로드 규칙
├── CLOUDINARY_RULE.txt
├── GOLDEN_PRODUCTION_MAPPING.md ← 골든↔생산 매핑 (레드2)
└── GOLDEN_PRODUCTION_MAPPING.txt
```

| 파일 | 역할 |
|------|------|
| FOLDER_STRUCTURE.md | contents/ 폴더 구조 (1_cover_only ~ 4_posted) |
| NAMING_RULE.md | 파일 네이밍 규칙 (PascalCase, 언더스코어 등) |
| FILE_MANAGEMENT_RULE.md | 원본 보존 원칙, 백업 정책 |
| CLOUDINARY_RULE.md | 중복 업로드 금지, URL 재사용 |
| GOLDEN_PRODUCTION_MAPPING.md | 골든 샘플 → 생산 파일 매핑 (레드2 대응) |

**03_Folder_rules 총계:** **10개 파일**

---

## 6. 04_QC_rules/ (품질 검수)

```
04_QC_rules/
├── QC_CHECKLIST.md              ← 전체 QC 체크리스트
├── QC_CHECKLIST.txt
├── REJECTION_CASES.md           ← 불합격 사례 모음
├── REJECTION_CASES.txt
└── TEXT_OVERLAY_QA_RULES.md     ← 텍스트 오버레이 QA
```

| 파일 | 역할 |
|------|------|
| QC_CHECKLIST.md | 전체 QC 체크리스트 (PASS/FAIL 판정) |
| REJECTION_CASES.md | 불합격 사례 모음 (재발 방지용) |
| TEXT_OVERLAY_QA_RULES.md | 텍스트 오버레이 전용 QA 규칙 |

**04_QC_rules 총계:** **5개 파일**

---

## 7. 05_Pipeline_rules/ (파이프라인)

```
05_Pipeline_rules/
├── PIPELINE_STANDARD.md         ← 파이프라인 표준 (v2.8)
├── PIPELINE_STANDARD.txt
├── PRODUCTION_PIPELINE_RULE.md  ← 제작 파이프라인 (v1.1)
├── PRODUCTION_PIPELINE_RULE.txt
├── AGENT_STANDARD.md            ← 에이전트 표준 (v2.2)
├── AGENT_STANDARD.txt
├── SESSION_PROTOCOL.md          ← 세션 관리 규칙
└── SESSION_PROTOCOL.txt
```

| 파일 | 버전 | 역할 |
|------|------|------|
| PIPELINE_STANDARD.md | v2.8 | 전체 파이프라인 표준 |
| PRODUCTION_PIPELINE_RULE.md | v1.1 | 5단계 제작 파이프라인 |
| AGENT_STANDARD.md | v2.2 | 에이전트 행동 표준 |
| SESSION_PROTOCOL.md | - | 세션 시작/종료 프로토콜 |

**PRODUCTION_PIPELINE_RULE 5단계:**
```
[1] 규칙확인 → [2] 규칙잠금 → [3] 생성 → [4] 자가검증 → [5] 제출
```

**05_Pipeline_rules 총계:** **8개 파일**

---

## 8. 06_Version_rules/ (버전 관리)

```
06_Version_rules/
└── RULE_VERSIONING.md           ← 규칙 버전 관리 정책
```

| 파일 | 역할 |
|------|------|
| RULE_VERSIONING.md | 규칙 문서 버전 관리 정책, 변경 이력 기록 방법 |

**06_Version_rules 총계:** **1개 파일**

---

## 9. 99_rules_backup/ (레거시 백업)

```
99_rules_backup/
├── RULES_v1.0.md                ← 초기 버전 규칙
├── FOLDER_RULES_legacy.md       ← 레거시 폴더 규칙
├── PHASE2_RULES.md              ← Phase 2 규칙
├── RULES_ARCHIVE.md             ← 아카이브
└── _backup_20260214/
    ├── CAPTION_MASTER_RULE.md   ← 구 캡션 마스터 규칙
    └── CAPTION_MASTER_RULE.txt
```

| 파일 | 역할 |
|------|------|
| RULES_v1.0.md | 프로젝트 초기 버전 규칙 (히스토리용) |
| FOLDER_RULES_legacy.md | 구 폴더 규칙 |
| PHASE2_RULES.md | Phase 2 전환 시 규칙 |
| RULES_ARCHIVE.md | 아카이브된 규칙 모음 |

**99_rules_backup 총계:** **6개 파일**

---

## 10. 전체 통계

### 10.1 폴더별 파일 수

| 폴더 | 규칙 문서 | 골든 샘플 | 합계 |
|------|----------|----------|------|
| Root (00_INDEX, RULES) | 4 | 0 | 4 |
| 01_Caption_rules | 6 | 15 | 21 |
| 02_Image_rules | 12 | 24 | 36 |
| 03_Folder_rules | 10 | 0 | 10 |
| 04_QC_rules | 5 | 0 | 5 |
| 05_Pipeline_rules | 8 | 0 | 8 |
| 06_Version_rules | 1 | 0 | 1 |
| 99_rules_backup | 6 | 0 | 6 |
| **합계** | **52** | **39** | **91** |

---

### 10.2 주요 규칙 버전 현황

| 규칙 | 버전 | 최종 수정 |
|------|------|----------|
| RULES.md | v4.2 | 2026-02-12 |
| 00_INDEX.md | v2.5 | 2026-02-15 |
| COVER_RULE.md | v2.0 | 2026-02-14 |
| BLOG_SLIDE_DESIGN_RULE.md | **v2.1** | 2026-02-15 |
| TEXT_OVERLAY_RULE.md | **v1.1** | 2026-02-15 |
| CAPTION_RULE.md | v1.0 | 2026-02-14 |
| SAFETY_MATRIX.md | v1.0 | 2026-02-14 |
| PRODUCTION_PIPELINE_RULE.md | v1.1 | 2026-02-14 |
| PIPELINE_STANDARD.md | v2.8 | - |
| AGENT_STANDARD.md | v2.2 | - |

---

### 10.3 안전도별 색상 체계 (SSOT)

| 등급 | 헤더 그라데이션 | 카드 배경 | 배지 | 강조색 |
|------|-----------------|-----------|------|--------|
| SAFE | #7ECEC1 → #A8DED2 | #E8F6F3 | #4CAF50 | #4CAF50 |
| CAUTION | #FFD93D → #FFE680 | #FFF8E1 | #FFD93D | #F9A825 |
| DANGER | #FF6B6B → #FF9B9B | #FDE8E8 | #FF6B6B | #FF6B6B |
| FORBIDDEN | #FF5252 → #FF7B7B | #FFEBEE | #FF5252 | #FF5252 |

---

## 11. 최근 변경 사항 (2026-02-15)

| 변경 항목 | 내용 |
|----------|------|
| TEXT_OVERLAY_RULE.md | §6 이모지/특수문자 처리 규칙 추가 (v1.0 → v1.1) |
| BLOG_SLIDE_DESIGN_RULE.md | §9 이모지 처리, §11 체크리스트 추가 (v2.0 → v2.1) |
| CAUTION 골든 샘플 | 5장 전면 재생성 (WO-GOLDEN-SLIDE-FIX-v2 완료) |
| 00_INDEX.md | 폴더명 변경 반영 (v2.4 → v2.5) |

---

## 12. 규칙 우선순위

```
RULES.md (헌법)
    ↓
00_INDEX.md (인덱스)
    ↓
01~06 세부 폴더 규칙
    ↓
개별 설정 파일
```

**충돌 시 상위 문서가 우선한다.**

---

## 13. 결론

00_rules 폴더는 다음과 같이 체계적으로 구성되어 있습니다:

1. **계층적 구조:** Root → 6개 카테고리 폴더 + 1개 백업 폴더
2. **이중 저장:** 모든 규칙은 .md + .txt 형식으로 저장
3. **SSOT 원칙:** SAFETY_MATRIX.md가 안전도 유일 기준
4. **골든 샘플 기반:** 39개 골든 샘플 (템플릿 15개 + 이미지 24개)
5. **파이프라인 통합:** PRODUCTION_PIPELINE_RULE로 품질 관리

---

**총 파일 수:** 91개 (규칙 52개 + 골든 샘플 39개)
**총 폴더 수:** 24개 (루트 포함)

---

_보고서 작성 완료_
_최부장 (Claude Code)_
_2026-02-15_
