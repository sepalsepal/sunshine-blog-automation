# 파일 네이밍 규칙

## 버전: 1.0
## 최종 수정: 2026-02-14

---

## 목적

모든 파일의 일관된 네이밍 규칙을 정의한다.

---

## 규칙

### 1. PascalCase 원칙

모든 파일명과 폴더명은 PascalCase를 사용한다.

```
✅ Pumpkin_Common_01_Cover.png
✅ SweetPotato_Safe_Insta_Caption.txt
❌ pumpkin_common_01_cover.png
❌ sweet_potato_safe_insta_caption.txt
```

---

### 2. 폴더 네이밍

```
{번호}_{PascalCase음식명}

예시:
001_Pumpkin
002_Carrot
005_SweetPotato
```

---

### 3. 공통 이미지 네이밍

| 유형 | 네이밍 패턴 |
|------|----------|
| 표지 | {Food}_Common_01_Cover.png |
| 음식 사진 | {Food}_Common_02_Food.png |
| CTA | {Food}_Common_08_Cta.png |

---

### 4. 클린 소스 네이밍

```
{Food}_Cover_Clean.png
{Food}_Food_Clean.png
{Food}_Cta_Clean.png
```

---

### 5. 캡션 네이밍

```
{Food}_{Safety}_{Platform}_Caption.txt

예시:
Pumpkin_Safe_Insta_Caption.txt
Pumpkin_Safe_Thread_Caption.txt
Pumpkin_Safe_Blog_Caption.txt
Carrot_Caution_Insta_Caption.txt
```

---

### 6. 블로그 슬라이드 네이밍

```
{Food}_Blog_03_Nutrition.png    ← 영양성분
{Food}_Blog_04_Feeding.png      ← 급여방법
{Food}_Blog_05_Amount.png       ← 급여량
{Food}_Blog_06_Caution.png      ← 주의사항
{Food}_Blog_07_Cooking.png      ← 조리방법
```

---

### 7. 인스타 이미지 네이밍

```
{Food}_Insta_03_Dog.png         ← 강아지 이미지 (해당 시)
```

---

### 8. 안전도 표기

| 안전도 | 표기 |
|--------|------|
| SAFE | Safe |
| CAUTION | Caution |
| DANGER | Danger |
| FORBIDDEN | Forbidden |

---

## 금지 사항

| 금지 | 예시 |
|------|------|
| snake_case | pumpkin_cover.png |
| 공백 | Pumpkin Cover.png |
| 특수문자 | Pumpkin-Cover.png |
| 한글 | 호박_표지.png |

---

## 위반 사례

| 위반 | 사례 |
|------|------|
| 소문자 | pumpkin_common_01_cover.png |
| 언더스코어 중복 | Pumpkin__Common__01.png |
| 안전도 누락 | Pumpkin_Insta_Caption.txt |
| 번호 누락 | Pumpkin_Common_Cover.png |

---

## Validator 체크리스트

```
□ PascalCase 사용
□ 안전도 표기 일치 (food_data 기준)
□ 번호 순서 정확
□ 플랫폼 표기 정확 (Insta/Thread/Blog)
□ 확장자 정확 (.png/.txt)
□ 공백/특수문자 없음
```
