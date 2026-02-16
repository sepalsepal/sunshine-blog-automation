# 폴더 구조 규칙

## 버전: 1.0
## 최종 수정: 2026-02-14

---

## 목적

프로젝트 콘텐츠 폴더의 일관된 구조를 정의한다.

---

## 규칙

### 1. 음식별 단일 폴더 원칙

**원칙:** 하나의 음식은 전체 contents 폴더에서 **단 하나의 폴더**만 가진다.

```
✅ 올바른 예:
   contents/001_Pumpkin/

❌ 잘못된 예 (중복):
   contents/1_cover_only/001_Pumpkin/
   contents/2_body_ready/001_Pumpkin/
```

**규칙:**
- 콘텐츠 진행 시 폴더를 **이동**하지 않고, 현재 위치에서 하위 폴더 추가
- 상태 변경 시 폴더 전체를 다음 단계로 이동
- 동일 번호/음식명 폴더가 여러 상태 폴더에 존재하면 **즉시 병합**

---

### 2. 플랫 + PascalCase 구조

```
contents/
├── 001_Pumpkin/
│   ├── Pumpkin_Common_01_Cover.png     ← 루트 (공통)
│   ├── Pumpkin_Common_02_Food.png      ← 루트 (공통)
│   ├── Pumpkin_Common_08_Cta.png       ← 루트 (공통)
│   ├── 00_Clean/
│   │   ├── Pumpkin_Cover_Clean.png
│   │   ├── Pumpkin_Food_Clean.png
│   │   └── Pumpkin_Cta_Clean.png
│   ├── 01_Insta&Thread/
│   │   ├── Pumpkin_Safe_Insta_Caption.txt
│   │   ├── Pumpkin_Safe_Thread_Caption.txt
│   │   └── Pumpkin_Insta_03_Dog.png
│   └── 02_Blog/
│       ├── Pumpkin_Safe_Blog_Caption.txt
│       ├── Pumpkin_Blog_03_Nutrition.png
│       ├── Pumpkin_Blog_04_Feeding.png
│       ├── Pumpkin_Blog_05_Amount.png
│       ├── Pumpkin_Blog_06_Caution.png
│       └── Pumpkin_Blog_07_Cooking.png
├── 002_Carrot/
...
└── 175_Mushroom/
```

---

### 3. 하위 폴더 구조

| 폴더 | 내용 |
|------|------|
| 00_Clean/ | 클린 소스 이미지 (배경용) |
| 01_Insta&Thread/ | 인스타+쓰레드 캡션 및 이미지 |
| 02_Blog/ | 블로그 캡션 및 슬라이드 |

---

### 4. 상태 폴더 (레거시)

```
1_cover_only/   ← 표지만 (이동 예정)
2_body_ready/   ← 본문 완료 (이동 예정)
3_approved/     ← PD 승인 (이동 예정)
4_posted/       ← 게시 완료
5_archived/     ← 비활성
```

**⚠️ 2026-02-13 이후:** 플랫 구조로 전환. 상태 폴더 사용 중단.

---

### 5. 골든 샘플 경로

**위치:** `00_rules/02_Image_rules/` (유일한 기준)

```
00_rules/02_Image_rules/
├── 01_Cover/
│   └── Golden_Cover_Sample.png       ← 표지 기준
├── 02_Food/
│   └── Golden_Food_Sample.png        ← 음식 이미지 기준
├── 03_DogWithFood/
│   └── Golden_DogWithFood_Sample.png ← 강아지+음식 기준
├── 08_HaetsalReal/
│   └── Golden_HaetsalReal_Sample.png ← 햇살이 실사 기준
└── Blog_04-07/
    ├── SAFE/Golden_Blog_Safe_03~07.png
    ├── CAUTION/Golden_Blog_CAUTION_03~07.png
    ├── DANGER/Golden_Blog_DANGER_03~07.png
    └── FORBIDDEN/Golden_Blog_FORBIDDEN_03~07.png
```

**⚠️ 절대 삭제 금지:** 이 폴더는 모든 콘텐츠의 품질 기준.
**⚠️ contents/0_Golden sample/ 폴더는 더 이상 사용하지 않음.**

---

## 위반 사례

| 위반 | 사례 |
|------|------|
| 중복 폴더 | 같은 음식이 1_cover_only와 2_body_ready에 모두 존재 |
| 네이밍 오류 | 001_pumpkin (소문자) |
| 하위 폴더 누락 | 00_Clean 없이 이미지 생성 |

---

## Validator 체크리스트

```
□ 폴더명 PascalCase (001_Pumpkin)
□ 중복 폴더 없음
□ 00_Clean/ 존재
□ 01_Insta&Thread/ 존재
□ 02_Blog/ 존재
□ 루트에 Common 파일 배치
```
